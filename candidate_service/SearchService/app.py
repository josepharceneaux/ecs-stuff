__author__ = 'naveen'


from flask import Flask, request, session, g, redirect, url_for, Response, jsonify, current_app
import TalentCloudSearch


app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Welcome to Flask..!'


@app.route('/search', methods=['GET', 'POST'])
def search_all_candidates():
    TalentCloudSearch.get_cloud_search_connection()
    request_vars = {}
    candidate_search_results = TalentCloudSearch.search_candidates(1, request_vars, 25)
    return jsonify(candidate_search_results)


def search_candidates_using_params():
    TalentCloudSearch.get_cloud_search_connection()


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8002, debug=True)
