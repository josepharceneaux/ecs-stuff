"""
This file contains API endpoints related to sms_campaign_service.
    Following is a list of API endpoints:
        - ConvertUrl:  /convert_url/
            GET     : This converts the given URL into shortened URL using
                      Google's Shorten URL API.

"""
# Standard Library
import json
import types

# Third Party
from flask import request
from flask import Blueprint
from flask.ext.restful import Api
from flask.ext.restful import Resource
from flask.ext.cors import CORS
# from sms_campaign_service.utilities import url_conversion
from sms_campaign_service.app.app_utils import authenticate, api_route, ApiResponse

sms_campaign_blueprint = Blueprint('sms_campaign_api', __name__)
api = Api()
api.init_app(sms_campaign_blueprint)
api.route = types.MethodType(api_route, api)


# Enable CORS
CORS(sms_campaign_blueprint, resources={
    r'/(sms_campaign_api)/*': {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})


@api.route('/convert_url')
class ConvertUrl(Resource):

    def get(self, *args, **kwargs):
        url = request.args.get('url')
        if url:
            short_url, long_url = url_conversion(url)
            data = {'short_url': short_url,
                    'long_url': long_url,
                    'status_code': 200}
        else:
            data = {'message': 'No URL given in request',
                    'status_code': 200}
        return ApiResponse(json.dumps(data), status=200)
