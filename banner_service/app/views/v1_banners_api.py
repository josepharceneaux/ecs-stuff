from flask import jsonify, Blueprint
from flask_restful import Resource
from banner_service.common.talent_api import TalentApi

banner_api_bp = Blueprint('v1_banner_api', __name__)
api = TalentApi(banner_api_bp)

class BannerResource(Resource):
    def get(self):
        return jsonify({'Response': 'Landed'})

api.add_resource(BannerResource, '/banners')