"""
File contains logic for Candidate Search API
"""
# Flask specific
from flask import request
from flask_restful import Resource

# Utilities
from candidate_service.common.utils.auth_utils import require_oauth, require_all_permissions
from candidate_service.common.utils.handy_functions import time_me

# Validations
from candidate_service.modules.validators import validate_and_format_data
from jsonschema import validate, ValidationError
from candidate_service.modules.json_schema import candidates_resource_schema_get
from candidate_service.modules.validators import do_candidates_belong_to_users_domain, get_candidate_if_exists

# Error handling
from candidate_service.common.error_handling import InvalidUsage, ForbiddenError
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error

# Modules
from candidate_service.candidate_app import logger
from candidate_service.modules.talent_cloud_search import (
    search_candidates, upload_candidate_documents, delete_candidate_documents
)
from candidate_service.modules.talent_candidates import fetch_candidate_info, get_search_params_of_smartlists

# Models
from candidate_service.common.models.user import Permission


class CandidateSearch(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CANDIDATES)
    @time_me(logger=logger, api='candidate-search')
    def get(self):
        """
        Search candidates based on the given filter criteria
        """
        # Authenticated user
        authed_user = request.user

        body_dict = request.get_json(silent=True)
        if body_dict:  # In case req-body is empty
            try:
                validate(instance=body_dict, schema=candidates_resource_schema_get)
            except ValidationError as e:
                raise InvalidUsage(error_message=e.message, error_code=custom_error.INVALID_INPUT)

            candidate_ids = body_dict.get('candidate_ids')

            # Candidate IDs must belong to user's domain
            if not do_candidates_belong_to_users_domain(authed_user, candidate_ids):
                raise ForbiddenError('Not authorized', custom_error.CANDIDATE_FORBIDDEN)

            retrieved_candidates = []
            for candidate_id in candidate_ids:
                # Check for candidate's existence and web-hidden status
                candidate = get_candidate_if_exists(candidate_id)
                retrieved_candidates.append(fetch_candidate_info(candidate=candidate))

            return {'candidates': retrieved_candidates}

        else:
            request_vars = validate_and_format_data(request.args)
            # Setting status to `active` if it's not provided already
            request_vars['status'] = request_vars.get('status', 'active')

            if 'smartlist_ids' in request_vars:
                request_vars['search_params_list'] = []
                smartlist_search_params_list = get_search_params_of_smartlists(request_vars.get('smartlist_ids'))
                for search_params in smartlist_search_params_list:
                    request_vars['search_params_list'].append(validate_and_format_data(search_params))

            # Get domain_id from auth_user
            domain_id = request.user.domain_id
            limit = request_vars.get('limit')
            search_limit = int(limit) if limit else 15
            count_only = True if 'count_only' in request.args.get('fields', '') else False

            # If limit is not requested then the Search limit would be taken as 15, the default value
            candidate_search_results = search_candidates(domain_id, request_vars, search_limit, count_only)

            return candidate_search_results


class CandidateDocuments(Resource):

    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_ADD_CANDIDATES)
    def post(self):
        """
        Upload Candidate Documents to Amazon Cloud Search
        """

        requested_data = request.get_json(silent=True)
        if not requested_data or 'candidate_ids' not in requested_data:
            raise InvalidUsage(error_message="Request body is empty or invalid")

        upload_candidate_documents.delay(requested_data.get('candidate_ids'))

        return '', 204

    @require_all_permissions(Permission.PermissionNames.CAN_DELETE_CANDIDATES)
    def delete(self):
        """
        Delete Candidate Documents from Amazon Cloud Search
        """

        requested_data = request.get_json(silent=True)
        if not requested_data or 'candidate_ids' not in requested_data:
            raise InvalidUsage(error_message="Request body is empty or invalid")

        delete_candidate_documents(candidate_ids=requested_data.get('candidate_ids'))

        return '', 204
