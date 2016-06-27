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
    Controller for /v1/ats-accounts
    """

    decorators = [require_oauth()]

    def get(self, **kwargs):
        """
        GET /v1/ats-accounts/:id

        Retrieve all ATS candidates in an ATS account of a user.
        """

        authenticated_user = request.user
        ats_service.app.logger.info("ATSAccount {} {} ({})".format(request.method, request.path, request.user.email))

        return "{ 'here-is' : 'a-value' }"

    def delete(self, **kwargs):
        """
        DELETE /v1/ats-accounts/:id/:account_id

        Decomission an ATS account for a user.
        """

        authenticated_user = request.user
        ats_service.app.logger.info("ATSAccount {} {} ({})".format(request.method, request.path, request.user.email))

        return "{ 'here-is' : 'a-value' }"

    def post(self, **kwargs):
        """
        POST /v1/ats-accounts/:id

        Register an ATS account for a user.
        """

        authenticated_user = request.user
        ats_service.app.logger.info("ATSAccount {} {} ({})".format(request.method, request.path, request.user.email))

        return "{ 'here-is' : 'a-value' }"


class ATSCandidateService(Resource):
    """
    Controller for /v1/ats-candidates
    """

    decorators = [require_oauth()]

    def get(self, **kwargs):
        """
        GET /v1/ats-candidates/:account_id

        Retrieve all ATS candidates stored locally associated with an ATS account
        """

        user_id = kwargs.get('id')
        authenticated_user = request.user
        ats_service.app.logger.info("User {} {} ({} {})".format(request.method, request.path, request.user.email, user_id))

        return "{ 'user' : '{}' }".format(user_id)

    def get(self, **kwargs):
        """
        GET /v1/ats-candidates/refresh/:account_id

        Update our local store of ATS candidates associated with an account from the ATS itself.
        """

        user_id = kwargs.get('id')
        authenticated_user = request.user
        ats_service.app.logger.info("User {} {} ({} {})".format(request.method, request.path, request.user.email, user_id))

        return "{ 'user' : '{}' }".format(user_id)

    # def post(self, **kwargs):
    #     """
    #     POST /v1/ats-candidates/:candidate_id/:ats_candidate_id

    #     Link a getTalent candidate to an ATS candidate.
    #     """

    #     authenticated_user = request.user
    #     ats_service.app.logger.info("User {} {} ({})".format(request.method, request.path, request.user.email))

    #     return "{ 'here-is' : 'a-value' }"

    # def delete(self, **kwargs):
    #     """
    #     DELETE /v1/ats-candidates/:candidate_id/:ats_candidate_id

    #     Remove an ATS account associated with a user.
    #     """

    #     authenticated_user = request.user
    #     ats_service.app.logger.info("User {} {} ({})".format(request.method, request.path, request.user.email))

    #     return "{ 'here-is' : 'a-value' }"


