"""
Helper functions for tests written for the candidate_service
"""
import time

# Third party
import pycountry as pc

# Models
from candidate_service.common.models.user import Permission



def check_for_id(_dict):
    """
    Checks for id-key in candidate_dict and all its nested objects that must have an id-key
    :type _dict:    dict
    :return False if an id-key is missing in candidate_dict or any of its nested objects
    """
    assert isinstance(_dict, dict)
    # Get top level keys
    top_level_keys = _dict.keys()

    # Top level dict must have an id-key
    if not 'id' in top_level_keys:
        return False

    # Remove id-key from top level keys
    top_level_keys.remove('id')

    # Remove contact_history key since it will not have an id-key to begin with
    if 'contact_history' in top_level_keys:
        top_level_keys.remove('contact_history')
    if 'talent_pool_ids' in top_level_keys:
        top_level_keys.remove('talent_pool_ids')

    for key in top_level_keys:
        obj = _dict[key]
        if isinstance(obj, dict):
            # If obj is an empty dict, e.g. obj = {}, continue with the loop
            if not any(obj):
                continue

            check = id_exists(_dict=obj)
            if check is False:
                return check

        if isinstance(obj, list):
            list_of_dicts = obj
            for dictionary in list_of_dicts:
                # Invoke function again if any of dictionary's key's value is a list-of-objects
                for _key in dictionary:
                    if type(dictionary[_key]) == list:
                        for i in range(0, len(dictionary[_key])):
                            check = check_for_id(_dict=dictionary[_key][i])  # recurse
                            if check is False:
                                return check

                check = id_exists(_dict=dictionary)
                if check is False:
                    return check


def id_exists(_dict):
    """
    :return True if id-key is found in _dict, otherwise False
    """
    assert isinstance(_dict, dict)
    check = True
    # Get _dict's keys
    keys = _dict.keys()

    # Ensure id-key exists
    if not 'id' in keys:
        check = False

    return check


def remove_id_key(_dict):
    """
    Function removes the id-key from candidate_dict and all its nested objects
    """
    # Remove contact_history key since it will not have an id-key to begin with
    if 'contact_history' in _dict:
        del _dict['contact_history']
    if 'talent_pool_ids' in _dict:
        del _dict['talent_pool_ids']

    # Remove id-key from top level dict
    if 'id' in _dict:
        del _dict['id']

    # Get dict-keys
    keys = _dict.keys()

    for key in keys:
        obj = _dict[key]

        if isinstance(obj, dict):
            # If obj is an empty dict, e.g. obj = {}, continue with the loop
            if not any(obj):
                continue
            # Remove id-key if found
            if 'id' in obj:
                del obj['id']

        if isinstance(obj, list):
            list_of_dicts = obj
            for dictionary in list_of_dicts:
                # Remove id-key from each dictionary
                if 'id' in dictionary:
                    del dictionary['id']

                # Invoke function again if any of dictionary's key's value is a list-of-objects
                for _key in dictionary:
                    if isinstance(dictionary[_key], list):
                        for i in range(0, len(dictionary[_key])):
                            remove_id_key(_dict=dictionary[_key][i])  # recurse
    return _dict


def get_country_code_from_name(country_name):
    """
    Example: 'United States' = 'US'
    """
    try:
        country = pc.countries.get(name=country_name)
    except KeyError:
        return
    return country.alpha2


def get_int_version(x):
    """
    Function will only return input if it's an integer convertible
    :rtype:  int
    """
    try:
        return int(float(x))
    except ValueError:
        pass
    except TypeError:
        pass


def order_military_services(military_services_data):
    """
    Function will change the order of military services data based on its to_date value
    :param military_services_data: collection of candidate's military service information
    :type  military_services_data: list[dict]
    """
    # No need to order collection if only one dict is provided
    if len(military_services_data) <= 1:
        return military_services_data

    position_taken = 0  # starting position in list
    to_date = military_services_data[0].get('to_date') or '0000-00-00'

    for i, military_service in enumerate(military_services_data):
        to_date_value = military_service.get('to_date')
        if to_date_value and to_date_value > to_date:
            military_services_data.insert(position_taken, military_services_data.pop(i))
            position_taken += 1
            to_date = to_date_value

    return military_services_data


def order_work_experiences(work_experiences_data):
    """
    Function will change the order of work experiences data based on the following priorities:
      1. is current
      2. start year
      3. start month
    :param work_experiences_data: collection of candidate's work experiences
    :type  work_experiences_data: list[dict]
    """
    # No need to order collection if only one dict is provided
    if len(work_experiences_data) <= 1:
        return work_experiences_data

    # Move experience to first position if it's a current position
    start_year, start_month = work_experiences_data[0]['start_year'], work_experiences_data[0]['start_month']
    position_taken = 0
    for i, experience in enumerate(work_experiences_data):

        if experience.get('is_current') is True:
            work_experiences_data.insert(position_taken, work_experiences_data.pop(i))
            position_taken += 1
            continue  # Assume at most one of the experiences is current

        if experience.get('start_year') < start_year and experience.get('start_month') < start_month:
            start_year = experience.get('start_year')
            start_month = experience.get('start_month')
            work_experiences_data.insert(position_taken, work_experiences_data.pop(i))
            position_taken += 1

        elif experience.get('start_year') == start_year and experience.get('start_month') < start_month:
            start_month = experience.get('start_month')
            work_experiences_data.insert(position_taken, work_experiences_data.pop(i))
            position_taken += 1

    return work_experiences_data
