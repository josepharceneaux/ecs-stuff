"""
Classes implementing the ATS services endpoints.
"""

import types
import json

from flask import request, Blueprint
from flask_restful import Resource
from requests import codes

# Decorators
from ats_service.common.utils.auth_utils import require_oauth

# Modules
from ats_service.common.routes import ATSServiceApi, ATSServiceApiUrl
from ats_service.common.utils.api_utils import ApiResponse, api_route
from ats_service.common.talent_api import TalentApi
from ats_service.common.utils.handy_functions import get_valid_json_data

from ats_utils import validate_ats_account_data, validate_ats_candidate_data, new_ats, new_ats_account, new_ats_candidate, link_ats_candidate,  unlink_ats_candidate, delete_ats_account

# Why doesn't this work?
# from ats_service.app import logger
import ats_service.app

# Database
from ats_service.common.models.ats import ATS, ATSAccount, ATSCredential, ATSCandidate


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

        :rtype string, JSON describing all ATS in our system.
        """

        ats_service.app.logger.info("{} {} {} {}\n".format(request.method, request.path, request.user.email, request.user.id))
        authenticated_user = request.user

        return ATS.get_all_as_json()


@api.route(ATSServiceApi.ACCOUNT)
class ATSAccountService(Resource):
    """
    Controller for /v1/ats-accounts/:account_id
    """

    decorators = [require_oauth()]

    def get(self, account_id):
        """
        GET /v1/ats-accounts/:account_id

        Retrieve an ATS accoun.

        :param account_id: int, id of the ATS account.
        :rtype string, JSON describing the account.
        """

        ats_service.app.logger.info("{} {} {} {}\n".format(request.method, request.path, request.user.email, request.user.id))
        authenticated_user = request.user
        account = ATSAccount.get_by_id(account_id)
        if not account:
            ats_service.app.logger.info("Attempt to fetch non-existant ATS account {}".format(account_id))
            response = json.dumps(dict(id=account_id, message="ATS account (id = {}) does not exist.".format(account_id)))
            headers = dict(Location=ATSServiceApiUrl.ACCOUNT % account_id)
            return ApiResponse(response, headers=headers, status=codes.NOT_FOUND)

        account_dict = account.to_dict()
        credentials = ATSCredential.get_by_id(account.ats_credential_id)
        account_dict.update( { 'credentials' : credentials.credentials_json} )

        return json.dumps(account_dict)

    def delete(self, account_id):
        """
        DELETE /v1/ats-accounts/:account_id

        Decomission an ATS account for a user.

        :param account_id: int, id of the ATS account.
        :rtype string, JSON indicating success.
        """

        ats_service.app.logger.info("{} {} {} {}\n".format(request.method, request.path, request.user.email, request.user.id))
        delete_ats_account(request.user.id, account_id)

        return "{{ delete : success }}"


@api.route(ATSServiceApi.ACCOUNTS)
class ATSAccountsService(Resource):
    """
    Controller for /v1/ats-accounts
    """

    decorators = [require_oauth()]

    def get(self):
        """
        GET /v1/ats-accounts

        Retrieve all ATS accounts of a user.

        :rtype string, JSON describing account.
        """

        ats_service.app.logger.info("{} {} {} {}\n".format(request.method, request.path, request.user.email, request.user.id))
        authenticated_user = request.user
        return_json = ATSAccount.get_accounts_for_user_as_json(authenticated_user.id)

        return return_json

    def post(self):
        """
        POST /v1/ats-accounts/

        Register an ATS account for a user.

        :rtype string, JSON indicating success.
        """

        ats_service.app.logger.info("{} {} {} {}\n".format(request.method, request.path, request.user.email, request.user.id))
        authenticated_user = request.user
        data = get_valid_json_data(request)

        # Validate data fields
        validate_ats_account_data(data)

        # Search for this ATS account entry already existing
        account = ATSAccount.get_account(authenticated_user.id, data['ats_name'])
        if account:
            ats_service.app.logger.info("Attempt to create already existing ATS account {}".format(account.id))
            response = json.dumps(dict(id=account.id, message="ATS account already exists."))
            headers = dict(Location=ATSServiceApiUrl.ACCOUNTS % account.id)
            return ApiResponse(response, headers=headers, status=codes.OK)

        # Search for ATS entry, create if absent
        ats = ATS.get_by_name(data['ats_name'])
        if not ats:
            ats = new_ats(data)
            ats_service.app.logger.info("Adding new ATS account {}, id {}".format(ats.name, ats.id))

        # Create ATS account for user
        account = new_ats_account(authenticated_user.id, ats.id, data)
        ats_service.app.logger.info("Added new ATS account {}.".format(account.id))

        response = json.dumps(dict(id=account.id, message="ATS account successfully created."))
        headers = dict(Location=ATSServiceApiUrl.ACCOUNT % account.id)
        return ApiResponse(response, headers=headers, status=codes.CREATED)


@api.route(ATSServiceApi.CANDIDATES)
class ATSCandidatesService(Resource):
    """
    Controller for /v1/ats-candidates/:account_id
    """

    decorators = [require_oauth()]

    def get(self, account_id):
        """
        GET /v1/ats-candidates/:account_id

        Retrieve all ATS candidates stored locally associated with an ATS account

        :param account_id: int, id of the ATS account.
        :rtype string, JSON with all candidates.
        """

        ats_service.app.logger.info("{} {} {} {}\n".format(request.method, request.path, request.user.email, request.user.id))
        authenticated_user = request.user
        account = ATSAccount.get_by_id(account_id)
        if not account:
            ats_service.app.logger.info("ATS account not found {}".format(account_id))
            response = json.dumps(dict(account_id=account_id, message="ATS account not found {}".format(account_id)))
            headers = dict(Location=ATSServiceApiUrl.CANDIDATES % account)
            return ApiResponse(response, headers=headers, status=codes.NOT_FOUND)

        candidates = ATSCandidate.get_all_as_json(account_id)
        if candidates:
            return candidates

        ats_service.app.logger.info("No candidates in ATS account {}".format(account_id))
        response = json.dumps(dict(account_id=account_id, message="No candidates in ATS account {}".format(account_id)))
        headers = dict(Location=ATSServiceApiUrl.CANDIDATES % account)
        return ApiResponse(response, headers=headers, status=codes.NOT_FOUND)

    def post(self, account_id):
        """
        POST /v1/ats-candidates/:account_id

        Create a new ATS candidate.

        :param account_id: int, id of the ATS account.
        :rtype string, JSON indicating success.
        """

        ats_service.app.logger.info("{} {} {} {}\n".format(request.method, request.path, request.user.email, request.user.id))
        authenticated_user = request.user
        data = get_valid_json_data(request)

        # Validate data fields
        validate_ats_candidate_data(data)

        # Validate ATS Account
        account = ATSAccount.get_by_id(account_id)
        if not account:
            ats_service.app.logger.info("Attempt to create ATS candidate in non-existant ATS {}".format(data['ats_name']))
            response = json.dumps(dict(ats=data['ats_name'], message="Create candidate: non-existant ATS {}".format(account_id)))
            headers = dict(Location=ATSServiceApiUrl.CANDIDATES % account)
            return ApiResponse(response, headers=headers, status=codes.NOT_FOUND)

        # Create the candidate. No attempt to determine if duplicate.
        candidate = new_ats_candidate(account, data)

        response = json.dumps(dict(id=candidate.id, message="ATS candidate successfully created."))
        headers = dict(Location=ATSServiceApiUrl.CANDIDATES % candidate.id)
        return ApiResponse(response, headers=headers, status=codes.CREATED)


@api.route(ATSServiceApi.CANDIDATE)
class ATSCandidateService(Resource):
    """
    Controller for /v1/ats-candidates/:candidate_id/:ats_candidate_id
    """

    decorators = [require_oauth()]

    def post(self, candidate_id, ats_candidate_id):
        """
        POST /v1/ats-candidates/:candidate_id/:ats_candidate_id

        Link a getTalent candidate to an ATS candidate.

        :param candidate_id: int, id of the getTalent candidate.
        :param ats_candidate_id: int, id of the ATS candidate.
        :rtype string, JSON indicating success.
        """

        ats_service.app.logger.info("{} {} {} {}\n".format(request.method, request.path, request.user.email, request.user.id))
        link_ats_candidate(candidate_id, ats_candidate_id)

        return  "{ link : success }"

    def delete(self, candidate_id, ats_candidate_id):
        """
        DELETE /v1/ats-candidates/:candidate_id/:ats_candidate_id

        Unlink a getTalent candidate from an ATS candidate.

        :param candidate_id: int, id of the getTalent candidate.
        :param ats_candidate_id: int, id of the ATS candidate.
        :rtype string, JSON indicating success.
        """

        ats_service.app.logger.info("{} {} {} {}\n".format(request.method, request.path, request.user.email, request.user.id))
        unlink_ats_candidate(candidate_id, ats_candidate_id)

        return "{ unlink : success }"


@api.route(ATSServiceApi.CANDIDATES_REFRESH)
class ATSCandidateRefreshService(Resource):
    """
    Controller for /v1/ats-candidates/refresh/:account_id
    """

    decorators = [require_oauth()]

    def get(self, account_id):
        """
        GET /v1/ats-candidates/refresh/:account_id

        Update our local store of ATS candidates associated with an account from the ATS itself.

        :param account_id: int, id of the ATS account.
        :rtype string, JSON indicating success.
        """

        ats_service.app.logger.info("{} {} {} {}\n".format(request.method, request.path, request.user.email, request.user.id))
        authenticated_user = request.user

        # Magic happens here

        return "{{ account_id : {},  refresh : success }}".format(account_id)
