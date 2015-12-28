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
from push_notification_service.common.models.push_notification import PushNotification
from push_notification_service.one_signal_sdk import OneSignalSdk
from push_notification_service.constants import ONE_SIGNAL_REST_API_KEY, ONE_SIGNAL_APP_ID, DEFAULT_NOTIFICATION_OFFSET, \
    DEFAULT_NOTIFICATION_LIMIT, DEFAULT_PLAYERS_OFFSET, DEFAULT_PLAYERS_LIMIT
from push_notification_service.push_notification_campaign import PushNotificationCampaign

# creating blueprint
push_notification_blueprint = Blueprint('push_notification_api', __name__)
api = TalentApi()
api.init_app(push_notification_blueprint)
api.route = types.MethodType(api_route, api)


# Enable CORS
CORS(push_notification_blueprint, resources={
    r'push_notifications/*': {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})

one_signal_client = OneSignalSdk(app_id=ONE_SIGNAL_APP_ID,
                                 rest_key=ONE_SIGNAL_REST_API_KEY)


@api.route('/v1/push_notifications/')
class PushNotifications(Resource):

    decorators = [require_oauth]

    def get(self, *args, **kwargs):
        data = request.values
        offset = int(data['offset']) if 'offset' in data and data['offset'].isdigit() else DEFAULT_NOTIFICATION_OFFSET
        limit = int(data['limit']) if 'limit' in data and data['limit'].isdigit() else DEFAULT_NOTIFICATION_LIMIT
        res = one_signal_client.get_notifications(limit=limit, offset=offset)
        return res.json()

    def post(self, *args, **kwargs):
        user = request.user
        data = request.get_json()
        players = data.get('players')
        req = one_signal_client.create_notification(data['url'], data['message'], data['title'], players=players)
        response = req.json()
        if req.ok:
            recipients = response['recipients']
            one_signal_pn_id = response['id']
            push_notification = PushNotification(content=data['message'], url=data['url'],
                                                 title=data['title'], user_id=user.id,
                                                 recipients=recipients, one_signal_id=one_signal_pn_id)
            PushNotifications.save(push_notification)
            response = dict(id=push_notification.id, message='Push notification created successfully')
            response = json.dump(response)
            headers = dict(Location='/v1/push_notifications/%s' % push_notification.id)
            return ApiResponse(response, headers=headers, status=201)
        else:
            errors = '\n'.join(response['errors'])
            return {"errors": errors}, 500


@api.route('/v1/push_notifications/<int:push_notification_id>/send')
class PushNotificationSend(Resource):

    decorators = [require_oauth]

    def post(self, push_notification_id, **kwargs):
        user = request.user
        campaign = PushNotificationCampaign(user_id=user.id)
        subscribed_candidate_ids, unsubscribed_candidate_ids = campaign.process_send(push_notification_id)
        if unsubscribed_candidate_ids:
            response = dict(message='Unable to send Push notification to some candidates as they have unsubscribed',
                            unsubscribed_candiate_ids=unsubscribed_candidate_ids,
                            subscribed_candidate_ids=subscribed_candidate_ids)
            return response, 207
        else:
            response = dict(message='Push notification has been sent successfully to all candidates')
            return response, 200


@api.route('/v1/players/')
class Players(Resource):

    decorators = [require_oauth]

    def get(self, *args, **kwargs):
        data = request.values
        offset = int(data['offset']) if 'offset' in data and data['offset'].isdigit() else DEFAULT_PLAYERS_OFFSET
        limit = int(data['limit']) if 'limit' in data and data['limit'].isdigit() else DEFAULT_PLAYERS_LIMIT
        res = one_signal_client.get_players(limit=limit, offset=offset)
        return res.json()

    def post(self, *args, **kwargs):
        pass