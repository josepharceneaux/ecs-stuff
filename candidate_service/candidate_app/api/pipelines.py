"""
This file contains Pipeline-restful-services
"""
# Standard library
import requests
import json

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
from candidate_service.common.models.talent_pools_pipelines import TalentPipeline, TalentPoolCandidate
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

        # Candidate's talent pool ID
        candidate_talent_pool_ids = [tp.talent_pool_id for tp in TalentPoolCandidate.query.
            filter_by(candidate_id=candidate_id).all()]

        # Get User-domain's 10 most recent talent pipelines in order of added time
        talent_pipelines = TalentPipeline.query.join(User).filter(
            TalentPipeline.is_hidden == is_hidden,
            TalentPipeline.talent_pool_id.in_(candidate_talent_pool_ids)
        ).order_by(TalentPipeline.added_time.desc()).limit(max_requests).all()

        # Use Search API to retrieve candidate's domain-pipeline inclusion
        found_candidate_ids = []
        talent_pipeline_ids = []

        for number_of_requests, talent_pipeline in enumerate(talent_pipelines, start=1):
            search_response = search_candidates_from_params(
                search_params=format_search_params(talent_pipeline.search_params),
                access_token=request.oauth_token,
                url_args='?id={}&talent_pool_id={}'.format(candidate_id, talent_pipeline.talent_pool_id))

            found_candidate_ids.extend(candidate['id'] for candidate in search_response['candidates'])

            # Return if candidate_id is found in one of the Pipelines AND 5 or more requests have been made
            if search_response.get('candidates'):
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


def format_search_params(search_params):
    """
    Function will format talent-pipeline's search-params to conform with the search API
        E.g.: search_params: {"skills": ["Python", "Java"], "user_ids": 45} => "skills=Python,Java&user_ids=45"
    :rtype: str
    """
    fixed_search_params = ''
    for key, value in json.loads(search_params).iteritems():
        if not value:
            continue
        fixed_search_params += key
        fixed_search_params += '='
        if isinstance(value, list):
            values = ','.join(v for v in value)
            fixed_search_params += values
            fixed_search_params += '&'
        else:
            fixed_search_params += str(value)
            fixed_search_params += '&'

    return fixed_search_params[:-1]  # slice string to remove the last ampersand
