"""
This file entails Candidate-restful-services
"""
from flask import request
from flask_restful import Resource
from candidate_service.common.models.db import db
from common.utils.validators import (is_number, is_valid_email)
from common.utils.auth_utils import require_oauth
from common.error_handling import (ForbiddenError, InvalidUsage)
from candidate_service.common.models.user import User
from candidate_service.modules.talent_candidates import (
    fetch_candidate_info, get_candidate_id_from_candidate_email
)
from candidate_service.common.models.email_marketing import EmailCampaign
from candidate_service.modules.validators import (
    does_candidate_belong_to_user, is_custom_field_authorized,
    is_area_of_interest_authorized, does_email_campaign_belong_to_domain
)
from candidate_service.modules.talent_candidates import create_candidate_from_params


class CandidateResource(Resource):
    # decorators = [require_oauth]

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
        # authed_user = request.user
        authed_user = db.session.query(User).get(2)

        # Either candidate_id or candidate_email must be provided
        candidate_id = kwargs.get('id')
        candidate_email = kwargs.get('email')
        if not candidate_id and not candidate_email:
            raise InvalidUsage(error_message="Candidate's ID or candidate's email is required")

        if candidate_id:
            # Candidate ID must be an integer
            if not is_number(candidate_id):
                raise InvalidUsage(error_message="Candidate ID must be an integer")

        if candidate_email:
            # Email address must be valid
            if not is_valid_email(candidate_email):
                raise InvalidUsage(error_message="A valid email address is required")

            candidate_id = get_candidate_id_from_candidate_email(candidate_email)

        # Candidate must belong to logged in user
        if not does_candidate_belong_to_user(user_row=authed_user, candidate_id=candidate_id):
            raise ForbiddenError(error_message="Not authorized")

        candidate_data = fetch_candidate_info(candidate_id=candidate_id)
        if not candidate_data:
            raise ForbiddenError(error_message="Candidate not found")

        return {'candidate': candidate_data}

    def post(self, **kwargs):
        """
        POST /web/api/candidates
        input: {'candidates': [candidateObject1, candidateObject2, ...]}

        Creates new candidate(s).

        Takes a JSON dict containing:
            - a candidates key and a list of candidate-object(s) as values
        Function only accepts JSON dict.
        JSON dict must contain candidate's email address(s).

        :return: {'candidates': [{'id': candidate_id}, {'id': candidate_id}, ...]}
        """
        # authed_user = request.user
        from candidate_service.common.models.user import User
        authed_user = db.session.query(User).get(1)

        # Parse request body
        body_dict = request.get_json(force=True)

        # Retrieve candidate object(s)
        list_of_candidate_dicts = body_dict.get('candidates')

        # Candidate dict(s) must be in a list
        if not isinstance(list_of_candidate_dicts, list):
            raise InvalidUsage(error_message="Unacceptable input: Candidate object(s) must be in a list")

        created_candidate_ids = []
        for candidate_dict in list_of_candidate_dicts:

            emails = [{'label': email.get('label'), 'address': email.get('address')}
                      for email in candidate_dict.get('emails')]
            # Email address is required for creating a candidate
            if not any(emails):
                raise InvalidUsage(error_message="Email address required")

            # Validate email address' format
            if filter(lambda email: not is_valid_email(email['address']), emails):
                raise InvalidUsage(error_message="Invalid email address/format")

            # Prevent user from adding custom field(s) to other domain(s)
            custom_fields = candidate_dict.get('custom_fields', [])
            custom_field_ids = [custom_field['id'] for custom_field in custom_fields]
            is_authorized = is_custom_field_authorized(custom_field_ids=custom_field_ids,
                                                       user_domain_id=authed_user.domain_id)
            if not is_authorized:
                # raise ForbiddenError(error_message="Unauthorized custom field IDs")
                pass

            # Prevent user from adding area(s) of interest to other domain(s)
            areas_of_interest = candidate_dict.get('areas_of_interest', [])
            area_of_interest_ids = [area_of_interest['id'] for area_of_interest in areas_of_interest]
            is_authorized = is_area_of_interest_authorized(area_of_interest_ids=area_of_interest_ids,
                                                           user_domain_id=authed_user.domain_id)
            if not is_authorized:
                pass
                # raise ForbiddenError(error_message="Unauthorized area of interest IDs")

            addresses = candidate_dict.get('addresses')
            country_id = addresses[0].get('country') if addresses else 1
            if not country_id:
                country_id = 1  # country_code_or_name_to_id returns None if no match

            user_id = authed_user.id
            first_name = candidate_dict.get('first_name')
            last_name = candidate_dict.get('last_name')
            full_name = candidate_dict.get('full_name')
            status_id = body_dict.get('status_id')
            phones = candidate_dict.get('phones')
            educations = candidate_dict.get('educations')
            military_services = candidate_dict.get('military_services')
            social_networks = candidate_dict.get('social_networks', [])
            work_experiences = candidate_dict.get('work_experiences', [])
            work_preference = candidate_dict.get('work_preference')
            preferred_locations = candidate_dict.get('preferred_locations')
            skills = candidate_dict.get('skills', [])
            dice_social_profile_id = body_dict.get('openweb_id')
            dice_profile_id=body_dict.get('dice_profile_id')

            resp_dict = create_candidate_from_params(
                user_id=user_id,
                first_name=first_name,
                last_name=last_name,
                formatted_name=full_name,
                status_id=status_id,
                emails=emails,
                phones=phones,
                addresses=addresses,
                educations=educations,
                military_services=military_services,
                area_of_interest_ids=area_of_interest_ids,
                custom_field_ids=custom_field_ids,
                social_networks=social_networks,
                work_experiences=work_experiences,
                work_preference=work_preference,
                preferred_locations=preferred_locations,
                skills=skills,
                dice_social_profile_id=dice_social_profile_id,
                dice_profile_id=dice_profile_id
            )
            created_candidate_ids.append(resp_dict['candidate_id'])
            if not resp_dict:
                raise InvalidUsage(error_message="Candidate already exists, creation failed.")

        return {'candidates': [{'id': candidate_id} for candidate_id in created_candidate_ids]}


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
