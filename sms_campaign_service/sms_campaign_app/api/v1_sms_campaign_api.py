"""
 Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

This file contains API endpoints related to sms_campaign_service.
    Following is a list of API endpoints:

        - SmsCampaigns: /v1/sms-campaigns

            GET     : Gets list of all the SMS campaigns that belong to user
            POST    : Creates new campaign and save it in database
            DELETE  : Deletes SMS campaigns of user using given campaign ids as a list

        - ScheduleSmsCampaign: /v1/sms-campaigns/:campaign_id/schedule

            POST    : Schedules the campaign from given campaign_id and data provided
            PUT     : Re-schedules the campaign from given campaign_id and data provided
            DELETE  : Un-schedules the campaign from given campaign_id

        - SmsCampaigns: /v1/sms-campaigns/:campaign_id

            GET     : Gets campaign data using given id
            PUT    : Updates existing campaign using given id
            DELETE  : Deletes SMS campaign from db using given id

        - SendSmsCampaign: /v1/sms-campaigns/:campaign_id/send

            POST    : Sends the SMS Campaign by campaign id

        - SmsCampaignUrlRedirection: /v1/redirect/:id

            GET    : Redirects the candidate to our app to keep track of number of clicks, hit_count
                    and create activity.

        - SmsReceive: /v1/receive

            POST    : When candidate replies to an SMS campaign, this endpoint is hit from Twilio
                        to notify our app.

        - SmsCampaignBlasts:  /v1/sms-campaigns/:campaign_id/blasts

            GET    : Gets the all the "blast" records for given SMS campaign id from db table
                    "sms_campaign_blast"

        - SmsCampaignBlastById:  /v1/sms-campaigns/:campaign_id/blasts/:blast_id

            GET    : Gets the "blast" record for given SMS campaign id and blast_id from db table
                    "sms_campaign_blast"

        - SmsCampaignBlastSends:  /v1/sms-campaigns/:campaign_id/blasts/:blast_id/sends

            GET    : Gets the "sends" records for given SMS campaign id and blast_id
                        from db table 'sms_campaign_sends'.

        - SmsCampaignBlastReplies:  /v1/sms-campaigns/:campaign_id/blasts/:blast_id/replies

            GET    : Gets the "replies" records for given SMS campaign id and blast_id
                        from db table 'sms_campaign_replies'

        - SmsCampaignSends:  /v1/sms-campaigns/:campaign_id/sends

            GET    : Gets all the "sends" records for given SMS campaign id
                        from db table sms_campaign_sends

        - SmsCampaignReplies:  /v1/sms-campaigns/:campaign_id/replies

            GET    : Gets all the "replies" records for given SMS campaign id
                        from db table "sms_campaign_replies"
"""


# Standard Library
import types
from werkzeug.utils import redirect

# Third Party
import requests
from flask import request
from flask import Blueprint
from flask.ext.restful import Resource

# Service Specific
from sms_campaign_service.sms_campaign_app import logger
from sms_campaign_service.common.models.sms_campaign import (SmsCampaignSend,
                                                             SmsCampaignReply, SmsCampaign)
from sms_campaign_service.modules.sms_campaign_base import SmsCampaignBase
from sms_campaign_service.modules.handy_functions import (request_from_google_shorten_url_api,
                                                          get_valid_blast_obj)

# Common Utils
from sms_campaign_service.common.talent_api import TalentApi
from sms_campaign_service.common.routes import SmsCampaignApi
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.utils.auth_utils import require_oauth
from sms_campaign_service.common.utils.api_utils import (api_route, ApiResponse,
                                                         get_pagination_params,
                                                         get_paginated_response)
from sms_campaign_service.common.campaign_services.campaign_base import CampaignBase
from sms_campaign_service.common.campaign_services.validators import get_valid_json_data
from sms_campaign_service.common.campaign_services.campaign_utils import \
    (CampaignUtils, raise_if_dict_values_are_not_int_or_long)
from sms_campaign_service.common.campaign_services.custom_errors import CampaignException
from sms_campaign_service.common.error_handling import (ResourceNotFound, InvalidUsage,
                                                        ForbiddenError,  InternalServerError)


# creating blueprint
sms_campaign_blueprint = Blueprint('sms_campaign_api', __name__)
api = TalentApi()
api.init_app(sms_campaign_blueprint)
api.route = types.MethodType(api_route, api)


@api.route(SmsCampaignApi.CAMPAIGNS)
class SMSCampaigns(Resource):
    """
    Endpoint looks like /v1/sms-campaigns
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
        :rtype: json

        :Example:

        >>> import requests

        >>> headers = {'Authorization': 'Bearer <access_token>'}
        >>> response = requests.get(SmsCampaignApiUrl.CAMPAIGNS, headers=headers)

        .. Response::

            {
                  "campaigns": [
                            {
                              "added_datetime": "2016-02-09T16:13:21+00:00",
                              "start_datetime": null,
                              "frequency": "Once",
                              "user_id": 1,
                              "name": "Smartlist",
                              "body_text": null,
                              "list_ids": [1, 2, 3],
                              "id": 1,
                              "end_datetime": null
                            },
                            {
                              "added_datetime": "2016-02-09T17:44:05+00:00",
                              "start_datetime": null,
                              "frequency": "Once",
                              "user_id": 1,
                              "name": "Smartlist",
                              "body_text": null,
                              "list_ids": [2],
                              "id": 4,
                              "end_datetime": null
                            }
                            ]
            }

        .. Status:: 200 (OK)
                    401 (Unauthorized to access getTalent)
                    500 (Internal Server Error)
        """
        page, per_page = get_pagination_params(request)
        camp_obj = SmsCampaignBase(request.user.id)
        query = camp_obj.get_all_campaigns()
        return get_paginated_response('campaigns', query, page, per_page,
                                      parser=SmsCampaign.to_dict)

    def post(self):
        """
        This method takes data to create SMS campaign in database table 'sms_campaign'.
        :return: id of created campaign
        :rtype: json

        :Example:

        >>> import json
        >>> import requests

        >>> headers = {'Authorization': 'Bearer <access_token>',
        >>>             'content-type': 'application/json'
        >>>           }
        >>> campaign_data = {"name": "My SMS Campaign",
        >>>                  "body_text": "HI all, we have few openings at getTalent",
        >>>                  "smartlist_ids": [1, 25]
        >>>                  }
        >>> data = json.dumps(campaign_data)
        >>> response = requests.post(SmsCampaignApiUrl.CAMPAIGNS, headers=headers,
        >>>                         data=data)


        .. Response::

            {
                id: 123
            }

        .. Status:: 201 (Resource Created)
                    401 (Unauthorized to access getTalent)
                    403 (Forbidden error)
                    500 (Internal Server Error)

        ..Error Codes::
                        5001 (INVALID_URL_FORMAT)
                        5002 (MultipleTwilioNumbersFoundForUser)
                        5003 (TwilioApiError)
                        5005 (MultipleUsersFound)
        """
        data_from_ui = get_valid_json_data(request)
        campaign_obj = SmsCampaignBase(request.user.id)
        campaign_id, invalid_smartlist_ids = campaign_obj.save(data_from_ui)
        headers = {'Location': SmsCampaignApiUrl.CAMPAIGN % campaign_id}
        logger.debug('Campaign(id:%s) has been saved.' % campaign_id)
        # If any of the smartlist_id found invalid
        if invalid_smartlist_ids['count']:
            return ApiResponse(dict(id=campaign_id,
                                    invalid_smartlist_ids=invalid_smartlist_ids),
                               status=requests.codes.MULTI_STATUS, headers=headers)
        else:
            return ApiResponse(dict(id=campaign_id),
                               status=requests.codes.CREATED, headers=headers)

    def delete(self):
        """
        Deletes multiple campaigns using ids given in list in request data.
        :return:

        :Example:

        >>> import json
        >>> import requests

        >>> headers = {'Authorization': 'Bearer <access_token>',
        >>>             'content-type': 'application/json'
        >>>           }
        >>> campaign_ids = {'ids': [1, 2, 3]}
        >>> data = json.dumps(campaign_ids)
        >>> response = requests.delete(SmsCampaignApiUrl.CAMPAIGNS, headers=headers,
        >>>                            data=data)


        .. Response::

            {
                'message': '3 Campaigns have been deleted successfully'
            }

        .. Status:: 200 (Resource deleted)
                    207 (Not all deleted)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Forbidden error)
                    404 (Campaign not found)
                    500 (Internal Server Error)
        """
        req_data = get_valid_json_data(request)
        campaign_ids = req_data['ids'] if 'ids' in req_data else []
        if not isinstance(req_data['ids'], list):
            raise InvalidUsage('Bad request, include campaign_ids as list data',
                               error_code=InvalidUsage.http_status_code())
        # check if campaigns_ids list is not empty
        if not campaign_ids:
            return dict(message='No campaign id provided to delete'), requests.codes.OK

        if not all([isinstance(campaign_id, (int, long)) for campaign_id in campaign_ids]):
            raise InvalidUsage('Bad request, campaign_ids must be integer',
                               error_code=InvalidUsage.http_status_code())
        not_deleted = []
        not_found = []
        not_owned = []
        status_code = None
        for campaign_id in campaign_ids:
            campaign_obj = SmsCampaignBase(request.user.id)
            try:
                deleted = campaign_obj.delete(campaign_id)
                if not deleted:
                    # error has been logged inside delete()
                    not_deleted.append(campaign_id)
            except ForbiddenError:
                status_code = ForbiddenError.http_status_code()
                not_owned.append(campaign_id)
            except ResourceNotFound:
                status_code = ResourceNotFound.http_status_code()
                not_found.append(campaign_id)
            except InvalidUsage:
                status_code = InvalidUsage.http_status_code()
                not_deleted.append(campaign_id)
        if status_code and len(campaign_ids) == 1:  # It means only one campaign_id was provided
            return dict(message='Unable to delete campaign.'), status_code
        count_invalid_ids = len(not_deleted) + len(not_found) + len(not_owned)
        if not count_invalid_ids:
            return dict(message='%d campaign(s) deleted successfully.'
                                % len(campaign_ids)), requests.codes.OK
        if count_invalid_ids == len(campaign_ids):
            status_code = InvalidUsage.http_status_code()
        else:
            status_code = requests.codes.MULTI_STATUS
        return dict(message='Unable to delete %d campaign(s).' % count_invalid_ids,
                    not_deleted_ids=not_deleted, not_found_ids=not_found,
                    not_owned_ids=not_owned), status_code


@api.route(SmsCampaignApi.SCHEDULE)
class ScheduleSmsCampaign(Resource):
    """
    Endpoint looks like /v1/sms-campaigns/:campaign_id/schedule
    This resource is used to
        1- Schedule SMS Campaign using scheduler_service [POST]
        2- Re-schedule SMS Campaign using scheduler_service [PUT]
        3- Un-schedule SMS Campaign using scheduler_service [DELETE]
    """
    decorators = [require_oauth()]

    def post(self, campaign_id):
        """
        It schedules an SMS campaign using given campaign_id by making HTTP POST request to
         scheduler_service.

        :param campaign_id: integer, unique id representing campaign in GT database
        :type campaign_id: int | long
        :return: JSON containing message and task_id.
        :rtype: json

        :Example:

        >>> import json
        >>> import requests

        >>> headers = {'Authorization': 'Bearer <access_token>',
        >>>             'content-type': 'application/json'
        >>>           }
        >>> schedule_data = {
        >>>                    "frequency_id": 2,
        >>>                    "start_datetime": "2015-11-26T08:00:00.000Z",
        >>>                    "end_datetime": "2015-11-30T08:00:00.000Z"
        >>>                 }
        >>> data = json.dumps(schedule_data)
        >>> campaign_id = 1
        >>> response = requests.post(SmsCampaignApiUrl.SCHEDULE % campaign_id, headers=headers,
        >>>                         data=data)

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
        """
        # validate data to schedule
        pre_processed_data = SmsCampaignBase.data_validation_for_campaign_schedule(request,
                                                                                   campaign_id,
                                                                                   CampaignUtils.SMS)
        # create object of class SmsCampaignBase
        sms_camp_obj = SmsCampaignBase(request.user.id)
        # assign campaign to object
        sms_camp_obj.campaign = pre_processed_data['campaign']
        # call schedule() method to schedule the campaign and get the task_id
        task_id = sms_camp_obj.schedule(pre_processed_data['data_to_schedule'])
        return dict(message='SMS Campaign(id:%s) has been scheduled.' % campaign_id,
                    task_id=task_id), requests.codes.OK

    def put(self, campaign_id):
        """
        This endpoint is to re-schedule a campaign.
        We check if given campaign has task_id and task is scheduled on scheduler_service.

        If task is not scheduled, we raise Invalid Usage saying 'Campaign is not scheduled. Use POST
        method instead to schedule it'.

        If campaign is scheduled, we get scheduled task from scheduler_service. We then compare
        the fields of scheduled task with the requested field values (e.g. frequency,
        start_datetime, end_datetime etc.) If requested field values are different than the field
        values of scheduled_task, we un-schedule first previous schedule of that campaign and then
        schedule it again with new parameters. Otherwise we return the message that campaign
        is already scheduled with given parameters.

        :param campaign_id: integer, unique id representing campaign in getTalent's database
        :type campaign_id: int | long
        :return: JSON containing message and task_id.
        :rtype: json

        :Example:

        >>> import json
        >>> import requests

        >>> headers = {'Authorization': 'Bearer <access_token>',
        >>>             'content-type': 'application/json'
        >>>           }
        >>> schedule_data = {
        >>>                    "frequency_id": 2,
        >>>                    "start_datetime": "2015-11-26T08:00:00.000Z",
        >>>                    "end_datetime": "2015-11-30T08:00:00.000Z"
        >>>                 }
        >>> data = json.dumps(schedule_data)
        >>> campaign_id = 1
        >>> response = requests.put(SmsCampaignApiUrl.SCHEDULE % campaign_id, headers=headers,
        >>>                         data=data)

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
        """
        # create object of class SmsCampaignBase
        sms_camp_obj = SmsCampaignBase(request.user.id, campaign_id)
        # call method reschedule() to re-schedule the campaign and get the task_id
        task_id = sms_camp_obj.reschedule(request, campaign_id)
        if task_id:
            message = 'Campaign(id:%s) has been re-scheduled.' % campaign_id
        else:
            message = 'Campaign(id:%s) is already scheduled with given data.' % campaign_id
            task_id = sms_camp_obj.campaign.scheduler_task_id
        return dict(message=message, task_id=task_id), requests.codes.OK

    def delete(self, campaign_id):
        """
        Unschedule a single campaign from scheduler_service and removes the scheduler_task_id
        from getTalent's database.

        :param campaign_id: (Integer) unique id in sms_campaign table on GT database.
        :type campaign_id: int | long

        :Example:

        >>> import requests

        >>> headers = {'Authorization': 'Bearer <access_token>'}
        >>> campaign_id = 1
        >>> response = requests.delete(SmsCampaignApiUrl.SCHEDULE % campaign_id, headers=headers)

        .. Response::

            {
                'message': 'Campaign(id:125) has been unscheduled.'
            }

        .. Status:: 200 (Resource Deleted)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Forbidden: Current user cannot un-schedule SMS campaign)
                    404 (Campaign not found)
                    500 (Internal Server Error)
        """
        task_unscheduled = SmsCampaignBase.unschedule(campaign_id, request, CampaignUtils.SMS)
        if task_unscheduled:
            return dict(message='Campaign(id:%s) has been unscheduled.' % campaign_id), requests.codes.OK
        else:
            return dict(message='Campaign(id:%s) is already unscheduled.' % campaign_id), requests.codes.OK


@api.route(SmsCampaignApi.CAMPAIGN)
class CampaignById(Resource):
    """
    Endpoint looks like /v1/sms-campaigns/:campaign_id
    This resource is used to
        1- Get campaign from given campaign_id [GET]
        2- Update an existing SMS campaign [PUT]
        3- Delete campaign by given campaign id [DELETE]
    """
    decorators = [require_oauth()]

    def get(self, campaign_id):
        """
        Returns campaign object with given id
        :param campaign_id: integer, unique id representing campaign in GT database
        :type campaign_id: int | long
        :return: JSON for required campaign
        :rtype: json

        :Example:

        >>> import requests
        >>> headers = {'Authorization': 'Bearer <access_token>'}
        >>> campaign_id = 1
        >>> response = requests.get(SmsCampaignApiUrl.CAMPAIGN % campaign_id, headers=headers)

        .. Response::

            {
                  "campaign": {
                        "added_datetime": "2016-02-09T16:13:21+00:00",
                        "start_datetime": "2016-02-09T16:13:21+00:00",
                        "frequency": "Once",
                        "user_id": 1,
                        "name": "Job opening at getTalent",
                        "body_text": "HI all, we have few openings at https://www.gettalent.com",
                        "list_ids": [1, 2, 3],
                        "id": 1,
                        "end_datetime": null
                      }
            }

        .. Status:: 200 (OK)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Forbidden: Current user cannot get SMS campaign record)
                    404 (Campaign not found)
                    500 (Internal Server Error)
        """
        campaign = SmsCampaignBase.get_campaign_if_domain_is_valid(campaign_id, request.user,
                                                                   CampaignUtils.SMS)
        return dict(campaign=campaign.to_dict()), requests.codes.OK

    def put(self, campaign_id):
        """
        Updates campaign in getTalent's database

        :param campaign_id: id of campaign on getTalent database
        :type campaign_id: int | long

        :Example:

        >>> import json
        >>> import requests

        >>> headers = {'Authorization': 'Bearer <access_token>',
        >>>             'content-type': 'application/json'
        >>>           }
        >>> campaign_data = {"name": "Updated SMS Campaign",
        >>>                  "body_text": "HI all, we have few openings at abc.com",
        >>>                  "smartlist_ids": [1, 25]
        >>>                  }
        >>> data = json.dumps(campaign_data)
        >>> campaign_id = 1
        >>> response = requests.put(SmsCampaignApiUrl.CAMPAIGN % campaign_id, headers=headers,
        >>>                         data=data)

        ..Response::
                    {
                          "not_found_smartlist_ids": [25],
                          "invalid_smartlist_ids": [],
                          "message": "SMS Campaign(id:1) has been updated successfully"
                    }

        .. Status:: 200 (Resource Modified)
                    207 (Not all modified)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Forbidden: Current user cannot update SMS campaign)
                    404 (Campaign not found)
                    500 (Internal Server Error)

        .. Error codes::
                    5017 (INVALID_URL_FORMAT)
        """
        campaign_data = get_valid_json_data(request)
        camp_obj = SmsCampaignBase(request.user.id, campaign_id)
        invalid_smartlist_ids = camp_obj.update(campaign_data, campaign_id=campaign_id)
        # If any of the smartlist_id found invalid
        if invalid_smartlist_ids['count']:
            return dict(
                message='SMS Campaign(id:%s) has been updated successfully' % campaign_id,
                invalid_smartlist_ids=invalid_smartlist_ids), 207
        else:
            return dict(message='SMS Campaign(id:%s) has been updated successfully'
                                % campaign_id), requests.codes.OK

    def delete(self, campaign_id):
        """
        Removes a single campaign from getTalent's database.
        :param campaign_id: (Integer) unique id in sms_campaign table on GT database.
        :type campaign_id: int | long

        :Example:

        >>> import requests
        >>> headers = {'Authorization': 'Bearer <access_token>'}
        >>> campaign_id = 1
        >>> response = requests.delete(SmsCampaignApiUrl.CAMPAIGN % campaign_id, headers=headers)

        .. Response::

            {
                'message': 'Campaign(id:125) has been deleted successfully'
            }
        .. Status:: 200 (Resource Deleted)
                    400 (Bad request)
                    403 (Forbidden: Current user cannot delete SMS campaign)
                    404 (Campaign not found)
                    500 (Internal Server Error)

        ..Error codes::
                    5010 (ERROR_DELETING_SMS_CAMPAIGN)
        """
        campaign_obj = SmsCampaignBase(request.user.id, campaign_id)
        campaign_deleted = campaign_obj.delete(campaign_id)
        if campaign_deleted:
            return dict(message='Campaign(id:%s) has been deleted successfully.' % campaign_id), requests.codes.OK
        else:
            raise InternalServerError(
                'Campaign(id:%s) was not deleted.' % campaign_id,
                error_code=CampaignException.ERROR_DELETING_CAMPAIGN)


@api.route(SmsCampaignApi.SEND)
class SendSmsCampaign(Resource):
    """
    Endpoint looks like /v1/sms-campaigns/:campaign_id/send
    This resource is used to send SMS Campaign to candidates [POST]
    """
    decorators = [require_oauth()]

    def post(self, campaign_id):
        """
        It sends given Campaign (from given campaign id) to the smartlist candidates
            associated with given campaign.
        Once the campaign is scheduled, _scheduler_service_ will pick it up and it will ping the
        this endpoint (https://sms-campaign-service.gettalent.com/v1/sms-campaign/:campaign_id/send)

        :param campaign_id: integer, unique id representing campaign in GT database
        :type campaign_id: int | long

        :Example:

        >>> import requests
        >>> headers = {'Authorization': 'Bearer <access_token>'}
        >>> campaign_id = 1
        >>> response = requests.post(SmsCampaignApiUrl.SEND % campaign_id, headers=headers)

        .. Response::

                {
                    "message": "Campaign(id:1) is being sent to candidates"
                }

        .. Status:: 200 (OK)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Forbidden Error)
                    404 (Campaign not found)
                    500 (Internal Server Error)

        .. Error Codes::
                         5002 (MultipleTwilioNumbersFoundForUser)
                         5003 (TwilioApiError)
                         5004 (GoogleShortenUrlAPIError)
                         5014 (ErrorUpdatingBodyText)
                         5101 (Empty message body to send)
                         5102 (NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN)
                         5103 (NO_CANDIDATE_ASSOCIATED_WITH_SMARTLIST)
        """
        camp_obj = SmsCampaignBase(request.user.id, campaign_id)
        camp_obj.send()
        return dict(message='Campaign(id:%s) is being sent to candidates.' % campaign_id), requests.codes.OK


@api.route(SmsCampaignApi.REDIRECT)
class SmsCampaignUrlRedirection(Resource):
    """
    This endpoint redirects the candidate to our app.
    For details, kindly see below or read README.md under app_common/common/campaign_services/.
    """

    def get(self, url_conversion_id):
        """
        This endpoint is /v1/redirect/:id

        :param url_conversion_id: id of url_conversion record in db
        :type url_conversion_id: int
        :return: redirects to the destination URL else raises exception

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
        """
        # Google's shorten URL API hits this end point while converting long_url to shorter version.
        if request_from_google_shorten_url_api(request.headers.environ):
            return requests.codes.OK
        try:
            redirection_url = CampaignBase.url_redirect(url_conversion_id, CampaignUtils.SMS,
                                                        verify_signature=True,
                                                        request_args=request.args,
                                                        requested_url=request.full_path)
            return redirect(redirection_url)
        # In case any type of exception occurs, candidate should only get internal server error
        except Exception as error:
            # As this endpoint is hit by client, so we log the error, and return internal server
            # error.
            logger.exception("Error occurred while URL redirection for SMS campaign. %s"
                             % error.message)
        return dict(message='Internal Server Error'), InternalServerError.http_status_code()


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


@api.route(SmsCampaignApi.BLASTS)
class SmsCampaignBlasts(Resource):
    """
    Endpoint looks like /v1/sms-campaigns/:campaign_id/blasts.
    This class returns all the blast objects associated with given campaign.
    """
    decorators = [require_oauth()]

    def get(self, campaign_id):
        """
        This endpoint returns a list of blast objects (dict) associated with a specific
        SMS campaign.

        :param campaign_id: int, unique id of a SMS campaign
        :type campaign_id: int | long
        :return: JSON data containing list of blasts
        :rtype: json

        :Example:

        >>> import requests
        >>> headers = {'Authorization': 'Bearer <access_token>'}
        >>> campaign_id = 1
        >>> blast_id = 1
        >>> response = requests.get(SmsCampaignApiUrl.BLASTS % campaign_id, headers=headers)

        .. Response::

            {
                  "blasts": [
                                {
                                  "sends": 763,
                                  "campaign_id": 1,
                                  "id": 1,
                                  "replies": 26,
                                  "updated_time": "2016-01-06 00:00:43",
                                  "clicks": 55,
                                  "sent_datetime": "2016-01-05 14:59:56"
                                },
                                {
                                  "sends": 0,
                                  "campaign_id": 1,
                                  "id": 396,
                                  "replies": 0,
                                  "updated_time": "2016-01-06 00:12:56",
                                  "clicks": 0,
                                  "sent_datetime": "2016-01-06 00:14:21"
                                }
                            ]
            }

        .. Status:: 200 (OK)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Requested campaign does not belong to user's domain)
                    404 (Campaign not found)
                    500 (Internal Server Error)
        """
        # get pagination params
        page, per_page = get_pagination_params(request)

        # Get campaign object if it belongs to user's domain
        campaign = SmsCampaignBase.get_campaign_if_domain_is_valid(campaign_id, request.user,
                                                                   CampaignUtils.SMS)
        # Serialize blasts of a campaign and get paginated response
        return get_paginated_response('blasts', campaign.blasts, page, per_page)


@api.route(SmsCampaignApi.BLAST)
class SmsCampaignBlastById(Resource):
    """
    Endpoint looks like /v1/sms-campaigns/:campaign_id/blasts/:blast_id
    This gives the blast object for the request campaign_id and blast_id
    """
    decorators = [require_oauth()]

    def get(self, campaign_id, blast_id):
        """
        This endpoint returns a blast object for a given campaign_id and blast_id. From which
        we can extract sends, clicks and replies.
        :param campaign_id: int, unique id of a SMS campaign
        :param blast_id: id of blast object
        :type campaign_id: int | long
        :type blast_id: int | long
        :return: JSON data containing list of blasts
        :rtype: json

        :Example:

        >>> import requests
        >>> headers = {'Authorization': 'Bearer <access_token>'}
        >>> campaign_id = 1
        >>> blast_id = 1
        >>> response = requests.get(SmsCampaignApiUrl.BLAST % (campaign_id, blast_id),
        >>>                         headers=headers)

        .. Response::

               {
                      "blast": {
                        "sends": 763,
                        "campaign_id": 1,
                        "id": 1,
                        "replies": 26,
                        "updated_time": "2016-01-06 00:00:43",
                        "clicks": 55,
                        "sent_datetime": "2016-01-05 14:59:56"
                              }
                }

        .. Status:: 200 (OK)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Requested campaign does not belong to user's domain)
                    404 (Campaign not found)
                    500 (Internal server error)
        """
        raise_if_dict_values_are_not_int_or_long(dict(campaign_id=campaign_id, blast_id=blast_id))
        # Validate that campaign belongs to user's domain
        SmsCampaignBase.get_campaign_if_domain_is_valid(campaign_id, request.user,
                                                        CampaignUtils.SMS)
        blast_obj = get_valid_blast_obj(blast_id, campaign_id)
        return dict(blast=blast_obj.to_json()), requests.codes.OK


@api.route(SmsCampaignApi.BLAST_SENDS)
class SmsCampaignBlastSends(Resource):
    """
    Endpoint looks like /v1/sms-campaigns/:campaign_id/blasts/:blast_id/sends
    This resource is used to GET Campaign "sends" for one particular blast of a given campaign.
    """
    decorators = [require_oauth()]

    def get(self, campaign_id, blast_id):
        """
        Returns Campaign sends for given campaign_id and blast_id

        :param campaign_id: int, unique id of a SMS campaign
        :param blast_id: id of blast object
        :type campaign_id: int | long
        :type blast_id: int | long
        :return: dictionary containing SMS campaign sends records as dict
        :rtype: dict

        :Example:

        >>> import requests
        >>> headers = {'Authorization': 'Bearer <access_token>'}
        >>> campaign_id = 1
        >>> blast_id = 1
        >>> response = requests.get(SmsCampaignApiUrl.BLAST_SENDS % (campaign_id, blast_id),
        >>>                         headers=headers)

        .. Response::

            {
                "sends":
                        [
                            {
                              "candidate_id": 1,
                              "id": 9,
                              "sent_datetime": "2015-11-23 18:25:09",
                              "blast_id": 1,
                              "updated_time": "2015-11-23 18:25:08"
                            },
                            {
                              "candidate_id": 2,
                              "id": 10,
                              "sent_datetime": "2015-11-23 18:25:13",
                              "blast_id": 1,
                              "updated_time": "2015-11-23 18:25:13"
                           }
                        ]
            }

        .. Status:: 200 (OK)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Requested campaign does not belong to user's domain)
                    404 (Campaign not found)
                    500 (Internal Server Error)
        """
        # get pagination params
        page, per_page = get_pagination_params(request)
        raise_if_dict_values_are_not_int_or_long(dict(campaign_id=campaign_id, blast_id=blast_id))
        # Validate that campaign belongs to user's domain
        SmsCampaignBase.get_campaign_if_domain_is_valid(campaign_id, request.user,
                                                        CampaignUtils.SMS)
        blast_obj = get_valid_blast_obj(blast_id, campaign_id)
        # Serialize sends of a campaign and get paginated response
        return get_paginated_response('sends', blast_obj.blast_sends, page, per_page)


@api.route(SmsCampaignApi.BLAST_REPLIES)
class SmsCampaignBlastReplies(Resource):
    """
    Endpoint looks like /v1/sms-campaigns/:campaign_id/blasts/:blast_id/replies
    This gives the replies object for the request campaign_id and blast_id
    """
    decorators = [require_oauth()]

    def get(self, campaign_id, blast_id):
        """
        This endpoint returns a blast object for a given campaign_id and blast_id. From which
        we can extract sends, clicks and replies.

        :param campaign_id: int, unique id of a SMS campaign
        :param blast_id: id of blast object
        :type campaign_id: int | long
        :type blast_id: int | long
        :return: JSON data containing list of blasts
        :rtype: json

        :Example:

        >>> import requests
        >>> headers = {'Authorization': 'Bearer <access_token>'}
        >>> campaign_id = 1
        >>> blast_id = 1
        >>> response = requests.get(SmsCampaignApiUrl.BLAST_REPLIES % (campaign_id, blast_id),
        >>>                         headers=headers)

        .. Response::

               {
                    "replies": [
                        {
                          "candidate_phone_id": 1,
                          "added_datetime": "2015-12-07 19:14:59",
                          "id": 4,
                          "blast_id": 1,
                          "body_text": "Why would you do that"
                        },

                        {
                          "candidate_phone_id": 1,
                          "added_datetime": "2015-12-17 12:51:22",
                          "id": 5,
                          "blast_id": 1,
                          "body_text": "Why would you do that"
                        },
                }

        .. Status:: 200 (OK)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Requested campaign does not belong to user's domain)
                    404 (Campaign not found)
                    500 (Internal server error)
        """
        # get pagination params
        page, per_page = get_pagination_params(request)
        raise_if_dict_values_are_not_int_or_long(dict(campaign_id=campaign_id,
                                                      blast_id=blast_id))
        # Validate that campaign object belongs to user's domain
        SmsCampaignBase.get_campaign_if_domain_is_valid(campaign_id, request.user,
                                                        CampaignUtils.SMS)
        blast_obj = get_valid_blast_obj(blast_id, campaign_id)

        # Serialize replies of an sms-campaign and get paginated response
        return get_paginated_response('replies', blast_obj.blast_replies, page, per_page)


@api.route(SmsCampaignApi.SENDS)
class SmsCampaignSends(Resource):
    """
    Endpoint looks like /v1/sms-campaigns/:campaign_id/sends
    This resource is used to GET Campaign sends
    """
    decorators = [require_oauth()]

    def get(self, campaign_id):
        """
        Returns Campaign sends for given campaign id

        :param campaign_id: integer, unique id representing campaign in GT database
        :type campaign_id: int | long
        :return: SMS campaign sends records as dict


        :Example:

        >>> import requests
        >>> headers = {'Authorization': 'Bearer <access_token>'}
        >>> campaign_id = 1
        >>> response = requests.get(SmsCampaignApiUrl.SENDS % str(campaign_id), headers=headers)

        .. Response::

            {
                  "sends": [
                        {
                          "updated_time": "2016-01-05 14:59:55",
                          "sent_datetime": "2016-01-05 09:59:52",
                          "id": 9,
                          "blast_id": 1,
                          "candidate_id": 1
                        },
                        {
                          "updated_time": "2015-12-18 17:31:08",
                          "sent_datetime": "2015-12-18 17:31:08",
                          "id": 10,
                          "blast_id": 1,
                          "candidate_id": 2
                        },
            }

        .. Status:: 200 (OK)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Requested campaign does not belong to user's domain)
                    404 (Campaign not found)
                    500 (Internal Server Error)

        :param campaign_id: integer, unique id representing campaign in GT database
        :return: SMS campaign sends records as dict
        """
        # get pagination params
        page, per_page = get_pagination_params(request)
        # Get campaign object if it belongs to user's domain
        campaign = SmsCampaignBase.get_campaign_if_domain_is_valid(campaign_id, request.user,
                                                                   CampaignUtils.SMS)
        # Get blast_ids related to requested campaign_id
        blast_ids = map(lambda blast: blast.id, campaign.blasts.all())
        query = SmsCampaignSend.get_by_blast_ids(blast_ids)
        # Serialize sends of a campaign and get paginated response
        return get_paginated_response('sends', query, page, per_page)


@api.route(SmsCampaignApi.REPLIES)
class SmsCampaignReplies(Resource):
    """
    Endpoint looks like /v1/sms-campaigns/:campaign_id/replies
    This resource is used to GET Campaign replies
    """
    decorators = [require_oauth()]

    def get(self, campaign_id):
        """
        Returns Campaign replies for given campaign id

        :param campaign_id: integer, unique id representing campaign in GT database
        :type campaign_id: int | long
        :return: SMS campaign replies records as dict

        :Example:

        >>> import requests
        >>> headers = {'Authorization': 'Bearer <access_token>'}
        >>> campaign_id = 1
        >>> response = requests.get(SmsCampaignApiUrl.REPLIES % str(campaign_id), headers=headers)

        .. Response::

                {
                      "replies": [
                            {
                              "candidate_phone_id": 1,
                              "added_datetime": "2015-12-07 19:14:59",
                              "id": 4,
                              "blast_id": 1,
                              "body_text": "Why would you do that?"
                            },

                            {
                              "candidate_phone_id": 1,
                              "added_datetime": "2015-12-17 12:51:22",
                              "id": 5,
                              "blast_id": 1,
                              "body_text": "I got your message Sir."
                           }
                }

        .. Status:: 200 (OK)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Requested campaign does not belong to user's domain)
                    404 (Campaign not found)
                    500 (Internal Server Error)
        """
        # get pagination params
        page, per_page = get_pagination_params(request)
        # Get campaign object if it belongs to user's domain
        campaign = SmsCampaignBase.get_campaign_if_domain_is_valid(campaign_id, request.user,
                                                                   CampaignUtils.SMS)
        # Get blast_ids related to requested campaign_id
        blast_ids = map(lambda blast: blast.id, campaign.blasts.all())
        query = SmsCampaignReply.get_by_blast_ids(blast_ids)
        # Serialize replies of a campaign and get paginated response
        return get_paginated_response('replies', query, page, per_page)
