# Standard Library
import json
import types
from datetime import datetime
from urlparse import urlparse

# Third Party
import requests
from flask import request
from flask import Blueprint
from flask.ext.cors import CORS
from flask.ext.restful import Resource


# Application Specific
from push_notification_service import logger
from push_notification_service.common.models.candidate import Candidate, CandidateDevice
from push_notification_service.common.models.misc import UrlConversion
from push_notification_service.common.talent_api import TalentApi
from push_notification_service.common.utils.auth_utils import require_oauth
from push_notification_service.common.utils.api_utils import api_route, ApiResponse
from push_notification_service.common.models.push_notification import PushCampaign, PushCampaignSmartlist, \
    PushCampaignBlast
from push_notification_service.common.error_handling import *
from push_notification_service.custom_exceptions import *
from push_notification_service.one_signal_sdk import OneSignalSdk
from push_notification_service.constants import ONE_SIGNAL_REST_API_KEY, ONE_SIGNAL_APP_ID, DEFAULT_NOTIFICATION_OFFSET, \
    DEFAULT_NOTIFICATION_LIMIT, DEFAULT_PLAYERS_OFFSET, DEFAULT_PLAYERS_LIMIT
from push_notification_service.push_notification_campaign import PushCampaignBase

# creating blueprint
push_notification_blueprint = Blueprint('push_notification_api', __name__)
api = TalentApi()
api.init_app(push_notification_blueprint)
api.route = types.MethodType(api_route, api)


# Enable CORS
CORS(push_notification_blueprint, resources={
    r'v1/campaigns/*': {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})

one_signal_client = OneSignalSdk(app_id=ONE_SIGNAL_APP_ID,
                                 rest_key=ONE_SIGNAL_REST_API_KEY)


@api.route('/v1/campaigns')
class PushCampaigns(Resource):

    decorators = [require_oauth()]

    def get(self, *args, **kwargs):
        # data = request.values
        # offset = int(data['offset']) if 'offset' in data and data['offset'].isdigit() else DEFAULT_NOTIFICATION_OFFSET
        # limit = int(data['limit']) if 'limit' in data and data['limit'].isdigit() else DEFAULT_NOTIFICATION_LIMIT
        # res = one_signal_client.get_notifications(limit=limit, offset=offset)
        # return res.json()
        user = request.user
        campaigns = [campaign.to_json() for campaign in PushCampaign.get_by_user_id(user.id)]
        return dict(campaigns=campaigns, count=len(campaigns)), 200

    def post(self):
        user = request.user
        data = request.get_json()
        missing_values = [key for key in ['title', 'content', 'url', 'smartlist_ids'] if key not in data or not data[key]]
        if missing_values:
            raise RequiredFieldsMissing('Some required fields are missing: %s' % missing_values)
        push_campaign = PushCampaign(content=data['content'], url=data['url'],
                                     title=data['title'], user_id=user.id)
        PushCampaign.save(push_campaign)
        smartlist_ids = data.get('smartlist_ids')
        if isinstance(smartlist_ids, list):
            for smartlist_id in smartlist_ids:
                push_campaign_smartlist = PushCampaignSmartlist(smartlist_id=smartlist_id, campaign_id=push_campaign.id)
                PushCampaignSmartlist.save(push_campaign_smartlist)
        response = dict(id=push_campaign.id, message='Push campaign was created successfully')
        response = json.dumps(response)
        headers = dict(Location='/v1/campaigns/%s' % push_campaign.id)
        return ApiResponse(response, headers=headers, status=201)


@api.route('/v1/campaigns/<int:campaign_id>/schedule')
class SchedulePushCampaign(Resource):

    decorators = [require_oauth()]

    def post(self, campaign_id):
        """
        It schedules an Push Notification campaign using given campaign_id by making HTTP request to
         scheduler_service.

        :Example:

            headers = {'Authorization': 'Bearer <access_token>',
                       'Content-type': 'application/json'}

            schedule_data =
                        {
                            "frequency_id": 2,
                            "start_datetime": "2015-11-26T08:00:00Z",
                            "end_datetime": "2015-11-30T08:00:00Z"
                        }

            campaign_id = 1

            response = requests.post(API_URL + '/v1/campaigns/' + str(campaign_id) + '/schedule',
                                        headers=headers, data=schedule_data)

        .. Response::

                {
                    "message": "Campaign(id:1) is has been scheduled.
                    "task_id"; "33e32e8ac45e4e2aa710b2a04ed96371"
                }

        .. Status:: 200 (OK)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Forbidden Error)
                    404 (Campaign not found)
                    500 (Internal Server Error)

        .. Error codes:
                    7006 (CampaignAlreadyScheduled)

        :param campaign_id: integer, unique id representing campaign in GT database
        :return: JSON containing message and task_id.
        """
        user = request.user

        pre_processed_data = PushCampaignBase.pre_process_schedule(request, campaign_id)
        campaign_obj = PushCampaignBase(user.id)
        campaign_obj.campaign = pre_processed_data['campaign']
        task_id = campaign_obj.schedule(pre_processed_data['data_to_schedule'])
        return dict(message='Campaign(id:%s) has been scheduled.' % campaign_id,
                    task_id=task_id), 200

    def put(self, campaign_id):
        """
        This endpoint is to reschedule a campaign. It first deletes the old schedule of
        campaign from scheduler_service and then creates new task.

        :Example:

            headers = {'Authorization': 'Bearer <access_token>',
                       'Content-type': 'application/json'}

            schedule_data =
                        {
                            "frequency_id": 2,
                            "start_datetime": "2015-11-26T08:00:00Z",
                            "end_datetime": "2015-11-30T08:00:00Z"
                        }

            campaign_id = 1

            response = requests.put(API_URL + '/campaigns/' + str(campaign_id) + '/schedule',
                                        headers=headers, data=schedule_data)

        .. Response::

                {
                    "message": "Campaign(id:1) is has been re-scheduled.
                    "task_id"; "33e32e8ac45e4e2aa710b2a04ed96371"
                }

        .. Status:: 200 (OK)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Forbidden Error)
                    404 (Campaign not found)
                    500 (Internal Server Error)

        :param campaign_id: integer, unique id representing campaign in GT database
        :return: JSON containing message and task_id.
        """
        pre_processed_data = PushCampaignBase.pre_process_schedule(request, campaign_id)
        PushCampaignBase.pre_process_re_schedule(pre_processed_data)
        campaign_obj = PushCampaignBase(request.user.id)
        campaign_obj.campaign = pre_processed_data['campaign']
        task_id = campaign_obj.schedule(pre_processed_data['data_to_schedule'])
        return dict(message='Campaign(id:%s) has been re-scheduled.' % campaign_id,
                    task_id=task_id), 200


@api.route('/v1/campaigns/<int:campaign_id>/send')
class SendPushCampaign(Resource):

    decorators = [require_oauth()]

    def post(self, campaign_id):
        user = request.user
        campaign = PushCampaignBase(user_id=user.id)
        subscribed_candidate_ids, unsubscribed_candidate_ids = campaign.process_send(campaign_id)
        if unsubscribed_candidate_ids:
            response = dict(message='Unable to send Push notification to some candidates as they have unsubscribed',
                            unsubscribed_candiate_ids=unsubscribed_candidate_ids,
                            subscribed_candidate_ids=subscribed_candidate_ids)
            return response, 207
        else:
            response = dict(message='Push notification has been sent successfully to all candidates')
            return response, 200


@api.route('/v1/campaigns/<int:campaign_id>/blasts/<int:blast_id>/sends')
class PushCampaignBlastSends(Resource):

    decorators = [require_oauth()]

    def get(self, campaign_id, blast_id):
        user = request.user
        push_campaign = PushCampaign.get_by_id_and_user_id(campaign_id, user.id)
        if not push_campaign:
            raise ResourceNotFound('Push campaign does not exists with id %s for this user' % campaign_id)
        blast = filter(lambda item: item.id == blast_id, push_campaign.blasts)
        if len(blast):
            blast = blast[0]
            sends = [send.to_json() for send in blast.blast_sends]
            response = dict(sends=sends, count=len(sends))
            return response, 200
        else:
            return ResourceNotFound('Push Campaign Blast not found with id: %s' % blast_id)


@api.route('/v1/campaigns/<int:campaign_id>/sends')
class PushCampaignSends(Resource):

    decorators = [require_oauth()]

    def get(self, campaign_id):
        user = request.user
        push_campaign = PushCampaign.get_by_id_and_user_id(campaign_id, user.id)
        if not push_campaign:
            raise ResourceNotFound('Push campaign does not exists with id %s for this user' % campaign_id)
        sends = []
        [sends.extend(blast.blast_sends) for blast in push_campaign.blasts]
        sends = [send.to_json() for send in sends]
        response = dict(sends=sends, count=len(sends))
        return response, 200


@api.route('/v1/campaigns/<int:campaign_id>/blasts')
class PushNotificationBlasts(Resource):

    decorators = [require_oauth()]

    def get(self, campaign_id):
        user = request.user
        push_campaign = PushCampaign.get_by_id_and_user_id(campaign_id, user.id)
        if not push_campaign:
            raise ResourceNotFound('Push campaign does not exists with id %s for this user' % campaign_id)
        blasts = [blast.to_json() for blast in push_campaign.blasts]

        response = dict(blasts=blasts, count=len(blasts))
        return response, 200


@api.route('/v1/devices')
class Devices(Resource):

    decorators = [require_oauth()]

    # def get(self, *args, **kwargs):
    #     data = request.values
    #     offset = int(data['offset']) if 'offset' in data and data['offset'].isdigit() else DEFAULT_PLAYERS_OFFSET
    #     limit = int(data['limit']) if 'limit' in data and data['limit'].isdigit() else DEFAULT_PLAYERS_LIMIT
    #     res = one_signal_client.get_players(limit=limit, offset=offset)
    #     return res.json()

    def post(self, *args, **kwargs):
        data = request.get_json()
        candidate_id = data.get('candidate_id')
        device_id = data.get('device_id')
        candidate = Candidate.get_by_id(candidate_id)
        if not candidate:
            raise ForbiddenError('Unable to create a device for a non existing candidate id: %s' % candidate_id)
        if device_id:
            resp = one_signal_client.get_player(device_id)
            if resp.ok:
                candidate_device = CandidateDevice(candidate_id=candidate_id,
                                                   one_signal_device_id=device_id,
                                                   registered_at=datetime.now())
                CandidateDevice.save(candidate_device)
                return dict(messgae='Device registered successfully with candidate (id: %s)' % candidate_id)
            else:
                raise ResourceNotFound('Device is not registered with OneSignal with id %s' % device_id)
        else:
            raise InvalidUsage('device_id is not found in post data')


