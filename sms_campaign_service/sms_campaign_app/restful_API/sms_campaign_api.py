"""
This file contains API endpoints related to sms_campaign_service.
    Following is a list of API endpoints:

        - SmsCampaigns: /campaigns/

            GET     : Gets list of all the sms campaigns that belong to user
            POST    : Creates new campaign and save it in database
            DELETE  : Deletes sms campaigns of user by provided campaign ids as a list

        - SmsCampaigns: /campaigns/:id

            GET     : Gets campaign data from given id
            POST    : Updates existing campaign using given id
            DELETE  : Deletes sms campaign from db for given id

        - SmsCampaignSends:  /campaigns/:id/sms_campaign_sends

            GET    : Gets the "sends" records for given sms campaign id
                    from db table sms_campaign_sends

        - SendSmsCampaign: /campaigns/:id/send

            POST    : Sends the SMS Campaign by campaign id
"""
__author__ = 'basit.gettalent@gmail.com'

# Standard Library
import json
import types

# Third Party
from flask import request
from flask import Blueprint
from flask.ext.cors import CORS
from flask.ext.restful import Resource

# Application Specific
from sms_campaign_service import logger
from sms_campaign_service.common.error_handling import *
from sms_campaign_service.common.talent_api import TalentApi
from sms_campaign_service.sms_campaign_base import SmsCampaignBase
from sms_campaign_service.sms_campaign_app.app_utils import api_route, ApiResponse
from sms_campaign_service.common.utils.auth_utils import require_oauth
from sms_campaign_service.common.models.sms_campaign import SmsCampaign, SmsCampaignBlast, \
    SmsCampaignSend

# creating blueprint
sms_campaign_blueprint = Blueprint('sms_campaign_api', __name__)
api = TalentApi()
api.init_app(sms_campaign_blueprint)
api.route = types.MethodType(api_route, api)


# # Enable CORS
# CORS(sms_campaign_blueprint, resources={
#     r'/(campaigns)/*': {
#         'origins': '*',
#         'allow_headers': ['Content-Type', 'Authorization']
#     }
# })


@api.route('/campaigns/')
class SMSCampaigns(Resource):
    """
    This resource is used to
        1- Get all campaigns created by current user [GET]
        2- Create an sms campaign [POST]
        3- Delete campaigns by taking campaign ids [DELETE]
    """
    decorators = [require_oauth]

    def get(self):
        """
        This action returns a list of all Campaigns for logged in user.

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
                              "added_time": "2015-11-19 18:54:04",
                              "frequency_id": 1,
                              "id": 3,
                              "name": "New Campaign",
                              "send_time": "",
                              "sms_body_text": "Welcome all boys",
                              "stop_time": "",
                              "updated_time": "2015-11-19 18:53:55",
                              "user_phone_id": 1
                            },
                            {
                              "added_time": "2015-11-19 18:55:08",
                              "frequency_id": 1,
                              "id": 4,
                              "name": "New Campaign",
                              "send_time": "",
                              "sms_body_text": "Job opening at...",
                              "stop_time": "",
                              "updated_time": "2015-11-19 18:54:51",
                              "user_phone_id": 1
                            }
              ]
            }

        .. Status:: 200 (OK)
                    401 (Unauthorized to access getTalent)
                    500 (Internal Server Error)
        """

        camp_obj = SmsCampaignBase(user_id=request.user.id)
        campaigns = camp_obj.get_all_campaigns()
        all_campaigns = [campaign.to_json() for campaign in campaigns]
        data = {'count': len(all_campaigns),
                'campaigns': all_campaigns}
        return data, 200

    def post(self, *args, **kwargs):
        """
        This method takes data to create sms campaign in database.
        :return: id of created campaign
        :type: json

        :Example:

            campaign_data = {
                                "name": "New SMS Campaign",
                                "sms_body_text": "HI all, we have few openings at abc.com",
                                "frequency_id": 2,
                                "added_time": "2015-11-24T08:00:00",
                                "send_time": "2015-11-26T08:00:00",
                                "stop_time": "2015-11-30T08:00:00",
                             }

            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
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
                    500 (Internal Server Error)

        ..Error Codes:: 5002 (MultipleMobileNumbers)
                        5003 (TwilioAPIError)
                        5009 (ErrorSavingSMSCampaign)

        """
        # get json post request data
        campaign_data = request.get_json(force=True)
        campaign_obj = SmsCampaignBase(user_id=request.user.id)
        campaign_id = campaign_obj.save(campaign_data)
        headers = {'Location': '/campaigns/%s' % campaign_id}
        logger.debug('Campaign(id:%s) has been saved.' % campaign_id)
        return ApiResponse(json.dumps(dict(id=campaign_id)), status=201, headers=headers)

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
                        'Content-Type': 'application/json'
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
                    500 (Internal Server Error)

        """
        # get campaign_ids for campaigns to be deleted
        req_data = request.get_json(force=True)
        campaign_ids = req_data['ids'] if 'ids' in req_data else []
        if not isinstance(req_data['ids'], list):
            raise InvalidUsage('Bad request, include campaign_ids as list data', error_code=400)
        # check if campaigns_ids list is not empty
        if campaign_ids:
            status_list = [SmsCampaign.delete(_id) for _id in campaign_ids]
            if all(status_list):
                return dict(message='%s Campaigns deleted successfully' % len(campaign_ids)), 200
            else:
                return dict(message='Unable to delete %s campaigns' % status_list.count(False)), 207
        else:
            return dict(message='No campaign id provided to delete'), 200


@api.route('/campaigns/<int:campaign_id>')
class CampaignById(Resource):
    """
    This resource is used to
        1- Get Campaign from given campaign_id [GET]
        2- Updates an existing sms campaign [POST]
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
                          "sms_body_text": "Dear all, please visit http://www.qc-technologies.com",
                          "frequency_id": 1,
                          "updated_time": "2015-11-24 16:31:09",
                          "user_phone_id": 1,
                          "send_time": "",
                          "added_time": "2015-11-24 16:30:57",
                          "stop_time": "",
                          "id": 1,
                          "name": "UpdatedName"
                        }
            }

        .. Status:: 200 (OK)
                    401 (Unauthorized to access getTalent)
                    404 (Campaign not found)
                    500 (Internal Server Error)

        :param campaign_id: integer, unique id representing campaign in GT database
        :return: json for required campaign
        """
        campaign = SmsCampaign.get_by_id(campaign_id)
        if campaign:
            return dict(campaign=campaign.to_json()), 200
        else:
            raise ResourceNotFound(error_message='SMS Campaign does not exist with id %s'
                                                 % campaign_id)

    def post(self, campaign_id):
        """
        Updates campaign in getTalent's database
        :param campaign_id: id of campaign on getTalent database

        :Example:

            campaign_data = {

                            "name": "New SMS Campaign",
                            "sms_body_text": "HI all, we have few openings at abc.com",
                            "frequency_id": 2,
                            "added_time": "2015-11-24T08:00:00",
                            "send_time": "2015-11-26T08:00:00",
                            "stop_time": "2015-11-30T08:00:00",
                            "id": 1
                            }

            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }
            data = json.dumps(campaign_data)
            campaign_id = campaign_data['id']
            response = requests.post(
                                        API_URL + '/campaign/' + str(campaign_id)',
                                        data=data,
                                        headers=headers,
                                    )

        .. Response::

            No Content

        .. Status:: 200 (Resource Modified)
                    401 (Unauthorized to access getTalent)
                    404 (Campaign not found)
                    500 (Internal Server Error)
        """
        # TODO: Update custom error handler status codes
        campaign_data = request.get_json(force=True)
        camp_obj = SmsCampaignBase(user_id=int(request.user.id))
        camp_obj.create_or_update_sms_campaign(campaign_data, campaign_id=campaign_id)
        return dict(message='SMS Campaign(id:%s) has been updated successfully' % campaign_id,), 200

    def delete(self, campaign_id):
        """
        Removes a single campaign from getTalent's database.
        :param id: (Integer) unique id in sms_campaign table on GT database.

        :Example:
            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
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
                    403 (Forbidden: Campaign not found for this user)
                    404 (Campaign not found)
                    500 (Internal Server Error)
        """
        campaign = SmsCampaign.get_by_id(campaign_id)
        if campaign:
            delete_status = SmsCampaign.delete(campaign_id)
            if delete_status:
                return dict(message='Campaign(id:%s) deleted successfully' % campaign_id), 200
            else:
                raise ForbiddenError
        else:
            raise ResourceNotFound(error_message='SMS Campaign(id=%s) not found.' % campaign_id)


@api.route('/campaigns/<int:campaign_id>/sms_campaign_sends')
class SmsCampaignSends(Resource):
    """
    This resource is used to Get Campaign sends [GET]
    """
    decorators = [require_oauth]

    def get(self, campaign_id):
        """
        Returns Campaign sends for given campaign id

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            campaign_id = 1
            response = requests.get(API_URL + '/campaigns/' + str(campaign_id)
                                + '/sms_campaign_sends/', headers=headers)

        .. Response::

            {
                "campaign_sends":
                                    [
                                        {
                                          "candidate_id": 1,
                                          "id": 9,
                                          "sent_time": "2015-11-23 18:25:09",
                                          "sms_campaign_blast_id": 1,
                                          "updated_time": "2015-11-23 18:25:08"
                                        },
                                        {
                                          "candidate_id": 2,
                                          "id": 10,
                                          "sent_time": "2015-11-23 18:25:13",
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
        :return: json for required campaign
        """
        campaign_blasts = SmsCampaignBlast.get_by_campaign_id(campaign_id)
        if campaign_blasts:
            campaign_sends = SmsCampaignSend.get_by_campaign_id(campaign_blasts.id)
            campaign_sends_json = [campaign_send.to_json() for campaign_send in campaign_sends]
            data = {'count': len(campaign_sends_json),
                    'campaign_sends': campaign_sends_json}
            return data, 200
        else:
            raise ResourceNotFound(error_message='SMS Campaign id=%s not found.'
                                                 % campaign_id)


@api.route('/campaigns/<int:campaign_id>/send')
class SendSmsCampaign(Resource):
    """
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
                    "total_sends": 2,
                    "message": "Campaign(id:1) has been sent successfully"
                }

        .. Status:: 200 (OK)
                    401 (Unauthorized to access getTalent)
                    404 (Campaign not found)
                    500 (Internal Server Error)

        .. Error Codes:: 5001 (Empty message body to send)
                         5002 (User has MultipleMobileNumbers)
                         5003 (TwilioAPIError)
                         5004 (GoogleShortenUrlAPIError)

        :param campaign_id: integer, unique id representing campaign in GT database
        :return: json for required campaign containing message and total sends.
        """
        camp_obj = SmsCampaignBase(user_id=request.user.id)
        total_sends = camp_obj.process_send(campaign_id=campaign_id)
        return dict(message='Campaign(id:%s) has been sent successfully'
                            % campaign_id, total_sends=total_sends), 200
