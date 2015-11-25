"""
This file contains API endpoints related to Url Conversion.
    Following is a list of API endpoints:
        - ConvertUrl:  /url_conversion
            GET     : This converts the given URL into shortened URL using
                      Google's Shorten URL API.

"""
__author__ = 'basit'

# Standard Library
import json
import types

# Third Party
from flask import request
from flask import Blueprint
from flask.ext.cors import CORS
from flask.ext.restful import Api
from flask.ext.restful import Resource

# Application Specific
from sms_campaign_service import logger
from sms_campaign_service.utilities import url_conversion
from sms_campaign_service.common.utils.auth_utils import require_oauth
from sms_campaign_service.app.app_utils import api_route, ApiResponse
from sms_campaign_service.common.error_handling import InternalServerError

url_conversion_blueprint = Blueprint('url_conversion_api', __name__)
api = Api()
api.init_app(url_conversion_blueprint)
api.route = types.MethodType(api_route, api)


# Enable CORS
CORS(url_conversion_blueprint, resources={
    r'/(url_conversion)/*': {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})


@api.route('/url_conversion')
class ConvertUrl(Resource):
    """
    This end point converts the given url into shorter version using
    Google's shorten URL API.
    """
    decorators = [require_oauth]

    def get(self):
        """
        This action returns shorted url of given url
        :return short_url: a dictionary containing short url
        :rtype json

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.get(API_URL + '/url_conversion/', headers=headers)

        .. Response::

            {
              "short_url": "https://goo.gl/CazBJG",
              "status_code": 200
            }

        .. Status:: 200 (OK)
                    500 (Internal Server Error)
                    401 (Unauthorized to access getTalent)
        """
        if request.values.get('url'):
            try:
                short_url = url_conversion(request.values['url'])
                data = {'short_url': short_url}
            except:
                logger.exception('ConvertUrl:')
                raise InternalServerError
        else:
            data = {'message': 'No URL given in request'}
        return ApiResponse(json.dumps(data), status=200)
