__author__ = 'naveen'

from flask import Flask, jsonify, request

import TalentCloudSearch

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Welcome to Flask..!'


# Search all the candidates in the domain
@app.route('/search', methods=['GET'])
def search_all_candidates():
    TalentCloudSearch.get_cloud_search_connection()
    request_vars = {}
    candidate_search_results = TalentCloudSearch.search_candidates(1, request_vars, 10)
    return jsonify(candidate_search_results)


# Search candidates which are having the values passed by URL(Eg; location)
@app.route('/search_params', methods=['GET'])
def search_candidates_using_params():
    TalentCloudSearch.get_cloud_search_connection()
    location = request.args.get('location')
    user = request.args.get('usernameFacet')
    skills = request.args.get('skillDescriptionFacet')
    area_of_interest = request.args.get('areaOfInterestIdFacet')
    status = request.args.get("statusFacet")
    source = request.args.get('sourceFacet')
    min_exp = request.args.get('minimum_years_experience')
    max_exp = request.args.get('maximum_years_experience')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    position = request.args.get('positionFacet') # job title = position
    degree = request.args.get('degreeTypeFacet')
    school = request.args.get('schoolNameFacet')
    concentration = request.args.get('concentrationTypeFacet')
    degree_end_year_from = request.args.get('degree_end_year_from')
    degree_end_year_to = request.args.get('degree_end_year_to')
    service_status = request.args.get('serviceStatus')
    branch = request.args.get('branch')
    grade = request.args.get('highestGrade')
    military_end_date_from = request.args.get('military_end_date_from')
    military_end_date_to = request.args.get('military_end_date_to')

    request_vars = {"location": location, "skillDescriptionFacet": skills,
                    "areaOfInterestIdFacet": area_of_interest, "statusFacet": status, "sourceFacet": source,
                    "minimum_years_experience": min_exp, "maximum_years_experience": max_exp,
                    "date_from": date_from, "date_to": date_to, "positionFacet": position,
                    "degreeTypeFacet": degree, "schoolNameFacet": school, "concentrationTypeFacet": concentration,
                    "degree_end_year_from": degree_end_year_from, "degree_end_year_to": degree_end_year_to,
                    "serviceStatus": service_status, "branch": branch, "highestGrade": grade,
                    "military_end_date_from": military_end_date_from, "military_end_date_to": military_end_date_to,
                    "usernameFacet": user
                    }
    candidate_search_results = TalentCloudSearch.search_candidates(1, request_vars, 1000)
    return jsonify(candidate_search_results)


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8002, debug=True)
