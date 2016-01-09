"""
Functions related to candidate_service/candidate_app/api validations
"""
import json
from candidate_service.common.models.db import db
from candidate_service.candidate_app import logger
from candidate_service.common.models.candidate import Candidate
from candidate_service.common.models.user import User
from candidate_service.common.models.misc import (AreaOfInterest, CustomField)
from candidate_service.common.models.email_marketing import EmailCampaign
from candidate_service.cloudsearch_constants import (RETURN_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH,
                                                     SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH)
from candidate_service.common.error_handling import InvalidUsage
from candidate_service.common.utils.validators import is_number
from datetime import datetime


def does_candidate_belong_to_user_and_its_domain(user_row, candidate_id):
    """
    Function checks if:
        1. Candidate belongs to user AND
        2. Candidate is in the same domain as the user
    :type   candidate_id: int
    :type   user_row: User
    :rtype: bool
    """
    assert isinstance(candidate_id, (int, long))
    candidate_row = db.session.query(Candidate).join(User).filter(
            Candidate.id == candidate_id, Candidate.user_id == user_row.id,
            User.domain_id == user_row.domain_id
    ).first()

    return True if candidate_row else False


def do_candidates_belong_to_user_and_its_domain(user_row, candidate_ids):
    """
    Function checks if:
        1. Candidates belong to user AND
        2. Candidates are in the same domain as the user
    :type user_row:         User
    :type candidate_ids:    list
    :rtype  bool
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
    :type   user_domain_id:   int
    :type   custom_field_ids: [int]
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
    :type   user_domain_id:       int
    :type   area_of_interest_ids: [int]
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


def validate_id_list(key, values):
    if ',' in values or isinstance(values, list):
        values = values.split(',') if ',' in values else values
        for value in values:
            if not value.strip().isdigit():
                raise InvalidUsage("`%s` must be comma separated ids" % key)
        # if multiple values then return as list else single value.
        return values[0] if values.__len__() == 1 else values
    else:
        return values.strip()


def validate_string_list(key, values):
    if ',' in values:
        values = [value.strip() for value in values.split(',') if value.strip()]
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
        raise InvalidUsage(error_message="Field name `%s` is not correct `return field` name", error_code=400)
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
    "search_params": 'json_encoded',
    # return fields
    "fields": 'return_fields',
    # Id of a talent_pool from where to search candidates
    "talent_pool_id": 'digit',
    # List of ids of dumb_lists (For Internal TalentPipeline Search Only)
    "dumb_list_ids": 'id_list',
    # candidate id : to check if candidate is present in smartlist.
    "id": 'digit'
}


def validate_and_format_data(request_data):
    request_vars = {}
    for key, value in request_data.iteritems():
        if key not in SEARCH_INPUT_AND_VALIDATIONS:
            raise InvalidUsage("`%s` is an invalid input" % key, 400)
        if value.strip():
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
            if SEARCH_INPUT_AND_VALIDATIONS[key] == 'json_encoded':
                request_vars[key] = validate_encoded_json(value)
        # Custom fields. Add custom fields to request_vars.
        if key.startswith('cf-'):
            request_vars[key] = value
    return request_vars
