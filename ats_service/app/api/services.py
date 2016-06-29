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

    def get(self):
        """
        GET /v1/ats
        """

        authenticated_user = request.user
        ats_service.app.logger.info("ATS {} {} ({})".format(request.method, request.path, request.user.email))

        return ATS.get_all_as_json()


@api.route(ATSServiceApi.ACCOUNT)
class ATSAccountService(Resource):
    """
    Controller for /v1/ats-accounts/:user_id/:account_id
    """

    decorators = [require_oauth()]

    def delete(self, user_id, account_id):
        """
        DELETE /v1/ats-accounts/:user_id/:account_id

        Decomission an ATS account for a user.
        """

        authenticated_user = request.user
        ats_service.app.logger.info("ATSAccount {} {} ({})".format(request.method, request.path, request.user.email))

        values = "`user`: {}, 'account': {}".format(user_id, account_id)
        return "{ 'accounts' : 'delete', " + values + " }"


@api.route(ATSServiceApi.ACCOUNTS)
class ATSAccountsService(Resource):
    """
    Controller for /v1/ats-accounts/:user_id
    """

    decorators = [require_oauth()]

    def get(self, user_id):
        """
        GET /v1/ats-accounts/:user_id

        Retrieve all ATS candidates in an ATS account of a user.
        """

        authenticated_user = request.user
        ats_service.app.logger.info("ATSAccount {} {} ({})".format(request.method, request.path, request.user.email))
        ats_service.app.logger.info("user_id: |{}|".format(user_id))

        return "{" + "'accounts' : 'get', 'user_id' : {}".format(user_id) +  "}"

    def post(self, user_id):
        """
        POST /v1/ats-accounts/:user_id

        Register an ATS account for a user.
        """

        authenticated_user = request.user
        ats_service.app.logger.info("ATSAccount {} {} ({})".format(request.method, request.path, request.user.email))

        return "{" + "'accounts' : 'post', 'user_id' : {}".format(user_id) +  "}"


@api.route(ATSServiceApi.CANDIDATES)
class ATSCandidatesService(Resource):
    """
    Controller for /v1/ats-candidates
    """

    decorators = [require_oauth()]

    def get(self, account_id):
        """
        GET /v1/ats-candidates/:account_id

        Retrieve all ATS candidates stored locally associated with an ATS account
        """

        authenticated_user = request.user
        ats_service.app.logger.info("User {} {} ({} {})".format(request.method, request.path, request.user.email, account_id))

        values = "'account': {}".format(account_id)
        return "{ 'candidates' : 'get', " + values + " }"


@api.route(ATSServiceApi.CANDIDATE)
class ATSCandidateService(Resource):
    """
    Controller for /v1/ats-candidates
    """

    decorators = [require_oauth()]

    def post(self, candidate_id, ats_id):
        """
        POST /v1/ats-candidates/:candidate_id/:ats_candidate_id

        Link a getTalent candidate to an ATS candidate.
        """

        authenticated_user = request.user
        ats_service.app.logger.info("User {} {} ({})".format(request.method, request.path, request.user.email))

        values = "'candidate': {}, ats: {}".format(candidate_id, ats_id)
        return "{ 'candidates' : 'post', " + values + " }"

    def delete(self, candidate_id, ats_id):
        """
        DELETE /v1/ats-candidates/:candidate_id/:ats_candidate_id

        Remove an ATS account associated with a user.
        """

        authenticated_user = request.user
        ats_service.app.logger.info("User {} {} ({})".format(request.method, request.path, request.user.email))

        values = "'candidate': {}, ats: {}".format(candidate_id, ats_id)
        return "{ 'candidates' : 'delete', " + values + " }"


@api.route(ATSServiceApi.CANDIDATES_REFRESH)
class ATSCandidateRefreshService(Resource):
    """
    Controller for /v1/ats-candidates/refresh
    """

    decorators = [require_oauth()]

    def get(self, account_id):
        """
        GET /v1/ats-candidates/refresh/:account_id

        Update our local store of ATS candidates associated with an account from the ATS itself.
        """

        authenticated_user = request.user
        ats_service.app.logger.info("User {} {} ({} {})".format(request.method, request.path, request.user.email, account_id))

        values = "'account': {}".format(account_id)
        return "{ 'refresh' : 'get', " + values + " }"
