"""
Functions related to candidate_service/candidate_app/api validations
"""
# Flask Specific
from flask import request
import json
import re
from candidate_service.common.models.db import db
from candidate_service.common.models.candidate import (
    Candidate, CandidateEmail, CandidateEducation, CandidateExperience, CandidatePhone,
    CandidatePreferredLocation, CandidateSkill, CandidateSocialNetwork, CandidateMilitaryService
)
from candidate_service.common.models.email_campaign import EmailClient
from candidate_service.common.models.user import User
from candidate_service.common.models.misc import (AreaOfInterest, CustomField)

from candidate_service.common.models.email_campaign import EmailCampaign
from candidate_service.cloudsearch_constants import (RETURN_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH,
                                                     SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH)
from candidate_service.common.error_handling import InvalidUsage, NotFoundError
from ..custom_error_codes import CandidateCustomErrors as custom_error
from candidate_service.common.utils.validators import is_number
from candidate_service.common.utils.validators import format_phone_number
from datetime import datetime


def get_json_if_exist(_request):
    """ Function will ensure data's content-type is JSON, and it isn't empty
    :type _request:  request
    """
    if "application/json" not in _request.content_type:
        raise InvalidUsage("Request body must be a JSON object", custom_error.INVALID_INPUT)
    if not _request.get_data():
        raise InvalidUsage("Request body cannot be empty", custom_error.MISSING_INPUT)
    return _request.get_json()


def get_candidate_if_exists(candidate_id):
    """
    Function checks to see if candidate exists in the database and is not web-hidden.
    If candidate is web-hidden or is not found, the appropriate exception will be raised;
    otherwise the Candidate-query-object will be returned.
    :type candidate_id: int|long
    """
    assert isinstance(candidate_id, (int, long))
    candidate = Candidate.get_by_id(candidate_id=candidate_id)
    if not candidate:
        raise NotFoundError(error_message='Candidate not found: {}'.format(candidate_id),
                            error_code=custom_error.CANDIDATE_NOT_FOUND)
    if candidate.is_web_hidden:
        raise NotFoundError(error_message='Candidate not found: {}'.format(candidate_id),
                            error_code=custom_error.CANDIDATE_IS_HIDDEN)
    return candidate


def does_candidate_belong_to_user_and_its_domain(user_row, candidate_id):
    """
    Function checks if:
        1. Candidate belongs to user AND
        2. Candidate is in the same domain as the user
    :type   candidate_id: int|long
    :type   user_row: User
    :rtype: bool
    """
    assert isinstance(candidate_id, (int, long))
    candidate_row = db.session.query(Candidate).join(User).filter(
            Candidate.id == candidate_id, Candidate.user_id == user_row.id,
            User.domain_id == user_row.domain_id
    ).first()

    return True if candidate_row else False


def do_candidates_belong_to_users_domain(user_row, candidate_ids):
    """Checks if provided candidate-IDs belong to the user's domain
    :type user_row:  User
    :type candidate_ids:  list
    :rtype:  bool
    """
    assert isinstance(candidate_ids, list)
    exists = db.session.query(Candidate).join(User). \
                 filter(Candidate.id.in_(candidate_ids),
                        User.domain_id != user_row.domain_id).count() == 0
    return exists


def does_candidate_belong_to_users_domain(user, candidate_id):
    """Checks if requested candidate ID belongs to the user's domain
    :type   user:           User
    :type  candidate_id:   Candidate.id
    :rtype: bool
    """
    assert isinstance(candidate_id, (int, long))
    exist = db.session.query(Candidate).join(User).filter(Candidate.id == candidate_id) \
        .filter(User.domain_id == user.domain_id).first()

    return True if exist else False


def is_custom_field_authorized(user_domain_id, custom_field_ids):
    """
    Function checks if custom_field_ids belong to the logged-in-user's domain
    :type   user_domain_id:   int|long
    :type   custom_field_ids: list
    :rtype: bool
    """
    assert isinstance(custom_field_ids, list)
    exists = db.session.query(CustomField). \
                 filter(CustomField.id.in_(custom_field_ids),
                        CustomField.domain_id != user_domain_id).count() == 0
    return exists


def is_area_of_interest_authorized(user_domain_id, area_of_interest_ids):
    """
    Function checks if area_of_interest_ids belong to the logged-in-user's domain
    :type   user_domain_id:       int|long
    :type   area_of_interest_ids: list[int]
    :rtype: bool
    """
    assert isinstance(area_of_interest_ids, list)
    exists = db.session.query(AreaOfInterest). \
                 filter(AreaOfInterest.id.in_(area_of_interest_ids),
                        AreaOfInterest.domain_id != user_domain_id).count() == 0
    return exists


def does_email_campaign_belong_to_domain(user):
    """
    Function retrieves all email campaigns belonging to user's domain
    :rtype: bool
    """
    assert isinstance(user, User)
    email_campaign_rows = db.session.query(EmailCampaign).join(User). \
        filter(User.domain_id == user.domain_id).first()

    return True if email_campaign_rows else False


def validate_is_digit(key, value):
    if not value.isdigit():
        raise InvalidUsage("`%s` should be a whole number" % key, 400)
    return value


def validate_is_number(key, value):
    if not is_number(value):
        raise InvalidUsage("`%s` should be a numeric value" % key, 400)
    return value


def validate_id_list(key, values):
    if ',' in values or isinstance(values, list):
        values = values.split(',') if ',' in values else values
        for value in values:
            if not value.strip().isdigit():
                raise InvalidUsage("`%s` must be comma separated ids" % key)
        # if multiple values then return as list else single value.
        return values[0] if values.__len__() == 1 else values
    else:
        if not values.strip().isdigit():
            raise InvalidUsage("`%s` must be comma separated ids()" % key)
        return values.strip()


def validate_string_list(key, values):
    if ',' in values or isinstance(values, list):
        values = [value.strip() for value in values.split(',') if value.strip()] if ',' in values else values
        return values[0] if values.__len__() == 1 else values
    else:
        return values.strip()


def validate_sort_by(key, value):
    # If sorting is present, modify it according to cloudsearch sorting variables.
    try:
        sort_by = SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH[value]
    except KeyError:
        raise InvalidUsage(error_message="sort_by `%s` is not correct input for sorting." % value, error_code=400)
    return sort_by


def validate_encoded_json(value):
    """ This function will validate and decodes a encoded json string """
    try:
        return json.loads(value)
    except Exception as e:
        raise InvalidUsage(error_message="Encoded JSON %s couldn't be decoded because: %s" % (value, e.message))


def validate_fields(key, value):
    # If `fields` are present, validate and modify `fields` values according to cloudsearch supported return field names.
    fields = [field.strip() for field in value.split(',') if field.strip()]
    try:
        fields = ','.join([RETURN_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH[field] for field in fields])
    except KeyError:
        raise InvalidUsage(error_message="Field name `%s` is not correct `return field` name" % fields, error_code=400)
    return fields


def convert_date(key, value):
    """
    Convert the given date into cloudsearch's desired format and return.
    Raise error if input date string is not matching the "MM/DD/YYYY" format.
    """
    if value:
        try:
            formatted_date = datetime.strptime(value, '%m/%d/%Y')
        except ValueError:
            raise InvalidUsage("Field `%s` contains incorrect date format. "
                               "Date format should be MM/DD/YYYY (eg. 12/31/2015)" % key)
        return formatted_date.isoformat() + 'Z'  # format it as required by cloudsearch.


SEARCH_INPUT_AND_VALIDATIONS = {
    "sort_by": 'sorting',
    "limit": 'digit',
    "page": 'digit',
    "query": '',
    # Facets
    "date_from": 'date_range',
    "date_to": 'date_range',
    "user_ids": 'id_list',
    "location": '',
    "radius": 'number',
    "area_of_interest_ids": 'id_list',
    "status_ids": 'id_list',
    "source_ids": 'id_list',
    "minimum_years_experience": 'number',
    "maximum_years_experience": 'number',
    "skills": 'string_list',
    "job_title": 'string_list',
    "school_name": 'string_list',
    "degree_type": 'string_list',
    "major": 'string_list',
    "degree_end_year_from": 'digit',
    "degree_end_year_to": 'digit',
    "military_service_status": 'string_list',
    "military_branch": 'string_list',
    "military_highest_grade": 'string_list',
    "military_end_date_from": 'digit',
    "military_end_date_to": 'digit',
    # return fields
    "fields": 'return_fields',
    # Id of a talent_pool from where to search candidates
    "talent_pool_id": 'digit',
    # List of ids of dumb_lists (For Internal TalentPipeline Search Only)
    "dumb_list_ids": 'id_list',
    # List of ids of smart_lists (For Internal TalentPipeline Search Only)
    "smartlist_ids": 'id_list',
    # candidate id : to check if candidate is present in smartlist.
    "id": 'digit'
}


def convert_to_snake_case(key):
    """
    Convert camelCase to snake_case
    Copied from: http://goo.gl/648F0n
    :param key:
    :return:
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', key)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def is_backward_compatible(key):
    """
    This method will check for backward compatibility of old web2py based app's search keys
    :param key: Key which is to be converted to new format
    :return: Converted key
    """
    if key not in SEARCH_INPUT_AND_VALIDATIONS:
        key = convert_to_snake_case(key)
        if 'facet' in key:
            key = key.replace('_facet', '')

        if key == 'username':
            key = 'user_ids'
        elif key == 'area_of_interest_id' or key == 'area_of_interest_name':
            key = 'area_of_interest_ids'
        elif key == 'status' or key == 'source':
            key += '_ids'
        elif key == 'skill_description':
            key = 'skills'
        elif key == 'position':
            key = 'job_title'
        elif key == 'concentration_type':
            key = 'major'
        elif key == 'branch':
            key = 'military_branch'
        elif key == 'highest_grade':
            key = 'military_highest_grade'

        if key not in SEARCH_INPUT_AND_VALIDATIONS:
            return -1

    return key


def validate_and_format_data(request_data):
    request_vars = {}
    for key, value in request_data.iteritems():
        key = is_backward_compatible(key)
        if key == -1 or not value or (isinstance(value, basestring) and not value.strip()):
            continue
        if is_number(value):
            value = str(value)

        if SEARCH_INPUT_AND_VALIDATIONS[key] == '':
            request_vars[key] = value
        if SEARCH_INPUT_AND_VALIDATIONS[key] == 'digit':
            request_vars[key] = validate_is_digit(key, value)
        if SEARCH_INPUT_AND_VALIDATIONS[key] == 'number':
            request_vars[key] = validate_is_number(key, value)
        if SEARCH_INPUT_AND_VALIDATIONS[key] == "id_list":
            request_vars[key] = validate_id_list(key, value)
        if SEARCH_INPUT_AND_VALIDATIONS[key] == "sorting":
            request_vars[key] = validate_sort_by(key, value)
        if SEARCH_INPUT_AND_VALIDATIONS[key] == "string_list":
            request_vars[key] = validate_string_list(key, value)
        if SEARCH_INPUT_AND_VALIDATIONS[key] == "return_fields":
            request_vars[key] = validate_fields(key, value)
        if SEARCH_INPUT_AND_VALIDATIONS[key] == "date_range":
            request_vars[key] = convert_date(key, value)
        # Custom fields. Add custom fields to request_vars.
        if key.startswith('cf-'):
            request_vars[key] = value
    return request_vars


def is_valid_email_client(client_id):
    """
    Validate if client id is in the system
    :param client_id: int
    :return: string: email client name
    """
    return db.session.query(EmailClient.name).filter(EmailClient.id == int(client_id)).first()


def is_date_valid(date):
    """
    Checks if date format is: yyyy-mm-dd
    :type date:  basestring|str
    :rtype:  bool
    """
    try:
        datetime.strptime(date, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def does_address_exist(candidate, address_dict):
    """
    :type candidate:  Candidate
    :type address_dict:  dict[str]
    :rtype:  bool
    """
    for address in candidate.addresses:
        address_line_1, address_line_2 = (address.address_line_1 or '').lower(), (address.address_line_2 or '').lower()
        address_dict_address_line_1 = (address_dict.get('address_line_1') or '').lower()
        address_dict_address_line_2 = (address_dict.get('address_line_2') or '').lower()
        if address_line_1 and not address_line_2:
            if address_line_1 == address_dict_address_line_1:
                return True
        elif address_line_1 and address_line_2:
            if address_line_1 == address_dict_address_line_1 and address_line_2 == address_dict_address_line_2:
                return True
    return False


def does_candidate_cf_exist(candidate, custom_field_dict):
    """
    :type candidate:  Candidate
    :type custom_field_dict: dict[str]
    :rtype:  bool
    """
    for custom_field in candidate.custom_fields:
        custom_field_value = (custom_field.value or '').lower()
        if custom_field_value == (custom_field_dict.get('value') or '').lower():
            return True
    return False


def get_candidate_email_from_domain_if_exists(user_id, email_address):
    """
    Function will retrieve CandidateEmail belonging to the requested candidate
    in the same domain if found.
    :type user_id:       int|long
    :type email_address: basestring
    :rtype: CandidateEmail|None
    """
    user_domain_id = User.get_domain_id(_id=user_id)
    candidate_email = CandidateEmail.query.join(Candidate).join(User).filter(
            CandidateEmail.address == email_address, User.domain_id == user_domain_id).first()
    return candidate_email if candidate_email else None


def get_education_if_exists(educations, education_dict, education_degrees):
    """
    Function will check to see if the requested education information already exists in the database
    :type educations:  list[CandidateEducation]
    :param educations:  candidate.educations
    :param education_degrees:  education-degrees' info from the request
    :type education_degrees:  list[dict[str]]
    :type education_dict: dict[str]
    """
    for education in educations:
        school_name = (education.school_name or '').lower()
        if school_name == (education_dict.get('school_name') or '').lower():

            existing_degree_dicts = [
                {
                    'start_year': existing_degree.start_year,
                    'end_year': existing_degree.end_year,
                    'title': existing_degree.degree_title
                } for existing_degree in education.degrees
            ]

            new_degree_dicts = [
                {
                    'start_year': new_degree.get('start_year'),
                    'end_year': new_degree.get('end_year'),
                    'title': new_degree.get('title')
                } for new_degree in education_degrees
            ]

            common_dicts = [common for common in existing_degree_dicts if common in new_degree_dicts]
            if common_dicts:
                return education.id

    return None  # for readability


def get_education_degree_if_exists(educations, education_degree):
    """
    :type educations:  list[CandidateEducation]
    :type education_degree:  dict[str]
    """
    for education in educations:
        for degree in education.degrees:

            existing_degree_dicts = {
                'start_year': degree.start_year,
                'end_year': degree.end_year,
                'title': degree.degree_title
            }

            new_degree_dicts = {
                'start_year': education_degree.get('start_year'),
                'end_year': education_degree.get('end_year'),
                'title': education_degree.get('degree_title')
            }

            if existing_degree_dicts.values() == new_degree_dicts.values():
                return degree.id

    return None  # For readability


def does_education_degree_bullet_exist(candidate_educations, education_degree_bullet_dict):
    """
    :type candidate_educations:  list[CandidateEducation]
    :param candidate_educations:  candidate.educations
    :type education_degree_bullet_dict:  dict[str]
    :rtype:  bool
    """
    for education in candidate_educations:
        for degree in education.degrees:
            for bullet in degree.bullets:
                if bullet:
                    concentration_type = (bullet.concentration_type or '').lower()
                    if concentration_type == (education_degree_bullet_dict.get('concentration_type') or '').lower():
                        return True
    return False


def get_work_experience_if_exists(experiences, experience_dict):
    """
    :type experiences:  list[CandidateExperience]
    :type experience_dict: dict[str]
    """
    for experience in experiences:
        organization = (experience_dict.get('organization') or '').lower()
        if experience.organization and (experience.start_year or experience.end_year):
            if experience.start_year == experience_dict.get('start_year') and \
                            experience.organization.lower() == organization:
                return experience.id

            if experience.end_year == experience_dict.get('end_year') and \
                            experience.organization.lower() == organization:
                return experience.id
        elif experience.organization and not (experience.start_year or experience.end_year):
            if experience.organization.lower() == organization:
                return experience.id
    return None  # for readability


def does_experience_bullet_exist(experiences, bullet_dict):
    """
    :type experiences:  list[CandidateExperience]
    :type bullet_dict:  dict[str]
    :rtype:  bool
    """
    for experience in experiences:
        for bullet in experience.bullets:
            description = (bullet.description or '').lower()
            if description == (bullet_dict.get('description') or '').lower():
                return True
    return False


def does_phone_exist(phones, phone_dict):
    """
    :type phones:  list[CandidatePhone]
    :type phone_dict:  dict[str]
    :rtype:  bool
    """
    for phone in phones:
        value = phone_dict.get('value')
        if value:
            if phone.value == format_phone_number(value)['formatted_number']:
                return True
    return False


def does_preferred_location_exist(preferred_locations, preferred_location_dict):
    """
    :type preferred_locations:  list[CandidatePreferredLocation]
    :type preferred_location_dict:  dict[str]
    :rtype:
    """
    for location in preferred_locations:
        city, region = preferred_location_dict.get('city') or '', preferred_location_dict.get('region') or ''
        if (location.city or '').lower() == city.lower() and (location.region or '').lower() == region.lower():
            return True
    return False


def does_skill_exist(skills, skill_dict):
    """
    :type skills:  list[CandidateSkill]
    :type skill_dict:  dict[str]
    :rtype:  bool
    """
    for skill in skills:
        description = (skill_dict.get('description') or '').lower()
        if (skill.description or '').lower() == description:
            return True
    return False


def does_social_network_exist(social_networks, social_network_dict):
    """
    :type social_networks:  list[CandidateSocialNetwork]
    :type social_network_dict:  dict[str]
    :rtype:  bool
    """
    for social_network in social_networks:
        profile_url = (social_network_dict.get('social_profile_url') or '').lower()
        if (social_network.social_profile_url or '').lower() == profile_url:
            return True
    return False


def does_military_service_exist(military_services, military_service_dict):
    """
    :type military_services:  list[CandidateMilitaryService]
    :type military_service_dict:  dict[str]
    :rtype:  bool
    """
    for military_service in military_services:
        from_date, to_date = military_service_dict.get('from_date'), military_service_dict.get('to_date')
        if military_service.from_date == from_date or military_service.to_date == to_date:
            return True
    return False

