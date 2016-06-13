"""
This file contains Pipeline-restful-services
"""
# Standard library
import requests

# Flask specific
from flask import request
from flask_restful import Resource

# Validators
from candidate_service.modules.validators import get_candidate_if_validated

# Decorators
from candidate_service.common.utils.auth_utils import require_oauth, require_all_roles

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

        # Ensure candidate exists and belongs to user's domain
        get_candidate_if_validated(user=authed_user, candidate_id=candidate_id)

        # Maximum number of Talent Pipeline objects used for searching.
        # This is to prevent client from waiting too long for a response
        max_requests = 10

        # Get User-domain's 10 most recent talent pipelines in order of added time
        talent_pipelines = TalentPipeline.query.join(User).filter(
            User.domain_id == authed_user.domain_id).order_by(
            TalentPipeline.added_time.desc()).limit(max_requests).all()

        # Use Search API to retrieve candidate's domain-pipeline inclusion
        found_candidate_ids = []
        talent_pipeline_ids = []
        for number_of_requests, talent_pipeline in enumerate(talent_pipelines, start=1):
            search_response = search_candidates_from_params(search_params=talent_pipeline.search_params,
                                                            access_token=request.oauth_token,
                                                            url_args='?id={}'.format(candidate_id))

            found_candidate_ids.extend(candidate['id'] for candidate in search_response['candidates'])

            # Return if candidate_id is found in one of the Pipelines AND 5 or more requests have been made
            found = unicode(candidate_id) in found_candidate_ids
            if found:
                talent_pipeline_ids.append(talent_pipeline.id)
                if number_of_requests >= 5:
                    break

        result = []

        # Only return pipeline data if candidate is found from pipeline's search params
        if talent_pipeline_ids:
            candidates_talent_pipelines = TalentPipeline.query.filter(TalentPipeline.id.in_(talent_pipeline_ids)).all()
            for talent_pipeline in candidates_talent_pipelines:
                user_id = talent_pipeline.user_id
                user_candidate = Candidate.query.filter_by(user_id=user_id).first()
                result.append({
                    "id": talent_pipeline.id,
                    "candidate_id": user_candidate.id if user_candidate else None,
                    "name": talent_pipeline.name,
                    "description": talent_pipeline.description,
                    "open_positions": talent_pipeline.positions,
                    "datetime_needed": str(talent_pipeline.date_needed),
                    "user_id": user_id,
                    "added_datetime": str(talent_pipeline.added_time)
                })

        return {'candidate_pipelines': result}
