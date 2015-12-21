# Standard Library
import json
import types

# Third Party
from flask import request
from flask import Blueprint
from flask.ext.cors import CORS
from flask.ext.restful import Resource

# Application Specific
from push_notification_service import logger
from push_notification_service.common.error_handling import *
from push_notification_service.common.talent_api import TalentApi
from push_notification_service.common.utils.auth_utils import require_oauth
from push_notification_service.common.utils.api_utils import api_route, ApiResponse
from push_notification_service.one_signal_sdk import OneSignalSdk
from push_notification_service.constants import ONE_SIGNAL_REST_API_KEY, ONE_SIGNAL_APP_ID

# creating blueprint
push_notification_blueprint = Blueprint('push_notification_api', __name__)
api = TalentApi()
api.init_app(push_notification_blueprint)
api.route = types.MethodType(api_route, api)


# Enable CORS
CORS(push_notification_blueprint, resources={
    r'' + 'push_notifications/*': {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})

one_signal_client = OneSignalSdk(app_id=ONE_SIGNAL_APP_ID,
                                 rest_key=ONE_SIGNAL_REST_API_KEY)


@api.route('/push_notifications/')
class PushNotifications(Resource):

    decorators = [require_oauth]

    def get(self, user, **kwargs):
        res = one_signal_client.get_notifications()
        return res.content

    def post(self, *args, **kwargs):
        user = request.user
        data = request.get_json()
        players = data.get('players')
        req = one_signal_client.create_notification(data['url'], data['message'], data['title'], players=players)
        if req.ok:
            return req.json()
        else:
            return {"error": "Unable to send notification"}