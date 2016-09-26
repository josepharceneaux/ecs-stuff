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
from candidate_service.common.utils.auth_utils import require_oauth, require_all_permissions, is_number

# Handlers
from candidate_service.common.error_handling import InvalidUsage

# Models
from candidate_service.common.models.user import Permission, User
from candidate_service.common.models.candidate import Candidate
from candidate_service.common.models.talent_pools_pipelines import TalentPipeline
from candidate_service.modules.candidate_engagement import top_most_engaged_pipelines_of_candidate
from candidate_service.common.inter_service_calls.candidate_service_calls import search_candidates_from_params


class CandidatePipelineResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CANDIDATES)
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

        is_hidden = request.args.get('is_hidden', 0)
        if not is_number(is_hidden) or int(is_hidden) not in (0, 1):
            raise InvalidUsage('`is_hidden` can be either 0 or 1')

        # Get User-domain's 10 most recent talent pipelines in order of added time
        talent_pipelines = TalentPipeline.query.join(User).filter(
            TalentPipeline.is_hidden == is_hidden,  User.domain_id == authed_user.domain_id).order_by(
            TalentPipeline.added_time.desc()).limit(max_requests).all()

        # Use Search API to retrieve candidate's domain-pipeline inclusion
        found_candidate_ids = []
        talent_pipeline_ids = []
        for number_of_requests, talent_pipeline in enumerate(talent_pipelines, start=1):
            search_response = search_candidates_from_params(search_params=talent_pipeline.search_params,
                                                            access_token=request.oauth_token,
                                                            url_args='?id={}&talent_pool_id={}'.
                                                            format(candidate_id, talent_pipeline.talent_pool_id))

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
            pipeline_engagements = top_most_engaged_pipelines_of_candidate(candidate_id)
            candidates_talent_pipelines = TalentPipeline.query.filter(TalentPipeline.id.in_(talent_pipeline_ids)).all()
            for talent_pipeline in candidates_talent_pipelines:
                user_id = talent_pipeline.user_id
                user_candidate = Candidate.query.filter_by(user_id=user_id, id=candidate_id).first()
                if user_candidate:
                    result.append({
                        "id": talent_pipeline.id,
                        "candidate_id": user_candidate.id if user_candidate else None,
                        "name": talent_pipeline.name,
                        "description": talent_pipeline.description,
                        "open_positions": talent_pipeline.positions,
                        "pipeline_engagement": pipeline_engagements.get(int(talent_pipeline.id), None),
                        "datetime_needed": str(talent_pipeline.date_needed),
                        'is_hidden': talent_pipeline.is_hidden,
                        "user_id": user_id,
                        "added_datetime": str(talent_pipeline.added_time)
                    })

        return {'candidate_pipelines': result}
