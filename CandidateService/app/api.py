__author__ = 'amirhb'

import json
from lib2to3.pgen2 import parse
from flask_restful import Api, reqparse, inputs
from oauth import app

api = Api(app=app)

parser = reqparse.RequestParser()
parse.add_argument(u'time_now', type=inputs.date)


# Api order => CRUD: POST, GET, PUT, DELETE

@app.route('/api/candidates', methods=['GET'])
def get_candidates():
    candidates = Candidate.query.all()
    candidate_list = {'candidates': [candidate] for candidate in candidates}

    return json.dumps({'candidates': candidate_list}), 200, {'Content-Type': 'application/json'}