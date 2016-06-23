"""
Classes implementing the ATS services endpoints.
"""

from flask import request
from flask_restful import Resource

# Decorators
from ats_service.common.utils.auth_utils import require_oauth

# Modules
import ats_service.app
# Why doesn't this work?
# from ats_service.app import logger

# Database
from ats_service.common.models.ats import ATS


class ATSService(Resource):
    """
    Controller for /v1/ats

    Return a list of ATS we have integrated with.
    """

    decorators = [require_oauth()]

    def get(self, **kwargs):
        """
        GET /v1/ats
        """

        # Authenticated user
        authenticated_user = request.user

        ats_service.app.logger.info("ATS {} {} ({})".format(request.method, request.path, request.user.email))
        return ATS.get_all_as_json()

    def put(self, **kwargs):
        """
        GET /v1/ats/:account_id

        Refresh the ATS data for an account.
        """


class UsersService(Resource):
    """
    Controller for /v1/users
    """
    
    decorators = [require_oauth()]

    def get(self, **kwargs):
        """
        GET /v1/users/:id

        Retrieve a list of ATS accounts associated with a user.
        """

    def post(self, **kwargs):
        """
        GET /v1/users/:id

        Register an ATS account with a user.
        """

    def delete(self, **kwargs):
        """
        GET /v1/users/:id

        Remove an ATS account associated with a user.
        """


class CandidateService(Resource):
    """
    Controller for /v1/candidate
    """
