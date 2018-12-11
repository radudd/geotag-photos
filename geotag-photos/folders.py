#/usr/bin/env python
import logger
import os

log = logger.generate_logger()
location = {
 "Areas": {
  "Praslin": {
   "Ferdinand Nature Reserve": 18,
   "Fond Ferdinand Nature Reserve (Guided tours at 9:30, 11:00 & 12:30)": 1,
   "CatCocos Praslin Office": 1,
   "Fond Ferdinand Nature Reserve": 1
  },
  "La Digue": {
   "La Digue Ferry Terminal": 1
  }
 },
 "Country": "Seychelles"
}
directory = '2018_09_10'

"""Based on the dictionary of locations returned by photos.geotag_dir(), generate a folder name

  Args: 
     locations dictionary, directory name

  Returns:
     new directory name in format: Seychelles - Praslin (Ferdinand Nature Reserve, CatCocos), La Digue
"""  
def _generate_name(locations, directory):
    if locations is None:
        return None
    country = locations['Country']
    areas_orig = locations['Areas']
    areas = []
    for area,places_orig in areas_orig.items():
        places = [place for place,count in places_orig.items() if count >= 3]
        if len(places) > 0:
            areas.append(area + ' (' + ', '.join(places) + ')')
        else:
            areas.append(area)
    new_name = directory + " " + country + " - " + ', '.join(areas) if country else directory + " " + ', '.join(areas)
    return new_name

"""Rename the folders with the name computed by the generate_name function
  
   Args:
        directory: absolute path of the directory
        directory_original_name: original absolut path of the directory in format yyyy_mm_dd
        location: location dictionary computed by geotag_dir()

   Returns:
        True or False 
"""
def rename(directory, directory_original_name, location, dry_run=False):
    directory_new_name = _generate_name(location,directory_original_name)
    if directory_new_name == None:
        return None
    log.warning(directory + ' -> ' + directory_new_name)
    if not dry_run:
        try:
            os.rename(directory, directory_new_name)
            return True
        except OSError as e:
            log.error("Error by renaming: " + e)
            return False