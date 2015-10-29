"""
This module contains api endpoint which are very much Events App specific.
It contains endpoint for timezones which returns a list of all timezones.
"""
from datetime import datetime
import json
import types
from flask import Blueprint
from flask.ext.restful import Resource, Api
from flask.ext.cors import CORS
import pytz
from social_network_service.app.app_utils import api_route, ApiResponse, CustomApi

data_blueprint = Blueprint('data_api', __name__)
api = CustomApi()
api.init_app(data_blueprint)
api.route = types.MethodType(api_route, api)


# Enable CORS
CORS(data_blueprint, resources={
    r'/data/*': {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})


@api.route('/data/timezones/')
class TimeZones(Resource):
    """
        This resource returns a list of timezones
    """
    def get(self, **kwargs):
        """
        This action returns a list of user timezones.

            :Example:

                    headers = {
                                'Authorization': 'Bearer <access_token>'
                               }
                    response = requests.get(
                                                API_URL + '/data/timezones',
                                                headers=headers,
                                            )




        .. Response:
                {
                  "timezones": [
                    {
                      "name": "GMT +00:00  Africa/Abidjan",
                      "value": "Africa/Abidjan"
                    },
                    {
                      "name": "GMT +00:00  Africa/Accra",
                      "value": "Africa/Accra"
                    },
                    {
                      "name": "GMT +00:00  Africa/Bamako",
                      "value": "Africa/Bamako"
                    },
                    {
                      "name": "GMT +00:00  Africa/Banjul",
                      "value": "Africa/Banjul"
                    },
                    .
                    .
                    .
                    .
                    .
                   ]
                }
        """
        try:
            timezones = get_timezones()
        except Exception as e:
            return ApiResponse(json.dumps(dict(messsage='APIError: Internal Server Error')), status=500)
        return ApiResponse(json.dumps(dict(timezones=timezones)), status=200)


def get_timezones():
    """
    This function returns a list of timezones.
    It uses pytz to get commonly used timezones.
    :return:
    """
    timezones = []
    for timezone_name in pytz.common_timezones:
        offset = datetime.now(pytz.timezone(timezone_name)).strftime('%z')
        offset_hours = offset[:3]
        offset_minutes = offset[3:]
        timezone = dict(name='GMT ' + offset_hours + ':' + offset_minutes + '  ' + timezone_name,
                        value=timezone_name)
        timezones += [timezone]
        timezones.sort()
    return timezones
