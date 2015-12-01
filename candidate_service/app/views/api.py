"""API for the Candidate Search Service App"""

from flask import jsonify, request, Blueprint
import talent_cloud_search
from candidate_service.common.utils.auth_utils import require_oauth
from candidate_service.candidate_app import logger

mod = Blueprint('candidate_search_api', __name__)


@mod.route('/')
def hello_world():
    return 'Welcome to Candidate Search Service..!'


@mod.route('/candidates', methods=['GET'])
@require_oauth
def search():
    """
    Search candidates with different search filters
    :return: Candidate data in json format
    """
    # Get cloud_search connection
    talent_cloud_search.get_cloud_search_connection()

    # Get the parameters passed in the url
    location = request.args.get('location')
    owner_ids = request.args.get('user_ids')
    skills = request.args.get('skills')
    area_of_interest_ids = request.args.get('area_of_interest_ids')
    status_ids = request.args.get("status_ids")
    source_ids = request.args.get('source_ids')
    min_exp = request.args.get('minimum_experience')
    max_exp = request.args.get('maximum_experience')
    position = request.args.get('job_title')
    degree = request.args.get('degree_type')
    school = request.args.get('school_name')
    concentration = request.args.get('major')  # Higher Education or Concentration on your major
    degree_end_year_from = request.args.get('degree_end_year_from')
    degree_end_year_to = request.args.get('degree_end_year_to')
    service_status = request.args.get('military_service_status')
    branch = request.args.get('military_branch')
    grade = request.args.get('military_highest_grade')
    military_end_date_from = request.args.get('military_end_date_from')
    military_end_date_to = request.args.get('military_end_date_to')
    sort_by = request.args.get("sort_by")
    pages = request.args.get("page")
    radius = request.args.get('radius')
    query = request.args.get("q")
    limit = request.args.get("limit")
    fields = request.args.get("fields")

    # Handling custom fields
    custom_field_with_id = None
    cf_id = None
    for value in request.args.iteritems():
        cf_str = [cf for cf in value if 'cf-' in cf]
        if cf_str:
            cf_id = int(cf_str[0].split('-')[1])
            custom_field_with_id = request.args.get("cf-%d" % cf_id)

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

    # Get domain_id from auth_user
    domain_id = request.user.domain_id
    logger.info("Searching candidates in the domain:%s" % domain_id)
    search_limit = int(limit) if limit else 15

    # If limit is not requested then the Search limit would be taken as 15, the default value
    candidate_search_results = talent_cloud_search.search_candidates(domain_id, request_vars,
                                                                     search_limit)

    return jsonify(candidate_search_results)
