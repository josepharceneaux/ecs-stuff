"""
This file contains Pipeline-restful-services
"""
# Standard library
import requests
import json
import urllib

# Flask specific
from flask import request
from flask_restful import Resource

from candidate_service.candidate_app import logger

# Validators
from candidate_service.modules.validators import get_candidate_if_validated

# Decorators
from candidate_service.common.utils.auth_utils import require_oauth, require_all_permissions, is_number

# Handlers
from candidate_service.common.error_handling import InvalidUsage

# Models
from candidate_service.common.models.user import Permission, User
from candidate_service.common.models.talent_pools_pipelines import (
    TalentPipeline, TalentPoolCandidate, TalentPipelineIncludedCandidates, TalentPipelineExcludedCandidates
)
from candidate_service.modules.candidate_engagement import top_most_engaged_pipelines_of_candidate
from candidate_service.common.inter_service_calls.candidate_service_calls import search_candidates_from_params

from candidate_service.common.utils.handy_functions import time_me


class CandidatePipelineResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CANDIDATES)
    @time_me(logger=logger, api='candidate_pipeline_inclusion')
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
        max_requests = 30

        is_hidden = request.args.get('is_hidden', 0)
        if not is_number(is_hidden) or int(is_hidden) not in (0, 1):
            raise InvalidUsage('`is_hidden` can be either 0 or 1')

        # Candidate's talent pool ID
        candidate_talent_pool_ids = [tp.talent_pool_id for tp in TalentPoolCandidate.query.filter_by(
                candidate_id=candidate_id).all()]

        added_pipelines = TalentPipelineIncludedCandidates.query.filter_by(candidate_id=candidate_id).all()
        added_pipelines = map(lambda x: x.talent_pipeline, added_pipelines)

        removed_pipeline_ids = map(lambda x: x[0], TalentPipelineExcludedCandidates.query.with_entities(
                TalentPipelineExcludedCandidates.talent_pipeline_id).filter_by(candidate_id=candidate_id).all())

        # Get User-domain's 10 most recent talent pipelines in order of added time
        talent_pipelines = TalentPipeline.query.join(User).filter(
            TalentPipeline.is_hidden == is_hidden,
            TalentPipeline.talent_pool_id.in_(candidate_talent_pool_ids),
            TalentPipeline.id.notin_(removed_pipeline_ids)
        ).order_by(TalentPipeline.added_time.desc()).limit(max_requests).all()

        # Use Search API to retrieve candidate's domain-pipeline inclusion
        found_talent_pipelines = []

        for number_of_requests, talent_pipeline in enumerate(talent_pipelines, start=1):
            search_params = talent_pipeline.search_params
            if search_params:
                search_response = search_candidates_from_params(
                        search_params=format_search_params(talent_pipeline.search_params),
                        access_token=request.oauth_token,
                        url_args='?id={}&talent_pool_id={}'.format(candidate_id, talent_pipeline.talent_pool_id))

                logger.info("\ncandidate_id: {}\ntalent_pipeline_id: {}\nsearch_params: {}\nsearch_response: {}".format(
                    candidate_id, talent_pipeline.id, search_params, search_response))

                # Return if candidate_id is found in one of the Pipelines AND 5 or more requests have been made
                if search_response.get('candidates'):
                    found_talent_pipelines.append(talent_pipeline)

        result = []

        found_talent_pipelines += added_pipelines
        found_talent_pipelines = list(set(found_talent_pipelines))

        logger.info("\nfound_talent_pipelines: {}".format(found_talent_pipelines))

        # Only return pipeline data if candidate is found from pipeline's search params
        if found_talent_pipelines:
            pipeline_engagements = top_most_engaged_pipelines_of_candidate(candidate_id)
            for talent_pipeline in found_talent_pipelines:
                result.append({
                    "id": talent_pipeline.id,
                    "candidate_id": candidate_id,
                    "name": talent_pipeline.name,
                    "description": talent_pipeline.description,
                    "open_positions": talent_pipeline.positions,
                    "pipeline_engagement": pipeline_engagements.get(int(talent_pipeline.id), None),
                    "datetime_needed": str(talent_pipeline.date_needed),
                    'is_hidden': talent_pipeline.is_hidden,
                    "user_id": talent_pipeline.user_id,
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
            values = ','.join(str(v) for v in value)
            fixed_search_params += values
            fixed_search_params += '&'
        else:
            fixed_search_params += str(value)
            fixed_search_params += '&'

    return fixed_search_params[:-1]  # slice string to remove the last ampersand
