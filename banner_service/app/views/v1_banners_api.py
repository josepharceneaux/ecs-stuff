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
from banner_service.app.modules.v1_api_processors import create_banner, read_banner, delete_banner

BANNER_REDIS_KEY = 'gt_global_banner'
REQUIRED_DATA = ('title', 'text', 'link', 'color')

banner_api_bp = Blueprint('v1_banner_api', __name__)
api = TalentApi(banner_api_bp)


class BannerResource(Resource):
    """
    CRD API for interacting with Redis.
    """
    # TODO add role decorator
    decorators = [require_role('POTATO'), require_oauth()]

    def get(self):
        return jsonify(read_banner())

    # TODO content-type decorator
    # TODO add role decorator
    def post(self):
        posted_data = request.get_json()
        return jsonify({'banner_created': create_banner(posted_data)})

    # TODO add role decorator
    def delete(self):
        return jsonify({'banner_delete': delete_banner()})


api.add_resource(BannerResource, '/banners')
