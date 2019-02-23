import yaml
import json
import unidecode
import requests
import sys
import time
import logger
from config import log


def _set_dict(orig_attr, orig_dict, result_attr, result_dict):
    if orig_attr not in orig_dict or orig_dict[orig_attr] is None:
        result_dict[result_attr] = None
        return False
    try:
        result_dict[result_attr] = unidecode.unidecode(
            orig_dict[orig_attr].replace('.', ''))
    except:
        log.warning("Cannot encode {} to ASCII. Skipping...".format(
            orig_dict[orig_attr]))
    return True


def _set_attributes(location_dict, area, *args):
    """
    This function sets 'Area' and 'Place'. The first argument is
    the target dictionary. The second argument is the candidate for Area ->
    if this argument is null, then the function exits. The next arguments
    are candidates for Places in the priority order. The first match
    will be set to 'Place'. If none matches, then the function
    will set just the 'Area'.
    """
    # If 'Area' is set or the candidate argument is None then function exits. 
    # If it doesn't, then set it to the value of it
    if 'Area' in location_dict or location_dict[area] is None:
        return False
    location_dict['Area'] = location_dict[area]
    # Check if argument by argument exists and if so, set the 'Place' 
    # to its value. If not, set it to None
    for place in args:
        if location_dict[place] is not None: 
            location_dict['Place'] = location_dict[place]
        return True
    location_dict['Place'] = None
    return True


def compute(openmaps_response):
    # based on the openmaps_response_json, add results to location dict
    # default attributes which don't exist to None, as there many
    # inconsistencies. The _attrib are temporary attributes which will be used
    # just for logic in the set_attributes function the capital Atrributes
    # are the ones needed later
    stored_location = {}

    _set_dict('name', openmaps_response, '_name', stored_location)
    _set_dict('city', openmaps_response['address'], '_city', stored_location)
    _set_dict('town', openmaps_response['address'], '_town', stored_location)
    _set_dict(
        'neighbourhood', openmaps_response['address'],
        '_neighbourhood', stored_location)
    _set_dict('state', openmaps_response['address'], '_state', stored_location)
    _set_dict(
        'state_district', openmaps_response['address'],
        '_state_district', stored_location)
    _set_dict(
        'county', openmaps_response['address'], '_county', stored_location)
    _set_dict(
        'village', openmaps_response['address'], '_village', stored_location)

    # No logic for Country - just set it now already
    _set_dict(
        'country', openmaps_response['address'], 'Country', stored_location)

    """
    Logic and options
    """
    if 'error' not in openmaps_response:
        _set_attributes(stored_location, '_city', '_name', '_neighbourhood')
        _set_attributes(stored_location, '_town', '_name')
        _set_attributes(
            stored_location, '_state', '_state_district', '_name', '_county')
        _set_attributes(stored_location, '_county', '_name', '_village')

        return stored_location


if __name__ == "__main__":
    # This will moved to the pytests
    # This function should contain just the main
    if len(sys.argv) >= 2:
        try:
            [lat, lon] = sys.argv[1].split(",")
        except KeyError as e:
            log.error("Key {} not found".format(str(e)))
    else:
        log.warning("Please provide the latitude and longitude as a sinle parameter \
            separated by comma(,)\n EX: python3 openmaps.py lat,long")
