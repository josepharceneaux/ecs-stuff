"""
This file contains Pipeline-restful-services
"""
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

from candidate_service.common.utils.test_utils import send_request
from candidate_service.common.routes import CandidateApiUrl


class CandidatePipelineResource(Resource):
    decorators = [require_oauth()]

    @require_all_roles(DomainRole.Roles.CAN_GET_CANDIDATES)
    def get(self, **kwargs):
        """
        Function will return user's 5 most recently added Pipelines. One of the pipelines will
          include the specified candidate.
        :return:
        """
        # Authenticated user & candidate ID
        authed_user, candidate_id = request.user, kwargs['candidate_id']

        # Check if candidate exists & is web-hidden
        get_candidate_if_exists(candidate_id)

        # Candidate must belong to user's domain
        if not does_candidate_belong_to_users_domain(authed_user, candidate_id):
            raise ForbiddenError("Not authorized", custom_error.CANDIDATE_FORBIDDEN)

        # Get User-domain's five most recent talent pipelines in order of added time
        talent_pipelines = TalentPipeline.query.join(User).filter(
            User.domain_id == authed_user.domain_id).order_by(TalentPipeline.added_time.desc()).limit(5).all()

        # Use Search API to retrieve candidate's domain-pipeline inclusion
        smart_list_ids = ','.join(map(str, [talent_pipeline.id for talent_pipeline in talent_pipelines]))
        url = CandidateApiUrl.CANDIDATE_SEARCH_URI + '?id={}&smart_list_ids={}'.format(candidate_id, smart_list_ids)
        search_response = send_request('get', url, access_token=authed_user.token[0].access_token)

        found_candidate_ids = [candidate['id'] for candidate in search_response.json()['candidates']]
        if candidate_id not in found_candidate_ids:
            return {'candidate_pipelines': []}

        else:
            return [{
                        'id': talent_pipeline.id,
                        'candidate_id': Candidate.query.filter_by(user_id=talent_pipeline.user_id).first().id,
                        'name': talent_pipeline.name,
                        'description': talent_pipeline.description,
                        'open_positions': talent_pipeline.positions,
                        'datetime_needed': str(talent_pipeline.date_needed),
                        'user_id': talent_pipeline.user_id,
                        'added_datetime': str(talent_pipeline.added_time)
                    } for talent_pipeline in talent_pipelines]
