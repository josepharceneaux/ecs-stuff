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


class ATSAccountService(Resource):
    """
    Controller for /v1/ats/account
    """

    decorators = [require_oauth()]

    def put(self, **kwargs):
        """
        PUT /v1/ats/account/:id

        Refresh the ATS data for an account.
        """

        authenticated_user = request.user
        ats_service.app.logger.info("ATSAccount {} {} ({})".format(request.method, request.path, request.user.email))

        return "{ 'here-is' : 'a-value' }"

    def get(self, **kwargs):
        """
        GET /v1/ats/account/:id

        Retrieve all ATS candidates in an account.
        """

        authenticated_user = request.user
        ats_service.app.logger.info("ATSAccount {} {} ({})".format(request.method, request.path, request.user.email))

        return "{ 'here-is' : 'a-value' }"


class UserService(Resource):
    """
    Controller for /v1/user
    """
    
    decorators = [require_oauth()]

    def get(self, **kwargs):
        """
        GET /v1/user/:id

        Retrieve a list of ATS accounts associated with a user.
        """

        user_id = kwargs.get('id')
        authenticated_user = request.user
        ats_service.app.logger.info("User {} {} ({} {})".format(request.method, request.path, request.user.email, user_id))

        return "{ 'user' : '{}' }".format(user_id)

    def post(self, **kwargs):
        """
        POST /v1/user/:id

        Register an ATS account with a user.
        """

        authenticated_user = request.user
        ats_service.app.logger.info("User {} {} ({})".format(request.method, request.path, request.user.email))

        return "{ 'here-is' : 'a-value' }"

    def delete(self, **kwargs):
        """
        DELETE /v1/user/:id

        Remove an ATS account associated with a user.
        """

        authenticated_user = request.user
        ats_service.app.logger.info("User {} {} ({})".format(request.method, request.path, request.user.email))

        return "{ 'here-is' : 'a-value' }"


class CandidateService(Resource):
    """
    Controller for /v1/candidate
    """
    
    decorators = [require_oauth()]

    def post(self, **kwargs):
        """
        POST /v1/candidate/:id/:ats_candidate_id

        Link a getTalent candidate to an ATS candidate.
        """

        authenticated_user = request.user
        ats_service.app.logger.info("Candidate {} {} ({})".format(request.method, request.path, request.user.email))

        return "{ 'here-is' : 'a-value' }"

    def delete(self, **kwargs):
        """
        DELETE /v1/candidate/:id/:ats_candidate_id

        Unlink a getTalent candidate from an ATS candidate.
        """

        authenticated_user = request.user
        ats_service.app.logger.info("Candidate {} {} ({})".format(request.method, request.path, request.user.email))

        return "{ 'here-is' : 'a-value' }"
