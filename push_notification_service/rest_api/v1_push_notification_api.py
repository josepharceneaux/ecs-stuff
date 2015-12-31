# Standard Library
import types
from datetime import datetime

# Third Party
from flask import request
from flask import Blueprint
from flask.ext.cors import CORS
from flask.ext.restful import Resource


# Application Specific
from push_notification_service.common.models.candidate import Candidate, CandidateDevice
from push_notification_service.common.talent_api import TalentApi
from push_notification_service.common.utils.auth_utils import require_oauth
from push_notification_service.common.utils.api_utils import api_route, ApiResponse
from push_notification_service.common.models.push_notification import PushCampaign, PushCampaignSmartlist
from push_notification_service.common.error_handling import *
from push_notification_service.custom_exceptions import *
from push_notification_service.one_signal_sdk import OneSignalSdk
from push_notification_service.constants import ONE_SIGNAL_REST_API_KEY, ONE_SIGNAL_APP_ID
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
        """
        This action returns a list of all Campaigns for current user.

        :return campaigns_data: a dictionary containing list of campaigns and their count
        :rtype json

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.get(API_URL + '/campaigns/', headers=headers)

        .. Response::

            {
                "count": 2,
                "campaigns": [
                            {
                              "added_datetime": "2015-11-19 18:54:04",
                              "frequency_id": 2,
                              "id": 3,
                              "title": "QC Technologies",
                              "start_datetime": "2015-11-19 18:55:08",
                              "end_datetime": "2015-11-25 18:55:08"
                              "content": "Join QC Technologies.",
                              "url": "https://www.qc-technologies.com/careers"
                            },
                            {
                              "added_datetime": "2015-11-19 18:55:08",
                              "frequency_id": 1,
                              "id": 4,
                              "title": "getTalent",
                              "start_datetime": "2015-12-12 10:55:08",
                              "end_datetime": "2015-12-31 18:55:08"
                              "content": "Job opening at QC Technologies",
                              "url": "https://www.qc-technologies.com/careers"
                            }
              ]
            }

        .. Status:: 200 (OK)
                    401 (Unauthorized to access getTalent)
                    403 (Forbidden error)
                    500 (Internal Server Error)
        """
        user = request.user
        campaigns = [campaign.to_json() for campaign in PushCampaign.get_by_user_id(user.id)]
        return dict(campaigns=campaigns, count=len(campaigns)), 200

    def post(self):
        """
        This method takes data to create a Push campaign in database. This campaign is just a
        draft and we need to schedule or send it later.
        :return: id of created campaign and a success message
        :type: json

        :Example:

            campaign_data = {
                                "title": "QC Technologies",
                                "content": "New job openings...",
                                "url": "https://www.qc-technologies.com",
                                "smartlist_ids": [1, 2, 3]
                             }

            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'content-type': 'application/json'

                       }
            data = json.dumps(campaign_data)
            response = requests.post(
                                        API_URL + '/v1/campaigns/',
                                        data=data,
                                        headers=headers,
                                    )

        .. Response::

            {
                id: 11
            }

        .. Status:: 201 (Resource Created)
                    401 (Unauthorized to access getTalent)
                    403 (Forbidden error)
                    500 (Internal Server Error)

        ..Error Codes:: 7003 (RequiredFieldsMissing)
        """
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
        """
        It sends given Campaign (from given campaign id) to the smartlist candidates
            associated with given campaign.

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            campaign_id = 1
            response = requests.post(API_URL + '/v1/campaigns/' + str(campaign_id)
                                + '/send', headers=headers)

        .. Response::

                {
                    "message": "Push campaign (id: 1) has been sent successfully to all candidates"
                }

        .. Status:: 200 (OK)
                    401 (Unauthorized to access getTalent)
                    404 (Campaign not found)
                    500 (Internal Server Error)

        .. Error Codes:: 7002 (NoSmartlistAssociated)

        :param campaign_id: integer, unique id representing campaign in GT database
        """
        user = request.user
        campaign = PushCampaignBase(user_id=user.id)
        subscribed_candidate_ids, unsubscribed_candidate_ids = campaign.process_send(campaign_id)
        if unsubscribed_candidate_ids:
            response = dict(message='Unable to send Push notification to some candidates as they have unsubscribed',
                            unsubscribed_candiate_ids=unsubscribed_candidate_ids,
                            subscribed_candidate_ids=subscribed_candidate_ids)
            return response, 207
        else:
            response = dict(message='Push campaign (id:%s) has been sent successfully to all candidates' % campaign_id)
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
        """
        Returns Campaign sends for given push campaign id

        :param campaign_id: integer, unique id representing puah campaign in getTalent database
        :return: 1- count of campaign sends and 2- Push campaign sends

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            campaign_id = 1
            response = requests.get(API_URL + '/v1/campaigns/' + str(campaign_id)
                                + '/sends/', headers=headers)

        .. Response::

            {
                "campaign_sends": [
                            {
                              "campaign_blast_id": 10,
                              "candidate_id": 268,
                              "id": 6,
                              "sent_datetime": "2015-12-30 17:03:53"
                            },
                            {
                              "campaign_blast_id": 12,
                              "candidate_id": 268,
                              "id": 7,
                              "sent_datetime": "2015-12-30 17:07:39"
                            }
                ],
                "count": 2

            }

        .. Status:: 200 (OK)
                    401 (Unauthorized to access getTalent)
                    404 (Campaign not found)
                    500 (Internal Server Error)
        """
        user = request.user
        push_campaign = PushCampaign.get_by_id_and_user_id(campaign_id, user.id)
        if not push_campaign:
            raise ResourceNotFound('Push campaign does not exists with id %s for this user' % campaign_id)
        sends = []
        [sends.extend(blast.blast_sends) for blast in push_campaign.blasts]
        sends = [send.to_json() for send in sends]
        response = dict(campaign_sends=sends, count=len(sends))
        return response, 200


@api.route('/v1/campaigns/<int:campaign_id>/blasts')
class PushNotificationBlasts(Resource):

    decorators = [require_oauth()]

    def get(self, campaign_id):
        """
        This endpoint returns a list of blast objects (dict) associated with a specific push campaign.

        :param campaign_id: int, unique id of a push campaign
        :return: json data containing list of blasts and their counts


        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            campaign_id = 1
            response = requests.get(API_URL + '/v1/campaigns/' + str(campaign_id)+ '/blasts',
                                    headers=headers)

        .. Response::

            {
                "blasts": [
                            {
                              "campaign_id": 2,
                              "clicks": 6,
                              "id": 1,
                              "sends": 10,
                              "updated_time": "2015-12-30 14:33:44"
                            },
                            {
                              "campaign_id": 2,
                              "clicks": 11,
                              "id": 2,
                              "sends": 20,
                              "updated_time": "2015-12-30 14:33:00"
                            }
                ],
                "count": 2

            }

        .. Status:: 200 (OK)
                    401 (Unauthorized to access getTalent)
                    404 (Campaign not found)
                    500 (Internal Server Error)
        """
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

    def post(self):
        """
        This endpoint is used to register a candidate's device with getTalent.
        Device id is a unique string given by OneSignal API.
        for more information about device id see here
        https://documentation.onesignal.com/docs/website-sdk-api#getIdsAvailable

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            data = {
                    "candidate_id": 268,
                    "device_id": "56c1d574-237e-4a41-992e-c0094b6f2ded"

                }
            data = json.dumps(data)
            campaign_id = 1
            response = requests.post(API_URL + '/v1/devices, data=data, headers=headers)

        .. Response::

                {
                    "message": "Device registered successfully with candidate (id: 268)"
                }

        .. Status:: 200 (OK)
                    401 (Unauthorized to access getTalent)
                    403 (Can't add device for non existing candidate)
                    500 (Internal Server Error)
        """
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


