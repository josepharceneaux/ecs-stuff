# StdLib
from time import time
# Third Party
from flask import Blueprint, jsonify, request
from flask_restful import Resource
# Module Specific
from banner_service.app import redis_store
from banner_service.common.error_handling import InvalidUsage
from banner_service.common.talent_api import TalentApi

BANNER_REDIS_KEY = 'gt_global_banner'
REQUIRED_DATA = ('title', 'text', 'link', 'color')

banner_api_bp = Blueprint('v1_banner_api', __name__)
api = TalentApi(banner_api_bp)


class BannerResource(Resource):
    """
    CRD API for interacting with Redis.
    """

    def get(self):
        return jsonify({'Response': 'Landed'})

    #TODO content-type decorator
    def post(self):
        # Check to see if there is an existing entry at the key prefix
        existing_banner = redis_store.hgetall(BANNER_REDIS_KEY)
        # Return Error if so
        if existing_banner:
            raise InvalidUsage(
                error_message="Cannot POST banner when an active banner exists")

        posted_data = request.get_json()
        for required_param in REQUIRED_DATA:
            if not posted_data.get(required_param):
                raise InvalidUsage(
                    error_message='Missing param: {}'.format(required_param))

        posted_data['timestamp'] = time()
        # TODO Implement validated user ID
        # posted_data['owner_id'] = request.user.id

        current_banner = redis_store.hmset(posted_data)

        return jsonify(current_banner)


api.add_resource(BannerResource, '/banners')
