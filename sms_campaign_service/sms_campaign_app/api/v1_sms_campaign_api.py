"""
 Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

This file contains API endpoints related to sms_campaign_service.
    Following is a list of API endpoints:

        - SmsCampaigns: /v1/campaigns

            GET     : Gets list of all the SMS campaigns that belong to user
            POST    : Creates new campaign and save it in database
            DELETE  : Deletes SMS campaigns of user using given campaign ids as a list

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
"""

# Standard Library
import json
import types
from werkzeug.exceptions import BadRequest

# Third Party
from flask import request
from flask import Blueprint
from flask.ext.cors import CORS
from flask.ext.restful import Resource

# Service Specific
from sms_campaign_service import logger
from sms_campaign_service.sms_campaign_base import SmsCampaignBase
from sms_campaign_service.custom_exceptions import ErrorDeletingSMSCampaign
from sms_campaign_service.utilities import (validate_form_data, validate_header,
                                            delete_sms_campaign, is_owner_of_campaign,
                                            validate_scheduler_data)

# Common Utils
from sms_campaign_service.common.error_handling import *
from sms_campaign_service.common.talent_api import TalentApi
from sms_campaign_service.common.routes import SmsCampaignApi
from sms_campaign_service.common.utils.auth_utils import require_oauth
from sms_campaign_service.common.utils.api_utils import api_route, ApiResponse

# Database Models
from sms_campaign_service.common.models.sms_campaign import (SmsCampaign, SmsCampaignBlast,
                                                             SmsCampaignSend)

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
    decorators = [require_oauth]

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
                              "send_datetime": "",
                              "body_text": "Welcome all boys",
                              "stop_datetime": "",
                              "updated_time": "2015-11-19 18:53:55",
                              "user_phone_id": 1
                            },
                            {
                              "added_datetime": "2015-11-19 18:55:08",
                              "frequency_id": 1,
                              "id": 4,
                              "name": "New Campaign",
                              "send_datetime": "",
                              "body_text": "Job opening at...",
                              "stop_datetime": "",
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
        """
        validate_header(request)
        # get json post request data
        try:
            data_from_ui = request.get_json()
        except BadRequest:
            raise InvalidUsage(error_message='Given data is not in json format')
        if not data_from_ui:
            raise InvalidUsage(error_message='No data provided to create SMS campaign')
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

        .. Error Codes::
                    ErrorDeletingSMSCampaign (5010)

        """
        validate_header(request)
        # get campaign_ids for campaigns to be deleted
        try:
            req_data = request.get_json()
        except Exception:
            raise InvalidUsage(error_message='id(s) of campaign should be in a list')
        campaign_ids = req_data['ids'] if 'ids' in req_data else []
        if not isinstance(req_data['ids'], list):
            raise InvalidUsage(error_message='Bad request, include campaign_ids as list data',
                               error_code=InvalidUsage.http_status_code())
        # check if campaigns_ids list is not empty
        if not campaign_ids:
            return dict(message='No campaign id provided to delete'), 200

        if not all([isinstance(campaign_id, (int, long)) for campaign_id in campaign_ids]):
            raise InvalidUsage(error_message='Bad request, campaign_ids must be integer',
                               error_code=InvalidUsage.http_status_code())
        not_deleted = []
        for campaign_id in campaign_ids:
            try:
                delete_sms_campaign(campaign_id, request.user.id)
            except ForbiddenError or ResourceNotFound or ErrorDeletingSMSCampaign:
                if len(campaign_ids) == 1:
                    raise
                # error has been logged inside delete_sms_campaign()
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
    This resource is used to schedule SMS Campaign using scheduler_service [POST]
    """
    decorators = [require_oauth]

    def post(self, campaign_id):
        """
        It schedules given Campaign (from given campaign id) to the smartlist candidates
            associated with given campaign.

        :Example:

            headers = {'Authorization': 'Bearer <access_token>',
                       'Content-type': 'application/json'}

            schedule_data =
                        {
                            "frequency_id": 2,
                            "send_datetime": "2015-11-26T08:00:00Z",
                            "stop_datetime": "2015-11-30T08:00:00Z"
                        }

            campaign_id = 1

            response = requests.post(API_URL + '/campaigns/' + str(campaign_id) + '/schedule',
                                        headers=headers, data=schedule_data)

        .. Response::

                {
                    "message": "Campaign(id:1) is has been scheduled.
                    "task_id"; ""
                }

        .. Status:: 200 (OK)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Forbidden Error)
                    404 (Campaign not found)
                    500 (Internal Server Error)

        .. Error codes:
                    5017 (InvalidDatetime)
                    5019 (InvalidFrequencyId)

        :param campaign_id: integer, unique id representing campaign in GT database
        :return: json for required campaign containing message and total sends.
        """
        validate_header(request)
        if is_owner_of_campaign(campaign_id, request.user.id):
            campaign = SmsCampaign.get_by_id(campaign_id)
            if not campaign:
                raise ResourceNotFound(error_message='SMS Campaign(id=%s) Not found.' % campaign_id)
            try:
                schedule_data = request.get_json()
            except BadRequest:
                raise InvalidUsage(error_message='Given data should be in dict format')
            if not schedule_data:
                raise InvalidUsage(error_message='schedule_data not provided')
            validate_scheduler_data(schedule_data)
            camp_obj = SmsCampaignBase(request.user.id)
            camp_obj.campaign = campaign
            task_id = camp_obj.schedule(schedule_data)
            return dict(message='Campaign(id:%s) has been scheduled.' % campaign_id,
                        task_id=task_id), 200


@api.route(SmsCampaignApi.CAMPAIGN)
class CampaignById(Resource):
    """
    Endpoint looks like /v1/campaigns/:id
    This resource is used to
        1- Get Campaign from given campaign_id [GET]
        2- Update an existing SMS campaign [POST]
        3- Delete campaign by given campaign id [DELETE]
    """
    decorators = [require_oauth]

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
                          "send_datetime": "",
                          "added_datetime": "2015-11-24 16:30:57",
                          "stop_datetime": "",
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
        if not is_owner_of_campaign(campaign_id, request.user.id):
            raise ForbiddenError(
                error_message='User(id:%s) is not owner of SMS campaign(id:%s)'
                              % (request.user.id, campaign_id))
        campaign = SmsCampaign.get_by_id(campaign_id)
        if not campaign:
            raise ResourceNotFound(error_message='SMS Campaign does not exist with id %s'
                                                 % campaign_id)
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
                            "send_datetime": "2015-11-26T08:00:00Z",
                            "stop_datetime": "2015-11-30T08:00:00Z",
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
        """
        validate_header(request)
        try:
            campaign_data = request.get_json()
        except BadRequest:
            raise InvalidUsage(error_message='Given data should be in dict format')
        if not campaign_data:
            raise InvalidUsage(error_message='No data provided to update SMS campaign')
        if not is_owner_of_campaign(campaign_id, request.user.id):
            raise ForbiddenError(
                error_message='User(id:%s) is not authorized to update SMS campaign(id:%s)'
                              % (request.user.id, campaign_id))
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
                'message': 'Campaign(id:%s) deleted successfully' % campaign_id
            }
        .. Status:: 200 (Resource Deleted)
                    403 (Forbidden: Current user cannot delete SMS campaign)
                    404 (Campaign not found)
                    500 (Internal Server Error)

        ..Error codes::
                    5010 (ErrorDeletingSMSCampaign)
        """

        delete_sms_campaign(campaign_id, request.user.id)
        return dict(message='Campaign(id:%s) deleted successfully' % campaign_id), 200


@api.route(SmsCampaignApi.SENDS)
class SmsCampaignSends(Resource):
    """
    Endpoint looks like /v1/campaigns/:id/sends
    This resource is used to GET Campaign sends
    """
    decorators = [require_oauth]

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
                    404 (Campaign not found)
                    500 (Internal Server Error)

        :param campaign_id: integer, unique id representing campaign in GT database
        :return: 1- count of campaign sends and 2- SMS campaign sends records in as dict
        """
        campaign = SmsCampaign.get_by_id(campaign_id)
        if not campaign:
            raise ResourceNotFound(error_message='SMS Campaign(id=%s) not found.' % campaign_id)
        campaign_blasts = SmsCampaignBlast.get_by_campaign_id(campaign_id)
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
    decorators = [require_oauth]

    def post(self, campaign_id):
        """
        It sends given Campaign (from given campaign id) to the smart list candidates
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
        if is_owner_of_campaign(campaign_id, request.user.id):
            campaign = SmsCampaign.get_by_id(campaign_id)
            if not campaign:
                raise ResourceNotFound(error_message='SMS Campaign(id=%s) Not found.' % campaign_id)
            camp_obj = SmsCampaignBase(request.user.id)
            camp_obj.process_send(campaign)
            return dict(message='Campaign(id:%s) is being sent to candidates.' % campaign_id), 200
