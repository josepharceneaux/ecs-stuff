"""
This file contains Pipeline-restful-services
"""
# Standard library
import requests

# Flask specific
from flask import request
from flask_restful import Resource

# Validators
from candidate_service.modules.validators import get_candidate_if_exists, does_candidate_belong_to_users_domain

# Decorators
from candidate_service.common.utils.auth_utils import require_oauth, require_all_roles

# Error handling
from candidate_service.common.error_handling import ForbiddenError
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error

# Models
from candidate_service.common.models.user import DomainRole, User
from candidate_service.common.models.candidate import Candidate
from candidate_service.common.models.talent_pools_pipelines import TalentPipeline

from candidate_service.common.inter_service_calls.candidate_service_calls import search_candidates_from_params


class CandidatePipelineResource(Resource):
    decorators = [require_oauth()]

    @require_all_roles(DomainRole.Roles.CAN_GET_CANDIDATES)
    def get(self, **kwargs):
        """
        Function will return user's 5 most recently added Pipelines. One of the pipelines will
          include the specified candidate.
        :rtype:  dict[list[dict]]
        Usage:
            >>> requests.get('host/v1/candidates/:candidate_id/pipelines')
            <Response [200]>
        """
        # Authenticated user & candidate ID
        authed_user, candidate_id = request.user, kwargs['candidate_id']

        # Check if candidate exists & is web-hidden
        get_candidate_if_exists(candidate_id)

        # Candidate must belong to user's domain
        if not does_candidate_belong_to_users_domain(authed_user, candidate_id):
            raise ForbiddenError("Not authorized", custom_error.CANDIDATE_FORBIDDEN)

        # Maximum number of Talent Pipeline objects used for searching.
        # This is to prevent client from waiting too long for a response
        max_requests = 10

        # Get User-domain's 10 most recent talent pipelines in order of added time
        talent_pipelines = TalentPipeline.query.join(User).filter(
            User.domain_id == authed_user.domain_id).order_by(
            TalentPipeline.added_time.desc()).limit(max_requests).all()

        # Use Search API to retrieve candidate's domain-pipeline inclusion
        found_candidate_ids = []
        found = False
        access_token = authed_user.token[0].access_token
        for count, talent_pipeline in enumerate(talent_pipelines, start=1):
            search_response = search_candidates_from_params(talent_pipeline.search_params, access_token)
            found_candidate_ids.extend(candidate['id'] for candidate in search_response['candidates'])

            # Return if candidate_id is found in one of the Pipelines AND 5 or more requests have been made
            found = unicode(candidate_id) in found_candidate_ids
            if found and count >= 5:
                break

        # If candidate is not found in the 10 most recently added domain pipelines, return empty list
        if not found:
            return {'candidate_pipelines': []}

        # Return only five pipelines if candidate is found in more than 5 domain pipelines
        return {'candidate_pipelines': [
            {
                'id': talent_pipeline.id,
                'candidate_id': Candidate.query.filter_by(user_id=talent_pipeline.user_id).first().id,
                'name': talent_pipeline.name,
                'description': talent_pipeline.description,
                'open_positions': talent_pipeline.positions,
                'datetime_needed': str(talent_pipeline.date_needed),
                'user_id': talent_pipeline.user_id,
                'added_datetime': str(talent_pipeline.added_time)
            } for talent_pipeline in talent_pipelines]}
