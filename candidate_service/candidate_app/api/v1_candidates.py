"""
This file entails Candidate-restful-services for CRUD operations
"""
# Flask specific
from flask import request
from flask_restful import Resource

# Database connection
from candidate_service.common.models.db import db

# Validators
from candidate_service.common.utils.validators import (is_number, is_valid_email)
from candidate_service.modules.validators import (
    does_candidate_belong_to_user, is_custom_field_authorized,
    is_area_of_interest_authorized, does_email_campaign_belong_to_domain
)

# Decorators
from candidate_service.common.utils.auth_utils import require_oauth

# Error handling
from candidate_service.common.error_handling import ForbiddenError, InvalidUsage, NotFoundError

# Models
from candidate_service.common.models.email_marketing import EmailCampaign
from candidate_service.common.models.candidate import Candidate, CandidateAddress

# Module
from candidate_service.modules.talent_candidates import (
    fetch_candidate_info, get_candidate_id_from_candidate_email,
    create_or_update_candidate_from_params
)


class CandidateResource(Resource):
    decorators = [require_oauth]

    def get(self, **kwargs):
        """
        Endpoints can do these operations:
            1. Fetch a candidate via two methods:
                I.  GET /v1/candidates/:id
                    Takes an integer as candidate's ID, parsed from kwargs

                OR
                II. GET /v1/candidates/:email
                    Takes a valid email address, parsed from kwargs

        :return:    A dict of candidate info
                    404 status if candidate is not found
        """
        # Authenticated user
        authed_user = request.user

        # Either candidate_id or candidate_email must be provided
        candidate_id, candidate_email = kwargs.get('id'), kwargs.get('email')
        if not candidate_id and not candidate_email:
            raise InvalidUsage(error_message="Candidate's ID or candidate's email is required")

        if candidate_id:
            # Candidate ID must be an integer
            if not is_number(candidate_id):
                raise InvalidUsage(error_message="Candidate ID must be an integer")

        elif candidate_email:
            # Email address must be valid
            if not is_valid_email(candidate_email):
                raise InvalidUsage(error_message="A valid email address is required")

            # Get candidate ID from candidate's email
            candidate_id = get_candidate_id_from_candidate_email(candidate_email)

        # If Candidate is web hidden, it is assumed "deleted"
        candidate = Candidate.get_by_id(candidate_id=candidate_id)
        if not candidate:
            raise NotFoundError(error_message='Candidate not found.')

        if candidate.is_web_hidden:
            raise NotFoundError(error_message='Candidate not found.')

        # Candidate must belong to user, and must be in the same domain as the user's domain
        if not does_candidate_belong_to_user(user_row=authed_user, candidate_id=candidate_id):
            raise ForbiddenError(error_message="Not authorized")

        candidate_data_dict = fetch_candidate_info(candidate=candidate)

        return {'candidate': candidate_data_dict}

    def post(self, **kwargs):
        """
        POST /v1/candidates
        input: {'candidates': [candidateObject1, candidateObject2, ...]}

        Creates new candidate(s).

        Takes a JSON dict containing:
            - a candidates key and a list of candidate-object(s) as values
        Function only accepts JSON dict.
        JSON dict must contain candidate's email address(s).

        :return: {'candidates': [{'id': candidate_id}, {'id': candidate_id}, ...]}
        """
        # Authenticate user
        authed_user = request.user

        # Parse request body
        body_dict = request.get_json(force=True)
        if not any(body_dict):
            raise InvalidUsage(error_message="JSON body cannot be empty.")

        # Retrieve candidate object(s)
        list_of_candidate_dicts = body_dict.get('candidates') or [body_dict.get('candidate')]

        # list_of_candidate_dicts must be in a list
        if not isinstance(list_of_candidate_dicts, list):
            list_of_candidate_dicts = [list_of_candidate_dicts]

        # List of Candidate dicts must not be empty
        if not any(list_of_candidate_dicts):
            error_message = "Missing input: At least one Candidate-object is required for candidate creation"
            raise InvalidUsage(error_message=error_message)

        created_candidate_ids = []
        for candidate_dict in list_of_candidate_dicts:

            # Ensure emails list is provided
            if not candidate_dict.get('emails'):
                raise InvalidUsage(error_message="Email address is required for creating candidate")

            emails = [{'label': email.get('label'), 'address': email.get('address'),
                       'is_default': email.get('is_default')} for email in candidate_dict.get('emails')]
            # Email address is required for creating a candidate
            if not any(emails):
                raise InvalidUsage(error_message="Email address required")

            # Validate email addresses' format
            if filter(lambda email: not is_valid_email(email['address']), emails):
                raise InvalidUsage(error_message="Invalid email address/format")

            # Prevent user from adding custom field(s) to other domains
            custom_fields = candidate_dict.get('custom_fields', [])
            custom_field_ids = [custom_field.get('id') for custom_field in custom_fields]
            is_authorized = is_custom_field_authorized(custom_field_ids=custom_field_ids,
                                                       user_domain_id=authed_user.domain_id)
            if not is_authorized:
                raise ForbiddenError(error_message="Unauthorized custom field IDs")

            # Prevent user from adding area(s) of interest to other domains
            areas_of_interest = candidate_dict.get('areas_of_interest', [])
            area_of_interest_ids = [area_of_interest.get('id') for area_of_interest in areas_of_interest]
            is_authorized = is_area_of_interest_authorized(area_of_interest_ids=area_of_interest_ids,
                                                           user_domain_id=authed_user.domain_id)
            if not is_authorized:
                raise ForbiddenError(error_message="Unauthorized area of interest IDs")

            # TODO: Validate all input formats and existence
            user_id = authed_user.id
            addresses = candidate_dict.get('addresses')
            first_name = candidate_dict.get('first_name')
            last_name = candidate_dict.get('last_name')
            full_name = candidate_dict.get('full_name')
            status_id = body_dict.get('status_id')
            phones = candidate_dict.get('phones')
            educations = candidate_dict.get('educations')
            military_services = candidate_dict.get('military_services')
            social_networks = candidate_dict.get('social_networks')
            work_experiences = candidate_dict.get('work_experiences')
            work_preference = candidate_dict.get('work_preference')
            preferred_locations = candidate_dict.get('preferred_locations')
            skills = candidate_dict.get('skills')
            dice_social_profile_id = body_dict.get('openweb_id')
            dice_profile_id=body_dict.get('dice_profile_id')

            resp_dict = create_or_update_candidate_from_params(
                user_id=user_id,
                is_creating=True,
                first_name=first_name,
                last_name=last_name,
                formatted_name=full_name,
                status_id=status_id,
                emails=emails,
                phones=phones,
                addresses=addresses,
                educations=educations,
                military_services=military_services,
                areas_of_interest=areas_of_interest,
                custom_fields=custom_fields,
                social_networks=social_networks,
                work_experiences=work_experiences,
                work_preference=work_preference,
                preferred_locations=preferred_locations,
                skills=skills,
                dice_social_profile_id=dice_social_profile_id,
                dice_profile_id=dice_profile_id
            )
            created_candidate_ids.append(resp_dict['candidate_id'])

        return {'candidates': [{'id': candidate_id} for candidate_id in created_candidate_ids]}, 201

    def patch(self, **kwargs):
        """
        PATCH /v1/candidates
        Function can update candidate(s).

        Takes a JSON dict containing:
            - a candidates key and a list of candidate-object(s) as values
        Function only accepts JSON dict.
        JSON dict must contain candidate's ID.

        :return: {'candidates': [{'id': candidate_id}, {'id': candidate_id}, ...]}
        """
        # Authenticated user
        authed_user = request.user

        # Parse request body
        body_dict = request.get_json(force=True)
        if not any(body_dict):
            raise InvalidUsage(error_message="JSON body cannot be empty.")

        # Retrieve candidate object(s)
        list_of_candidate_dicts = body_dict.get('candidates') or [body_dict.get('candidate')]

        # list_of_candidate_dicts must be in a list
        if not isinstance(list_of_candidate_dicts, list):
            list_of_candidate_dicts = [list_of_candidate_dicts]

        # List of Candidate dicts must not be empty
        if not any(list_of_candidate_dicts):
            error_message = "Missing input: At least one Candidate-object is required for candidate creation"
            raise InvalidUsage(error_message=error_message)

        updated_candidate_ids = []
        for candidate_dict in list_of_candidate_dicts:

            emails = candidate_dict.get('emails') # TODO: validate emails and format
            if emails:
                emails = [{'id': email.get('id'), 'label': email.get('label'), 'address': email.get('address'),
                           'is_default': email.get('is_default')} for email in candidate_dict.get('emails')]

                # Validate email addresses' format
                if filter(lambda email: not is_valid_email(email['address']), emails):
                    raise InvalidUsage(error_message="Invalid email address/format")

            # Prevent user from updating custom field(s) from other domains
            custom_fields = candidate_dict.get('custom_fields', [])
            custom_field_ids = [custom_field.get('id') for custom_field in custom_fields]
            is_authorized = is_custom_field_authorized(custom_field_ids=custom_field_ids,
                                                       user_domain_id=authed_user.domain_id)
            if not is_authorized:
                raise ForbiddenError(error_message="Unauthorized custom field IDs")

            # Retrieve areas_of_interest
            areas_of_interest = candidate_dict.get('areas_of_interest', [])
            area_of_interest_ids = [area_of_interest.get('id') for area_of_interest in areas_of_interest]

            # If AreaOfInterest ID is not provided, assume it needs to be created
            if not any(area_of_interest_ids):
                pass

            # Prevent user from updating area(s) of interest from other domains
            is_authorized = is_area_of_interest_authorized(authed_user.domain_id, area_of_interest_ids)
            if not is_authorized:
                raise ForbiddenError(error_message="Unauthorized area of interest IDs")

            # TODO: Validate all input formats and existence
            user_id = authed_user.id
            candidate_id = candidate_dict.get('id')
            addresses = candidate_dict.get('addresses')
            first_name = candidate_dict.get('first_name')
            last_name = candidate_dict.get('last_name')
            full_name = candidate_dict.get('full_name')
            status_id = body_dict.get('status_id')
            phones = candidate_dict.get('phones')
            educations = candidate_dict.get('educations')
            military_services = candidate_dict.get('military_services')
            social_networks = candidate_dict.get('social_networks')
            work_experiences = candidate_dict.get('work_experiences')
            work_preference = candidate_dict.get('work_preference')
            preferred_locations = candidate_dict.get('preferred_locations')
            skills = candidate_dict.get('skills')
            dice_social_profile_id = body_dict.get('openweb_id')
            dice_profile_id=body_dict.get('dice_profile_id')

            resp_dict = create_or_update_candidate_from_params(
                user_id=user_id,
                is_updating=True,
                candidate_id=candidate_id,
                first_name=first_name,
                last_name=last_name,
                formatted_name=full_name,
                status_id=status_id,
                emails=emails,
                phones=phones,
                addresses=addresses,
                educations=educations,
                military_services=military_services,
                areas_of_interest=areas_of_interest,
                custom_fields=custom_fields,
                social_networks=social_networks,
                work_experiences=work_experiences,
                work_preference=work_preference,
                preferred_locations=preferred_locations,
                skills=skills,
                dice_social_profile_id=dice_social_profile_id,
                dice_profile_id=dice_profile_id
            )
            updated_candidate_ids.append(resp_dict['candidate_id'])

        return {'candidates': [{'id': updated_candidate_id} for updated_candidate_id in updated_candidate_ids]}

    def delete(self, **kwargs):
        """
        DELETE /v1/candidates/id
        Function will set requested Candidate's is_web_hidden to True in the db.

        Caveats:
        - Only candidate's owner can hide the Candidate.
        - Candidate must be in the same domain as authenticated user

        :return: {'candidates': [{'id': candidate_id}, {'id': candidate_id}, ...]}
        """
        # Authenticate user
        authed_user = request.user

        # candidate_id must be provided
        candidate_id = kwargs.get('id')
        if not candidate_id:
            raise InvalidUsage(error_message="Candidate's ID is required for deactivating.")

        # Prevent user from deleting candidate(s) outside of its domain; or other user's candidates
        is_authorized = does_candidate_belong_to_user(authed_user, candidate_id)
        if not is_authorized:
            raise ForbiddenError(error_message="Not authorized")

        # Hide Candidate
        Candidate.set_is_web_hidden_to_true(candidate_id=candidate_id)

        return {'candidate': {'id': candidate_id}}


class CandidateAddresses(Resource):
    decorators = [require_oauth]

    def delete(self, **kwargs):
        """
        Function deletes stuff
        """
        # Authenticated user
        authed_user = request.user

        # Get candidate_id and address_id
        candidate_id, address_id = kwargs.get('candidate_id'), kwargs.get('id')
        single_address, list_of_addresses = False, False

        if candidate_id and address_id:
            single_address = True
        elif candidate_id and not address_id:
            list_of_addresses = True
        else:
            raise InvalidUsage(error_message='Candidate ID is required.')

        # Prevent user from deleting address of the candidates outside of its domain
        is_authorized = does_candidate_belong_to_user(authed_user, candidate_id)
        if not is_authorized:
            raise ForbiddenError(error_message="Not authorized")

        if single_address:
            # Ensure address belong to Candidate
            candidate_address = CandidateAddress.get_by_id(_id=address_id)
            if candidate_address:
                if candidate_address.candidate_id != candidate_id:
                    raise ForbiddenError(error_message='Not authorized')
            else:
                raise NotFoundError(error_message='Candidate address not found.')

            # Remove CandidateAddress
            db.session.delete(candidate_address)

        elif list_of_addresses:
            # Remove candidate's addresses
            candidate = Candidate.get_by_id(candidate_id)
            for address in candidate.candidate_addresses:
                db.session.delete(address)

        db.session.commit()
        return '', 204


class CandidateEmailCampaignResource(Resource):
    decorators = [require_oauth]

    def get(self, **kwargs):
        """
        Fetch and return all EmailCampaignSend objects sent to a known candidate.
            GET /v1/candidates/<int:id>/email_campaigns/<int:email_campaign_id>/email_campaign_sends
            - This requires an email_campaign_id & a candidate_id
            - Email campaign must belong to the candidate & candidate must belong to the logged in user.
        :return: A list of EmailCampaignSend object(s)
        """
        authed_user = request.user
        candidate_id = kwargs.get('id')
        email_campaign_id = kwargs.get('email_campaign_id')
        if not candidate_id or not email_campaign_id:
            raise InvalidUsage(error_message="Candidate ID and email campaign ID are required")

        # Candidate must belong to user & email campaign must belong to user's domain
        validate_1 = does_candidate_belong_to_user(user_row=authed_user, candidate_id=candidate_id)
        validate_2 = does_email_campaign_belong_to_domain(user_row=authed_user)
        if not validate_1 or not validate_2:
            raise ForbiddenError(error_message="Not authorized")

        email_campaign = db.session.query(EmailCampaign).get(email_campaign_id)

        # Get all email_campaign_send objects of the requested candidate
        from candidate_service.modules.talent_candidates import retrieve_email_campaign_send
        email_campaign_send_rows = retrieve_email_campaign_send(email_campaign, candidate_id)

        return {'email_campaign_sends': email_campaign_send_rows}

