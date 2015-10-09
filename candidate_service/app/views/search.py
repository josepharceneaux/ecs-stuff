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
    candidate_search_results = TalentCloudSearch.search_candidates(1, request_vars, 1000)
    return jsonify(candidate_search_results)


# Search candidates which are having the values passed by URL(Eg; location)
@app.route('/search_params', methods=['GET'])
def search_candidates_using_params():
    TalentCloudSearch.get_cloud_search_connection()
    location = request.args.get('location')
    request_vars = {"location": location}
    candidate_search_results = TalentCloudSearch.search_candidates(1, request_vars, 1000)
    return jsonify(candidate_search_results)


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8002, debug=True)
