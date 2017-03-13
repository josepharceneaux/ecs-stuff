__author__ = 'erikfarmer'
from widget_service.app import db
from widget_service.app import logger
from widget_service.common.models.misc import AreaOfInterest
from widget_service.common.models.misc import CustomField


def parse_interest_ids_from_form(interests_string, domain_id):
    """Converts tag-manager input string into usable format for candidate dict.
    :param interests_string: (string) String in format:
        "<Master_Category>: <Sub_category or 'All Subcategories'>|
         <Master_Category>: <Sub_category or 'All Subcategories'>"
    :return: a list of dictionaries containing usable ids for a candidate object
    """
    processed_interest_ids = []
    raw_interests = interests_string.split('|')
    for interest in raw_interests:
        category, subcategory = interest.split(':')
        subcategory = subcategory.lstrip()
        interest_to_query = category if subcategory == 'All Subcategories' else subcategory
        aoi = db.session.query(AreaOfInterest.id).filter(AreaOfInterest.name == interest_to_query,
                                                         AreaOfInterest.domain_id == domain_id).first()
        if aoi:
            processed_interest_ids.append({'area_of_interest_id': aoi.id})
        else:
            logger.error("WidgetService::Error Interest id for {} not found within domain {} ".format(interest_to_query,
                                                                                                      domain_id))
    return processed_interest_ids


def parse_city_and_state_ids_from_form(locations_string):
    """Converts tag-manager input string into usable format for candidate dict.
    :param locations_string: (string) String in format:
        "<Region>: <sub_region or 'All Cities'>|
         <Region>: <sub_region or 'All Cities'>"
    :return: a list of dictionaries containing usable location ids for a candidate object
    """
    processed_locations = []
    raw_locations = locations_string.split('|')
    for location in raw_locations:
        state, city = location.split(':')
        city = city.lstrip()
        processed_locations.append({'city': city, 'state': state})
    return processed_locations


def process_city_and_state_from_fields(city, state):
    processed_locations = []
    processed_locations.append({'city': city, 'state': state})
    return processed_locations
