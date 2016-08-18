"""
This file entails Candidate-restful-services for CRUD operations.
Notes:
    i. "optional-input" indicates that the resource can handle
    other specified inputs or no inputs (if not specified)
"""
# Standard libraries
import logging, datetime, os, requests, json
from time import time
from datetime import date

# Third Party
from redo import retry
from _mysql_exceptions import OperationalError

# Flask specific
from flask import request
from flask_restful import Resource
from candidate_service.candidate_app import logger

# Database connection
from candidate_service.common.models.db import db

# Validators

from candidate_service.common.talent_config_manager import TalentConfigKeys
from candidate_service.common.talent_config_manager import TalentEnvs
from candidate_service.common.utils.models_utils import to_json
from candidate_service.common.utils.validators import is_valid_email, is_country_code_valid, is_number
from candidate_service.modules.validators import (
    does_candidate_belong_to_users_domain, is_custom_field_authorized,
    is_area_of_interest_authorized, do_candidates_belong_to_users_domain,
    is_valid_email_client, get_json_if_exist, is_date_valid,
    get_json_data_if_validated, get_candidate_if_validated
)

# JSON Schemas
from candidate_service.modules.json_schema import (
    candidates_resource_schema_post, candidates_resource_schema_patch, resource_schema_preferences,
    resource_schema_photos_post, resource_schema_photos_patch, language_schema,
)
from jsonschema import validate, FormatChecker, ValidationError
from candidate_service.common.utils.datetime_utils import DatetimeUtils

# Decorators
from candidate_service.common.utils.auth_utils import require_oauth, require_all_permissions

# Error handling
from candidate_service.common.error_handling import (
    ForbiddenError, InvalidUsage, NotFoundError, InternalServerError, ResourceNotFound
)
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error

# Models
from candidate_service.common.models.candidate import (
    Candidate, CandidateAddress, CandidateEducation, CandidateEducationDegree,
    CandidateEducationDegreeBullet, CandidateExperience, CandidateExperienceBullet,
    CandidateWorkPreference, CandidateEmail, CandidatePhone, CandidateMilitaryService,
    CandidatePreferredLocation, CandidateSkill, CandidateSocialNetwork, CandidateDevice,
    CandidateSubscriptionPreference, CandidatePhoto, CandidateSource,
    CandidateStatus
)
from candidate_service.common.models.language import CandidateLanguage
from candidate_service.common.models.misc import AreaOfInterest, Frequency, CustomField
from candidate_service.common.models.talent_pools_pipelines import TalentPipeline, TalentPool
from candidate_service.common.models.associations import CandidateAreaOfInterest
from candidate_service.common.models.user import User, Permission

# Module
from candidate_service.modules.talent_candidates import (
    fetch_candidate_info, get_candidate_id_from_email_if_exists_in_domain,
    create_or_update_candidate_from_params, fetch_candidate_edits, fetch_candidate_views,
    add_candidate_view, fetch_candidate_subscription_preference,
    add_or_update_candidate_subs_preference, add_photos, update_photo,
    fetch_aggregated_candidate_views, update_total_months_experience, fetch_candidate_languages,
    add_languages, update_candidate_languages, CachedData
)
from candidate_service.modules.candidate_engagement import calculate_candidate_engagement_score
from candidate_service.modules.api_calls import create_smartlist, create_campaign, create_campaign_send
from candidate_service.modules.talent_cloud_search import upload_candidate_documents, delete_candidate_documents
from candidate_service.modules.talent_openweb import (
    match_candidate_from_openweb, convert_dice_candidate_dict_to_gt_candidate_dict,
    find_in_openweb_by_email
)
from candidate_service.modules.contsants import ONE_SIGNAL_APP_ID, ONE_SIGNAL_REST_API_KEY
from onesignalsdk.one_signal_sdk import OneSignalSdk
from candidate_service.common.utils.handy_functions import normalize_value

from candidate_service.common.inter_service_calls.candidate_pool_service_calls import assert_smartlist_candidates


class CandidatesResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_ADD_CANDIDATES)
    def post(self):
        """
        Endpoint:  POST /v1/candidates
        Input: {'candidates': [CandidateObject, CandidateObject, ...]}

        Function Creates new candidate(s).

        Caveats:
             i. Requires a JSON dict containing a 'candidates'-key
                 and a-list-of-candidate-dict(s) as values
            ii. JSON dict must contain at least one CandidateObject.

        :return: {'candidates': [{'id': candidate_id}, {'id': candidate_id}, ...]}
        """
        start_time = time()

        # Validate and retrieve json data
        body_dict = get_json_data_if_validated(request, candidates_resource_schema_post)

        # Get authenticated user & user's domain ID
        authed_user = request.user
        domain_id = authed_user.domain_id

        candidates = body_dict.get('candidates')

        # Input validations
        is_creating, is_updating, candidate_id = True, False, None
        all_cf_ids, all_aoi_ids = [], []
        email_addresses = []
        for candidate_dict_ in candidates:

            candidate_ids_from_candidate_email_obj = []

            email_addresses.extend(email.get('address') for email in candidate_dict_.get('emails') or [])

            # Strip, lower, and remove empty email addresses
            email_addresses = filter(None, map(normalize_value, email_addresses))

            # All email addresses must be valid emails
            if not all(map(is_valid_email, email_addresses)):
                raise InvalidUsage('Invalid email address/format: {}'.format(email_addresses),
                                   error_code=custom_error.INVALID_EMAIL)

            candidate_email_objects = CandidateEmail.get_emails_in_domain(domain_id, email_addresses)
            for candidate_email_obj in candidate_email_objects:

                # Cache candidate's email
                CachedData.candidate_emails.append(candidate_email_obj)

                candidate_id = candidate_email_obj.candidate_id

                # We need to prevent duplicate creation in case candidate has multiple email addresses in db
                candidate_ids_from_candidate_email_obj.append(candidate_id)
                candidate = Candidate.get_by_id(candidate_id)

                # Raise error if candidate is not hidden and its email matches another candidate's email
                if not candidate.is_web_hidden and (candidate_email_obj not in CachedData.candidate_emails):
                    # Clear cached data
                    CachedData.candidate_emails = []

                    raise InvalidUsage('Candidate with email: {}, already exists'.format(candidate_email_obj.address),
                                       error_code=custom_error.CANDIDATE_ALREADY_EXISTS,
                                       additional_error_info={'id': candidate_id})

                # Un-hide candidate from web, if found
                if candidate.is_web_hidden:
                    candidate.is_web_hidden = 0

                    # If candidate's web-hidden is set to false, it will be treated as an update
                    is_creating, is_updating = False, True

                elif candidate_id in candidate_ids_from_candidate_email_obj:
                    continue

            # Provided source ID must belong to candidate's domain
            source_id = candidate_dict_.get('source_id')
            if source_id:
                if not CandidateSource.get_domain_source(source_id=source_id, domain_id=domain_id):
                    raise InvalidUsage("Provided source ID ({source_id}) not "
                                       "recognized for candidate's domain (id = {domain_id})"
                                       .format(source_id=source_id, domain_id=domain_id),
                                       error_code=custom_error.INVALID_SOURCE_ID)

            source_product_id = candidate_dict_.get('source_product_id', 2)
            if source_product_id and (not is_number(source_product_id) or int(source_product_id) not in (1, 2, 3, 4)):
                raise InvalidUsage("Provided source product id ({source_product_id}) not recognized".format(
                        source_product_id=source_product_id),  error_code=custom_error.INVALID_SOURCE_PRODUCT_ID)

            candidate_dict_['source_product_id'] = int(source_product_id)

            for custom_field in candidate_dict_.get('custom_fields') or []:
                custom_field_id = custom_field.get('custom_field_id')
                if custom_field_id:
                    if not CustomField.get_by_id(_id=custom_field_id):
                        raise NotFoundError('Custom field not recognized: {}'.format(custom_field_id),
                                            custom_error.CUSTOM_FIELD_NOT_FOUND)
                all_cf_ids.append(custom_field_id)

            for aoi in candidate_dict_.get('areas_of_interest') or []:
                aoi_id = aoi.get('area_of_interest_id')
                if aoi_id:
                    if not AreaOfInterest.get_by_id(_id=aoi_id):
                        raise NotFoundError('Area of interest not recognized: {}'.format(aoi_id),
                                            custom_error.AOI_NOT_FOUND)
                all_aoi_ids.append(aoi_id)

            # to_date & from_date in military_service dict must be formatted properly
            for military_service in candidate_dict_.get('military_services') or []:
                from_date, to_date = military_service.get('from_date'), military_service.get('to_date')
                if from_date:
                    if not is_date_valid(date=from_date):
                        raise InvalidUsage("Military service's date must be in a date format",
                                           error_code=custom_error.MILITARY_INVALID_DATE)
                elif to_date:
                    if not is_date_valid(date=to_date):
                        raise InvalidUsage("Military service's date must be in a date format",
                                           error_code=custom_error.MILITARY_INVALID_DATE)
                country_code = military_service['country_code'].upper() if military_service.get('country_code') else None
                if country_code:
                    if not is_country_code_valid(country_code):
                        raise InvalidUsage("Country code not recognized: {}".format(country_code))

        # Custom fields must belong to user's domain
        if all_cf_ids:
            if not is_custom_field_authorized(domain_id, all_cf_ids):
                raise ForbiddenError("Unauthorized custom field IDs", custom_error.CUSTOM_FIELD_FORBIDDEN)

        # Areas of interest must belong to user's domain
        if all_aoi_ids:
            if not is_area_of_interest_authorized(domain_id, all_aoi_ids):
                raise ForbiddenError("Unauthorized area of interest IDs", custom_error.AOI_FORBIDDEN)

        # Create candidate(s)
        created_candidate_ids = []
        for candidate_dict in candidates:

            user_id = authed_user.id
            emails = [
                {
                    'label': (email.get('label') or '').strip(),
                    'address': email['address'].strip(),
                    'is_default': email.get('is_default')
                } for email in candidate_dict.get('emails') or []
            ] if email_addresses else None  # CandidateEmail object must only be created if email has an address

            added_datetime = DatetimeUtils.isoformat_to_mysql_datetime(candidate_dict['added_datetime']) \
                if candidate_dict.get('added_datetime') else None

            resp_dict = create_or_update_candidate_from_params(
                user_id=user_id,
                is_creating=is_creating,
                is_updating=is_updating,
                candidate_id=candidate_id,
                first_name=candidate_dict.get('first_name'),
                middle_name=candidate_dict.get('middle_name'),
                last_name=candidate_dict.get('last_name'),
                formatted_name=candidate_dict.get('full_name'),
                status_id=candidate_dict.get('status_id') or CandidateStatus.DEFAULT_STATUS_ID,
                emails=emails,
                phones=candidate_dict.get('phones'),
                addresses=candidate_dict.get('addresses'),
                educations=candidate_dict.get('educations'),
                military_services=candidate_dict.get('military_services'),
                areas_of_interest=candidate_dict.get('areas_of_interest'),
                custom_fields=candidate_dict.get('custom_fields'),
                social_networks=candidate_dict.get('social_networks'),
                work_experiences=candidate_dict.get('work_experiences'),
                work_preference=candidate_dict.get('work_preference'),
                preferred_locations=candidate_dict.get('preferred_locations'),
                skills=candidate_dict.get('skills'),
                dice_social_profile_id=candidate_dict.get('openweb_id'),
                dice_profile_id=candidate_dict.get('dice_profile_id'),
                added_datetime=added_datetime,
                source_id=candidate_dict.get('source_id'),
                source_product_id=candidate_dict.get('source_product_id'),
                objective=candidate_dict.get('objective'),
                summary=candidate_dict.get('summary'),
                talent_pool_ids=candidate_dict.get('talent_pool_ids', {'add': [], 'delete': []}),
                resume_url=candidate_dict.get('resume_url')
            )
            created_candidate_ids.append(resp_dict['candidate_id'])

        # Add candidates to cloud search
        upload_candidate_documents.delay(created_candidate_ids)

        logger.info('BENCHMARK - candidate POST: \nuser_id: {user_id}\ndomain_id: {domain_id}\ntime: {t}'.
                    format(user_id=authed_user.id, domain_id=authed_user.domain_id, t=time() - start_time))

        return {'candidates': [{'id': candidate_id} for candidate_id in created_candidate_ids]}, requests.codes.CREATED

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def patch(self, **kwargs):
        """
        Endpoints:
             i. PATCH /v1/candidates
            ii. PATCH /v1/candidates/:id

        Function can update any of candidate(s)'s information.

        Caveats:
              i. Requires a JSON dict containing a 'candidates'-key and a-list-of-candidate-dict(s) as values
             ii. Each JSON dict must contain candidate's ID
            iii. To update any of candidate's fields, the field ID must be provided,
                 otherwise a new record will be added to the specified candidate
        Usage:
            >>> url = 'host/v1/candidates'
            >>> headers = {'Authorization': 'Bearer {access_token}', 'content-type': 'application/json'}
            >>> data =
                        {
                            'candidates': [
                                {
                                    'id': 4, 'objective': 'looking for new opportunity',
                                    'emails': [
                                        {'id': 546, 'address': 'updated.address@example.com'}
                                    ]
                                }
                            ]
                        }
            >>> requests.patch(url=url, headers=headers, data=json.dumps(data))
            <Response [200]>

        :return: {'candidates': [{'id': candidate_id}, {'id': candidate_id}, ...]}
        """
        start_time = time()

        # Validate and retrieve json data
        body_dict = get_json_data_if_validated(request, candidates_resource_schema_patch)

        # Get authenticated user & candidate ID
        authed_user, candidate_id_from_url = request.user, kwargs.get('id')

        domain_id = authed_user.domain_id

        # If candidate ID is provided via url, only one candidate update is permitted
        candidates = body_dict['candidates']
        if candidate_id_from_url and len(candidates) > 1:
            raise InvalidUsage(
                "Error: You requested an update for one candidate but provided data for multiple candidates.",
                custom_error.INVALID_USAGE)

        # Input validations
        skip = False  # If True, skip all validations & unnecessary db communications for candidates that must be hidden
        all_cf_ids, all_aoi_ids = [], []
        hidden_candidate_ids = []  # Aggregate candidate IDs that will be hidden
        for _candidate_dict in candidates:

            # Candidate ID must be provided in json dict or in the url
            candidate_id = candidate_id_from_url or _candidate_dict.get('id')
            if not candidate_id:
                raise InvalidUsage("Candidate ID is required", custom_error.INVALID_USAGE)

            # Candidate must belong to user's domain
            if not does_candidate_belong_to_users_domain(authed_user, candidate_id):
                raise ForbiddenError("Not authorized", custom_error.CANDIDATE_FORBIDDEN)

            # Check for candidate's existence
            candidate = Candidate.get_by_id(candidate_id)
            if not candidate:
                raise NotFoundError('Candidate not found: {}'.format(candidate_id), custom_error.CANDIDATE_NOT_FOUND)

            # Hide or un-hide candidate if requested
            hide_candidate = _candidate_dict.get('hide')
            if hide_candidate is True:
                candidate.is_web_hidden = 1
                hidden_candidate_ids.append(candidate_id)
                skip = True
            else:  # json-schema will only allow True or False
                candidate.is_web_hidden = 0

            # No need to validate anything since candidate is set to hidden
            if not skip:
                # Check if candidate is web-hidden
                if candidate.is_web_hidden:
                    raise NotFoundError('Candidate not found: {}'.format(candidate_id),
                                        custom_error.CANDIDATE_IS_HIDDEN)

                # Emails' addresses must be properly formatted
                for emails in _candidate_dict.get('emails') or []:
                    if emails.get('address'):
                        if not is_valid_email(emails.get('address')):
                            raise InvalidUsage("Invalid email address/format", custom_error.INVALID_EMAIL)

                for custom_field in _candidate_dict.get('custom_fields') or []:
                    all_cf_ids.append(custom_field.get('custom_field_id'))

                for aoi in _candidate_dict.get('areas_of_interest') or []:
                    all_aoi_ids.append(aoi.get('area_of_interest_id'))

                # to_date & from_date in military_service dict must be formatted properly
                for military_service in _candidate_dict.get('military_services') or []:
                    from_date, to_date = military_service.get('from_date'), military_service.get('to_date')
                    if from_date:
                        if not is_date_valid(date=from_date):
                            raise InvalidUsage("Military service's date must be in a date format",
                                               error_code=custom_error.MILITARY_INVALID_DATE)
                    elif to_date:
                        if not is_date_valid(date=to_date):
                            raise InvalidUsage("Military service's date must be in a date format",
                                               error_code=custom_error.MILITARY_INVALID_DATE)

            # If source_id key is not provided, its value must default to empty string
            # this is because this API will treat NULL values as "delete the record"
            source_id = _candidate_dict.get('source_id', '')

            # Provided source ID must belong to candidate's domain
            if source_id:
                if not CandidateSource.get_domain_source(source_id=source_id, domain_id=domain_id):
                    raise InvalidUsage("Provided source ID ({source_id}) not "
                                       "recognized for candidate's domain (id = {domain_id})"
                                       .format(source_id=source_id, domain_id=domain_id),
                                       error_code=custom_error.INVALID_SOURCE_ID)

            source_product_id = _candidate_dict.get('source_product_id')
            if source_product_id and (not is_number(source_product_id) or int(source_product_id) not in (1, 2, 3, 4)):
                raise InvalidUsage("Provided source product id ({source_product_id}) not recognized".format(
                        source_product_id=source_product_id),  error_code=custom_error.INVALID_SOURCE_PRODUCT_ID)

            _candidate_dict['source_product_id'] = int(source_product_id) if source_product_id else None

        if skip:
            db.session.commit()
            # Delete candidate from CS when set to hidden
            delete_candidate_documents(hidden_candidate_ids)
            return {'hidden_candidate_ids': hidden_candidate_ids}, requests.codes.OK

        # Custom fields must belong to user's domain
        if all_cf_ids:
            if not is_custom_field_authorized(domain_id, all_cf_ids):
                raise ForbiddenError("Unauthorized custom field IDs", custom_error.CUSTOM_FIELD_FORBIDDEN)

        # Areas of interest must belong to user's domain
        if all_aoi_ids:
            if not is_area_of_interest_authorized(domain_id, all_aoi_ids):
                raise ForbiddenError("Unauthorized area of interest IDs", custom_error.AOI_FORBIDDEN)

        # Candidates must belong to user's domain
        list_of_candidate_ids = [_candidate_dict.get('id') for _candidate_dict in candidates]
        if not do_candidates_belong_to_users_domain(authed_user, list_of_candidate_ids):
            raise ForbiddenError('Not authorized', custom_error.CANDIDATE_FORBIDDEN)

        # Update candidate(s)
        updated_candidate_ids = []
        for candidate_dict in candidates:

            emails = candidate_dict.get('emails')
            if emails:
                emails = [{'id': email.get('id'), 'label': email.get('label'),
                           'address': email.get('address'), 'is_default': email.get('is_default')}
                          for email in candidate_dict.get('emails')]

            added_datetime = DatetimeUtils.isoformat_to_mysql_datetime(candidate_dict['added_datetime']) \
                if candidate_dict.get('added_datetime') else None

            """
            status_id, source_id, objective, summary, and resume_url will default to an empty-string
            if the keys are not provided in the request body. This is because NULL values for the
            aforementioned fields will be treated as "delete the record"
            """
            resp_dict = create_or_update_candidate_from_params(
                user_id=authed_user.id,
                is_updating=True,
                candidate_id=candidate_dict.get('id') or candidate_id_from_url,
                first_name=candidate_dict.get('first_name'),
                middle_name=candidate_dict.get('middle_name'),
                last_name=candidate_dict.get('last_name'),
                formatted_name=candidate_dict.get('full_name'),
                status_id=candidate_dict.get('status_id', ''),
                emails=emails,
                phones=candidate_dict.get('phones'),
                addresses=candidate_dict.get('addresses'),
                educations=candidate_dict.get('educations'),
                military_services=candidate_dict.get('military_services'),
                areas_of_interest=candidate_dict.get('areas_of_interest'),
                custom_fields=candidate_dict.get('custom_fields'),
                social_networks=candidate_dict.get('social_networks'),
                work_experiences=candidate_dict.get('work_experiences'),
                work_preference=candidate_dict.get('work_preference'),
                preferred_locations=candidate_dict.get('preferred_locations'),
                skills=candidate_dict.get('skills'),
                dice_social_profile_id=candidate_dict.get('openweb_id'),
                dice_profile_id=candidate_dict.get('dice_profile_id'),
                added_datetime=added_datetime,
                source_id=candidate_dict.get('source_id', ''),
                source_product_id=candidate_dict.get('source_product_id'),
                objective=candidate_dict.get('objective', ''),
                summary=candidate_dict.get('summary', ''),
                talent_pool_ids=candidate_dict.get('talent_pool_id', {'add': [], 'delete': []}),
                resume_url=candidate_dict.get('resume_url', '')
            )
            updated_candidate_ids.append(resp_dict['candidate_id'])

        # Update candidates in cloud search
        upload_candidate_documents.delay(updated_candidate_ids)
        logger.info('BENCHMARK - candidate PATCH: {}'.format(time() - start_time))
        return {'candidates': [{'id': updated_candidate_id} for updated_candidate_id in updated_candidate_ids]}


class CandidateResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CANDIDATES)
    def get(self, **kwargs):
        """
        Endpoints can do these operations:
            1. Fetch and return a candidate via two methods:
                I.  GET /v1/candidates/:id
                    Takes an integer as candidate's ID, retrieve from kwargs
                OR
                II. GET /v1/candidates/:email
                    Takes a valid email address, parsed from kwargs

        :return:    A dict of candidate info
        """
        start_time = time()
        # Get authenticated user
        authed_user = request.user

        # Either candidate_id or candidate_email must be provided
        candidate_id, candidate_email = kwargs.get('id'), kwargs.get('email')

        if candidate_email:
            # Email address must be valid
            if not is_valid_email(candidate_email):
                raise InvalidUsage("A valid email address is required", custom_error.INVALID_EMAIL)

            # Get candidate ID from candidate's email
            candidate_id = get_candidate_id_from_email_if_exists_in_domain(authed_user, candidate_email)

        # Check for candidate's existence and web-hidden status
        candidate = get_candidate_if_validated(authed_user, candidate_id)

        candidate_data_dict = fetch_candidate_info(candidate=candidate)
        candidate_data_dict['engagement_score'] = calculate_candidate_engagement_score(candidate_id)

        logger.info('BENCHMARK - candidate GET: {}'.format(time() - start_time))
        return {'candidate': candidate_data_dict}

    @require_all_permissions(Permission.PermissionNames.CAN_DELETE_CANDIDATES)
    def delete(self, **kwargs):
        """
        Endpoints can do these operations:
            1. Delete a candidate via two methods:
                I.  DELETE /v1/candidates/:id
                OR
                II. DELETE /v1/candidates/:email
        """
        # Get authenticated user
        authed_user = request.user
        candidate_id, candidate_email = kwargs.get('id'), kwargs.get('email')

        if candidate_email:
            # Email address must be valid
            if not is_valid_email(candidate_email):
                raise InvalidUsage("A valid email address is required", custom_error.INVALID_EMAIL)

            # Get candidate ID from candidate's email
            candidate_id = get_candidate_id_from_email_if_exists_in_domain(authed_user, candidate_email)

        # Check for candidate's existence and web-hidden status
        candidate = get_candidate_if_validated(authed_user, candidate_id)

        # Delete Candidate
        db.session.delete(candidate)
        db.session.commit()

        # Delete candidate from cloud search
        delete_candidate_documents([candidate_id])
        return '', 204


class CandidateAddressResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def delete(self, **kwargs):
        """
        Endpoints:
             i. DELETE /v1/candidates/:candidate_id/addresses
            ii. DELETE /v1/candidates/:candidate_id/addresses/:id
        Depending on the endpoint requested, function will delete all of Candidate's
        addresses or just a single one.
        """
        # Get authenticated user
        authed_user = request.user

        # Get candidate_id and address_id
        candidate_id, address_id = kwargs.get('candidate_id'), kwargs.get('id')

        # Check for candidate's existence and web-hidden status
        candidate = get_candidate_if_validated(authed_user, candidate_id)

        if address_id:  # Delete specified address
            candidate_address = CandidateAddress.get_by_id(_id=address_id)
            if not candidate_address:
                raise NotFoundError('Candidate address not found', custom_error.ADDRESS_NOT_FOUND)

            # Address must belong to Candidate
            if candidate_address.candidate_id != candidate_id:
                raise ForbiddenError('Not authorized', custom_error.ADDRESS_FORBIDDEN)

            db.session.delete(candidate_address)

        else:  # Delete all of candidate's addresses
            map(db.session.delete, candidate.addresses)

        db.session.commit()

        # Update cloud search
        upload_candidate_documents([candidate_id])
        return '', 204


class CandidateAreaOfInterestResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def delete(self, **kwargs):
        """
        Endpoints:
             i. DELETE /v1/candidates/:candidate_id/areas_of_interest
            ii. DELETE /v1/candidates/:candidate_id/areas_of_interest/:id
        Depending on the endpoint requested, function will delete all of Candidate's
        areas of interest or just a single one.
        """
        # Get authenticated user
        authed_user = request.user

        # Get candidate_id and area_of_interest_id
        candidate_id, area_of_interest_id = kwargs['candidate_id'], kwargs.get('id')

        # Check for candidate's existence and web-hidden status
        candidate = get_candidate_if_validated(authed_user, candidate_id)

        # Prevent user from deleting area_of_interest of candidates outside of its domain
        if not is_area_of_interest_authorized(authed_user.domain_id, [area_of_interest_id]):
            raise ForbiddenError("Unauthorized area of interest IDs", custom_error.AOI_FORBIDDEN)

        if area_of_interest_id:  # Delete specified area of interest
            # Area of interest must be associated with candidate's CandidateAreaOfInterest
            candidate_aoi = CandidateAreaOfInterest.get_aoi(candidate_id, area_of_interest_id)
            if not candidate_aoi:
                raise ForbiddenError("Unauthorized area of interest IDs", custom_error.AOI_FORBIDDEN)

            # Delete CandidateAreaOfInterest
            db.session.delete(candidate_aoi)

        else:  # Delete all of Candidate's areas of interest
            domain_aois = AreaOfInterest.get_domain_areas_of_interest(authed_user.domain_id)
            areas_of_interest_ids = [aoi.id for aoi in domain_aois]
            for aoi_id in areas_of_interest_ids:
                candidate_aoi = CandidateAreaOfInterest.get_aoi(candidate_id, aoi_id)
                if candidate_aoi:
                    db.session.delete(candidate_aoi)

        db.session.commit()

        # Update cloud search
        upload_candidate_documents([candidate_id])
        return '', 204


class CandidateEducationResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def delete(self, **kwargs):
        """
        Endpoints:
              i. DELETE /v1/candidates/:candidate_id/educations
             ii. DELETE /v1/candidates/:candidate_id/educations/:id
        Depending on the endpoint requested, function will delete all of Candidate's
        educations or just a single one.
        """
        # Get authenticated user
        authed_user = request.user

        # Get candidate_id and education_id
        candidate_id, education_id = kwargs.get('candidate_id'), kwargs.get('id')

        # Check for candidate's existence and web-hidden status
        candidate = get_candidate_if_validated(authed_user, candidate_id)

        if education_id:  # Delete specified Candidate's education
            can_education = CandidateEducation.get_by_id(_id=education_id)
            if not can_education:
                raise NotFoundError('Education not found', custom_error.EDUCATION_NOT_FOUND)

            # Education must belong to Candidate
            if can_education.candidate_id != candidate_id:
                raise ForbiddenError('Not authorized', custom_error.EDUCATION_FORBIDDEN)

            db.session.delete(can_education)

        else:  # Delete all of Candidate's educations
            map(db.session.delete, candidate.educations)

        db.session.commit()

        # Update cloud search
        upload_candidate_documents([candidate_id])
        return '', 204


class CandidateEducationDegreeResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def delete(self, **kwargs):
        """
        Endpoints:
             i. DELETE /v1/candidates/:candidate_id/educations/:education_id/degrees
            ii. DELETE /v1/candidates/:candidate_id/educations/:education_id/degrees/:id
        Depending on the endpoint requested, function will delete all of Candidate's
        education-degrees or just a single one.
        """
        # Get authenticated user
        authed_user = request.user

        # Get candidate_id, education_id, and degree_id
        candidate_id, education_id = kwargs.get('candidate_id'), kwargs.get('education_id')
        degree_id = kwargs.get('id')

        # Check for candidate's existence and web-hidden status
        get_candidate_if_validated(authed_user, candidate_id)

        if degree_id:  # Delete specified degree
            # Verify that degree belongs to education, and education belongs to candidate
            candidate_degree = db.session.query(CandidateEducation).join(CandidateEducationDegree). \
                filter(CandidateEducation.candidate_id == candidate_id). \
                filter(CandidateEducationDegree.id == degree_id).first()
            if not candidate_degree:
                raise NotFoundError('Education degree not found', custom_error.DEGREE_NOT_FOUND)

            db.session.delete(candidate_degree)

        else:  # Delete all degrees
            education = CandidateEducation.get_by_id(_id=education_id)
            if not education:
                raise NotFoundError('Education not found', custom_error.EDUCATION_NOT_FOUND)

            # Education must belong to candidate
            if education.candidate_id != candidate_id:
                raise ForbiddenError('Not Authorized', custom_error.EDUCATION_FORBIDDEN)

            map(db.session.delete, education.degrees)

        db.session.commit()

        # Update cloud search
        upload_candidate_documents([candidate_id])
        return '', 204


class CandidateEducationDegreeBulletResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def delete(self, **kwargs):
        """
        Endpoints:
             i. DELETE /v1/candidates/:candidate_id/educations/:education_id/degrees/:degree_id/bullets
            ii. DELETE /v1/candidates/:candidate_id/educations/:education_id/degrees/:degree_id/bullets/:id
        Depending on the endpoint requested, function will delete all of Candidate's
        education-degree-bullets or just a single one.
        """
        # Get authenticated user
        authed_user = request.user

        # Get required IDs
        candidate_id, education_id = kwargs.get('candidate_id'), kwargs.get('education_id')
        degree_id, bullet_id = kwargs.get('degree_id'), kwargs.get('id')

        # Check for candidate's existence and web-hidden status
        get_candidate_if_validated(authed_user, candidate_id)

        if bullet_id:  # Delete specified bullet
            # degree_bullet must belongs to degree; degree must belongs to education;
            # and education must belong to candidate
            candidate_degree_bullet = db.session.query(CandidateEducationDegreeBullet). \
                join(CandidateEducationDegree).join(CandidateEducation). \
                filter(CandidateEducation.candidate_id == candidate_id). \
                filter(CandidateEducation.id == education_id). \
                filter(CandidateEducationDegree.id == degree_id). \
                filter(CandidateEducationDegreeBullet.id == bullet_id).first()
            if not candidate_degree_bullet:
                raise NotFoundError('Degree bullet not found', custom_error.DEGREE_NOT_FOUND)

            db.session.delete(candidate_degree_bullet)

        else:  # Delete all bullets
            education = CandidateEducation.get_by_id(_id=education_id)
            if not education:
                raise NotFoundError('Candidate education not found', custom_error.EDUCATION_NOT_FOUND)

            # Education must belong to Candidate
            if education.candidate_id != candidate_id:
                raise ForbiddenError('Not authorized', custom_error.EDUCATION_FORBIDDEN)

            degree = db.session.query(CandidateEducationDegree).get(degree_id)
            if not degree:
                raise NotFoundError('Candidate education degree not found', custom_error.DEGREE_NOT_FOUND)

            degree_bullets = degree.bullets
            if not degree_bullets:
                raise NotFoundError(error_message='Candidate education degree bullet not found',
                                    error_code=custom_error.DEGREE_BULLET_NOT_FOUND)

            map(db.session.delete, degree_bullets)

        db.session.commit()

        # Update cloud search
        upload_candidate_documents([candidate_id])
        return '', 204


class CandidateWorkExperienceResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def delete(self, **kwargs):
        """
        Resources:
             i. DELETE /v1/candidates/:candidate_id/work_experiences
            ii. DELETE /v1/candidates/:candidate_id/work_experiences/:id
        Depending on the endpoint requested, function will delete all of Candidate's
        work_experiences or just a single one.
        """
        # Get authenticated user
        authed_user = request.user

        # Get candidate_id and experience_id
        candidate_id, experience_id = kwargs['candidate_id'], kwargs.get('id')

        # Check for candidate's existence and web-hidden status
        candidate = get_candidate_if_validated(authed_user, candidate_id)

        if experience_id:  # Delete specified experience
            experience = CandidateExperience.get_by_id(experience_id)
            if not experience:
                raise NotFoundError('Candidate experience not found', custom_error.EXPERIENCE_NOT_FOUND)

            # Experience must belong to Candidate
            if experience.candidate_id != candidate_id:
                raise ForbiddenError('Not authorized', custom_error.EXPERIENCE_FORBIDDEN)

            db.session.delete(experience)
            update_total_months_experience(candidate, candidate_experience=experience, deleted=True)

        else:  # Delete all experiences
            map(db.session.delete, candidate.experiences)

            # Set Candidate's total_months_experience to 0
            candidate.total_months_experience = 0

        db.session.commit()

        # Update cloud search
        upload_candidate_documents([candidate_id])
        return '', 204


class CandidateWorkExperienceBulletResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def delete(self, **kwargs):
        """
        Endpoints:
             i. DELETE /v1/candidates/:candidate_id/experiences/:experience_id/bullets
            ii. DELETE /v1/candidates/:candidate_id/experiences/:experience_id/bullets/:id
        Depending on the endpoint requested, function will delete all of Candidate's
        work_experience-bullets or just a single one.
        """
        # Get authenticated user
        authed_user = request.user

        # Get required IDs
        candidate_id, experience_id = kwargs.get('candidate_id'), kwargs.get('experience_id')
        bullet_id = kwargs.get('id')

        # Check for candidate's existence and web-hidden status
        get_candidate_if_validated(authed_user, candidate_id)

        if bullet_id:
            # Experience must belong to Candidate and bullet must belong to CandidateExperience
            bullet = db.session.query(CandidateExperienceBullet).join(CandidateExperience).join(Candidate). \
                filter(CandidateExperienceBullet.id == bullet_id). \
                filter(CandidateExperience.id == experience_id). \
                filter(CandidateExperience.candidate_id == candidate_id).first()
            if not bullet:
                raise NotFoundError(error_message='Candidate experience bullet not found',
                                    error_code=custom_error.EXPERIENCE_BULLET_NOT_FOUND)

            db.session.delete(bullet)

        else:  # Delete all bullets
            experience = CandidateExperience.get_by_id(_id=experience_id)
            if not experience:
                raise NotFoundError('Candidate experience not found', custom_error.EXPERIENCE_NOT_FOUND)

            # Experience must belong to Candidate
            if experience.candidate_id != candidate_id:
                raise ForbiddenError('Not authorized', custom_error.EXPERIENCE_FORBIDDEN)

            bullets = experience.bullets
            if not bullets:
                raise NotFoundError(error_message='Candidate experience bullet not found',
                                    error_code=custom_error.EXPERIENCE_BULLET_NOT_FOUND)

            map(db.session.delete, bullets)

        db.session.commit()

        # Update cloud search
        upload_candidate_documents([candidate_id])
        return '', 204


class CandidateEmailResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def delete(self, **kwargs):
        """
        Endpoints:
             i. DELETE /v1/candidates/:candidate_id/emails
            ii. DELETE /v1/candidates/:candidate_id/emails/:id
        Depending on the endpoint requested, function will delete all of Candidate's
        emails or just a single one.
        """
        # Get authenticated user
        authed_user = request.user

        # Get candidate_id and email_id
        candidate_id, email_id = kwargs.get('candidate_id'), kwargs.get('id')

        # Check for candidate's existence and web-hidden status
        candidate = get_candidate_if_validated(authed_user, candidate_id)

        if email_id:  # Delete specified email
            email = CandidateEmail.get_by_id(_id=email_id)
            if not email:
                raise NotFoundError('Candidate email not found', custom_error.EMAIL_NOT_FOUND)

            # Email must belong to candidate
            if email.candidate_id != candidate_id:
                raise ForbiddenError('Not authorized', custom_error.EMAIL_FORBIDDEN)

            db.session.delete(email)

        else:  # Delete all of Candidate's emails
            map(db.session.delete, candidate.emails)

        db.session.commit()

        # Update cloud search
        upload_candidate_documents([candidate_id])
        return '', 204


class CandidateMilitaryServiceResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def delete(self, **kwargs):
        """
        Endpoints:
             i. DELETE /v1/candidates/:candidate_id/military_services
            ii. DELETE /v1/candidates/:candidate_id/military_services/:id
        Depending on the endpoint requested, function will delete all of Candidate's
        military_services or just a single one.
        """
        # Get authenticated user
        authed_user = request.user

        # Get candidate_id and military_service_id
        candidate_id, military_service_id = kwargs.get('candidate_id'), kwargs.get('id')

        # Check for candidate's existence and web-hidden status
        candidate = get_candidate_if_validated(authed_user, candidate_id)

        if military_service_id:  # Delete specified military-service
            military_service = CandidateMilitaryService.get_by_id(_id=military_service_id)
            if not military_service:
                raise NotFoundError('Candidate military service not found', custom_error.MILITARY_NOT_FOUND)

            # CandidateMilitaryService must belong to Candidate
            if military_service.candidate_id != candidate_id:
                raise ForbiddenError('Not authorized', custom_error.MILITARY_FORBIDDEN)

            db.session.delete(military_service)

        else:  # Delete all of Candidate's military services
            map(db.session.delete, candidate.military_services)

        db.session.commit()

        # Update cloud search
        upload_candidate_documents([candidate_id])
        return '', 204


class CandidatePhoneResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def delete(self, **kwargs):
        """
        Endpoints:
             i. DELETE /v1/candidates/:candidate_id/phones
            ii. DELETE /v1/candidates/:candidate_id/phones/:id
        Depending on the endpoint requested, function will delete all of Candidate's
        phones or just a single one.
        """
        # Get authenticated user
        authed_user = request.user

        # Get candidate_id and phone_id
        candidate_id, phone_id = kwargs.get('candidate_id'), kwargs.get('id')

        # Check for candidate's existence and web-hidden status
        candidate = get_candidate_if_validated(authed_user, candidate_id)

        if phone_id:  # Delete specified phone
            phone = CandidatePhone.get_by_id(_id=phone_id)
            if not phone:
                raise NotFoundError('Candidate phone not found', custom_error.PHONE_NOT_FOUND)

            # Phone must belong to Candidate
            if phone.candidate_id != candidate_id:
                raise ForbiddenError('Not authorized', custom_error.PHONE_FORBIDDEN)

            db.session.delete(phone)

        else:  # Delete all of Candidate's phones
            map(db.session.delete, candidate.phones)

        db.session.commit()

        # Update cloud search
        upload_candidate_documents([candidate_id])
        return '', 204


class CandidatePreferredLocationResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def delete(self, **kwargs):
        """
        Endpoints:
             i. DELETE /v1/candidates/:candidate_id/preferred_locations
            ii. DELETE /v1/candidates/:candidate_id/preferred_locations/:id
        Depending on the endpoint requested, function will delete all of Candidate's
        preferred_locations or just a single one.
        """
        # Get authenticated user
        authed_user = request.user

        # Get candidate_id and preferred_location_id
        candidate_id, preferred_location_id = kwargs.get('candidate_id'), kwargs.get('id')

        # Check for candidate's existence and web-hidden status
        candidate = get_candidate_if_validated(authed_user, candidate_id)

        if preferred_location_id:  # Delete specified preferred location
            preferred_location = CandidatePreferredLocation.get_by_id(_id=preferred_location_id)
            if not preferred_location_id:
                raise NotFoundError(error_message='Candidate preferred location not found',
                                    error_code=custom_error.PREFERRED_LOCATION_NOT_FOUND)

            # Preferred location must belong to Candidate
            if preferred_location.candidate_id != candidate_id:
                raise ForbiddenError('Not authorized', custom_error.PREFERRED_LOCATION_FORBIDDEN)

            db.session.delete(preferred_location)

        else:  # Delete all of Candidate's preferred locations
            map(db.session.delete, candidate.preferred_locations)

        db.session.commit()

        # Update cloud search
        upload_candidate_documents([candidate_id])
        return '', 204


class CandidateSkillResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def delete(self, **kwargs):
        """
        Endpoint:
             i. DELETE /v1/candidates/:candidate_id/skills
            ii. DELETE /v1/candidates/:candidate_id/skills/:id
        Depending on the endpoint requested, function will delete all of Candidate's
        skills or just a single one.
        """
        # Get authenticated user
        authed_user = request.user

        # Get candidate_id and work_preference_id
        candidate_id, skill_id = kwargs.get('candidate_id'), kwargs.get('id')

        # Check for candidate's existence and web-hidden status
        candidate = get_candidate_if_validated(authed_user, candidate_id)

        if skill_id:  # Delete specified skill
            # skill = CandidateSkill.get_by_id(_id=skill_id)
            skill = db.session.query(CandidateSkill).get(skill_id)
            if not skill:
                raise NotFoundError('Candidate skill not found', custom_error.SKILL_NOT_FOUND)

            # Skill must belong to Candidate
            if skill.candidate_id != candidate_id:
                raise ForbiddenError('Not authorized', custom_error.SKILL_FORBIDDEN)

            db.session.delete(skill)

        else:  # Delete all of Candidate's skills
            map(db.session.delete, candidate.skills)

        db.session.commit()

        # Update cloud search
        upload_candidate_documents([candidate_id])
        return '', 204


class CandidateSocialNetworkResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_DELETE_CANDIDATE_SOCIAL_PROFILE)
    def delete(self, **kwargs):
        """
        Endpoint:
             i. DELETE /v1/candidates/:candidate_id/social_networks
            ii. DELETE /v1/candidates/:candidate_id/social_networks/:id
        Depending on the endpoint requested, function will delete all of Candidate's
        social_networks or just a single one.
        """
        # Get authenticated user
        authed_user = request.user

        # Get candidate_id and work_preference_id
        candidate_id, social_networks_id = kwargs.get('candidate_id'), kwargs.get('id')

        # Check for candidate's existence and web-hidden status
        candidate = get_candidate_if_validated(authed_user, candidate_id)

        if social_networks_id:  # Delete specified social network
            # social_network = CandidateSocialNetwork.get_by_id(_id=social_networks_id)
            social_network = db.session.query(CandidateSocialNetwork).get(social_networks_id)

            if not social_network:
                raise NotFoundError('Candidate social network not found',
                                    custom_error.SOCIAL_NETWORK_NOT_FOUND)

            # Social network must belong to Candidate
            if social_network.candidate_id != candidate_id:
                raise ForbiddenError('Not authorized', custom_error.SOCIAL_NETWORK_FORBIDDEN)

            db.session.delete(social_network)

        else:  # Delete all of Candidate's social networks
            map(db.session.delete, candidate.social_networks)

        db.session.commit()

        # Update cloud search
        upload_candidate_documents([candidate_id])
        return '', 204


class CandidateWorkPreferenceResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def delete(self, **kwargs):
        """
        Resource:
             i. DELETE /v1/candidates/:candidate_id/work_preference
            ii. DELETE /v1/candidates/:candidate_id/work_preference/:id
        Function will delete Candidate's work_preference
        """
        # Get authenticated user
        authed_user, candidate_id = request.user, kwargs['candidate_id']

        # Check for candidate's existence and web-hidden status
        get_candidate_if_validated(authed_user, candidate_id)

        work_preference = CandidateWorkPreference.get_by_candidate_id(candidate_id)
        if not work_preference:
            raise NotFoundError('Candidate does not have a work preference', custom_error.WORK_PREF_NOT_FOUND)

        db.session.delete(work_preference)
        db.session.commit()

        # Update cloud search
        upload_candidate_documents([candidate_id])
        return '', 204


class CandidateEditResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CANDIDATES)
    def get(self, **kwargs):
        """
        Endpoint: GET /v1/candidates/:id/edits
        Function will return requested Candidate with all of its edits.
        """
        # Get authenticated user & candidate_id
        authed_user, candidate_id = request.user, kwargs.get('id')

        # Check for candidate's existence and web-hidden status
        get_candidate_if_validated(authed_user, candidate_id)

        candidate_edits = fetch_candidate_edits(candidate_id=candidate_id)
        return {'candidate': {'id': candidate_id, 'edits': [
            candidate_edit for candidate_edit in candidate_edits]}}


class CandidateOpenWebResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CANDIDATES)
    def get(self, **kwargs):
        """
        Endpoint: GET /v1/candidates/openweb?url=http://...
        Function will return requested Candidate url, email from openweb endpoint
        """
        # Get authenticated user
        authed_user = request.user
        url, email, is_gt_candidate = request.args.get('url'), request.args.get('email'), None

        if url:
            is_gt_candidate, find_candidate = match_candidate_from_openweb(url, authed_user)
        elif email:
            is_gt_candidate, find_candidate = find_in_openweb_by_email(email)

        if is_gt_candidate:
            candidate = {'candidate': fetch_candidate_info(find_candidate)}

        else:
            try:
                candidate = {'candidate': convert_dice_candidate_dict_to_gt_candidate_dict(find_candidate, authed_user)}
            except Exception as e:
                logging.exception("Converting candidate from dice to gT went wrong")
                raise InvalidUsage(error_message=e.message)

        return candidate


class CandidateClientEmailCampaignResource(Resource):
    decorators = [require_oauth()]

    def post(self, **kwargs):
        """ POST /v1/candidates/client_email_campaigns
            input:
             {
                'candidates': [{candidateObject1}, {candidateObject2}, ...],
                'email_subject': 'Email Subject',
                'email_from': 'Samuel L. Jackson',
                'email_reply_to': 'amir@gettalent.com',
                'email_body_html': '<html><body>Email Body</body></html>',
                'email_body_text': 'Plaintext part of email goes here, if any',
                'email_client_id': int,
                'sent_datetime': datetime,
             }

        Function will create a list, email_campaign, email_campaign_send, and a url_conversion

        :return:    email-campaign-send objects for each candidate => [email_campaign_send]
        """
        authed_user = request.user
        body_dict = request.get_json(force=True)
        if not any(body_dict):
            raise InvalidUsage(error_message="JSON body cannot be empty.")

        candidates_list = body_dict.get('candidates')
        subject = body_dict.get('email_subject')
        # this is to handle the case if we get an email without subject, so that it does not cause the client email
        # campaign creation to fail. (This is in the case of the browser plugins).
        if not subject or subject.strip() == '':
            subject = 'No Subject'
        _from = body_dict.get('email_from')
        reply_to = body_dict.get('email_reply_to')
        body_html = body_dict.get('email_body_html')
        body_text = body_dict.get('email_body_text')
        email_client_id = body_dict.get('email_client_id')

        if not _from or not reply_to or not email_client_id or not candidates_list:
            raise InvalidUsage(error_message="Fields are missing.")

        if not isinstance(candidates_list, list):
            raise InvalidUsage(error_message="Candidates must be a list.")

        candidate_ids = [int(candidate['id']) for candidate in candidates_list]
        if not do_candidates_belong_to_users_domain(authed_user, candidate_ids):
            raise ForbiddenError(error_message="Candidates do not belong to logged-in user")

        email_client_name = is_valid_email_client(email_client_id)
        if not email_client_name:
            raise InvalidUsage(error_message="Email client is not supported.")

        campaign_name = 'Campaign %s %s' % (subject, email_client_name[0])
        list_name = 'List %s' % campaign_name

        # @XXX, @FIXME
        # we can't at this point loop through pipelines in cloudsearch just to get the candidate pipeline
        # so we created a pipeline called "gT Extensions Pipeline" that belong to getTalent domain.
        # the issue here is the user owner, not sure if we can create the pipeline under the current domain
        # and add new table field to hide it (then we will need to create a hidden pool).

        current_domain_users = [int(_user.id) for _user in db.session.query(User.id).filter_by(domain=request.user.domain).all()]

        talent_pipeline = db.session.query(TalentPipeline.id). \
            filter(TalentPipeline.name == "gT Extensions Pipeline",
                   TalentPipeline.user_id.in_(current_domain_users)).first()

        if not talent_pipeline:
            gt_talent_pool = db.session.query(TalentPool.id).\
                filter(TalentPool.domain_id == request.user.domain_id).first()

            if not gt_talent_pool:
                logger.warn("domain (%s) don't have any talent pools" % request.user.domain_id)
                raise InvalidUsage(error_message="Current domain don't have any talent pools")

            date_needed = date.today().replace(year=date.today().year + 10)

            talent_pipeline = TalentPipeline(name="gT Extensions Pipeline",
                                             description="Default talent pipeline for all extensions",
                                             positions=None,
                                             date_needed=date_needed,
                                             user_id=request.user.id,
                                             talent_pool_id=gt_talent_pool.id,
                                             search_params="")

            db.session.add(talent_pipeline)
            db.session.commit()

        if not talent_pipeline:
            logger.warn("Email Campaign is trying to send to candidate (%s) outside a pipeline" % candidate_ids[0])
            raise InvalidUsage(error_message="talent does not belong to pipeline")

        smartlist_object = {
            "name": list_name,
            "candidate_ids": candidate_ids,
            "talent_pipeline_id": talent_pipeline.id
        }

        create_smartlist_resp = create_smartlist(smartlist_object, request.headers.get('authorization'))
        if create_smartlist_resp.status_code != 201:
            return create_smartlist_resp.json(), create_smartlist_resp.status_code

        created_smartlist = create_smartlist_resp.json()
        if not created_smartlist or not created_smartlist.get('smartlist'):
            raise InternalServerError(error_message="Could not create smartlist")
        else:
            created_smartlist_id = created_smartlist.get('smartlist', {}).get('id')

        # Pool the Smartlist API to assert candidate(s) have been associated with smartlist
        error_message = 'Candidate(s) (id(s): %s) could not be found for smartlist(id:%s)' \
                        % (candidate_ids, created_smartlist_id)
        try:
            # timeout=60 is just an upper limit to poll the Smartlist API
            # (needed this for some tests, it shouldn't affect normal API flow)
            retry(assert_smartlist_candidates, sleeptime=3,  attempts=20, sleepscale=1,
                  retry_exceptions=(AssertionError,), args=(created_smartlist_id, len(candidate_ids),
                                                            request.headers.get('authorization')))

            logger.info('candidate_client_email_campaign:%s candidate(s) found for smartlist(id:%s)'
                        % (len(candidate_ids), created_smartlist_id))
        except AssertionError:
            raise InternalServerError(error_message)

        # create campaign
        email_campaign_object = {
            "name": campaign_name,
            "subject": subject,
            "from": _from,
            "reply_to": reply_to,
            "body_html": body_html,
            "body_text": body_text,
            "email_client_id": email_client_id,
            "frequency_id": Frequency.ONCE,
            "list_ids": [int(created_smartlist_id)]
        }
        email_campaign_created = create_campaign(email_campaign_object, request.headers.get('authorization'))
        if email_campaign_created.status_code != 201:
            return email_campaign_created.json(), email_campaign_created.status_code

        email_campaign_send_created = create_campaign_send(email_campaign_created.json().get('campaign').get('id'),
                                                           access_token=request.headers.get('authorization'))
        if not email_campaign_send_created.ok:
            return email_campaign_send_created.json(), email_campaign_send_created.status_code

        return email_campaign_send_created.json(), 201


class CandidateViewResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CANDIDATES)
    def post(self, **kwargs):
        """
        Endpoint:  POST /v1/candidates/:candidate_id/views
        Function will increment candidate's view counts
        """
        authed_user, candidate_id = request.user, kwargs['id']

        # Check for candidate's existence & web-hidden status
        get_candidate_if_validated(authed_user, candidate_id)

        add_candidate_view(user_id=authed_user.id, candidate_id=candidate_id)
        return '', 204

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CANDIDATES)
    def get(self, **kwargs):
        """
        Endpoint:  GET /v1/candidates/:candidate_id/views
        Function will retrieve all view information pertaining to the requested Candidate
        """
        # Get authenticated user & candidate_id
        authed_user, candidate_id = request.user, kwargs['id']

        # Check for candidate's existence and web-hidden status
        get_candidate_if_validated(authed_user, candidate_id)

        request_vars = request.args
        aggregate_by = request_vars.get('aggregate_by')
        if aggregate_by:
            if 'user_id' in aggregate_by:
                views = fetch_aggregated_candidate_views(authed_user.domain_id, candidate_id)
                return {'aggregated_views': views}

        candidate_views = fetch_candidate_views(candidate_id)
        return {'candidate_views': [candidate_view for candidate_view in candidate_views]}


class CandidatePreferenceResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CANDIDATES)
    def get(self, **kwargs):
        """
        Endpoint: GET /v1/candidates/:id/preferences
        Function will return requested candidate's preference(s)
        """
        # Get authenticated user & candidate ID
        authed_user, candidate_id = request.user, kwargs.get('id')

        # Ensure Candidate exists & is not web-hidden
        get_candidate_if_validated(authed_user, candidate_id)

        candidate_subs_pref = fetch_candidate_subscription_preference(candidate_id=candidate_id)
        return {'candidate': {'id': candidate_id, 'subscription_preference': candidate_subs_pref}}

    @require_all_permissions(Permission.PermissionNames.CAN_ADD_CANDIDATES)
    def post(self, **kwargs):
        """
        Endpoint:  POST /v1/candidates/:id/preferences
        Function will create candidate's preference(s)
        input: {'frequency_id': 1}
        """
        # Get authenticated user & candidate ID
        authed_user, candidate_id = request.user, kwargs.get('id')

        # Ensure candidate exists & is not web-hidden
        get_candidate_if_validated(authed_user, candidate_id)

        body_dict = get_json_if_exist(_request=request)
        try:
            validate(instance=body_dict, schema=resource_schema_preferences)
        except Exception as e:
            raise InvalidUsage(error_message=e.message, error_code=custom_error.INVALID_INPUT)

        # Frequency ID must be recognized
        frequency_id = body_dict.get('frequency_id')
        if not Frequency.get_by_id(_id=frequency_id):
            raise NotFoundError('Frequency ID not recognized: {}'.format(frequency_id))

        # Candidate cannot have more than one subsctiption preference
        if CandidateSubscriptionPreference.get_by_candidate_id(candidate_id=candidate_id):
            raise InvalidUsage('Candidate {} already has a subscription preference'.format(candidate_id),
                               custom_error.PREFERENCE_EXISTS)

        # Add candidate subscription preference
        add_or_update_candidate_subs_preference(candidate_id, frequency_id)

        # Update cloud search
        upload_candidate_documents([candidate_id])
        return '', 204

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def put(self, **kwargs):
        """
        Endpoint:  PATCH /v1/candidates/:id/preferences
        Function will update candidate's subscription preference
        Input: {'frequency_id': 1}
        """
        # Get authenticated user & candidate ID
        authed_user, candidate_id = request.user, kwargs.get('id')

        # Ensure candidate exists & is not web-hidden
        get_candidate_if_validated(authed_user, candidate_id)

        body_dict = get_json_if_exist(_request=request)
        try:
            validate(instance=body_dict, schema=resource_schema_preferences)
        except Exception as e:
            raise InvalidUsage(error_message=e.message, error_code=custom_error.INVALID_INPUT)

        # Frequency ID must be recognized
        frequency_id = body_dict.get('frequency_id')
        if not Frequency.get_by_id(_id=frequency_id):
            raise NotFoundError('Frequency ID not recognized: {}'.format(frequency_id))

        # Candidate must already have a subscription preference
        can_subs_pref = CandidateSubscriptionPreference.get_by_candidate_id(candidate_id)
        if not can_subs_pref:
            raise InvalidUsage('Candidate does not have a subscription preference.',
                               custom_error.NO_PREFERENCES)

        # Update candidate's subscription preference
        add_or_update_candidate_subs_preference(candidate_id, frequency_id, is_update=True)

        # Update cloud search
        upload_candidate_documents([candidate_id])
        return '', 204

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def delete(self, **kwargs):
        """
        Endpoint:  DELETE /v1/candidates/:id/preferences
        Function will delete candidate's subscription preference
        """
        # Get authenticated user & candidate ID
        authed_user, candidate_id = request.user, kwargs.get('id')

        # Ensure candidate exists & is not web-hidden
        get_candidate_if_validated(authed_user, candidate_id)

        candidate_subs_pref = CandidateSubscriptionPreference.get_by_candidate_id(candidate_id)
        if not candidate_subs_pref:
            raise NotFoundError(error_message='Candidate has no subscription preference',
                                error_code=custom_error.PREFERENCE_NOT_FOUND)

        db.session.delete(candidate_subs_pref)
        db.session.commit()

        # Update cloud search
        upload_candidate_documents([candidate_id])
        return '', 204


class CandidateDeviceResource(Resource):
    decorators = [require_oauth()]

    def get(self, **kwargs):
        """
        Endpoint: GET /v1/candidates/:id/devices
        Function will return requested candidate's associated devices
        :Example:

            >>> import requests
            >>> headers = {'Authorization': 'Bearer <access_token>'}
            >>> candidate_id = 1
            >>> response = requests.get(CandidateApiUrl.DEVICES % candidate_id,
            >>>                          headers=headers)
        """
        # Get authenticated user & candidate ID
        authenticated_user, candidate_id = request.user, kwargs['id']

        # Ensure Candidate exists & is not web-hidden
        candidate = get_candidate_if_validated(authenticated_user, candidate_id)

        devices = candidate.devices.all()
        devices = [to_json(device) for device in devices]
        return {'devices': devices}

    def post(self, **kwargs):
        """
        Endpoint:  POST /v1/candidates/:id/devices
        Function will associate a device to a candidate.
        This endpoint is used to register a candidate's device with getTalent. Device id
        is a unique string given by OneSignal API. For more information about device id see
        https://documentation.onesignal.com/docs/website-sdk-api#getIdsAvailable

        :Example:

            >>> import json
            >>> import requests
            >>> headers = {
            >>>              'Authorization': 'Bearer <token>',
            >>>               'Content-Type': 'application/json'
            >>>           }
            >>> data = {
            >>>            "device_id": "56c1d574-237e-4a41-992e-c0094b6f2ded"
            >>>         }
            >>> data = json.dumps(data)
            >>> candidate_id = 268
            >>> response = requests.post(CandidateAPiUrl.DEVICES % candidate_id, data=data,
            >>>                          headers=headers)

        .. Response::

                {
                    "message": "Device registered successfully with candidate (id: 268)"
                }

        .. Status:: 200 (OK)
                    401 (Unauthorized to access getTalent)
                    403 (Can't add device for non existing candidate)
                    404 (ResourceNotFound)
                    500 (Internal Server Error)
        """
        # Get authenticated user & candidate ID
        authenticated_user, candidate_id = request.user, kwargs['id']

        # Ensure candidate exists & is not web-hidden
        candidate = get_candidate_if_validated(authenticated_user, candidate_id)

        data = get_json_if_exist(_request=request)
        one_signal_device_id = data.get('one_signal_device_id')
        if not one_signal_device_id:
            raise InvalidUsage('device_id is not given in post data')
        if os.getenv(TalentConfigKeys.ENV_KEY) == TalentEnvs.PROD:
            device = CandidateDevice.get_device_by_one_signal_id_and_domain_id(one_signal_device_id,
                                                                               authenticated_user.domain_id)
            if device:
                raise InvalidUsage('Given OneSignal Device id (%s) is already associated to a '
                                   'candidate in your domain')
        one_signal_client = OneSignalSdk(app_id=ONE_SIGNAL_APP_ID,
                                         user_auth_key=ONE_SIGNAL_REST_API_KEY)
        # Send a GET request to OneSignal API to confirm that this device id is valid
        response = one_signal_client.get_player(one_signal_device_id)
        if response.ok:
            # Device exists with id
            candidate_device = CandidateDevice(candidate_id=candidate.id,
                                               one_signal_device_id=one_signal_device_id,
                                               registered_at_datetime=datetime.datetime.utcnow())
            # try:
            #     CandidateDevice.save(candidate_device)
            # except OperationalError as e:
            #     logger.info('Try again, Error occurred while saving candidate device. Error: %s', e)
            #     db.session.rollback()
            #     CandidateDevice.save(candidate_device)
            if os.getenv(TalentConfigKeys.ENV_KEY) == TalentEnvs.JENKINS:
                return retry(CandidateDevice.save, sleeptime=1, attempts=5, sleepscale=1,
                             retry_exceptions=(OperationalError,), args=(candidate_device,))
            else:
                CandidateDevice.save(candidate_device)

            return dict(message='Device (id: %s) registered successfully with candidate (id: %s)'
                                % (candidate_device.id, candidate.id)), 201
        else:
            # No device was found on OneSignal database.
            raise ResourceNotFound('Device is not registered with OneSignal with id %s' % one_signal_device_id)

    def delete(self, **kwargs):
        """
        Endpoint: DELETE /v1/candidates/:id/devices
        Function will delete requested candidate's associated device

        You have to pass device one_signal_id in request payload.
        :Example:
            >>> import json
            >>> import requests
            >>> candidate_id = 10
            >>> device_id = 'sad3232fedsagfewrq32323423dasdasd'
            >>> data = {
            >>>            'one_signal_device_id': device_id
            >>> }
            >>> data = json.dumps(data)
            >>> headers = {
            >>>             'Authorization': 'Bearer <token>',
            >>>             'Content-Type': 'application/json'
            >>> }
            >>> response = requests.delete(CandidateApiUrl.DEVICES % candidate_id, data=data,
            >>>                            headers=headers)

        .. Response::

                {
                    "message": "device (id: sad3232fedsagfewrq32323423dasdasd) has been deleted for candidate (id: 10)"
                }
        """
        # Get authenticated user & candidate ID
        authenticated_user, candidate_id = request.user, kwargs['id']

        # Ensure candidate exists & is not web-hidden
        get_candidate_if_validated(authenticated_user, candidate_id)

        data = get_json_if_exist(_request=request)
        one_signal_device_id = data.get('one_signal_device_id')
        if not one_signal_device_id:
            raise InvalidUsage('device_id is not given in post data')

        device = CandidateDevice.get_by_candidate_id_and_one_signal_device_id(candidate_id, one_signal_device_id)
        if not device:
            raise ResourceNotFound('Device not found with given OneSignalId (%s) and candidate_id (%s)'
                                   % (one_signal_device_id, candidate_id))
        db.session.delete(device)
        db.session.commit()

        return {'message': 'device (id: %s) has been deleted for candidate (id: %s)' % (device.id, candidate_id)}


class CandidatePhotosResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_ADD_CANDIDATES)
    def post(self, **kwargs):
        """
        Endpoint:  POST /v1/candidates/:id/photos
        Function will add candidate photo to db
        """
        # Get authenticated user
        authed_user, candidate_id = request.user, kwargs['candidate_id']

        # Check if candidate exists & is not web-hidden
        get_candidate_if_validated(authed_user, candidate_id)

        # Validate request body
        body_dict = get_json_if_exist(_request=request)
        try:
            validate(instance=body_dict, schema=resource_schema_photos_post, format_checker=FormatChecker())
        except ValidationError as e:
            raise InvalidUsage('JSON schema validation error: {}'.format(e),
                               error_code=custom_error.INVALID_INPUT)

        add_photos(candidate_id, body_dict['photos'])

        # Update cloud search
        upload_candidate_documents([candidate_id])
        return '', 204

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CANDIDATES)
    def get(self, **kwargs):
        """
        Endpoints:
           i.  GET /v1/candidates/:id/photos
          ii.  GET /v1/candidates/:candidate_id/photos/:id
        Function will return candidate photo(s) information
        """
        # Get authenticated user, candidate ID, and photo ID
        authed_user, candidate_id = request.user, kwargs['candidate_id']
        photo_id = kwargs.get('id')

        # Check if candidate exists & is web-hidden
        get_candidate_if_validated(authed_user, candidate_id)

        if photo_id:
            # Photo must be recognized
            photo = CandidatePhoto.get_by_id(_id=photo_id)
            """
            :type photo: CandidatePhoto
            """
            if not photo:
                raise NotFoundError('Candidate photo not found; photo-id: {}'.format(photo_id),
                                    error_code=custom_error.PHOTO_NOT_FOUND)

            # Photo must belong to candidate
            if photo.candidate_id != candidate_id:
                raise ForbiddenError('Not authorized', error_code=custom_error.PHOTO_FORBIDDEN)

            return {'candidate_photo': {'id': photo_id, 'image_url': photo.image_url,
                                        'is_default': photo.is_default}}

        else: # Get all of candidate's photos
            photos = CandidatePhoto.get_by_candidate_id(candidate_id=candidate_id)
            return {'candidate_photos': [
                {'id': photo.id, 'image_url': photo.image_url, 'is_default': photo.is_default}
                for photo in photos]}

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def patch(self, **kwargs):
        """
        Endpoint: PATCH /v1/candidates/:candidate_id/photos
        Function will update candidate's photos' information
        """
        # Get authenticated user, candidate ID, and photo ID
        authed_user, candidate_id = request.user, kwargs['candidate_id']

        # Check if candidate exists & is web-hidden
        get_candidate_if_validated(authed_user, candidate_id)

        # Validate request body
        body_dict = get_json_if_exist(_request=request)
        try:
            validate(instance=body_dict, schema=resource_schema_photos_patch)
        except ValidationError as e:
            raise InvalidUsage('JSON schema validation error: {}'.format(e),
                               error_code=custom_error.INVALID_INPUT)

        # Update candidate's photo
        photos = body_dict.get('photos')
        for photo_dict in photos:
            update_photo(candidate_id, authed_user.id, photo_dict)

        db.session.commit()

        # Update cloud search
        upload_candidate_documents([candidate_id])
        return '', 204

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def delete(self, **kwargs):
        """
        Endpoints:
             i.  DELETE /v1/candidates/:id/photos
            ii.  DELETE /v1/candidates/:candidate_id/photos/:id
        Function will delete candidate's photo(s) from database
        """
        # Get authenticated user, Candidate ID, and photo ID
        authed_user, candidate_id = request.user, kwargs['candidate_id']
        photo_id = kwargs.get('id')

        # Check if candidate exists & is web-hidden
        candidate = get_candidate_if_validated(authed_user, candidate_id)

        if photo_id:
            # Photo must already exist
            photo = CandidatePhoto.get_by_id(_id=photo_id)
            """
            :type photo: CandidatePhoto
            """
            if not photo:
                raise NotFoundError('Candidate photo not found; photo-id: {}'.format(photo_id),
                                    error_code=custom_error.PHOTO_NOT_FOUND)

            # Photo must belong to candidate
            if photo.candidate_id != candidate_id:
                raise ForbiddenError('Not authorized', error_code=custom_error.PHOTO_FORBIDDEN)

            db.session.delete(photo)

        else: # Delete all of candidate's photos
            map(db.session.delete, candidate.photos)

        db.session.commit()

        # Update cloud search
        upload_candidate_documents([candidate_id])
        return '', 204


class CandidateLanguageResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_ADD_CANDIDATES)
    def post(self, **kwargs):
        """
        Endpoint:  POST /v1/candidates/:candidate_id/languages
        Function will create language(s) for requested candidate
        """
        # Get authenticated user & candidate ID
        authed_user, candidate_id = request.user, kwargs['candidate_id']

        # Check if candidate exists & is web-hidden
        get_candidate_if_validated(authed_user, candidate_id)

        body_dict = get_json_if_exist(request)
        try:
            validate(instance=body_dict, schema=language_schema)
        except ValidationError as e:
            raise InvalidUsage('JSON schema validation error: {}'.format(e), custom_error.INVALID_INPUT)

        add_languages(candidate_id=candidate_id, data=body_dict['candidate_languages'])
        db.session.commit()
        return '', 204

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CANDIDATES)
    def get(self, **kwargs):
        """
        Endpoints:
             i. GET /v1/candidates/:candidate_id/languages
            ii. GET /v1/candidates/:candidate_id/languages/:id
        Function will retrieve all of candidate's languages
        """
        # Get authenticated user & candidate ID
        authed_user, candidate_id, language_id = request.user, kwargs['candidate_id'], kwargs.get('id')

        # Check if candidate exists & is web-hidden
        get_candidate_if_validated(authed_user, candidate_id)

        language = None
        if language_id:  # Get specified candidate's language
            language = CandidateLanguage.get_by_id(language_id)
            """
            :type language:  CandidateLanguage
            """
            if not language:
                raise NotFoundError('Candidate language not found: {}'.format(language_id),
                                    custom_error.LANGUAGE_NOT_FOUND)
            if language.candidate_id != candidate_id:
                raise ForbiddenError('Not authorized', custom_error.LANGUAGE_FORBIDDEN)

        return {'candidate_languages': fetch_candidate_languages(candidate_id, language)}

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def patch(self, **kwargs):
        """
        Endpoint:  PATCH /v1/candidates/:candidate_id/languages
        Function will update candidate's languages
        """
        # Get authenticated user & Candidate ID
        authed_user, candidate_id = request.user, kwargs['candidate_id']

        # Check if candidate exists & is web-hidden
        get_candidate_if_validated(authed_user, candidate_id)

        body_dict = get_json_if_exist(request)
        try:
            validate(instance=body_dict, schema=language_schema)
        except ValidationError as e:
            raise InvalidUsage('JSON schema validation error: {}'.format(e), custom_error.INVALID_INPUT)

        update_candidate_languages(candidate_id, body_dict['candidate_languages'], authed_user.id)
        db.session.commit()
        return '', 204

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def delete(self, **kwargs):
        """
        Endpoints:
             i. DELETE /v1/candidates/:candidate_id/languages/:id
            ii. DELETE /v1/candidates/:candidate_id/languages
        :returns:
            - status code: 200
            - json body: {'language_ids': [int, int, ...]}
        """
        # Get authenticated user, Candidate ID, and Language ID
        authed_user, candidate_id, language_id = request.user, kwargs['candidate_id'], kwargs.get('id')

        # Check if candidate exists & is web-hidden
        candidate = get_candidate_if_validated(authed_user, candidate_id)

        if language_id:  # Delete specified candidate's language
            language = CandidateLanguage.get_by_id(language_id)
            """
            :type language:  CandidateLanguage
            """
            if not language:
                raise NotFoundError('Candidate language not found: {}'.format(language_id),
                                    custom_error.LANGUAGE_NOT_FOUND)
            if language.candidate_id != candidate_id:
                raise ForbiddenError('Not authorized', custom_error.LANGUAGE_FORBIDDEN)

            db.session.delete(language)
            db.session.commit()

        else:  # Delete all of candidate's languages
            candidate_languages = candidate.languages
            map(db.session.delete, candidate_languages)

        db.session.commit()
        return '', 204
