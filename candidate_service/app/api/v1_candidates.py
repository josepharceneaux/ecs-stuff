# Flask specific
from flask import (request, jsonify)
from flask_restful import (Api, Resource)

# Candidate service specific
from candidate_service.app import (app, db, logger)
from candidate_service.modules.TalentCandidates import fetch_candidate_info
from candidate_service.common.models.user import User
from candidate_service.modules.validators import (
    does_candidate_belong_to_user, is_custom_field_authorized,
    is_area_of_interest_authorized
)

# Common utilities
from common.utils.validators import (is_number, is_valid_email)

# Standard Library
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

        if not does_candidate_belong_to_user(user_row=authed_user, candidate_id=candidate_id):
            return {'error': {'message': 'Not authorized'}}, 403

        candidate_data = fetch_candidate_info(candidate_id=candidate_id)

        return {'candidate': candidate_data}

    def post(self, **kwargs):
        """
        POST /web/api/candidates
        input: {'candidates': [candidateObject1, candidateObject2, ...]}

        Creates new candidate(s).

        Takes a JSON dict containing:
            - a candidates key and a list of candidate-object(s) as values
        Function only accepts JSON dict.
        JSON dict must contain candidate's email address(s).

        :return: {'candidates': [{'id': candidate_id}, {'id': candidate_id}, ...]}
        """
        # authed_user = authenticate_oauth_user(request=request)
        # if authed_user.get('error'):
        #     return {'error': {'code': 3, 'message': 'Authentication failed'}}, 401

        authed_user = db.session.query(User).get(1)

        # Parse request data
        body_dict = parse_request_data()
        if body_dict.get('error'):
            return body_dict

        # Retrieve candidate object(s)
        list_of_candidate_dicts = body_dict.get('candidates')

        # Candidate dict(s) must be in a list
        if not isinstance(list_of_candidate_dicts, list):
            return {'error': {'message': 'Unacceptable input: Candidate object(s) must be in a list'}}, 400

        created_candidate_ids = []
        for candidate_dict in list_of_candidate_dicts:

            emails = [{'label': email.get('label'), 'address': email.get('address')}
                      for email in candidate_dict.get('emails')]
            # Email address is required for creating a candidate
            if not any(emails):
                return {'error': {'message': 'Email address required'}}, 400

            # Validate email address' format
            if filter(lambda email: not is_valid_email(email['address']), emails):
                return {'error': {'message': 'Invalid email address/format'}}, 400

            phones = candidate_dict.get('phones')
            addresses = candidate_dict.get('addresses')
            educations = candidate_dict.get('educations')
            military_services = candidate_dict.get('military_services')
            social_networks = candidate_dict.get('social_networks', [])
            custom_fields = candidate_dict.get('custom_fields', [])
            areas_of_interest = candidate_dict.get('areas_of_interest', [])
            candidate_experiences = candidate_dict.get('work_experiences', [])

            # Prevent user from adding custom field(s) to other domain(s)
            custom_field_ids = [custom_field['id'] for custom_field in custom_fields]
            is_authorized = is_custom_field_authorized(custom_field_ids=custom_field_ids,
                                                       user_domain_id=authed_user.domain_id)
            if not is_authorized:
                return {'error': {'message': 'Unauthorized custom field IDs'}}, 403

            # Prevent user from adding area(s) of interest to other domain(s)
            area_of_interest_ids = [area_of_interest['id'] for area_of_interest in areas_of_interest]
            is_authorized = is_area_of_interest_authorized(area_of_interest_ids=area_of_interest_ids,
                                                           user_domain_id=authed_user.domain_id)
            if not is_authorized:
                return {'error': {'message': 'Unauthorized area of interest IDs'}}, 403


        return body_dict

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