"""
 Author: Hafiz Muhammad Basit, QC-Technologies,
        Lahore, Punjab, Pakistan <basit.gettalent@gmail.com>

    This file contains API endpoints related to Url Conversion.
        Following is a list of API endpoints:
            - ConvertUrl:  /v1/url_conversion
                POST     : This converts the given URL into shortened URL using
                          Google's Shorten URL API.

"""

# Standard Library
import types

# Third Party
from flask import request
from flask import Blueprint
from flask.ext.cors import CORS
from flask.ext.restful import Resource

# Common Utils
from sms_campaign_service.common.talent_api import TalentApi
from sms_campaign_service.common.utils.api_utils import api_route
from sms_campaign_service.common.error_handling import InvalidUsage
from sms_campaign_service.common.utils.auth_utils import require_oauth
from sms_campaign_service.common.utils.app_rest_urls import SmsCampaignApiUrl
from sms_campaign_service.common.utils.common_functions import url_conversion

# Service Specific
from sms_campaign_service.utilities import validate_header
from sms_campaign_service.custom_exceptions import (GoogleShortenUrlAPIError, MissingRequiredField)

# creating blueprint
url_conversion_blueprint = Blueprint('url_conversion_api', __name__)
api = TalentApi()
api.init_app(url_conversion_blueprint)
api.route = types.MethodType(api_route, api)

# Enable CORS
CORS(url_conversion_blueprint, resources={
    r''+SmsCampaignApiUrl.API_VERSION+'/(url_conversion)': {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})


@api.route(SmsCampaignApiUrl.URL_CONVERSION)
class ConvertUrl(Resource):
    """
    This end point converts the given url into shorter version using
    Google's shorten URL API.
    """
    decorators = [require_oauth]

    def post(self):
        """
        This action returns shorted URL of given URL.
        :return short_url: a dictionary containing short url
        :rtype json

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.post(API_URL + '/url_conversion/', headers=headers,
                        data={"long_url": 'https://webdev.gettalent.com/web/default/angular#!/'})

        .. Response::

            {
              "short_url": "https://goo.gl/CazBJG",
              "status_code": 200
            }

        .. Status:: 200 (OK)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    500 (Internal Server Error)

        .. Error codes:: 5004 (GoogleShortenUrlAPIError)
        """
        validate_header(request)
        try:
            json_data = request.get_json()
        except:
            raise InvalidUsage(error_message='Given data in not in json format.')
        if 'url' not in json_data:
            raise MissingRequiredField(
                error_message="Data must be provided as '{url: <value>}'")
        if not json_data['url']:
            raise InvalidUsage(error_message='No URL is given.')
        short_url, error = url_conversion(json_data['url'])
        if short_url:
            return {'short_url': short_url}
        elif error:
            raise GoogleShortenUrlAPIError(error_message=error)
