"""API for the Candidate Search App"""

from flask import jsonify, request, Blueprint
import TalentCloudSearch


mod = Blueprint('candidate_search_api', __name__)


@mod.route('/')
def hello_world():
    return 'Welcome to Candidate Search Service..!'


@mod.route('/candidates', methods=['GET'])
def search():
    TalentCloudSearch.get_cloud_search_connection()
    location = request.args.get('location')
    user = request.args.get('user_id')
    skills = request.args.get('skills')
    areas_of_interest = request.args.get('areas_of_interest_id')
    status = request.args.get("status_id")
    source = request.args.get('source_id')
    min_exp = request.args.get('minimum_experience')
    max_exp = request.args.get('maximum_experience')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    position = request.args.get('job_title')
    degree = request.args.get('degree_type')
    school = request.args.get('school_name')
    concentration = request.args.get('concentration')
    degree_end_year_from = request.args.get('degree_end_year_from')
    degree_end_year_to = request.args.get('degree_end_year_to')
    service_status = request.args.get('service_status')
    branch = request.args.get('branch')
    grade = request.args.get('highest_grade')
    military_end_date_from = request.args.get('military_end_date_from')
    military_end_date_to = request.args.get('military_end_date_to')
    social_networks = request.args.get('social_networks')
    query = request.args.get("q")
    limit = request.args.get("limit")

    request_vars = {"location": location, "skillDescriptionFacet": skills,
                    "areaOfInterestIdFacet": areas_of_interest, "statusFacet": status, "sourceFacet": source,
                    "minimum_years_experience": min_exp, "maximum_years_experience": max_exp,
                    "date_from": date_from, "date_to": date_to, "positionFacet": position,
                    "degreeTypeFacet": degree, "schoolNameFacet": school, "concentrationTypeFacet": concentration,
                    "degree_end_year_from": degree_end_year_from, "degree_end_year_to": degree_end_year_to,
                    "serviceStatus": service_status, "branch": branch, "highestGrade": grade,
                    "military_end_date_from": military_end_date_from, "military_end_date_to": military_end_date_to,
                    "usernameFacet": user, "social_networks": social_networks, "q": query, "limit": limit
                    }
    # If limit is not requested then the Search limit would be taken as 15, the default value
    candidate_search_results = TalentCloudSearch.search_candidates(1, request_vars, int(limit) if limit else 15)

    return jsonify(candidate_search_results)
