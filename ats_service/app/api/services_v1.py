"""
Classes implementing the ATS services endpoints.
"""

__author__ = 'Joseph Arceneaux'

import types
import json

from flask import request, Blueprint
from flask_restful import Resource
from requests import codes

# Decorators
from ats_service.common.utils.auth_utils import require_oauth

# Modules
from ats_service.common.routes import ATSServiceApi, ATSServiceApiUrl
from ats_service.common.models.ats import ATSCandidate
from ats_service.common.utils.api_utils import ApiResponse, api_route
from ats_service.common.talent_api import TalentApi
from ats_service.common.utils.handy_functions import get_valid_json_data
from ats_service.common.error_handling import *
from ats_service.ats.workday import *

from ats_utils import (validate_ats_account_data,
                       validate_ats_candidate_data,
                       invalid_account_fields_check,
                       new_ats,
                       new_ats_account,
                       update_ats_account,
                       delete_ats_account,
                       new_ats_candidate,
                       delete_ats_candidate,
                       update_ats_candidate,
                       link_ats_candidate,
                       unlink_ats_candidate,
                       fetch_auth_data,
                       create_ats_object)

# Why doesn't this work?
# from ats_service.app import logger
import ats_service.app

# Database
from ats_service.common.models.ats import ATS, ATSAccount, ATSCredential, ATSCandidate, ATSCandidateProfile


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

        ats_service.app.logger.info("{} {} {} {}".format(request.method, request.path, request.user.email, request.user.id))

        response = ATS.get_all_as_json()
        ats_service.app.logger.info("RESPONSE: {}".format(response))
        headers = dict(Location=ATSServiceApiUrl.ATS)
        # TODO
        # return ApiResponse(response, headers=headers, status=codes.OK)
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

        ats_service.app.logger.info("{} {} {} {}".format(request.method, request.path, request.user.email, request.user.id))
        account = ATSAccount.get_by_id(account_id)
        if not account:
            raise NotFoundError('Account id not found', additional_error_info=dict(account_id=account_id))

        account_dict = account.to_dict()
        credentials = ATSCredential.get_by_id(account.ats_credential_id)
        ats = ATS.get_by_id(account.ats_id)
        account_dict.update({'credentials' : credentials.credentials_json,
                             'ats_name' : ats.name, 'ats_homepage' : ats.homepage_url,
                             'ats_login' : ats.login_url})

        # TODO: Normalize response format; add values per Apiary doc.
        response = json.dumps(account_dict)
        headers = dict(Location=ATSServiceApiUrl.ACCOUNT % account_id)
        # TODO:
        # return ApiResponse(response, headers=headers, status=codes.OK)
        return response

    def delete(self, account_id):
        """
        DELETE /v1/ats-accounts/:account_id

        Decommission an ATS account for a user.

        :param account_id: int, id of the ATS account.
        :rtype string, JSON indicating success.
        """

        ats_service.app.logger.info("{} {} {} {}".format(request.method, request.path, request.user.email, request.user.id))
        delete_ats_account(request.user.id, account_id)

        return '{"delete" : "success"}'

    def put(self, account_id):
        """
        PUT /v1/ats-accounts/:account_id

        Modify an existing ATS account.

        :param account_id: int, id of the ATS account.
        :rtype string, JSON indicating success.
        """

        # Validate data fields
        ats_service.app.logger.info("{} {} {} {}".format(request.method, request.path, request.user.email, request.user.id))
        data = get_valid_json_data(request)
        invalid_account_fields_check(data)

        # Update the account
        # TODO: Handle the 'active' field
        update_ats_account(account_id, data)
        ats_service.app.logger.info("ATS account updated {}".format(account_id))

        response = json.dumps(dict(id=account_id, message="ATS account updated."))
        headers = dict(Location=ATSServiceApiUrl.ACCOUNT % account_id)
        return ApiResponse(response, headers=headers, status=codes.CREATED)


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

        ats_service.app.logger.info("{} {} {} {}".format(request.method, request.path, request.user.email, request.user.id))

        account_list = ATSAccount.get_user_accounts(request.user.id)
        response = json.dumps(account_list)
        headers = dict(Location=ATSServiceApiUrl.ACCOUNT % request.user.id)
        return ApiResponse(response, headers=headers, status=codes.OK)

    def post(self):
        """
        POST /v1/ats-accounts/

        Register an ATS account for a user.

        :rtype string, JSON indicating success.
        """

        ats_service.app.logger.info("{} {} {} {}".format(request.method, request.path, request.user.email, request.user.id))
        authenticated_user = request.user
        # data['active'] = True
        data = get_valid_json_data(request)

        # Validate data fields
        validate_ats_account_data(data)

        # Search for this ATS account entry already existing
        account = ATSAccount.get_account(authenticated_user.id, data['ats_name'])
        if account:
            raise NotFoundError('Account id not found', additional_error_info=dict(account_id=account_id))

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

        ats_service.app.logger.info("{} {} {} {}".format(request.method, request.path, request.user.email, request.user.id))
        account = ATSAccount.get_by_id(account_id)
        if not account:
            raise NotFoundError('Account id not found', additional_error_info=dict(account_id=account_id))

        candidates = ATSCandidate.get_all_as_json(account_id)
        if candidates:
            # TODO: Normalize this response
            # TODO: Add the ATS-particular entry.
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

        ats_service.app.logger.info("{} {} {} {}".format(request.method, request.path, request.user.email, request.user.id))
        data = get_valid_json_data(request)

        # Validate data fields
        validate_ats_candidate_data(data)

        # Validate ATS Account
        account = ATSAccount.get_by_id(account_id)
        if not account:
            raise NotFoundError('Account id not found', additional_error_info=dict(account_id=account_id))

        # Create the candidate. No attempt to determine if duplicate.
        candidate = new_ats_candidate(account_id, data)

        response = json.dumps(dict(id=candidate.id, message="ATS candidate successfully created."))
        headers = dict(Location=ATSServiceApiUrl.CANDIDATES % candidate.id)
        return ApiResponse(response, headers=headers, status=codes.CREATED)


@api.route(ATSServiceApi.CANDIDATE)
class ATSCandidateService(Resource):
    """
    Controller for /v1/ats-candidates/:account_id/:candidate_id
    """

    decorators = [require_oauth()]

    def get(self, account_id, candidate_id):
        """
        GET /v1/ats-candidates/:account_id/:candidate_id

        Retrieve an ATS candidate stored locally associated with an ATS account

        :param account_id: int, id of the ATS account.
        :param candidate_id: int, id of the ATS account.
        :rtype string, JSON with all candidates.
        """
        ats_service.app.logger.info("{} {} {} {}".format(request.method, request.path, request.user.email, request.user.id))

        candidate = ATSCandidate.get_by_id(candidate_id)
        if not candidate:
            raise NotFoundError('Candidate id not found', additional_error_info=dict(candidate_id=candidate_id))

        profile = ATSCandidateProfile.get_by_id(candidate.profile_id)
        if not profile:
            raise NotFoundError('Candidate profile id not found', additional_error_info=dict(profile_id=candidate.profile_id))

        candidate_dict = dict(id=candidate_id, ats_account_id=candidate.ats_account_id, ats_remote_id=candidate.ats_remote_id,
                              gt_candidate_id=candidate.gt_candidate_id, profile_json=profile.profile_json)
        response = json.dumps(candidate_dict)
        headers = dict(Location=ATSServiceApiUrl.CANDIDATE % (account_id, candidate_id))
        return ApiResponse(response, headers=headers, status=codes.OK)

    def put(self, account_id, candidate_id):
        """
        PUT /v1/ats-candidates/:account_id/:candidate_id

        Update an ATS candidate.

        :param account_id: int, id of the ATS account.
        :param candidate_id: int, id of the ATS candidate.
        :rtype string, JSON indicating success.
        """

        ats_service.app.logger.info("{} {} {} {}".format(request.method, request.path, request.user.email, request.user.id))
        data = get_valid_json_data(request)

        # Validate data fields
        validate_ats_candidate_data(data)

        # Update the candidate.
        candidate = update_ats_candidate(account_id, candidate_id, data)

        response = json.dumps(dict(id=candidate.id, message="ATS candidate successfully updated."))
        headers = dict(Location=ATSServiceApiUrl.CANDIDATES % candidate.id)
        return ApiResponse(response, headers=headers, status=codes.CREATED)

    def delete(self, account_id, candidate_id):
        """
        DELETE /v1/ats-candidates/:account_id/:candidate_id

        Delete an ATS candidate.

        :param account_id: int, id of the ATS account.
        :param candidate_id: int, id of the ATS candidate.
        :rtype string, JSON indicating success.
        """

        ats_service.app.logger.info("{} {} {} {}".format(request.method, request.path, request.user.email, request.user.id))
        delete_ats_candidate(candidate_id)

        response = json.dumps(dict(delete='success'))
        headers = dict(Location=ATSServiceApiUrl.CANDIDATES % candidate_id)
        return ApiResponse(response, headers=headers, status=codes.OK)


@api.route(ATSServiceApi.CANDIDATE_LINK)
class ATSCandidateLinkService(Resource):
    """
    Controller for /v1/ats-candidates/link/:candidate_id/:ats_candidate_id
    """

    decorators = [require_oauth()]

    def post(self, candidate_id, ats_candidate_id):
        """
        POST /v1/ats-candidates/link/:candidate_id/:ats_candidate_id

        Link a getTalent candidate to an ATS candidate.

        :param candidate_id: int, id of the getTalent candidate.
        :param ats_candidate_id: int, id of the ATS candidate.
        :rtype string, JSON indicating success.
        """

        ats_service.app.logger.info("{} {} {} {}".format(request.method, request.path, request.user.email, request.user.id))
        link_ats_candidate(candidate_id, ats_candidate_id)

        response = json.dumps(dict(id=candidate_id, message="ATS candidate successfully linked."))
        headers = dict(Location=ATSServiceApiUrl.CANDIDATE_LINK % (candidate_id, ats_candidate_id))
        return ApiResponse(response, headers=headers, status=codes.CREATED)

    def delete(self, candidate_id, ats_candidate_id):
        """
        DELETE /v1/ats-candidates/link/:candidate_id/:ats_candidate_id

        Unlink a getTalent candidate from an ATS candidate.

        :param candidate_id: int, id of the getTalent candidate.
        :param ats_candidate_id: int, id of the ATS candidate.
        :rtype string, JSON indicating success.
        """

        ats_service.app.logger.info("{} {} {} {}".format(request.method, request.path, request.user.email, request.user.id))
        unlink_ats_candidate(candidate_id, ats_candidate_id)

        response = json.dumps(dict(unlink='success'))
        headers = dict(Location=ATSServiceApiUrl.CANDIDATE_LINK % (candidate_id, ats_candidate_id))
        return ApiResponse(response, headers=headers, status=codes.OK)


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

        ats_service.app.logger.info("{} {} {} {}".format(request.method, request.path, request.user.email, request.user.id))

        # Create an ATS-specific object
        ats_name, url, user_id, credentials = fetch_auth_data(account_id)
        if not url:
            return '{{"account_id" : {},  "status" : "inactive"}}'.format(account_id)

        # Authenticate
        ats_object = create_ats_object(ats_service.app.logger, ats_name, url, user_id, credentials)
        ats_object.authenticate()

        # Get all candidate ids (references)
        individual_references = ats_object.fetch_individual_references()

        # For each candidate, fetch the candidate data and update our copy. Later this can be combined with the previous step.
        return_list = []
        created_count = 0
        updated_count = 0
        for ref in individual_references:
            individual = ats_object.fetch_individual(ref)
            return_list.append(individual)
            data = { 'profile_json' : individual, 'ats_remote_id' : ref }

            present = ATSCandidate.get_by_ats_id(account_id, ref)
            if present:
                # Update this individual
                if present.ats_table_id:
                    data['ats_table_id'] = present.ats_table_id
                update_ats_candidate(account_id, present.id, data)
                ats_object.save_individual(json.dumps(data), present.id)
                updated_count += 1
            else:
                # Create a new individual
                candidate = new_ats_candidate(account_id, data)
                i = ats_object.save_individual(json.dumps(data), candidate.id)
                data['ats_table_id'] = i.id
                update_ats_candidate(account_id, candidate.id, data)
                created_count += 1

        response = json.dumps(dict(updated_count=updated_count, created_count=created_count))
        headers = dict(Location=ATSServiceApiUrl.CANDIDATES_REFRESH % account_id)
        return ApiResponse(response, headers=headers, status=codes.OK)
