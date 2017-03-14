__author__ = 'erikfarmer'
from widget_service.app import db
from widget_service.app import logger
from widget_service.common.models.misc import AreaOfInterest, CustomField


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


def parse_city_and_state_ids_from_form(locations_string, domain_id):
    """Converts tag-manager input string into usable format for candidate dict.
    :param locations_string: (string) String in format:
        "<Region>: <sub_region or 'All Cities'>|
         <Region>: <sub_region or 'All Cities'>"
    :return: a list of dictionaries containing usable location ids for a candidate object
    """
    processed_locations = []
    state_cf_id, city_cf_id = get_domain_state_and_city_custom_fields(domain_id)
    if state_cf_id is None or city_cf_id is None:
        return processed_locations

    raw_locations = locations_string.split('|')
    for location in raw_locations:
        state, city = location.split(':')
        city = city.lstrip()
        processed_locations.extend([{
            'custom_field_id': state_cf_id.id,
            'value': state
        }, {
            'custom_field_id': city_cf_id.id,
            'value': city
        }])
    return processed_locations


def process_city_and_state_from_fields(city, state, domain_id):
    processed_locations = []
    state_cf_id, city_cf_id = get_domain_state_and_city_custom_fields(domain_id)
    if state_cf_id is None or city_cf_id is None:
        return processed_locations

    processed_locations.extend([{
        'custom_field_id': state_cf_id.id,
        'value': state
    }, {
        'custom_field_id': city_cf_id.id,
        'value': city
    }])
    return processed_locations


def get_domain_state_and_city_custom_fields(domain_id):
    state_custom_field = db.session.query(CustomField).filter(CustomField.domain_id == domain_id,
                                                              CustomField.name == 'State of Interest').first()
    city_custom_field = db.session.query(CustomField).filter(CustomField.domain_id == domain_id,
                                                             CustomField.name == 'City of Interest').first()
    if state_custom_field is None or city_custom_field is None:
        logger.error(
            'WidgetService::Error Domain - {} is missing CustomField City/State of interesrt'.format(domain_id))
        return None, None

    return state_custom_field.id, city_custom_field.id
