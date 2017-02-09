"""
Flask end points for checking is a user has seen a banner
"""
# Third Party
from flask import Blueprint, jsonify, request
from flask_restful import Resource
# Module Specific
from banner_service.common.talent_api import TalentApi
from banner_service.common.utils.auth_utils import require_oauth
from banner_service.app.modules.v1_user_banner_processors import create_user_banner_entry

user_banner_api_bp = Blueprint('v1_user_banner_api', __name__)
api = TalentApi(user_banner_api_bp)


class UserBannerResource(Resource):
    """
    CR API for interacting with Redis to see if a user has seen a banner.
    """
    decorators = [require_oauth()]

    def get(self):
        user_id = request.user.id
        return {'has_seen_banner': True}, 200

    def post(self):
        user_id = request.user.id
        return {'entry_created': create_user_banner_entry(user_id)}, 201


api.add_resource(UserBannerResource, '/user_banner')
