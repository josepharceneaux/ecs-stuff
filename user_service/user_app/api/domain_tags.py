"""
File contains endpoints for returning domain Tags
"""
# Standard libraries
import requests

# Flask specific
from flask import request
from flask_restful import Resource

# Models
from user_service.common.models.user import Permission
from user_service.common.models.tag import Tag
from user_service.common.models.user import User
from user_service.common.models.candidate import Candidate, CandidateTag

# Decorators
from user_service.common.utils.auth_utils import require_oauth, require_all_permissions

# Utilities
from user_service.user_app import logger
from user_service.common.utils.handy_functions import time_me
from user_service.common.utils.datetime_utils import DatetimeUtils


class DomainTagResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_DOMAINS)
    @time_me(logger, 'DomainTags')
    def get(self, **kwargs):
        """
        Function will return all tags belonging to domain
        Note: "description" is a required field
        Endpoint:  POST /v1/users/tags
        Usage:
            >>> headers = {'Authorization': 'Bearer {access_token}'}
            >>> requests.get(url="host/v1/domains/4/tags", headers=headers)
        """
        # Retrieve tags belonging to domain
        # TODO: Should link Tag to domain
        domain_tags = Tag.query.join(CandidateTag, Candidate, User). \
            filter(Candidate.user_id == User.id, User.domain_id == request.user.domain_id). \
            filter(CandidateTag.candidate_id == Candidate.id).all()

        return {
            'domain_tags':
                [{
                     'id': tag.id,
                     'name': tag.name,
                     'added_datetime': DatetimeUtils.to_utc_str(tag.added_datetime),
                     'updated_datetime': DatetimeUtils.to_utc_str(tag.updated_datetime),
                 } for tag in domain_tags]
        }
