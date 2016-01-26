"""
This module contains Restful API endpoints for Push Campaign Service.

A brief overview of all endpoints is as follows:

    1. Create a push campaign
        URL: /v1/campaigns [POST]

        Send a POST request to this endpoint with required data to create a push campaign.
        It actually creates a draft for campaign. To send a campaign, you need to schedule it.

    2. Get campaigns of a user
        URL: /v1/campaigns [GET]

        To get all campaigns of a user, send a GET request to this endpoint

    3. Schedule a campaign
        URL: /v1/campaigns/<int:campaign_id>/schedule [POST]

        User can schedule a campaign by sending a POST request to this endpoint with frequency,
        start_datetime and end_datetime.

    4. Reschedule a campaign
        URL: /v1/campaigns/<int:campaign_id>/schedule [PUT]

        User can reschedule his campaign by updating the frequency, start_datetime or end_datetime
        by sending a PUT request to this point.

    5. Send a campaign
        URL: /v1/campaigns/<int:campaign_id>/send [POST]

        This endpoint is used to send a campaign (that has already been created) to associated
        candidates by send a POST request to this endpoint.

    6. Get `Sends` of a Blast
        URL: /v1/campaigns/<int:campaign_id>/blasts/<int:blast_id>/sends [GET]

        A campaign can have multiple blast. To get sends of a single blast for a specific campaign
        send a GET request to this endpoint.

    7. Get `Sends` of a campaign
        URL: /v1/campaigns/<int:campaign_id>/sends [GET]

        To get all sends of a campaign, use this endpoint

    8. Get `Blasts` of a campaign
        URL: /v1/campaigns/<int:campaign_id>/blasts [GET]

        To get a list of all blasts associated to a campaign, send a GET request
        to this endpoint.A blast contains statistics of a campaign when a campaign
        is sent once to associated candidates.

    9. Register a device for candidate
        URL: /v1/devices [POST]

        Push notifications are sent to candidate devices using OneSignal API. One signal
        assigns a device id to each device which we need to assign to a candidate in getTalent
        database. In order to do that, we need to send a POST request to this endpoint with
        candidate id and device id (from OneSignal).


"""
# Standard Library
import types

# Third Party
from flask import request
from flask import redirect
from flask import Blueprint
from flask.ext.restful import Resource


# Application Specific
from push_campaign_service.common.campaign_services.campaign_base import CampaignBase
from push_campaign_service.common.campaign_services.campaign_utils import CampaignType
from push_campaign_service.common.error_handling import *
from push_campaign_service.common.talent_api import TalentApi
from push_campaign_service.common.routes import PushCampaignApi
from push_campaign_service.common.utils.auth_utils import require_oauth
from push_campaign_service.common.utils.api_utils import api_route, ApiResponse


from push_campaign_service.modules.custom_exceptions import *
from push_campaign_service.common.models.candidate import *
from push_campaign_service.common.models.push_campaign import *
from push_campaign_service.modules.one_signal_sdk import OneSignalSdk
from push_campaign_service.modules.push_campaign_base import PushCampaignBase
from push_campaign_service.modules.constants import (ONE_SIGNAL_REST_API_KEY,
                                                     ONE_SIGNAL_APP_ID)
from push_campaign_service.modules.utilities import (get_valid_json_data,
                                                     associate_smart_list_with_campaign)
from push_campaign_service.push_campaign_app import logger

# creating blueprint
push_notification_blueprint = Blueprint('push_notification_api', __name__)
api = TalentApi()
api.init_app(push_notification_blueprint)
api.route = types.MethodType(api_route, api)

one_signal_client = OneSignalSdk(app_id=ONE_SIGNAL_APP_ID,
                                 rest_key=ONE_SIGNAL_REST_API_KEY)


@api.route(PushCampaignApi.CAMPAIGNS)
class PushCampaignsResource(Resource):

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
                              "name": "QC Technologies",
                              "start_datetime": "2015-11-19 18:55:08",
                              "end_datetime": "2015-11-25 18:55:08"
                              "body_text": "Join QC Technologies.",
                              "url": "https://www.qc-technologies.com/careers"
                            },
                            {
                              "added_datetime": "2015-11-19 18:55:08",
                              "frequency_id": 1,
                              "id": 4,
                              "name": "getTalent",
                              "start_datetime": "2015-12-12 10:55:08",
                              "end_datetime": "2015-12-31 18:55:08"
                              "body_text": "Job opening at QC Technologies",
                              "url": "https://www.qc-technologies.com/careers"
                            }
              ]
            }

        .. Status:: 200 (OK)
                    401 (Unauthorized to access getTalent)
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
                                "name": "QC Technologies",
                                "body_text": "New job openings...",
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
        data = get_valid_json_data(request)
        missing_fields = [key for key in ['name', 'body_text',
                                          'url', 'smartlist_ids'] if key not in data or not data[key]]
        if missing_fields:
            raise RequiredFieldsMissing('Some required fields are missing',
                                        additional_error_info=dict(missing_fields=missing_fields))
        push_campaign = PushCampaign(body_text=data['body_text'], url=data['url'],
                                     name=data['name'], user_id=user.id)
        PushCampaign.save(push_campaign)
        smartlist_ids = data.get('smartlist_ids')
        if isinstance(smartlist_ids, list):
            for smartlist_id in smartlist_ids:
                push_campaign_smartlist = PushCampaignSmartlist(smartlist_id=smartlist_id, campaign_id=push_campaign.id)
                PushCampaignSmartlist.save(push_campaign_smartlist)
        response = dict(id=push_campaign.id, message='Push campaign was created successfully')
        response = json.dumps(response)
        headers = dict(Location='/%s/campaigns/%s' % (PushCampaignApi.VERSION, push_campaign.id))
        return ApiResponse(response, headers=headers, status=201)


@api.route(PushCampaignApi.CAMPAIGN)
class CampaignByIdResource(Resource):

    decorators = [require_oauth()]

    def get(self, campaign_id):
        """
        This action returns a single campaign created by current user.

        :return campaign_data: a dictionary containing campaign json serializable data
        :rtype json

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            campaign_id = 1
            response = requests.get(API_URL + '/campaigns/%s' % campaign_id,
                                    headers=headers)

        .. Response::

            {
                "campaign":{
                              "added_datetime": "2015-11-19 18:54:04",
                              "frequency_id": 2,
                              "id": 1,
                              "name": "QC Technologies",
                              "start_datetime": "2015-11-19 18:55:08",
                              "end_datetime": "2015-11-25 18:55:08"
                              "body_text": "Join QC Technologies.",
                              "url": "https://www.qc-technologies.com/careers"
                            }
            }
        .. Status:: 200 (OK)
                    401 (Unauthorized to access getTalent)
                    404 (ResourceNotFound)
                    500 (Internal Server Error)
        """
        user = request.user
        campaign = PushCampaignBase.validate_ownership_of_campaign(campaign_id, user.id)
        response = dict(campaign=campaign.to_json())
        return response, 200

    def put(self, campaign_id):
        """
        This method takes data to update a Push campaign components.

        :param campaign_id: unique id of push campaign
        :type campaign_id: int, long
        :return: success message
        :type: json

        :Example:

            campaign_data = {
                                "name": "QC Technologies",
                                "body_text": "New job openings...",
                                "url": "https://www.qc-technologies.com",
                                "smartlist_ids": [1, 2, 3]
                             }

            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'content-type': 'application/json'

                       }
            campaign_id = 1
            data = json.dumps(campaign_data)
            response = requests.put(
                                        API_URL + '/v1/campaigns/%s' % campaign_id ,
                                        data=data,
                                        headers=headers,
                                    )

        .. Response::

            {
                "message": "Push campaign has been updated successfully"
            }

        .. Status:: 201 (Resource Created)
                    401 (Unauthorized to access getTalent)
                    400 (Invalid Usage)
                    500 (Internal Server Error)

        ..Error Codes:: 7003 (RequiredFieldsMissing)
        """
        user = request.user
        data = get_valid_json_data(request)
        if not campaign_id > 0:
            raise ResourceNotFound('Campaign not found with id %s' % campaign_id)
        campaign = PushCampaignBase.validate_ownership_of_campaign(campaign_id, user.id)
        for key, value in data.items():
            if key not in ['name', 'body_text', 'url', 'smartlist_ids']:
                raise InvalidUsage('Invalid field in campaign data',
                                   additional_error_info=dict(invalid_field=key))
            if not value:
                raise InvalidUsage('Invalid value for field in campaign data',
                                   additional_error_info=dict(field=key,
                                                              invalid_value=value))

        data['user_id'] = user.id
        # We are confirmed that this key has some value after above validation
        smartlist_ids = data.pop('smartlist_ids')
        campaign.update(**data)
        associated_smartlist_ids = [smartlist.id for smartlist in campaign.smartlists]
        if isinstance(smartlist_ids, list):
            for smartlist_id in smartlist_ids:
                if smartlist_id not in associated_smartlist_ids:
                    associate_smart_list_with_campaign(smartlist_id, campaign.id)
                else:
                    logger.info('Smartlist (id: %s) already associated with campaign' % smartlist_id)
        elif isinstance(smartlist_ids, (int, long)):
            associate_smart_list_with_campaign(smartlist_ids, campaign.id)

        response = dict(message='Push campaign was updated successfully')
        return response, 200


@api.route(PushCampaignApi.SCHEDULE)
class SchedulePushCampaignResource(Resource):

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
        get_valid_json_data(request)
        if not campaign_id:
            raise InvalidUsage('campaign_id should be a positive number')
        pre_processed_data = PushCampaignBase.pre_process_schedule(request, campaign_id,
                                                                   CampaignType.PUSH)
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
        get_valid_json_data(request)
        if not campaign_id:
            raise InvalidUsage('campaign_id should be a positive number')
        pre_processed_data = PushCampaignBase.pre_process_schedule(request, campaign_id,
                                                                   CampaignType.PUSH)
        PushCampaignBase.pre_process_re_schedule(pre_processed_data)
        campaign_obj = PushCampaignBase(request.user.id)
        campaign_obj.campaign = pre_processed_data['campaign']
        task_id = campaign_obj.schedule(pre_processed_data['data_to_schedule'])
        return dict(message='Campaign(id:%s) has been re-scheduled.' % campaign_id,
                    task_id=task_id), 200

    def delete(self, campaign_id):
        """
        Unschedule a single campaign from scheduler_service and removes the scheduler_task_id
        from getTalent's database.

        :param campaign_id: (Integer) unique id in push_campaign table on GT database.

        :Example:
            headers = {
                        'Authorization': 'Bearer <access_token>',
                       }

            campaign_id = 1
            response = requests.delete(API_URL + '/campaigns/' + str(campaign_id) + '/schedule',
                                        headers=headers,
                                    )

        .. Response::

            {
                'message': 'Campaign(id:125) has been unscheduled.'
            }

        .. Status:: 200 (Resource Deleted)
                    403 (Forbidden: Current user cannot delete Push campaign)
                    404 (Campaign not found)
                    500 (Internal Server Error)
        """
        if not campaign_id:
            raise InvalidUsage('campaign_id should be a positive number')
        task_unscheduled = PushCampaignBase.unschedule(campaign_id, request, CampaignType.PUSH)
        if task_unscheduled:
            return dict(message='Campaign(id:%s) has been unschedule.' % campaign_id), 200
        else:
            return dict(message='Campaign(id:%s) is already unscheduled.' % campaign_id), 200


@api.route(PushCampaignApi.SEND)
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
        campaign = PushCampaignBase.validate_ownership_of_campaign(campaign_id, user.id)
        campaign_obj = PushCampaignBase(user_id=user.id)
        campaign_obj.process_send(campaign)
        return dict(message='Campaign(id:%s) is being sent to candidates' % campaign_id), 200


@api.route(PushCampaignApi.BLAST_SENDS)
class PushCampaignBlastSends(Resource):

    decorators = [require_oauth()]

    def get(self, campaign_id, blast_id):
        user = request.user
        # Get a campaign that was created by this user
        campaign = PushCampaignBase.validate_ownership_of_campaign(campaign_id, user.id)
        blast = PushCampaignBlast.get_by_id(blast_id)
        if not blast:
            raise ResourceNotFound('Campaign Blast not found with id: %s' % blast_id)
        if blast.campaign_id == campaign.id:
            sends = [send.to_json() for send in blast.blast_sends]
            response = dict(sends=sends, count=len(sends))
            return response, 200
        else:
            raise ForbiddenError('Campaign Blast (id: %s) is not assciated with campaign (id: %s)'
                                 % (blast_id, campaign.id))


@api.route(PushCampaignApi.SENDS)
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
        # Get a campaign that was created by this user
        campaign = PushCampaignBase.validate_ownership_of_campaign(campaign_id, user.id)
        sends = []
        # Add sends for every blast to `sends` list to get all sends of a campaign.
        # A campaign can have multiple blasts
        [sends.extend(blast.blast_sends.all()) for blast in campaign.blasts.all()]
        # Get JSON serializable data
        sends = [send.to_json() for send in sends]
        response = dict(sends=sends, count=len(sends))
        return response, 200


@api.route(PushCampaignApi.BLASTS)
class PushCampaignBlasts(Resource):

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
        # Get a campaign that was created by this user
        campaign = PushCampaignBase.validate_ownership_of_campaign(campaign_id, user.id)
        # Serialize blasts of a campaign
        blasts = [blast.to_json() for blast in campaign.blasts.all()]
        response = dict(blasts=blasts, count=len(blasts))
        return response, 200


@api.route(PushCampaignApi.BLAST)
class PushCampaignBlastById(Resource):

    decorators = [require_oauth()]

    def get(self, campaign_id, blast_id):
        """
        This endpoint returns a specific blast object (dict)
        associated with a specific push campaign.

        :param campaign_id: int, unique id of a push campaign
        :param blast_id: int, unique id of a blast of campaign
        :return: json data containing blast


        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            campaign_id = 1
            blast_id = 3
            response = requests.get(API_URL + '/v1/campaigns/' + str(campaign_id)+ \
                                    '/blasts/' + str(blast_id),
                                    headers=headers)

        .. Response::

            {
                "blast":
                        {
                          "campaign_id": 2,
                          "clicks": 6,
                          "id": 3,
                          "sends": 10,
                          "updated_time": "2015-12-30 14:33:44"
                        }
            }

        .. Status:: 200 (OK)
                    401 (Unauthorized to access getTalent)
                    404 (Blast not found, Campaign not found)
                    500 (Internal Server Error)
        """
        user = request.user
        # Get a campaign that was created by this user
        campaign = PushCampaignBase.validate_ownership_of_campaign(campaign_id, user.id)
        # Serialize blasts of a campaign
        blast = campaign.blasts.filter_by(id=blast_id).first()
        if blast:
            response = dict(blast=blast.to_json())
            return response, 200
        else:
            raise ResourceNotFound('Blast not found for campaign (id: %s) with id %s'
                                   % (campaign_id, blast_id))


@api.route(PushCampaignApi.DEVICES)
class AssociateDevice(Resource):

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
        data = get_valid_json_data(request)
        candidate_id = data.get('candidate_id')
        if not candidate_id:
            raise InvalidUsage('candidate_id is not given in post data')
        device_id = data.get('device_id')
        if not device_id:
            raise InvalidUsage('device_id is not given in post data')

        candidate = Candidate.get_by_id(candidate_id)
        # if candidate does not exists with given id, we can not add this device id
        if not candidate:
            raise ResourceNotFound('Unable to associate device with a non existing candidate id: %s' % candidate_id)

        # Send a GET request to OneSignal API to confirm that this device id is valid
        response = one_signal_client.get_player(device_id)
        if response.ok:
            # Device exists with id
            candidate_device = CandidateDevice(candidate_id=candidate_id,
                                               one_signal_device_id=device_id,
                                               registered_at=datetime.datetime.now())
            CandidateDevice.save(candidate_device)
            return dict(message='Device registered successfully with candidate (id: %s)' % candidate_id)
        else:
            # No device was found on OneSignal database.
            raise ResourceNotFound('Device is not registered with OneSignal with id %s' % device_id)


@api.route(PushCampaignApi.REDIRECT)
class PushCampaignUrlRedirection(Resource):
    """
    This endpoint redirects the candidate to our app.
    """
    def get(self, url_conversion_id):
        """
        This endpoint is /v1/redirect/:id

        When recruiter(user) assigns a URL as a redirect for that push notification,
        we save the original URL as destination URL in "url_conversion" database table.
        Then we create a new URL (which is
        created during the process of sending campaign to candidate) to redirect the candidate
        to our app. This looks like

                http://127.0.0.1:8013/v1/redirect/1
        After signing this URL, it looks like
        http://127.0.0.1:8013/v1/redirect/1052?valid_until=1453990099.0&auth_user=no_user&extra=
                &signature=cWQ43J%2BkYetfmE2KmR85%2BLmvuIw%3D
        This is called signed_url.

        When candidate clicks on above url, it is redirected to this flask endpoint, where we
        keep track of number of clicks and hit_counts for a URL. We then create activity that
        'this' candidate has clicked on 'this' campaign. Finally we redirect the candidate to
        destination URL (Original URL provided by the recruiter)

        .. Status:: 200 (OK)
                    400 (Invalid Usage)
                    401 (Unauthorized to access getTalent)
                    403 (Forbidden Error)
                    404 (Campaign not found)
                    500 (Internal Server Error)

        ., Error codes::
                    5005 (EmptyDestinationUrl)

        :param url_conversion_id: id of url_conversion record in db
        :type url_conversion_id: int
        :return: redirects to the destination URL else raises exception
        """
        try:
            redirection_url = CampaignBase.process_url_redirect(url_conversion_id, CampaignType.PUSH,
                                                                verify_signature=True,
                                                                request_args=request.args,
                                                                requested_url=request.full_path)
            return redirect(redirection_url)
        # In case any type of exception occurs, candidate should only get internal server error
        except Exception:
            # As this endpoint is hit by client, so we log the error, and return internal server
            # error.
            logger.exception("Error occurred while URL redirection for Push campaign.")
        return dict(message='Internal Server Error'), 500
