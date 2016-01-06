"""
 Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

This file contains API endpoints related to sms_campaign_service.
    Following is a list of API endpoints:

        - SmsCampaigns: /v1/campaigns

            GET     : Gets list of all the SMS campaigns that belong to user
            POST    : Creates new campaign and save it in database
            DELETE  : Deletes SMS campaigns of user using given campaign ids as a list

        - ScheduleSmsCampaign: /v1/campaigns/:id/schedule

            POST    : Schedules the campaign from given campaign_id and data provided
            PUT     : Re-schedules the campaign from given campaign_id and data provided
            DELETE  : Un-schedules the campaign from given campaign_id

        - SendSmsCampaign: /v1/campaigns/:id/schedule

            POST    : Schedules an SMS Campaign by campaign id

        - SmsCampaigns: /v1/campaigns/:id

            GET     : Gets campaign data using given id
            POST    : Updates existing campaign using given id
            DELETE  : Deletes SMS campaign from db using given id

        - SmsCampaignSends:  /v1/campaigns/:id/sends

            GET    : Gets the "sends" records for given SMS campaign id
                    from db table sms_campaign_sends

        - SendSmsCampaign: /v1/campaigns/:id/send

            POST    : Sends the SMS Campaign by campaign id

        - SmsCampaignUrlRedirection: /v1/redirect/:id

            GET    : Redirects the candidate to our app to keep track of number of clicks, hit_count
                    and create activity.

        - SmsReceive: /v1/receive

            POST    : When candidate replies to an SMS campaign, this endpoint is hit from Twilio
                        to notify our app.
"""


# Standard Library
import types
from werkzeug.utils import redirect
from werkzeug.exceptions import BadRequest

# Third Party
from flask import request
from flask import Blueprint
from flask.ext.cors import CORS
from flask.ext.restful import Resource

# Service Specific
from sms_campaign_service.sms_campaign_app import logger
from sms_campaign_service.sms_campaign_base import SmsCampaignBase
from sms_campaign_service.modules.validators import validate_form_data
from sms_campaign_service.modules.custom_exceptions import ErrorDeletingSMSCampaign
from sms_campaign_service.modules.handy_functions import request_from_google_shorten_url_api

# Common Utils
from sms_campaign_service.common.error_handling import *
from sms_campaign_service.common.talent_api import TalentApi
from sms_campaign_service.common.routes import SmsCampaignApi
from sms_campaign_service.common.utils.auth_utils import require_oauth
from sms_campaign_service.common.utils.api_utils import (api_route, ApiResponse)
from sms_campaign_service.common.campaign_services.campaign_base import CampaignBase
from sms_campaign_service.common.campaign_services.validators import validate_header
from sms_campaign_service.common.campaign_services.campaign_utils import CampaignType

# Database Models
from sms_campaign_service.common.models.sms_campaign import (SmsCampaignBlast, SmsCampaignSend)

# creating blueprint
sms_campaign_blueprint = Blueprint('sms_campaign_api', __name__)
api = TalentApi()
api.init_app(sms_campaign_blueprint)
api.route = types.MethodType(api_route, api)


# Enable CORS
CORS(sms_campaign_blueprint, resources={
    r'' + SmsCampaignApi.VERSION + '/(campaigns)/*': {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})


@api.route(SmsCampaignApi.CAMPAIGNS)
class SMSCampaigns(Resource):
    """
    Endpoint looks like /v1/campaigns
    This resource is used to
        1- Get all campaigns created by current user [GET]
        2- Create an SMS campaign [POST]
        3- Delete campaigns by taking campaign ids [DELETE]
    """
    decorators = [require_oauth()]

    def get(self):
        """
        This action returns a list of all Campaigns for logged-in user.

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
                              "frequency_id": 1,
                              "id": 3,
                              "name": "New Campaign",
                              "start_datetime": "",
                              "body_text": "Welcome all boys",
                              "end_datetime": "",
                              "updated_time": "2015-11-19 18:53:55",
                              "user_phone_id": 1
                            },
                            {
                              "added_datetime": "2015-11-19 18:55:08",
                              "frequency_id": 1,
                              "id": 4,
                              "name": "New Campaign",
                              "start_datetime": "",
                              "body_text": "Job opening at...",
                              "end_datetime": "",
                              "updated_time": "2015-11-19 18:54:51",
                              "user_phone_id": 1
                            }
              ]
            }

        .. Status:: 200 (OK)
                    401 (Unauthorized to access getTalent)
                    403 (Forbidden error)
                    500 (Internal Server Error)
        """

        camp_obj = SmsCampaignBase(request.user.id)
        all_campaigns = [campaign.to_json() for campaign in camp_obj.get_all_campaigns()]
        return dict(count=len(all_campaigns), campaigns=all_campaigns), 200

    def post(self, *args, **kwargs):
        """
        This method takes data to create SMS campaign in database.
        :return: id of created campaign
        :type: json

        :Example:

            campaign_data = {
                                "name": "New SMS Campaign",
                                "body_text": "Hi all, we have few openings at abc.com",
                                "smartlist_ids": [1, 2, 3]
                             }

            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'content-type': 'application/json'

                       }
            data = json.dumps(campaign_data)
            response = requests.post(
                                        API_URL + '/campaigns/',
                                        data=data,
                                        headers=headers,
                                    )

        .. Response::

            {
                id: 123
            }

        .. Status:: 201 (Resource Created)
                    401 (Unauthorized to access getTalent)
                    403 (Forbidden error)
                    500 (Internal Server Error)

        ..Error Codes:: 5002 (MultipleTwilioNumbersFoundForUser)
                        5003 (TwilioAPIError)
                        5006 (MissingRequiredField)
                        5009 (ErrorSavingSMSCampaign)
                        5017 (InvalidUrl)
        """
        validate_header(request)
        # get json post request data
        try:
            data_from_ui = request.get_json()
        except BadRequest:
            raise InvalidUsage('Given data is not in json format')
        if not data_from_ui:
            raise InvalidUsage('No data provided to create SMS campaign')
        # apply validation on fields
        invalid_smartlist_ids, not_found_smartlist_ids = validate_form_data(data_from_ui)
        campaign_obj = SmsCampaignBase(request.user.id)
        campaign_id = campaign_obj.save(data_from_ui)
        headers = {'Location': '/campaigns/%s' % campaign_id}
        logger.debug('Campaign(id:%s) has been saved.' % campaign_id)
        if not_found_smartlist_ids or invalid_smartlist_ids:
            return ApiResponse(dict(sms_campaign_id=campaign_id,
                                    not_found_smartlist_ids=not_found_smartlist_ids,
                                    invalid_smartlist_ids=invalid_smartlist_ids),
                               status=207, headers=headers)
        else:
            return ApiResponse(dict(sms_campaign_id=campaign_id),
                               status=201, headers=headers)

    def delete(self):
        """
        Deletes multiple campaigns using ids given in list in request data.
        :return:

        :Example:

            campaign_ids = {
                'ids': [1, 2, 3]
            }
            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'content-type': 'application/json'
                       }
            data = json.dumps(campaign_ids)
            response = requests.delete(
                                        API_URL + '/campaigns/',
                                        data=data,
                                        headers=headers,
                                    )

        .. Response::

            {
                'message': '3 Campaigns have been deleted successfully'
            }

        .. Status:: 200 (Resource deleted)
                    207 (Not all deleted)
                    400 (Bad request)
                    403 (Forbidden error)
                    500 (Internal Server Error)
        """
        validate_header(request)
        # get campaign_ids for campaigns to be deleted
        try:
            req_data = request.get_json()
        except Exception:
            raise InvalidUsage('id(s) of campaign should be in a list')
        campaign_ids = req_data['ids'] if 'ids' in req_data else []
        if not isinstance(req_data['ids'], list):
            raise InvalidUsage('Bad request, include campaign_ids as list data',
                               error_code=InvalidUsage.http_status_code())
        # check if campaigns_ids list is not empty
        if not campaign_ids:
            return dict(message='No campaign id provided to delete'), 200

        if not all([isinstance(campaign_id, (int, long)) for campaign_id in campaign_ids]):
            raise InvalidUsage('Bad request, campaign_ids must be integer',
                               error_code=InvalidUsage.http_status_code())
        not_deleted = []
        for campaign_id in campaign_ids:
            try:
                deleted = SmsCampaignBase.process_delete_campaign(
                    campaign_id=campaign_id, current_user_id=request.user.id,
                    bearer_access_token=request.oauth_token)
                if not deleted:
                    # error has been logged inside process_delete_campaign()
                    not_deleted.append(campaign_id)
            except ForbiddenError or ResourceNotFound or InvalidUsage:
                if len(campaign_ids) == 1:
                    raise
                # error has been logged inside process_delete_campaign()
                not_deleted.append(campaign_id)
        if not not_deleted:
            return dict(message='%s Campaigns deleted successfully' % len(campaign_ids)), 200
        else:
            return dict(message='Unable to delete %s campaigns' % len(not_deleted),
                        not_deleted_ids=not_deleted), 207


@api.route(SmsCampaignApi.SCHEDULE)
class ScheduleSmsCampaign(Resource):
    """
    Endpoint looks like /v1/campaigns/:id/schedule
    This resource is used to
        1- schedule SMS Campaign using scheduler_service [POST]
        2- Re-schedule SMS Campaign using scheduler_service [PUT]
    """
    decorators = [require_oauth()]

    def post(self, campaign_id):
        """
        It schedules an SMS campaign using given campaign_id by making HTTP request to
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

            response = requests.post(API_URL + '/campaigns/' + str(campaign_id) + '/schedule',
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

        :param campaign_id: integer, unique id representing campaign in GT database
        :return: JSON containing message and task_id.
        """
        # validate data to schedule
        pre_processed_data = SmsCampaignBase.pre_process_schedule(request, campaign_id)
        # create object of class SmsCampaignBase
        sms_camp_obj = SmsCampaignBase(request.user.id)
        # assign campaign to object
        sms_camp_obj.campaign = pre_processed_data['campaign']
        # call schedule() method to schedule the campaign and get the task_id
        task_id = sms_camp_obj.schedule(pre_processed_data['data_to_schedule'])
        return dict(message='Campaign(id:%s) has been scheduled.' % campaign_id,
                    task_id=task_id), 200

    def put(self, campaign_id):
        """
        This endpoint is to re-schedule a campaign. We Check if given campaign has task_id and
        task is scheduled on scheduler_service, If task is not scheduled, return 200 with message
        that task has stopped already
        Otherwise, remove the task from scheduler_service and remove task_id from  database table
        'sms_campaign' as well.

        :Example:

            headers = {'Authorization': 'Bearer <access_token>'}

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
            OR

                {
                    "message": "Campaign(id:1) is already scheduled with given data.
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
        # validate data to schedule
        pre_processed_data = SmsCampaignBase.pre_process_schedule(request, campaign_id)
        # check if task is already present on scheduler_service
        scheduled_task_id = SmsCampaignBase.pre_process_re_schedule(pre_processed_data)
        if not scheduled_task_id:  # Task not found on scheduler_service
            # create object of class SmsCampaignBase
            sms_camp_obj = SmsCampaignBase(request.user.id)
            # assign campaign to object
            sms_camp_obj.campaign = pre_processed_data['campaign']
            # call method schedule() to schedule the campaign and get the task_id
            task_id = sms_camp_obj.schedule(pre_processed_data['data_to_schedule'])
            message = 'Campaign(id:%s) has been re-scheduled.' % campaign_id
        else:
            message = 'Campaign(id:%s) is already scheduled with given data.' % campaign_id
            task_id = scheduled_task_id
        return dict(message=message, task_id=task_id), 200

    def delete(self, campaign_id):
        """
        Unschedule a single campaign from scheduler_service and removes the scheduler_task_id
        from getTalent's database.

        :param campaign_id: (Integer) unique id in sms_campaign table on GT database.

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
                    403 (Forbidden: Current user cannot delete SMS campaign)
                    404 (Campaign not found)
                    500 (Internal Server Error)
        """
        task_unscheduled = SmsCampaignBase.unschedule(campaign_id, request)
        if task_unscheduled:
            return dict(message='Campaign(id:%s) has been unschedule.' % campaign_id), 200
        else:
            return dict(message='Campaign(id:%s) is already unscheduled.' % campaign_id), 200


@api.route(SmsCampaignApi.CAMPAIGN)
class CampaignById(Resource):
    """
    Endpoint looks like /v1/campaigns/:id
    This resource is used to
        1- Get Campaign from given campaign_id [GET]
        2- Update an existing SMS campaign [POST]
        3- Delete campaign by given campaign id [DELETE]
    """
    decorators = [require_oauth()]

    def get(self, campaign_id):
        """
        Returns campaign object with given id

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            campaign_id = 1
            response = requests.get(API_URL + '/campaigns/' + str(campaign_id), headers=headers)

        .. Response::

            {
                "campaign": {
                          "body_text": "Dear all, please visit http://www.qc-technologies.com",
                          "frequency_id": 1,
                          "updated_time": "2015-11-24 16:31:09",
                          "user_phone_id": 1,
                          "start_datetime": "",
                          "added_datetime": "2015-11-24 16:30:57",
                          "end_datetime": "",
                          "id": 1,
                          "name": "UpdatedName"
                        }
            }

        .. Status:: 200 (OK)
                    401 (Unauthorized to access getTalent)
                    403 (Forbidden: Current user cannot get SMS campaign record)
                    404 (Campaign not found)
                    500 (Internal Server Error)

        :param campaign_id: integer, unique id representing campaign in GT database
        :return: json for required campaign
        """
        campaign = SmsCampaignBase.validate_ownership_of_campaign(campaign_id, request.user.id)
        return dict(campaign=campaign.to_json()), 200

    def post(self, campaign_id):
        """
        Updates campaign in getTalent's database
        :param campaign_id: id of campaign on getTalent database

        :Example:

            campaign_data = {

                            "name": "New SMS Campaign",
                            "body_text": "HI all, we have few openings at abc.com",
                            "frequency_id": 2,
                            "added_datetime": "2015-11-24T08:00:00Z",
                            "start_datetime": "2015-11-26T08:00:00Z",
                            "end_datetime": "2015-11-30T08:00:00Z",
                            "id": 1,
                            "smartlist_ids": [1, 2, 3]
                            }

            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'content-type': 'application/json'
                       }
            data = json.dumps(campaign_data)
            campaign_id = campaign_data['id']
            response = requests.post(
                                        API_URL + '/campaign/' + str(campaign_id)',
                                        data=data,
                                        headers=headers,
                                    )

        .. Status:: 200 (Resource Modified)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Forbidden: Current user cannot update SMS campaign)
                    404 (Campaign not found)
                    500 (Internal Server Error)

        .. Error codes::
                        5006 (MissingRequiredField)
                        5009 (ErrorSavingSMSCampaign)
                        5017 (InvalidUrl)
        """
        validate_header(request)
        try:
            campaign_data = request.get_json()
        except BadRequest:
            raise InvalidUsage('Given data should be in dict format')
        if not campaign_data:
            raise InvalidUsage('No data provided to update SMS campaign')
        SmsCampaignBase.validate_ownership_of_campaign(campaign_id, request.user.id)
        invalid_smartlist_ids, not_found_smartlist_ids = validate_form_data(campaign_data)
        camp_obj = SmsCampaignBase(request.user.id)
        camp_obj.create_or_update_sms_campaign(campaign_data, campaign_id=campaign_id)
        if not_found_smartlist_ids or invalid_smartlist_ids:
            return dict(message='SMS Campaign(id:%s) has been updated successfully' % campaign_id,
                        not_found_smartlist_ids=not_found_smartlist_ids,
                        invalid_smartlist_ids=invalid_smartlist_ids), 207
        else:
            return dict(message='SMS Campaign(id:%s) has been updated successfully'
                                % campaign_id), 200

    def delete(self, campaign_id):
        """
        Removes a single campaign from getTalent's database.
        :param campaign_id: (Integer) unique id in sms_campaign table on GT database.

        :Example:
            headers = {
                        'Authorization': 'Bearer <access_token>',
                       }

            campaign_id = 1
            response = requests.delete(
                                        API_URL + '/campaigns/' + str(campaign_id),
                                        headers=headers,
                                    )

        .. Response::

            {
                'message': 'Campaign(id:125) has been deleted successfully'
            }
        .. Status:: 200 (Resource Deleted)
                    403 (Forbidden: Current user cannot delete SMS campaign)
                    404 (Campaign not found)
                    500 (Internal Server Error)

        ..Error codes::
                    5010 (ErrorDeletingSMSCampaign)
        """
        campaign_deleted = SmsCampaignBase.process_delete_campaign(campaign_id=campaign_id,
                                                                   current_user_id=request.user.id,
                                                                   bearer_access_token=request.oauth_token)
        if campaign_deleted:
            return dict(message='Campaign(id:%s) has been deleted successfully' % campaign_id), 200
        else:
            raise ErrorDeletingSMSCampaign('Campaign(id:%s) was not deleted.' % campaign_id)


@api.route(SmsCampaignApi.SENDS)
class SmsCampaignSends(Resource):
    """
    Endpoint looks like /v1/campaigns/:id/sends
    This resource is used to GET Campaign sends
    """
    decorators = [require_oauth()]

    def get(self, campaign_id):
        """
        Returns Campaign sends for given campaign id

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            campaign_id = 1
            response = requests.get(API_URL + '/campaigns/' + str(campaign_id)
                                + '/sends/', headers=headers)

        .. Response::

            {
                "campaign_sends":
                                    [
                                        {
                                          "candidate_id": 1,
                                          "id": 9,
                                          "sent_datetime": "2015-11-23 18:25:09",
                                          "sms_campaign_blast_id": 1,
                                          "updated_time": "2015-11-23 18:25:08"
                                        },
                                        {
                                          "candidate_id": 2,
                                          "id": 10,
                                          "sent_datetime": "2015-11-23 18:25:13",
                                          "sms_campaign_blast_id": 1,
                                          "updated_time": "2015-11-23 18:25:13"
                                       }
                                    ],
                "count": 2

            }

        .. Status:: 200 (OK)
                    401 (Unauthorized to access getTalent)
                    403 (Not owner of campaign)
                    404 (Campaign not found)
                    500 (Internal Server Error)

        :param campaign_id: integer, unique id representing campaign in GT database
        :return: 1- count of campaign sends and 2- SMS campaign sends records in as dict
        """
        campaign = SmsCampaignBase.validate_ownership_of_campaign(campaign_id, request.user.id)
        campaign_blasts = SmsCampaignBlast.get_by_campaign_id(campaign.id)
        campaign_sends_json = []
        if campaign_blasts:
            campaign_sends = SmsCampaignSend.get_by_blast_id(campaign_blasts.id)
            campaign_sends_json = [campaign_send.to_json() for campaign_send in campaign_sends]
        return dict(count=len(campaign_sends_json), campaign_sends=campaign_sends_json), 200


@api.route(SmsCampaignApi.SEND)
class SendSmsCampaign(Resource):
    """
    Endpoint looks like /v1/campaigns/:id/send
    This resource is used to send SMS Campaign to candidates [POST]
    """
    decorators = [require_oauth()]

    def post(self, campaign_id):
        """
        It sends given Campaign (from given campaign id) to the smartlist candidates
            associated with given campaign.

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            campaign_id = 1
            response = requests.post(API_URL + '/campaigns/' + str(campaign_id)
                                + '/send', headers=headers)

        .. Response::

                {
                    "message": "Campaign(id:1) is being sent to candidates"
                }

        .. Status:: 200 (OK)
                    401 (Unauthorized to access getTalent)
                    403 (Forbidden Error)
                    404 (Campaign not found)
                    500 (Internal Server Error)

        .. Error Codes:: 5001 (Empty message body to send)
                         5002 (User has MultipleTwilioNumbersFoundForUser)
                         5003 (TwilioAPIError)
                         5004 (GoogleShortenUrlAPIError)
                         5014 (ErrorUpdatingBodyText)

        :param campaign_id: integer, unique id representing campaign in GT database
        """
        campaign = SmsCampaignBase.validate_ownership_of_campaign(campaign_id, request.user.id)
        camp_obj = SmsCampaignBase(request.user.id)
        camp_obj.process_send(campaign)
        return dict(message='Campaign(id:%s) is being sent to candidates.' % campaign_id), 200


@api.route(SmsCampaignApi.REDIRECT)
class SmsCampaignUrlRedirection(Resource):
    """
    This endpoint redirects the candidate to our app.
    """
    def get(self, url_conversion_id):
        """
        This endpoint is /v1/redirect/:id

        When recruiter(user) adds some URL in SMS body text, we save the original URL as
        destination URL in "url_conversion" database table. Then we create a new URL (which is
        created during the process of sending campaign to candidate) to redirect the candidate
        to our app. This looks like

                http://127.0.0.1:8012/v1/redirect/1
        After signing this URL, it looks like
        http://127.0.0.1:8012/v1/redirect/1052?valid_until=1453990099.0&auth_user=no_user&extra=
                &signature=cWQ43J%2BkYetfmE2KmR85%2BLmvuIw%3D
        This is called long_url. So, we first convert this long_url in short URL (using Google's
        shorten URL API) and send in SMS body text to candidate. Short URL looks like

                https://goo.gl/CazBJG

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
                    5006 (MissingRequiredField)

        :param url_conversion_id: id of url_conversion record in db
        :type url_conversion_id: int
        :return: redirects to the destination URL else raises exception
        """
        # Google's shorten URL API hits this end point while converting long_url to shorter version.
        if request_from_google_shorten_url_api(request.headers.environ):
            return 200
        try:
            redirection_url = CampaignBase.process_url_redirect(url_conversion_id, CampaignType.SMS,
                                                                verify_signature=True,
                                                                request_args=request.args,
                                                                requested_url=request.full_path)
            return redirect(redirection_url)
        # In case any type of exception occurs, candidate should only get internal server error
        except Exception:
            # As this endpoint is hit by client, so we log the error, and return internal server
            # error.
            logger.exception("Error occurred while URL redirection for SMS campaign.")
        return dict(message='Internal Server Error'), 500


@api.route(SmsCampaignApi.RECEIVE)
class SmsReceive(Resource):
    """
    This end point is is /v1/receive and is used by Twilio to notify getTalent when a candidate
    replies to an SMS.
    """
    def post(self):
        """
        - Recruiters(users) are assigned to one unique Twilio number. That number is configured with
         "sms_callback_url" which redirect the request at this end point with following data:

                    {
                          "From": "+12015617985",
                          "To": "+15039255479",
                          "Body": "Dear all, we have few openings at http://www.qc-technologies.com",
                          "SmsStatus": "received",
                          "FromCity": "FELTON",
                          "FromCountry": "US",
                          "FromZip": "95018",
                          "ToCity": "SHERWOOD",
                          "ToCountry": "US",
                          "ToZip": "97132",
                     }

         So whenever someone replies to that particular recruiter's SMS (from within getTalent), this
         endpoint is hit and we do the following:

            1- Search the candidate in GT database using "From" key
            2- Search the user in GT database using "To" key
            3- Stores the candidate's reply in database table "sms_campaign_reply"
            4- Create activity that 'abc' candidate has replied "Body"(key)
                on 'xyz' SMS campaign.

        :return: XML response to Twilio API
        """
        if request.values:
            try:
                logger.debug('SMS received from %(From)s on %(To)s.\n Body text is "%(Body)s"'
                             % request.values)
                SmsCampaignBase.process_candidate_reply(request.values)
            # Any type of exception should be catch as response returns to Twilio API.
            except Exception:
                logger.exception("sms_receive: Error Processing received SMS.")
        # So in the end we need to send properly formatted XML response back to Twilio
        return """
            <?xml version="1.0" encoding="UTF-8"?>
                <Response>
                </Response>
                """
