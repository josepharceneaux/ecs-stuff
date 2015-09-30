from datetime import datetime
import json
import types
from flask import Blueprint
from flask.ext.restful import Resource, Api
import pytz
from social_network_service.app.app_utils import api_route, ApiResponse

data_blueprint = Blueprint('data_api', __name__)
api = Api()
api.init_app(data_blueprint)
api.route = types.MethodType(api_route, api)


@api.route('/data/timezones/')
class TimeZones(Resource):
    """
        This resource returns a list of timezones
    """
    def get(self, **kwargs):
        """
        This action returns a list of user timezones.
        """
        try:
            timezones = get_timezones()
        except Exception as e:
            return ApiResponse(json.dumps(dict(messsage='APIError: Internal Server Error')), status=500)
        return ApiResponse(json.dumps(dict(timezones=timezones)), status=200)


def get_timezones():
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
