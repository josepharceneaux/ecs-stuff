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

def does_candidate_belong_to_user(user_row, candidate_id):
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


def do_candidates_belong_to_user(user_row, candidate_ids):
    """
    Function checks if:
        1. Candidates belong to user AND
        2. Candidates are in the same domain as the user
    :type user_row:         User
    :type candidate_ids:    list
    :rtype  bool
    """
    assert isinstance(candidate_ids, list)
    exists = db.session.query(Candidate).join(User).\
                 filter(Candidate.id.in_(candidate_ids),
                        User.domain_id != user_row.domain_id).count() == 0
    return exists


def is_custom_field_authorized(user_domain_id, custom_field_ids):
    """
    Function checks if custom_field_ids belong to the logged-in-user's domain
    :type   user_domain_id:   int
    :type   custom_field_ids: [int]
    :rtype: bool
    """
    assert isinstance(custom_field_ids, list)
    exists = db.session.query(CustomField).\
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
    exists = db.session.query(AreaOfInterest).\
                 filter(AreaOfInterest.id.in_(area_of_interest_ids),
                        AreaOfInterest.domain_id != user_domain_id).count() == 0
    return exists


def does_email_campaign_belong_to_domain(user):
    """
    Function retrieves all email campaigns belonging to user's domain
    :rtype: bool
    """
    assert isinstance(user, User)
    email_campaign_rows = db.session.query(EmailCampaign).join(User).\
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
    if ',' in values:
        values = values.split(',')
        for value in values:
            if not value.strip().isdigit():
                raise InvalidUsage("`%s` must be comma separated ids" % key)
        # if multiple values then return as list else single value.
        return values[0] if values.__len__() == 1 else values
    else:
        return values.strip()


def string_list(key, values):
    if ',' in values:
        values = [value.strip() for value in values.split(',') if value.strip()]
        return values[0] if values.__len__() == 1 else values


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


SEARCH_INPUT_AND_VALIDATIONS = {
    "sort_by": 'sorting',
    "limit": 'digit',
    "page": 'digit',
    "query": 'strip',
    # Facets
    # TODO: added_time facet search. Not visible in most domains. Required?
    "user_ids": 'id_list',
    "location": 'strip',
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
    # candidate id : to check if candidate is present in smartlist.
    "id": 'digit'
}


def validate_and_format_data(request_data):
    request_vars = {}
    for key, value in request_data.iteritems():
        if key not in SEARCH_INPUT_AND_VALIDATIONS:
            raise InvalidUsage("`%s` is an invalid input" % key, 400)
        if value.strip():
            if SEARCH_INPUT_AND_VALIDATIONS[key] == 'strip':
                request_vars[key] = value.strip()
            if SEARCH_INPUT_AND_VALIDATIONS[key] == 'digit':
                request_vars[key] = validate_is_digit(key, value)
            if SEARCH_INPUT_AND_VALIDATIONS[key] == 'number':
                request_vars[key] = validate_is_number(key, value)
            if SEARCH_INPUT_AND_VALIDATIONS[key] == "id_list":
                request_vars[key] = validate_id_list(key, value)
            if SEARCH_INPUT_AND_VALIDATIONS[key] == "sorting":
                request_vars[key] = validate_sort_by(key, value)
            if SEARCH_INPUT_AND_VALIDATIONS[key] == "string_list":
                request_vars[key] = string_list(key, value)
            if SEARCH_INPUT_AND_VALIDATIONS[key] == "return_fields":
                request_vars[key] = validate_fields(key, value)
            if SEARCH_INPUT_AND_VALIDATIONS[key] == 'json_encoded':
                request_vars[key] = validate_encoded_json(value)
        # TODO: handling of custom fields
    return request_vars


def format_search_request_data(request_data):
    request_vars = {}
    sort_by = request_data.get("sort_by")  # Sorting
    if sort_by:
        # If sorting is present, modify it according to cloudsearch sorting variables.
        try:
            request_vars['sort_by'] = SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH[sort_by]
        except KeyError:
            raise InvalidUsage(error_message="sort_by `%s` is not correct input for sorting.", error_code=400)

    limit = request_data.get("limit")
    if limit:
        if not limit.isdigit():
            raise InvalidUsage("`limit` should be a whole number", 400)
        request_vars["limit"] = limit

    page = request_data.get("page")
    if page:
        if not page.isdigit():
            raise InvalidUsage("`page` should be a whole number", 400)
        request_vars['page'] = page

    query = request_data.get("query") or request_data.get("q")  # Keyword search

    # Facets
    user_ids = request_data.get('user_ids')
    if user_ids.strip():
        if ',' in user_ids:
            user_ids = user_ids.split(',')
            for user_id in user_ids:
                if not user_id.strip().isdigit():
                    raise InvalidUsage("`user_ids` must be comma separated ids")
            # if multiple values then return as list else single value.
            user_ids[0] if user_ids.__len__() == 1 else user_ids

    location = request_data.get('location')
    if location and location.strip():
        request_vars['location'] = location.strip()
    radius = request_data.get('radius')
    area_of_interest_ids = request_data.get('area_of_interest_ids')
    status_ids = request_data.get("status_ids")
    source_ids = request_data.get('source_ids')
    min_exp = request_data.get('minimum_years_experience')
    max_exp = request_data.get('maximum_years_experience')
    skills = request_data.get('skills')
    position = request_data.get('job_title')
    school = request_data.get('school_name')
    degree = request_data.get('degree')
    concentration = request_data.get('major')  # Electrical Engineering or Concentration on your major
    degree_end_year_from = request_data.get('degree_end_year_from')
    degree_end_year_to = request_data.get('degree_end_year_to')
    service_status = request_data.get('military_service_status')
    branch = request_data.get('military_branch')
    grade = request_data.get('military_highest_grade')
    military_end_date_from = request_data.get('military_end_date_from')
    military_end_date_to = request_data.get('military_end_date_to')
    fields = request_data.get("fields")
    candidate_id = request_data.get("id")

    if fields:
        # If `fields` are present, validate and modify `fields` values according to cloudsearch supported return field names.
        fields = [field.strip() for field in fields.split(',') if field.strip()]
        try:
            fields = ','.join([RETURN_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH[field] for field in fields])
        except KeyError:
            raise InvalidUsage(error_message="Field name `%s` is not correct `return field` name", error_code=400)


    # Handling custom fields
    custom_field_with_id = None
    cf_id = None
    for value in request_data.keys():
        cf_str = [cf for cf in value if 'cf-' in cf]
        if cf_str:
            cf_id = int(cf_str[0].split('-')[1])
            custom_field_with_id = request_data.get("cf-%d" % cf_id)

    # Dictionary with all searchable filters
    request_vars_dict = {"location": location, "skills": skills,
                         "areaOfInterestIdFacet": area_of_interest_ids, "statusFacet": status_ids,
                         "sourceFacet": source_ids, "minimum_years_experience": min_exp,
                         "maximum_years_experience": max_exp, "positionFacet": position, "degreeTypeFacet": degree,
                         "schoolNameFacet": school, "concentrationTypeFacet": concentration,
                         "degree_end_year_from": degree_end_year_from, "degree_end_year_to": degree_end_year_to,
                         "serviceStatus": service_status, "branch": branch, "highestGrade": grade,
                         "military_end_date_from": military_end_date_from, "military_end_date_to": military_end_date_to,
                         "user_ids": owner_ids, "q": query, "limit": limit, "fields": fields, "page": pages,
                         "sort_by": sort_by, 'radius': radius, "id": candidate_id}
    if custom_field_with_id:
        request_vars_dict["cf-%d" % cf_id] = custom_field_with_id

    # Shortlist all the params passed in url
    request_vars = {}
    for key, value in request_vars_dict.iteritems():
        if value is not None:
            request_vars[key] = value

    return request_vars


