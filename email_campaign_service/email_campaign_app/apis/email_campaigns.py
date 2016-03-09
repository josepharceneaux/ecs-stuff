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

# Third Party
import types
from flask_restful import Resource
from werkzeug.utils import redirect
from flask import request, Blueprint, jsonify

# Service Specific
from email_campaign_service.email_campaign_app import logger
from email_campaign_service.modules.utils import get_valid_send_obj
from email_campaign_service.modules.email_marketing import (create_email_campaign,
                                                            send_emails_to_campaign,
                                                            update_hit_count)
from email_campaign_service.modules.validations import validate_and_format_request_data

# Common utils
from email_campaign_service.common.talent_api import TalentApi
from email_campaign_service.common.routes import EmailCampaignUrl
from email_campaign_service.common.models.misc import UrlConversion
from email_campaign_service.common.routes import EmailCampaignEndpoints
from email_campaign_service.common.utils.auth_utils import require_oauth
from email_campaign_service.common.models.email_campaign import EmailCampaign
from email_campaign_service.common.error_handling import (InvalidUsage, NotFoundError,
                                                          ForbiddenError)
from email_campaign_service.common.campaign_services.campaign_base import CampaignBase
from email_campaign_service.common.utils.api_utils import (api_route, get_paginated_response,
                                                           get_pagination_params)
from email_campaign_service.common.campaign_services.campaign_utils import CampaignUtils
from email_campaign_service.common.campaign_services.validators import \
    raise_if_dict_values_are_not_int_or_long


# Blueprint for email-campaign API
email_campaign_blueprint = Blueprint('email_campaign_api', __name__)
api = TalentApi()
api.init_app(email_campaign_blueprint)
api.route = types.MethodType(api_route, api)


@api.route(EmailCampaignEndpoints.CAMPAIGNS, EmailCampaignEndpoints.CAMPAIGN)
class EmailCampaignApi(Resource):

    # Access token decorator
    decorators = [require_oauth()]

    def get(self, **kwargs):
        """
        GET /v1/email-campaigns/<id>    Fetch email campaign object
        GET /v1/email-campaigns         Fetches all email campaign objects from auth user's domain

        """
        user = request.user
        email_campaign_id = kwargs.get('id')
        include_fields = request.values['fields'].split(',') if request.values.get('fields') else None
        if email_campaign_id:
            email_campaign = EmailCampaign.get_by_id(email_campaign_id)
            """:type : email_campaign_service.common.models.email_campaign.EmailCampaign"""

            if not email_campaign:
                raise NotFoundError("Email campaign with id: %s does not exist"
                                    % email_campaign_id)
            if not email_campaign.user.domain_id == user.domain_id:
                raise ForbiddenError("Email campaign doesn't belongs to user's domain")
            return {"email_campaign": email_campaign.to_dict(include_fields=include_fields)}
        else:
            page, per_page = get_pagination_params(request)
            # Get all email campaigns from logged in user's domain
            query = EmailCampaign.get_by_domain_id(user.domain_id)
            return get_paginated_response('email_campaigns', query, page, per_page,
                                          object_method=EmailCampaign.to_dict)

    def post(self):
        """
            POST /v1/email-campaigns
            Required parameters:
            name: Name of email campaign
            subject: subject of email
            body_html: email body
            list_ids: smartlist ids to which emails will be sent
        """
        user_id = request.user.id
        # Get and validate request data
        data = request.get_json(silent=True)
        if not data:
            raise InvalidUsage("Received empty request body")
        data = validate_and_format_request_data(data, user_id)

        campaign = create_email_campaign(user_id=user_id,
                                         oauth_token=request.oauth_token,
                                         name=data['name'],
                                         subject=data['subject'],
                                         _from=data['from'],
                                         reply_to=data['reply_to'],
                                         body_html=data['body_html'],
                                         body_text=data['body_text'],
                                         list_ids=data['list_ids'],
                                         email_client_id=data['email_client_id'],
                                         template_id=data['template_id'],
                                         start_datetime=data['start_datetime'],
                                         end_datetime=data['end_datetime'],
                                         frequency_id=data['frequency_id'])

        return {'campaign': campaign}, 201


@api.route(EmailCampaignEndpoints.SEND)
class EmailCampaignSendApi(Resource):
    """
    This endpoint looks like /v1/email-campaigns/:id/send
    """

    decorators = [require_oauth()]

    def post(self, campaign_id):
        """
        Sends campaign emails to the candidates present in smartlists of campaign.
        Scheduler service will call this to send emails to candidates.
        :param campaign_id: Campaign id
        """
        raise_if_dict_values_are_not_int_or_long(dict(campaign_id=campaign_id))
        campaign = EmailCampaign.query.get(campaign_id)
        if not campaign:
            raise NotFoundError("Given campaign_id: %s does not exists." % campaign_id)

        if not campaign.user.domain_id == request.user.domain_id:
            raise ForbiddenError("Email campaign doesn't belongs to user's domain")
        results_send = send_emails_to_campaign(campaign, new_candidates_only=False)
        if campaign.email_client_id:
            if not isinstance(results_send, list):
                raise InvalidUsage(error_message="Something went wrong, response is not list")
            data = {
                'email_campaign_sends': [
                    {
                        'email_campaign_id': campaign.id,
                        'new_html': new_email_html_or_text.get('new_html'),
                        'new_text': new_email_html_or_text.get('new_text'),
                        'candidate_email_address': new_email_html_or_text.get('email')
                    } for new_email_html_or_text in results_send
                ]
            }
            return jsonify(data)

        return dict(message='email_campaign(id:%s) is being sent to candidates.'
                            % campaign_id), 200


@api.route(EmailCampaignEndpoints.URL_REDIRECT)
class EmailCampaignUrlRedirect(Resource):
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
            logger.error('No record of url_conversion found for id: %s' % url_conversion_id)
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


@api.route(EmailCampaignEndpoints.BLASTS)
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
        >>> response = requests.get(EmailCampaignUrl.BLASTS % campaign_id, headers=headers)

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
        # Get a campaign that was created by this user
        campaign = CampaignBase.get_campaign_if_domain_is_valid(campaign_id, request.user,
                                                                CampaignUtils.EMAIL)
        # get paginated response
        page, per_page = get_pagination_params(request)
        return get_paginated_response('blasts', campaign.blasts, page, per_page)


@api.route(EmailCampaignEndpoints.BLAST)
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
        >>> response = requests.get(EmailCampaignUrl.BLAST % (campaign_id, blast_id),
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
        blast_obj = CampaignBase.get_valid_blast_obj(campaign_id, blast_id,
                                                     request.user,
                                                     CampaignUtils.EMAIL)
        return dict(blast=blast_obj.to_json()), 200


@api.route(EmailCampaignEndpoints.SENDS)
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
        >>> response = requests.get(EmailCampaignUrl.SENDS % campaign_id, headers=headers)

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
        # Get a campaign that was created by this user
        campaign = CampaignBase.get_campaign_if_domain_is_valid(campaign_id, request.user,
                                                                CampaignUtils.EMAIL)
        # get paginated response
        page, per_page = get_pagination_params(request)
        return get_paginated_response('sends', campaign.sends, page, per_page)


@api.route(EmailCampaignEndpoints.SEND_BY_ID)
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
        >>> response = requests.get(EmailCampaignUrl.SEND_BY_ID % (campaign_id, send_id),
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
        raise_if_dict_values_are_not_int_or_long(dict(campaign_id=campaign_id,
                                                      send_id=send_id))
        # Get valid send object
        send_obj = get_valid_send_obj(campaign_id, send_id, request.user,
                                      CampaignUtils.EMAIL)
        return dict(send=send_obj.to_json()), 200
