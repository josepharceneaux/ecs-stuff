__author__ = 'erikfarmer'

from widget_service.common.models.misc import CustomField
from widget_service.common.models.widget import WidgetPage
from widget_service.widget_app import db
from widget_service.common.models.misc import AreaOfInterest


def parse_interest_ids_from_form(interests_string):
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
        processed_interest_ids.append(
            {'id': db.session.query(AreaOfInterest.id).filter(
                AreaOfInterest.description==interest_to_query).first().id})
    return processed_interest_ids


def parse_city_and_state_ids_from_form(locations_string):
    """Converts tag-manager input string into usable format for candidate dict.
    :param locations_string: (string) String in format:
        "<Region>: <sub_region or 'All Cities'>|
         <Region>: <sub_region or 'All Cities'>"
    :return: a list of dictionaries containing usable location ids for a candidate object
    """
    processed_location_ids = []
    state_custom_field_id = db.session.query(CustomField).filter(
        CustomField.name=='State of Interest').first().id
    city_custom_field_id = db.session.query(CustomField).filter(
        CustomField.name=='City of Interest').first().id
    raw_locations = locations_string.split('|')
    for location in raw_locations:
        state, city = location.split(':')
        city = city.lstrip()
        if city == 'All Cities':
            processed_location_ids.append({'id': state_custom_field_id, 'value': state})
        else:
            processed_location_ids.append({'id': city_custom_field_id, 'value': city})
    return processed_location_ids


def process_city_and_state_from_fields(city, state):
    processed_location_ids = []
    state_custom_field_id = db.session.query(CustomField).filter(
        CustomField.name=='State of Interest').first().id
    city_custom_field_id = db.session.query(CustomField).filter(
        CustomField.name=='City of Interest').first().id
    processed_location_ids.append({'id': state_custom_field_id, 'value': state})
    processed_location_ids.append({'id': city_custom_field_id, 'value': city})
    return processed_location_ids


def create_candidate_educations_dict(major, degree, school_name, grad_date):
    return {
        'degree': degree,
        'major': major,
        'school_name': school_name,
        'graduation_date': grad_date
    }


def get_widget_user_from_unique_key(unique_key):
    widget = db.session.query(WidgetPage).filter(
        WidgetPage.id == unique_key).first()
    return getattr(widget, 'user_id', None)
