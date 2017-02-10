"""
Flask end points for v1 banner app api.
"""
__author__ = 'erik@getTalent'
# StdLib
# Third Party
from flask import Blueprint, jsonify, request
from flask_restful import Resource
# Module Specific
from banner_service.common.talent_api import TalentApi
from banner_service.common.utils.auth_utils import require_oauth, require_role
from banner_service.app.modules.v1_banner_processors import create_banner, read_banner, delete_banner

BANNER_REDIS_KEY = 'gt_global_banner'
REQUIRED_DATA = ('title', 'text', 'link', 'style')

banner_api_bp = Blueprint('v1_banner_api', __name__)
api = TalentApi(banner_api_bp)


class BannerResource(Resource):
    """
    CRD API for interacting with Redis for banners.
    """
    decorators = [require_oauth()]

    def get(self):
        return jsonify(read_banner())

    # TODO content-type decorator
    @require_role('TALENT_ADMIN')
    def post(self):
        posted_data = request.get_json()
        return {'banner_created': create_banner(posted_data)}

    @require_role('TALENT_ADMIN')
    def delete(self):
        return {'banner_delete': delete_banner()}


api.add_resource(BannerResource, '/banners')
