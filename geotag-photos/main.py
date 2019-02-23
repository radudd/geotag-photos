#!/usr/bin/env python

import glob
import yaml
import os.path
import sys
import json
import itertools

import photos
import folders
from cache import DiskCache
from config import logger, config, mongo


"""
One method would be to populate the database with the metadata of all folders.
It will have to options: one to check everything(for the first run)
and one to check starting with a specific year.
This is configurable in the vars.yaml file in start_year
"""


def filter(year):
    return [fn for fn in glob.iglob(
        "{}/*".format(year)) if not os.path.basename(fn).startswith('@eaDir')]
    # itertools.chain.from_iterable() - will be used to flatten the list later.
    # ie. combining all folders from all years in a single list


def get_folders():
    if not os.path.isdir(config['photos_path']):
        raise OSError
    if config['start_year'] == 'all':
        years = glob.glob("{}20*".format(config['photos_path']))
        folders_tbc = [glob.glob(filter(year)) for year in years]
        return list(itertools.chain.from_iterable(folders_tbc))

    # First extract all year folders and convert them in int
    # in order to compare with the start_year var
    all_years_folders = [int(os.path.basename(i)) for i in glob.glob(
        "{}/20*".format(config['photos_path']))]
    try:
        int_years_tbc = [year for year in all_years_folders if year >= int(
            config['start_year'])]
    except ValueError:
        sys.exit(1)

    years_tbc = [config['photos_path'] + str(year) for year in int_years_tbc]
    folders_tbc = [(filter(year)) for year in years_tbc]
    return list(itertools.chain.from_iterable(folders_tbc))


def rename_folder(folder, skip_db, openmaps_cache):
    folder_original_name, location, openmaps_cache = \
        photos.geotag_dir(folder, skip_db, openmaps_cache)
    folders.rename(folder, folder_original_name, location, dry_run=True)

if __name__ == "__main__":
    try:
        folders_to_check = get_folders()
        skip_db = False
        if not mongo:
            log.error("DB error: {}".format(e))
            skip_db = True
    except OSError as e:
        log.error(
            "No files in directory {} or directory not reachable".format(
                config['photos_path']))
        sys.exit(e.errno)

    openmaps_cache = {}
    for folder in folders_to_check:
        rename_folder(folder, skip_db, openmaps_cache)
    # Write to DiskCache
    DiskCache('.cache_openmaps.yaml').persist(openmaps_cache)

    # add force argument for geotag_dir
