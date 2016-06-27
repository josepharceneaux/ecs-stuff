"""
Classes implementing the ATS services endpoints.
"""

import types

from flask import request, Blueprint
from flask_restful import Resource

from ats_service.common.talent_api import TalentApi

# Decorators
from ats_service.common.utils.auth_utils import require_oauth

# Modules
from ats_service.common.routes import ATSServiceApi

# Why doesn't this work?
# from ats_service.app import logger

import ats_service.app

# Database
from ats_service.common.models.ats import ATS

from ats_service.common.utils.api_utils import api_route


api = TalentApi()
ats_service_blueprint = Blueprint('ats_service_api', __name__)
api.init_app(ats_service_blueprint)
api.route = types.MethodType(api_route, api)


@api.route(ATSServiceApi.ATS)
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


@api.route(ATSServiceApi.ACCOUNTS)
class ATSAccountService(Resource):
    """
    Controller for /v1/ats-accounts
    """

    decorators = [require_oauth()]

    def get(self, user_id):
        """
        GET /v1/ats-accounts/:id

        Retrieve all ATS candidates in an ATS account of a user.
        """

        authenticated_user = request.user
        ats_service.app.logger.info("ATSAccount {} {} ({})".format(request.method, request.path, request.user.email))
        # ats_service.app.logger.info("kargs: |{}|".format(kwargs))
        ats_service.app.logger.info("user_id: |{}|".format(user_id))

        return "{ 'accounts' : 'get', 'user_id' : ? }"

    def delete(self, **kwargs):
        """
        DELETE /v1/ats-accounts/:id/:account_id

        Decomission an ATS account for a user.
        """

        authenticated_user = request.user
        ats_service.app.logger.info("ATSAccount {} {} ({})".format(request.method, request.path, request.user.email))

        return "{ 'accounts' : 'delete' }"

    def post(self, **kwargs):
        """
        POST /v1/ats-accounts/:id

        Register an ATS account for a user.
        """

        authenticated_user = request.user
        ats_service.app.logger.info("ATSAccount {} {} ({})".format(request.method, request.path, request.user.email))

        return "{ 'accounts' : 'post' }"


@api.route(ATSServiceApi.CANDIDATES)
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

        return "{ 'candidates' : 'get' }"

    # def get(self, **kwargs):
    #     """
    #     GET /v1/ats-candidates/refresh/:account_id

    #     Update our local store of ATS candidates associated with an account from the ATS itself.
    #     """

    #     user_id = kwargs.get('id')
    #     authenticated_user = request.user
    #     ats_service.app.logger.info("User {} {} ({} {})".format(request.method, request.path, request.user.email, user_id))

    #     return "{ 'user' : '{}' }".format(user_id)

    def post(self, **kwargs):
        """
        POST /v1/ats-candidates/:candidate_id/:ats_candidate_id

        Link a getTalent candidate to an ATS candidate.
        """

        authenticated_user = request.user
        ats_service.app.logger.info("User {} {} ({})".format(request.method, request.path, request.user.email))

        return "{ 'candidates' : 'post' }"

    def delete(self, **kwargs):
        """
        DELETE /v1/ats-candidates/:candidate_id/:ats_candidate_id

        Remove an ATS account associated with a user.
        """

        authenticated_user = request.user
        ats_service.app.logger.info("User {} {} ({})".format(request.method, request.path, request.user.email))

        return "{ 'candidates' : 'delete' }"
