#!/usr/local/bin/python3

import exiftool
import yaml
import json
import os
import os.path
import glob
import sys
import subprocess
import argparse
import re
import hashlib
import geolocation
import folders
import requests
import time
import logging
from fake_useragent import UserAgent
from cache import Cache
from mongo import MongoConnector
from pymongo import errors as pymongo_errors
from requests import HTTPError
from bson import json_util
from collections import defaultdict,Counter,deque
from config import log


def compute_checksum(directory):
    """ Returns the checksum of the directory computed by calculating the md5 of "ls -t". 
    (Since the computing and aggregation of checksum for all files in the directory is to expensive, then dirhash will not be used)

    Args: 
        directory: full path of the directory
    Returns:
        directory checksum
    """
    log.info ("Calculating checksum for {} directory...".format(directory))
    #return dirhash(self.directory, 'md5', excluded_files=['@eaDir','.DS_Store'])
    ls_files = subprocess.run(['ls','-tr',directory],capture_output=True)
    return hashlib.md5(ls_files.stdout).hexdigest()

@Cache(cache=loaded_cache, maxsize=1024)
def get_metadata(directory):
    """ Get pictures metadata in using exiftool. The extraction is done per directory

        Args:
            directory: full path of the directory
        Returns:
            dictionary having the files as keys and files metadata as values.
    """ 
    files_list = glob.glob(directory + '/*')
    with exiftool.ExifTool() as et:
        log.info ("Getting picture metadata from files...")
        try:
            return et.get_metadata_batch(files_list)
        except OSError as e:
            log.error (str(e))

@Cache(cache=loaded_cache, maxsize=1024)
def openmaps_response(latitude, longitude):
    with open('config.yaml', 'r') as fh:
        config = yaml.load(fh)
    openmaps_base_url = config['openmaps_base_url']
    request_payload = {'lat': latitude, 'lon': longitude}
    # Create a fake User Agent for the requests
    request_headers = {'User-Agent': UserAgent().firefox} 

    response = requests.get(openmaps_base_url, params=request_payload, headers=request_headers)
    response.raise_for_status()
    return response

def geotag_dir(directory, skip_db=False):
    """ Computes 'locations' dictionary of the folder 

        Args:
            directory: absolute path of the photos directory
            force: if database check to be skipped and the checked to be performed anyway. Default: False
        Returns:
            locations dictionary
        Ex:
        {
            "Country": "Romania"
            "Areas": { 
                "Bucharest": ["Piata Unirii", "Piata Romana"] },
                "Roman": ["Primarie"] 
                }
        }
    """
    # Get basename for the directory name and also get the basename of its original name (yyyy_mm_dd)
    directory_original_name = re.sub(r'(\d{4}_\d{2}_\d{2}).*','\\1',directory)
    directory_date = os.path.basename(directory_original_name)
    directory_base = os.path.basename(directory)

    # Check if directory has already an entry in DB. This can be skipped and check can be forced by adding "force" as the second argument
    # Get checksum of the directory. Needed whether the check is forced or not, because needs to be either checked or stored in the DB
    directory_checksum = compute_checksum(directory)
    if not skip_db:
        locations = load_from_db(directory, directory_checksum)
        if locations is not None:
            return (directory_original_name, locations)
    # If not in DB, continue
    # Areas dict should be a defaultdict with the default element as Counter (to count the appereance of each Name)
    locations = {}   
    locations['Areas'] = defaultdict(Counter)     
    
    # Create a set to store all the URLs
    openmaps_urls = set()

    # Get the pictures metadata
    exiftools_metadata = get_metadata(directory)

    # Loop through pictures and get their location
    log.info ("Calling OpenMaps API to retrieve location information...")
    for picture in exiftools_metadata:
        try:
            latitude = picture['Composite:GPSLatitude']
            longitude = picture['Composite:GPSLongitude']
            response = openmaps_response(latitude, longitude)
            location = geolocation.compute(response.json())
            openmaps_urls.add(response.url)

            # Add Country to the locations dict
            if 'Country' not in locations:
                locations['Country'] = location['Country'] 
            # Add Area to locations dict
            if not locations['Areas']:
                locations['Areas'][location['Area']]
            # Add Areas and Places to locations. To each place key, add each "Place" which belongs to and its occurence
            if location['Place']:
                locations['Areas'][location['Area']].update([location['Place']])
            
            
        except HTTPError as e:
            log.error (str(e))
        except KeyError as e:
            pass

    # If country not in locations for all the files, we assume there was no valid response -> locations = None
    if 'Country' not in locations:
        locations = None
    # To be able to serialize/insert to URLs DB, convert the set to list
    openmaps_urls = list(openmaps_urls)

    if not skip_db:
        store_to_db(directory_date, directory_base, directory_checksum, 
                    exiftools_metadata, openmaps_urls, locations)

    # Return a tuple containing original directory name and the computed location
    return (directory_original_name, locations)
    #log.debug (json.dumps(locations,indent=1))


def load_from_db(directory, directory_checksum):
    """ Checks if the directory location information is already stored in the DB. 
        Checksum is also computed and compares with the one stored in the DB, in case there are changes in the directory

        Args:
            directory: absolute path of the photo directory
            directory_checksum: computed checksum of the directory
        Returns:
            database content corresponding to 'locations' key of the directory - if present
            None - if not present
    """ 
    try:
        with MongoConnector() as mongo:
            directory_base = os.path.basename(directory)
            # Check if and entry with the directory name is present in DB
            db_dir_metadata = mongo.find_one({'directory': directory_base}) or None
            # Check if directory has an entry in the db and if so if the checksum from db is the same as the computed one
            if db_dir_metadata and directory_checksum == db_dir_metadata['directory_checksum']:
                log.info ("Loading data from DB...")
                #log.debug (json.dumps(db_dir_metadata['locations'],indent=1))
                return db_dir_metadata['locations']
            return None
    except KeyError as e:
        log.warning("Check DB structure! Key {} is missing. Re-computing result!".format(e))
    except Exception as e:
        log.error (e)


def store_to_db(directory_date, directory_base, directory_checksum, exiftools_metadata, openmaps_urls, locations):
    """ Stores date, directory name, directory checksum, exiftool metadata, openmaps URLs and locations dictionary in the databaase

        Args:
            directory_date: directory original name containing just the date in format yyyy_mm_dd
            directory_base: basename of the photo directory
            directory_checksum: computed checksum of the directory
            exiftools_metadata: photos metadata
            openmaps_urls: list containing all the called openmaps URLs for this directory
            locations: dictionary containing the locations 
        Returns:
            True - if successfull; None - if exception occurs
    """ 
    try:
        with MongoConnector() as mongo:
            db_entry = {
                    "date": directory_date,
                    "directory": directory_base,
                    "directory_checksum": directory_checksum,
                    "exiftools_metadata": exiftools_metadata,
                    "openmaps_urls": openmaps_urls,
                    "locations": locations 
                    }
            if mongo.find_one({"date": directory_date}):
                mongo.update({"date": directory_date}, {"$set": db_entry})
            else:
                mongo.insert(db_entry)
            return True
    except pymongo_errors.DuplicateKeyError as py_e:
        log.info("Cannot insert {} in the DB: {}".format(db_entry,str(py_e)))

def main():
    with open('config.yaml', 'r') as fh:
        config = yaml.load(fh)
    
    # Add arguments for program
    # --force : geotag check to be peformed no matter if entry is stored in the DB
    # --directory PHOTO_DIR: directory to be checked. If not provided, the value from vars.yml will be used
    parser = argparse.ArgumentParser()
    parser.add_argument("--skipdb", help="don't check db for results", action="store_true", default=False)
    parser.add_argument("--directory", help="directory to be geotagged")
    args = parser.parse_args()

    directory = args.directory or config['directory']
    skip_db = args.skipdb

    locations = geotag_dir(directory, skip_db)
    logging.info (json.dumps(locations,indent=1))

if __name__ == "__main__":
    main()