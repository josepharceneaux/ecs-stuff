from candidate_service.app import (app, db, logger)
from flask_restful import (Api, Resource)
from candidate_service.modules.TalentCandidates import (
    does_candidate_belong_to_user, fetch_candidate_info
)
from candidate_service.common.models.user import User
from common.utils.validators import (is_number, is_valid_email)
from common.utils.auth_utils import authenticate_oauth_user
from flask import (request, jsonify)
import json


api = Api(app=app)

class CandidateResource(Resource):
    def get(self, **kwargs):

        # TODO: remove print statement. Assign authed_user to authenticate_oauth_user()
        print "kwargs = %s" % kwargs
        authed_user = db.session.query(User).get(1)

        # authed_user = authenticate_oauth_user(request=request)
        # if authed_user.get('error'):
        #     return {'error': {'code': 3, 'message': 'Authentication failed'}}, 401

        candidate_id = kwargs.get('id')
        # candidate_id is required
        if not candidate_id:
            return {'error': {'message': 'A valid candidate ID is required'}}, 400

        # candidate_id must be an integer
        if not is_number(candidate_id):
            return {'error': {'message': 'Candidate ID must be an integer'}}, 400

        # if not does_candidate_belong_to_user(user_row=authed_user, candidate_id=candidate_id):
        #     return {'error': {'message': 'Not authorized'}}, 403

        candidate_data = fetch_candidate_info(candidate_id=candidate_id)

        return {'candidate': candidate_data}

    def post(self, **kwargs):
        print "kwargs = %s" % kwargs

        request_data = parse_request_data()
        if request_data.get('error'):
            return request_data

        return request_data


api.add_resource(CandidateResource, '/v1/candidates/<id>', '/v1/candidates')


def parse_request_data():
    """
    :rtype:
    """
    request_data = ''
    try:
        request_data = request.data
        logger.info('%s:%s: Received request data: %s',
                    (request.url, request.method, request_data))
        body_dict = json.loads(request_data)
    except Exception:
        logger.info('%s:%s: Received request data: %s',
                    (request.url, request.method, request_data))
        return {'error': {'message': 'Unable to parse request data as JSON'}}, 400

    # Request data must be a JSON dict
    if not isinstance(body_dict, dict):
        return {'error': {'message': 'Request data must be a JSON dict'}}, 400

    # Request data cannot be empty
    if not any(body_dict):
        return {'error': {'message': 'Request data cannot be empty'}}, 400

    return body_dict