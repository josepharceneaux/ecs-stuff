from flask_restful import Resource
from candidate_service.candidate_app import db
from candidate_service.modules.TalentCandidates import (
    fetch_candidate_info, get_candidate_id_from_candidate_email
)
from common.models.user import User
from candidate_service.modules.validators import (
    does_candidate_belong_to_user, is_custom_field_authorized,
    is_area_of_interest_authorized
)
from common.utils.validators import (is_number, is_valid_email)
from common.utils.auth_utils import require_oauth
from candidate_service.helper.api import parse_request_data


class CandidateResource(Resource):
    # todo: add require_oauth as a decorator and authenticate user
    # todo: use flask built in error handling and blueprint
    # decorators = [require_oauth]

    def get(self, **kwargs):
        """ Function can fetch a candidate via two methods:
                I.  GET /v1/candidates/:id
                    Takes an integer as candidate's ID, parsed from kwargs

                OR
                II. GET /v1/candidates/:email
                    Takes a valid email address, parsed from kwargs

        :return:    A dict of candidate info
                    404 status if candidate is not found
        """
        print "kwargs = %s" % kwargs
        authed_user = db.session.query(User).get(2)

        candidate_id = kwargs.get('id')
        print "candidate id = %s" % candidate_id
        # Search via candidate_id or candidate_email
        if not is_number(candidate_id):
            # candidate_email is provided
            candidate_email = kwargs.get('email')

            # Email address must be valid
            if not is_valid_email(candidate_email):
                return {'error': {'message': 'Valid email address required'}}

            candidate_id = get_candidate_id_from_candidate_email(candidate_email=candidate_email)

        # Candidate must belong to logged in user
        if not does_candidate_belong_to_user(user_row=authed_user,
                                             candidate_id=candidate_id):
            return {'error': {'message': 'Not authorized'}}, 403

        candidate_data = fetch_candidate_info(candidate_id=candidate_id)
        if not candidate_data:
            return {'error': {'message': 'Candidate not found'}}, 404

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


# def parse_request_data():
#     """
#     :rtype:
#     """
#     request_data = ''
#     try:
#         request_data = request.data
#         logger.info('%s:%s: Received request data: %s',
#                     (request.url, request.method, request_data))
#         body_dict = json.loads(request_data)
#     except Exception:
#         logger.info('%s:%s: Received request data: %s',
#                     (request.url, request.method, request_data))
#         return {'error': {'message': 'Unable to parse request data as JSON'}}, 400
#
#     # Request data must be a JSON dict
#     if not isinstance(body_dict, dict):
#         return {'error': {'message': 'Request data must be a JSON dict'}}, 400
#
#     # Request data cannot be empty
#     if not any(body_dict):
#         return {'error': {'message': 'Request data cannot be empty'}}, 400
#
#     return body_dict