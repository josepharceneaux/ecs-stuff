__author__ = 'erikfarmer'

from widget_service.common.models.misc import CustomField
from widget_service.common.models.widget import WidgetPage
from widget_service.app import db, logger
from widget_service.common.models.misc import AreaOfInterest


def parse_interest_ids_from_form(interests_string, domain_id):
    """Converts tag-manager input string into usable format for candidate dict.
    :param interests_string: (string) String in format:
        "<Master_Category>: <Sub_category or 'All Subcategories'>|
         <Master_Category>: <Sub_category or 'All Subcategories'>"
    :return: a list of dictionaries containing usable ids for a candidate object
    """
    processed_interest_ids = []
    raw_interests = interests_string.split('|')
    logger.debug('WE HAVE RAW INTERESTS {}'.format(raw_interests))
    for interest in raw_interests:
        category, subcategory = interest.split(':')
        subcategory = subcategory.lstrip()
        interest_to_query = category if subcategory == 'All Subcategories' else subcategory
        # TODO handle None
        processed_interest_ids.append(
            {'area_of_interest_id': db.session.query(AreaOfInterest.id).filter(
                AreaOfInterest.name==interest_to_query, AreaOfInterest.domain_id==domain_id).first().id})
    return processed_interest_ids


def parse_city_and_state_ids_from_form(locations_string, domain_id):
    """Converts tag-manager input string into usable format for candidate dict.
    :param locations_string: (string) String in format:
        "<Region>: <sub_region or 'All Cities'>|
         <Region>: <sub_region or 'All Cities'>"
    :return: a list of dictionaries containing usable location ids for a candidate object
    """
    processed_location_ids = []
    state_custom_field_id = db.session.query(CustomField).filter(
        CustomField.name=='State of Interest', CustomField.domain_id==domain_id).first().id
    city_custom_field_id = db.session.query(CustomField).filter(
        CustomField.name=='City of Interest', CustomField.domain_id==domain_id).first().id
    raw_locations = locations_string.split('|')
    for location in raw_locations:
        state, city = location.split(':')
        city = city.lstrip()
        if city == 'All Cities':
            processed_location_ids.append({'custom_field_id': state_custom_field_id, 'value': state})
        else:
            processed_location_ids.append({'custom_field_id': city_custom_field_id, 'value': city})
    return processed_location_ids


def process_city_and_state_from_fields(city, state, domain_id):
    processed_location_ids = []
    state_custom_field_id = db.session.query(CustomField).filter(
        CustomField.name=='State of Interest', CustomField.domain_id==domain_id).first().id
    city_custom_field_id = db.session.query(CustomField).filter(
        CustomField.name=='City of Interest', CustomField.domain_id==domain_id).first().id
    processed_location_ids.append({'custom_field_id': state_custom_field_id, 'value': state})
    processed_location_ids.append({'custom_field_id': city_custom_field_id, 'value': city})
    return processed_location_ids


def create_candidate_educations_dict(major, degree, school_name, grad_date):
    return {
        'school_name': school_name,
        'degrees': [
            {
                'type': degree,
                'title': major,
                'end_year': grad_date.split(' ')[1],
                'degree_bullets': []
            }
        ]
    }


def get_widget_user_from_unique_key(unique_key):
    widget = db.session.query(WidgetPage).filter(
        WidgetPage.id == unique_key).first()
    return getattr(widget, 'user_id', None)
