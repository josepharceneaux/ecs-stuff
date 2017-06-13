"""
 Author: Jitesh Karesia, New Vision Software, <jitesh.karesia@newvisionsoftware.in>
         Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

This file contains API endpoints related to email_campaign_service.
    Following is a list of API endpoints:

        - EmailCampaigns: /v1/email-campaigns

            GET     : Gets list of all the email campaigns that belong to user
            POST    : Creates new campaign and save it in database

        - EmailCampaigns: /v1/email-campaigns/:id

            GET     : Gets campaign data using given id

        - SendEmailCampaign: /v1/email-campaigns/:id/send

            POST    : Sends the email campaign by campaign id

        - EmailCampaignUrlRedirection: /v1/redirect/:id

            GET    : Redirects the candidate to our app to keep track of number of clicks,
                    hit_count and create activity.

        - EmailCampaignBlasts:  /v1/email-campaigns/:id/blasts

            GET    : Gets the all the "blast" records for given email campaign id from
                    db table "email_campaign_blast"

        - EmailCampaignBlastById:  /v1/email-campaigns/:id/blasts/:id

            GET    : Gets the "blast" record for given email campaign id and blast_id from
                    db table "email_campaign_blast"

        - EmailCampaignSends:  /v1/email-campaigns/:id/sends

            GET    : Gets the "sends" records for given email campaign id from db
                    table "email_campaign_sends"

        - EmailCampaignSendById:  /v1/email-campaigns/:id/sends/:id

            GET    : Gets all the "sends" records for given email campaign id
                        from db table "email_campaign_sends"
"""
# Standard Library
import types

# Third Party
from requests import codes
from flask_restful import Resource
from werkzeug.utils import redirect
from flask import request, Blueprint, jsonify

# Service Specific
from email_campaign_service.email_campaign_app import logger
from email_campaign_service.common.models.user import (User, Role)
from email_campaign_service.modules.utils import get_valid_send_obj
from email_campaign_service.modules.email_campaign_base import EmailCampaignBase
from email_campaign_service.modules.validators import validate_and_format_request_data
from email_campaign_service.common.custom_errors.campaign import (NOT_NON_ZERO_NUMBER,
                                                                  INVALID_REQUEST_BODY,
                                                                  EMAIL_CAMPAIGN_NOT_FOUND,
                                                                  EMAIL_CAMPAIGN_FORBIDDEN,
                                                                  INVALID_VALUE_OF_QUERY_PARAM,
                                                                  INVALID_VALUE_OF_PAGINATION_PARAM,
                                                                  INVALID_INPUT)
from email_campaign_service.modules.email_marketing import (create_email_campaign, send_email_campaign,
                                                            update_hit_count, send_test_email)

# Common utils
from email_campaign_service.common.models.rsvp import RSVP
from email_campaign_service.common.talent_api import TalentApi
from email_campaign_service.common.routes import EmailCampaignApi
from email_campaign_service.common.utils.validators import is_number
from email_campaign_service.common.utils.auth_utils import require_oauth
from email_campaign_service.common.models.base_campaign import BaseCampaign
from email_campaign_service.common.utils.handy_functions import send_request
from email_campaign_service.common.models.misc import UrlConversion, Activity
from email_campaign_service.common.campaign_services.campaign_base import CampaignBase
from email_campaign_service.common.routes import (EmailCampaignApiUrl, ActivityApiUrl)
from email_campaign_service.common.models.email_campaign import (EmailCampaign, EmailCampaignSend)
from email_campaign_service.common.error_handling import (ForbiddenError, InvalidUsage, ResourceNotFound,
                                                          InternalServerError)
from email_campaign_service.common.utils.api_utils import (api_route, get_paginated_response, get_pagination_params,
                                                           SORT_TYPES)
from email_campaign_service.common.campaign_services.campaign_utils import (CampaignUtils, INVITATION_STATUSES)
from email_campaign_service.common.campaign_services.validators import raise_if_dict_values_are_not_int_or_long

# Blueprint for email-campaign API
email_campaign_blueprint = Blueprint('email_campaign_api', __name__)
api = TalentApi()
api.init_app(email_campaign_blueprint)
api.route = types.MethodType(api_route, api)


@api.route(EmailCampaignApi.CAMPAIGNS)
class EmailCampaigns(Resource):
    # Access token decorator
    decorators = [require_oauth()]

    def get(self):
        """
        GET /v1/email-campaigns         Fetches all EmailCampaign objects from auth user's domain
        """
        user = request.user
        page, per_page = get_pagination_params(request, error_code=INVALID_VALUE_OF_PAGINATION_PARAM[1])
        sort_type = request.args.get('sort_type', 'DESC')
        search_keyword = request.args.get('search', '')
        sort_by = request.args.get('sort_by', 'added_datetime')
        is_hidden = request.args.get('is_hidden', 0)
        user_id = request.args.get('user_id')

        # Validation of query parameters
        if isinstance(user_id, basestring):
            if not user_id.strip().isdigit() or int(user_id) <= 0:
                raise InvalidUsage(NOT_NON_ZERO_NUMBER[0].format('`user_id`'), error_code=NOT_NON_ZERO_NUMBER[1])
            if request.user.role.name != Role.TALENT_ADMIN \
                    and User.get_domain_id(user_id) != request.user.domain_id:
                raise ForbiddenError("Logged-in user and requested user_id are of different domains",
                                     EMAIL_CAMPAIGN_FORBIDDEN[1])
            user_id = int(user_id)

        if not is_number(is_hidden) or int(is_hidden) not in (0, 1):
            raise InvalidUsage('`is_hidden` can be either 0 or 1', error_code=INVALID_VALUE_OF_QUERY_PARAM[1])

        if sort_by not in ('added_datetime', 'name'):
            raise InvalidUsage('Value of sort_by parameter is not valid', error_code=INVALID_VALUE_OF_QUERY_PARAM[1])

        if sort_type not in SORT_TYPES:
            raise InvalidUsage('Value of sort_type parameter is not valid. Valid values are %s'
                               % list(SORT_TYPES), error_code=INVALID_VALUE_OF_QUERY_PARAM[1])

        # Get all email campaigns from logged in user's domain
        query = EmailCampaign.get_by_domain_id_and_filter_by_name(
            user.domain_id, search_keyword, sort_by, sort_type, int(is_hidden), user_id=user_id)

        return get_paginated_response('email_campaigns', query, page, per_page, parser=EmailCampaign.to_dict)

    def post(self):
        """
            POST /v1/email-campaigns
            Required parameters:
            name: Name of email campaign
            subject: subject of email
            body_html: email body
            list_ids: smartlist ids to which emails will be sent
        """
        # Get and validate request data
        data = request.get_json(silent=True)
        if not data:
            raise InvalidUsage(INVALID_REQUEST_BODY[0], INVALID_REQUEST_BODY[1])
        data = validate_and_format_request_data(data, request.user)

        campaign = create_email_campaign(user_id=request.user.id,
                                         oauth_token=request.oauth_token,
                                         name=data['name'],
                                         subject=data['subject'],
                                         description=data['description'],
                                         _from=data['from'],
                                         reply_to=data['reply_to'],
                                         body_html=data['body_html'],
                                         body_text=data['body_text'],
                                         list_ids=data['list_ids'],
                                         email_client_id=data['email_client_id'],
                                         start_datetime=data['start_datetime'],
                                         end_datetime=data['end_datetime'],
                                         frequency_id=data['frequency_id'],
                                         email_client_credentials_id=data['email_client_credentials_id'],
                                         base_campaign_id=data['base_campaign_id'])

        return {'campaign': campaign}, codes.CREATED


@api.route(EmailCampaignApi.CAMPAIGN)
class SingleEmailCampaign(Resource):
    # Access token decorator
    decorators = [require_oauth()]

    def get(self, campaign_id):
        """
        GET /v1/email-campaigns/<id>    Fetch EmailCampaign object
        """
        raise_if_dict_values_are_not_int_or_long(dict(campaign_id=campaign_id))
        include_fields = request.values['fields'].split(',') if request.values.get('fields') else None
        email_campaign = EmailCampaignBase.get_campaign_if_domain_is_valid(campaign_id, request.user)
        return {"email_campaign": email_campaign.to_dict(include_fields=include_fields)}

    def patch(self, campaign_id):
        """
        This endpoint updates an existing campaign
        :param int|long campaign_id: Id of campaign
        """
        raise_if_dict_values_are_not_int_or_long(dict(campaign_id=campaign_id))
        # Get and validate request data
        data = request.get_json(silent=True)
        if not data:
            raise InvalidUsage("Received empty request body", error_code=INVALID_REQUEST_BODY[1])
        is_hidden = data.get('is_hidden', False)
        if is_hidden not in (True, False, 1, 0):
            raise InvalidUsage("is_hidden field should be a boolean, given: %s" % is_hidden,
                               error_code=INVALID_INPUT[1])
        email_campaign = EmailCampaignBase.get_campaign_if_domain_is_valid(campaign_id, request.user)
        # Unschedule task from scheduler_service
        if email_campaign.scheduler_task_id:
            headers = {'Authorization': request.oauth_token}
            # campaign was scheduled, remove task from scheduler_service
            if CampaignUtils.delete_scheduled_task(email_campaign.scheduler_task_id, headers):
                email_campaign.update(scheduler_task_id='')  # Delete scheduler task id

        email_campaign.update(is_hidden=is_hidden)
        logger.info("Email campaign(id:%s) has been archived successfully" % campaign_id)
        return dict(message="Email campaign (id: %s) updated successfully" % campaign_id), codes.OK


@api.route(EmailCampaignApi.TEST_EMAIL)
class TestEmailResource(Resource):
    """
    This resource is to send test email to preview the email before sending the actual email campaign to candidates.
    """
    # Access token decorator
    decorators = [require_oauth()]

    def post(self):
        """
            POST /v1/test-email
            Send email campaign with data (subject, from, body_html, emails)
            Sample POST Data:

            {
              "subject": "Test Email",
              "from": "Zohaib Ijaz",
              "body_html": "<html><body><h1>Welcome to email campaign service <a href=https://www.github.com>Github</a></h1></body></html>",
              "emails": ["mzohaib.qc@gmail.com", "mzohaib.qc+1@gmail.com"],
              "reply_to": "abc@xyz.com"
            }
        """
        user = request.user
        send_test_email(user, request)
        return {'message': 'test email has been sent to given emails'}, codes.OK


@api.route(EmailCampaignApi.SEND)
class EmailCampaignSendApi(Resource):
    """
    This endpoint looks like /v1/email-campaigns/:id/send
    """
    decorators = [require_oauth()]

    def post(self, campaign_id):
        """
        Sends campaign emails to the candidates present in smartlists of campaign.
        Scheduler service will call this to send emails to candidates.
        :param int|long campaign_id: Campaign id
        """
        raise_if_dict_values_are_not_int_or_long(dict(campaign_id=campaign_id))
        email_campaign = EmailCampaignBase.get_campaign_if_domain_is_valid(campaign_id, request.user)
        if email_campaign.is_hidden:
            logger.info("Email campaign(id:%s) is archived, it cannot be sent." % campaign_id)
            # Unschedule task from scheduler_service
            if email_campaign.scheduler_task_id:
                headers = {'Authorization': request.oauth_token}
                # campaign was scheduled, remove task from scheduler_service
                if CampaignUtils.delete_scheduled_task(email_campaign.scheduler_task_id, headers):
                    email_campaign.update(scheduler_task_id='')  # Delete scheduler task id
            raise ResourceNotFound("Email campaign(id:%s) has been deleted." % campaign_id,
                                   error_code=EMAIL_CAMPAIGN_NOT_FOUND[1])
        email_client_id = email_campaign.email_client_id
        results_send = send_email_campaign(request.user, email_campaign, new_candidates_only=False)
        if email_client_id:
            if not isinstance(results_send, list):
                raise InternalServerError(error_message="Something went wrong, response is not list")
            data = {
                'email_campaign_sends': [
                    {
                        'email_campaign_id': email_campaign.id,
                        'new_html': new_email_html_or_text.get('new_html'),
                        'new_text': new_email_html_or_text.get('new_text'),
                        'candidate_email_address': new_email_html_or_text.get('email')
                    } for new_email_html_or_text in results_send
                ]
            }
            return jsonify(data)

        return dict(message='email_campaign(id:%s) is being sent to candidates.' % campaign_id), codes.OK


@api.route(EmailCampaignApi.URL_REDIRECT)
class EmailCampaignApiUrlRedirect(Resource):
    """
    This endpoint looks like /v1/redirect/:id
    This is hit when candidate open's an email or clicks on html content of email campaign
    """

    def get(self, url_conversion_id):
        """
        Id of url_conversion record
        """
        # Verify the signature of URL
        CampaignBase.pre_process_url_redirect(request.args, request.full_path)
        url_conversion = UrlConversion.query.get(url_conversion_id)
        if not url_conversion:
            logger.error('No record of url_conversion found for id:%s' % url_conversion_id)
            return
        # Update hitcount
        update_hit_count(url_conversion)
        # response.title = "getTalent.com: Redirecting to %s" % url_conversion.destinationUrl
        destination_url = url_conversion.destination_url
        # TODO: Destination URL shouldn't be empty. Need to raise custom exception
        # TODO: EmptyDestinationUrl here
        if (destination_url or '').lower().startswith('www.'):
            destination_url = "http://" + destination_url

        if destination_url == '#':
            # redirect(HOST_NAME + str(URL(a='web', c='dashboard', f='index')))
            destination_url = 'http://www.gettalent.com/'  # Todo
        return redirect(destination_url)


@api.route(EmailCampaignApi.BLASTS)
class EmailCampaignBlasts(Resource):
    """
    Endpoint looks like /v1/email-campaigns/:id/blasts.
    This resource returns all the blast objects associated with given campaign.
    """
    decorators = [require_oauth()]

    def get(self, campaign_id):
        """
        This endpoint returns a list of blast objects (dict) associated with a specific
        email campaign.

        :param campaign_id: int, unique id of a email campaign
        :type campaign_id: int | long
        :return: JSON data containing list of blasts and their counts

        :Example:

        >>> import requests
        >>> headers = {'Authorization': 'Bearer <access_token>'}
        >>> campaign_id = 1
        >>> response = requests.get(EmailCampaignApiUrl.BLASTS % campaign_id, headers=headers)

        .. Response::

            {
                  "blasts": [
                    {
                      "updated_datetime": "2016-02-10 19:37:15",
                      "sends": 1,
                      "bounces": 0,
                      "text_clicks": 0,
                      "campaign_id": 1,
                      "html_clicks": 0,
                      "complaints": 0,
                      "id": "1",
                      "opens": 0,
                      "sent_datetime": "2016-02-10 19:37:04"
                    },
                    {
                      "updated_datetime": "2016-02-10 19:40:46",
                      "sends": 1,
                      "bounces": 0,
                      "text_clicks": 0,
                      "campaign_id": 1,
                      "html_clicks": 0,
                      "complaints": 0,
                      "id": "2",
                      "opens": 0,
                      "sent_datetime": "2016-02-10 19:40:38"
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
        raise_if_dict_values_are_not_int_or_long(dict(campaign_id=campaign_id))
        # Get a campaign that was created by this user
        campaign = EmailCampaignBase.get_campaign_if_domain_is_valid(campaign_id, request.user)
        # get paginated response
        page, per_page = get_pagination_params(request, error_code=INVALID_VALUE_OF_PAGINATION_PARAM[1])
        return get_paginated_response('blasts', campaign.blasts, page, per_page)


@api.route(EmailCampaignApi.BLAST)
class EmailCampaignBlastById(Resource):
    """
    Endpoint looks like /v1/email-campaigns/:id/blasts/:id.
    This resource returns a blast object for given blast_id associated with given campaign.
    """
    decorators = [require_oauth()]

    def get(self, campaign_id, blast_id):
        """
        This endpoint returns a blast object for a given campaign_id and blast_id.
        From that blast object we can extract sends, clicks etc.
        :param campaign_id: int, unique id of a email campaign
        :param blast_id: id of blast object
        :type campaign_id: int | long
        :type blast_id: int | long
        :return: JSON data containing dict of blast object

        :Example:

        >>> import requests
        >>> headers = {'Authorization': 'Bearer <access_token>'}
        >>> campaign_id = 1
        >>> blast_id = 1
        >>> response = requests.get(EmailCampaignApiUrl.BLAST % (campaign_id, blast_id),
        >>>                         headers=headers)

        .. Response::

               {
                  "blast": {
                                "updated_datetime": "2016-02-10 19:37:15",
                                "sends": 1,
                                "bounces": 0,
                                "campaign_id": 1,
                                "text_clicks": 0,
                                "html_clicks": 0,
                                "complaints": 0,
                                "id": "1",
                                "opens": 0,
                                "sent_datetime": "2016-02-10 19:37:04"
                              }
               }

        .. Status:: 200 (OK)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Requested campaign does not belong to user's domain OR requested blast
                        object is not associated with given campaign_id)
                    404 (Campaign not found OR blast_obj with given id not found)
                    500 (Internal server error)
        """
        raise_if_dict_values_are_not_int_or_long(dict(campaign_id=campaign_id,
                                                      blast_id=blast_id))
        # Get valid blast object
        blast_obj = EmailCampaignBase.get_valid_blast_obj(campaign_id, blast_id, request.user)
        return dict(blast=blast_obj.to_json()), codes.OK


@api.route(EmailCampaignApi.SENDS)
class EmailCampaignSends(Resource):
    """
    Endpoint looks like /v1/email-campaigns/:id/sends
    This resource returns all the sends objects associated with given campaign.
    """
    decorators = [require_oauth()]

    def get(self, campaign_id):
        """
        This endpoint returns a list of send objects (dict) associated with a specific
        email campaign.

        :param campaign_id: int, unique id of a email campaign
        :type campaign_id: int | long
        :return: JSON data containing list of send objects and their count

        :Example:

        >>> import requests
        >>> headers = {'Authorization': 'Bearer <access_token>'}
        >>> campaign_id = 1
        >>> response = requests.get(EmailCampaignApiUrl.SENDS % campaign_id, headers=headers)

        .. Response::

            {
                "sends": [
                            {
                              "ses_message_id": "",
                              "is_ses_bounce": false,
                              "updated_datetime": "2016-02-29 15:26:08",
                              "ses_request_id": "",
                              "campaign_id": 1,
                              "candidate_id": 11,
                              "is_ses_complaint": false,
                              "id": 114,
                              "sent_datetime": "2016-02-29 15:41:38"
                            },
                            {
                              "ses_message_id": "",
                              "is_ses_bounce": false,
                              "updated_datetime": "2016-02-29 15:26:08",
                              "ses_request_id": "",
                              "campaign_id": 1,
                              "candidate_id": 1,
                              "is_ses_complaint": false,
                              "id": 115,
                              "sent_datetime": "2016-02-29 15:41:38"
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
        raise_if_dict_values_are_not_int_or_long(dict(campaign_id=campaign_id))
        # Get a campaign that was created by this user
        campaign = EmailCampaignBase.get_campaign_if_domain_is_valid(campaign_id, request.user)
        # get paginated response
        page, per_page = get_pagination_params(request, error_code=INVALID_VALUE_OF_PAGINATION_PARAM[1])
        return get_paginated_response('sends', campaign.sends, page, per_page)


@api.route(EmailCampaignApi.SEND_BY_ID)
class EmailCampaignSendById(Resource):
    """
    Endpoint looks like /v1/email-campaigns/:id/sends/:id.
    This resource returns a send object for given send_id associated with given campaign.
    """
    decorators = [require_oauth()]

    def get(self, campaign_id, send_id):
        """
        This endpoint returns a send object for a given campaign_id and send_id.
        :param campaign_id: int, unique id of a email campaign
        :param send_id: id of send object
        :type campaign_id: int | long
        :type send_id: int | long
        :return: JSON data containing dict of send object

        :Example:

        >>> import requests
        >>> headers = {'Authorization': 'Bearer <access_token>'}
        >>> campaign_id = 1
        >>> send_id = 1
        >>> response = requests.get(EmailCampaignApiUrl.SEND_BY_ID % (campaign_id, send_id),
        >>>                         headers=headers)

        .. Response::

               {
                  "send": {
                                "ses_message_id": "",
                                "is_ses_bounce": false,
                                "updated_datetime": "2016-02-29 15:26:08",
                                "ses_request_id": "",
                                "campaign_id": 1,
                                "candidate_id": 11,
                                "is_ses_complaint": false,
                                "id": 114,
                                "sent_datetime": "2016-02-29 15:41:38"
                              }
                }
        .. Status:: 200 (OK)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Requested campaign does not belong to user's domain or requested send
                        object is not associated with given campaign id)
                    404 (Campaign not found or send object with given id not found)
                    500 (Internal server error)
        """
        # Get valid send object
        send_obj = get_valid_send_obj(campaign_id, send_id, request.user)
        return dict(send=send_obj.to_json()), codes.OK


@api.route(EmailCampaignApi.INVITATION_STATUS)
class InvitationStatus(Resource):
    """
    This returns invitation status of candidate for given campaign.
    """
    # Access token decorator
    decorators = [require_oauth()]

    def get(self, email_campaign_id, candidate_id):
        """
        This returns invitation status of candidate for given campaign.
        Invitations statuses are as:
            Delivered: Candidate has received the email-campaign
            Not-Delivered: Candidate has not received the email-campaign
            Opened: Candidate has opened the email-campaign
            Accepted: Candidate RSVP'd YES to the promoted event
            Rejected: Candidate RSVP'd NO to the promoted event
        """
        user = request.user
        email_campaign_send_id = None
        invitation_status = INVITATION_STATUSES['Not-Delivered']
        email_campaign = EmailCampaignBase.get_campaign_if_domain_is_valid(email_campaign_id, request.user)
        # Check if candidate has received the email-campaign
        for send in email_campaign.sends.all():
            if candidate_id == send.candidate_id:
                invitation_status = INVITATION_STATUSES['Delivered']
                email_campaign_send_id = send.id
                break
        # Check if candidate has opened the email-campaign
        for activity_type in (Activity.MessageIds.CAMPAIGN_EMAIL_OPEN, Activity.MessageIds.CAMPAIGN_EMAIL_CLICK):
            url = "{}?type={}&source_id={}&source_table={}".format(ActivityApiUrl.ACTIVITIES, activity_type,
                                                                   email_campaign_send_id,
                                                                   EmailCampaignSend.__tablename__)
            response = send_request('get', url, request.headers['Authorization'])
            if response.ok:
                invitation_status = INVITATION_STATUSES['Opened']
        if email_campaign.base_campaign_id:
            base_campaign = BaseCampaign.search_by_id_in_domain(email_campaign.base_campaign_id, user.domain_id)
            base_campaign_events = base_campaign.base_campaign_events.all()
            if base_campaign_events:
                event = base_campaign_events[0].event
                rsvp_in_db = RSVP.filter_by_keywords(candidate_id=candidate_id, event_id=event.id)
                if rsvp_in_db and rsvp_in_db[0].status.lower() == 'yes':
                    invitation_status = INVITATION_STATUSES['Accepted']
                elif rsvp_in_db and rsvp_in_db[0].status.lower() == 'no':
                    invitation_status = INVITATION_STATUSES['Rejected']
        return dict(invitation_status=invitation_status), codes.OK
