"""API for the Candidate Search App"""

from flask import jsonify, request, Blueprint
import TalentCloudSearch
from common.utils.auth_utils import require_oauth

mod = Blueprint('candidate_search_api', __name__)


@mod.route('/')
def hello_world():
    return 'Welcome to Candidate Search Service..!'


@mod.route('/candidates', methods=['GET'])
@require_oauth
def search():
    TalentCloudSearch.get_cloud_search_connection()
    location = request.args.get('location')
    user = request.args.get('user_ids')
    skills = request.args.get('skills')
    areas_of_interest = request.args.get('area_of_interest_ids')
    status = request.args.get("status_id")
    source = request.args.get('source_ids')
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
    query = request.args.get("q")
    limit = request.args.get("limit")

    request_vars = {"location": location, "skillDescriptionFacet": skills,
                    "areaOfInterestIdFacet": areas_of_interest, "statusFacet": status, "sourceFacet": source,
                    "minimum_years_experience": min_exp, "maximum_years_experience": max_exp,
                    "positionFacet": position, "degreeTypeFacet": degree, "schoolNameFacet": school,
                    "concentrationTypeFacet": concentration, "degree_end_year_from": degree_end_year_from,
                    "degree_end_year_to": degree_end_year_to, "serviceStatus": service_status, "branch": branch,
                    "highestGrade": grade, "military_end_date_from": military_end_date_from,
                    "military_end_date_to": military_end_date_to, "usernameFacet": user, "q": query, "limit": limit
                    }
    # If limit is not requested then the Search limit would be taken as 15, the default value
    candidate_search_results = TalentCloudSearch.search_candidates(1, request_vars, int(limit) if limit else 15)

    return jsonify(candidate_search_results)
