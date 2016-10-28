"""
File contains resource(s) for tracking candidate's edits
"""
# Standard libraries
import requests

# Flask specific
from flask_restful import Resource
from flask import request

# Utilities
from candidate_service.common.utils.auth_utils import require_oauth, require_all_permissions

# Models
from candidate_service.common.models.user import Permission

# Modules
from candidate_service.modules.edits import fetch_candidate_edits
from candidate_service.modules.validators import get_candidate_if_validated


class CandidateEditResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CANDIDATES)
    def get(self, **kwargs):
        """
        Endpoint: GET /v1/candidates/:id/edits
        Function will return requested Candidate with all of its edits.

        Usage:
            >>> url = 'host/v1/candidates/4/edits'
            >>> headers = {'Authorization': 'Bearer 7UupqClvkNv4payNUPzZmUerW9Wwd5'}
            >>> requests.get(url=url, headers=headers)
            <Response [200]>

        :return: {
                    'candidate': [
                        {
                            'id': 4,
                            'edits': [
                                {
                                    'user_id': 45,
                                    'field': 'first_name',
                                    'old_value': 'john',
                                    'new_value': 'jon',
                                    'is_custom_field': False,
                                    'edit_action': 'updated',
                                    'edit_datetime': '2016-03-02T08:44:55+00:00'
                                },
                                {
                                    'user_id': 45,
                                    'field': 'middle_name',
                                    'old_value': 'eleven',
                                    'new_value': None,
                                    'is_custom_field': False,
                                    'edit_action': 'deleted',
                                    'edit_datetime': '2016-04-02T08:44:55+00:00'
                                }
                            ]
                        }
                    ]
                }
        """
        # Get authenticated user & candidate_id
        authed_user, candidate_id = request.user, kwargs.get('id')

        # Check for candidate's existence and web-hidden status
        get_candidate_if_validated(authed_user, candidate_id)

        return {'candidate': {
            'id': candidate_id, 'edits': fetch_candidate_edits(candidate_id)
        }}
