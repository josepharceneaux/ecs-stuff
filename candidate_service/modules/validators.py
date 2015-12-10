"""
Functions related to candidate_service/candidate_app/api validations
"""
from candidate_service.common.models.db import db
from candidate_service.candidate_app import logger
from candidate_service.common.models.candidate import Candidate
from candidate_service.common.models.user import User
from candidate_service.common.models.misc import (AreaOfInterest, CustomField)
from candidate_service.common.models.email_marketing import EmailCampaign
from candidate_service.cloudsearch_constants import RETURN_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH
from candidate_service.common.error_handling import InvalidUsage

def does_candidate_belong_to_user(user_row, candidate_id):
    """
    Function checks if:
        1. Candidate belongs to user AND
        2. Candidate is in the same domain as the user
    :type   candidate_id: int
    :type   user_row: User
    :rtype: bool
    """
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


def does_email_campaign_belong_to_domain(user_row):
    """
    Function retrieves all email campaigns belonging to user's domain
    :rtype: bool
    """
    email_campaign_rows = db.session.query(EmailCampaign).join(User).\
        filter(User.domain_id == user_row.domain_id).first()

    return True if email_campaign_rows else False


def format_search_request_data(request_data):
    sort_by = request_data.get("sort_by")  # Sorting
    limit = request_data.get("limit")
    pages = request_data.get("page")
    query = request_data.get("query") or request_data.get("q")  # Keyword search
    # Facets
    owner_ids = request_data.get('user_ids')
    location = request_data.get('location')
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
        fields = fields.split(',')
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
    request_vars_dict = {"location": location, "skillDescriptionFacet": skills,
                         "areaOfInterestIdFacet": area_of_interest_ids, "statusFacet": status_ids,
                         "sourceFacet": source_ids, "minimum_years_experience": min_exp,
                         "maximum_years_experience": max_exp, "positionFacet": position, "degreeTypeFacet": degree,
                         "schoolNameFacet": school, "concentrationTypeFacet": concentration,
                         "degree_end_year_from": degree_end_year_from, "degree_end_year_to": degree_end_year_to,
                         "serviceStatus": service_status, "branch": branch, "highestGrade": grade,
                         "military_end_date_from": military_end_date_from, "military_end_date_to": military_end_date_to,
                         "usernameFacet": owner_ids, "q": query, "limit": limit, "fields": fields, "page": pages,
                         "sort_by": sort_by, 'radius': radius}
    if custom_field_with_id:
        request_vars_dict["cf-%d" % cf_id] = custom_field_with_id

    # Shortlist all the params passed in url
    request_vars = {}
    for key, value in request_vars_dict.iteritems():
        if value is not None:
            request_vars[key] = value

    return request_vars
