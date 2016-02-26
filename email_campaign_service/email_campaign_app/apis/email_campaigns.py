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

            GET    : Redirects the candidate to our app to keep track of number of clicks, hit_count
                    and create activity.

        - EmailCampaignBlasts:  /v1/email-campaigns/:id/blasts

            GET    : Gets the all the "blast" records for given email campaign id from db table
                    "email_campaign_blast"

        - EmailCampaignBlastById:  /v1/email-campaigns/:id/blasts/:id

            GET    : Gets the "blast" record for given email campaign id and blast_id from db table
                    "email_campaign_blast"

        - EmailCampaignBlastSends:  /v1/email-campaigns/:id/blasts/:id/sends

            GET    : Gets the "sends" records for given email campaign id and blast_id
                        from db table 'email_campaign_sends'.

        - EmailCampaignSends:  /v1/email-campaigns/:id/sends

            GET    : Gets all the "sends" records for given email campaign id
                        from db table email_campaign_sends
"""

# Third Party
import types
from flask_restful import Resource
from werkzeug.utils import redirect
from flask import request, Blueprint, jsonify

# Service Specific
from email_campaign_service.email_campaign_app import logger
from email_campaign_service.modules.email_marketing import (create_email_campaign,
                                                            send_emails_to_campaign,
                                                            update_hit_count)
from email_campaign_service.modules.validations import validate_and_format_request_data

# Common utils
from email_campaign_service.common.talent_api import TalentApi
from email_campaign_service.common.routes import EmailCampaignUrl
from email_campaign_service.common.models.misc import UrlConversion
from email_campaign_service.common.utils.api_utils import api_route
from email_campaign_service.common.routes import EmailCampaignEndpoints
from email_campaign_service.common.utils.auth_utils import require_oauth
from email_campaign_service.common.models.email_campaign import EmailCampaign
from email_campaign_service.common.campaign_services.campaign_base import CampaignBase
from email_campaign_service.common.error_handling import (InvalidUsage, NotFoundError,
                                                          ForbiddenError)
from email_campaign_service.common.campaign_services.validators import \
    raise_if_dict_values_are_not_int_or_long
from email_campaign_service.common.campaign_services.campaign_utils import CampaignUtils


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
        GET /email-campaigns/<id>    Fetch email campaign object
        GET /email-campaigns         Fetches all email campaign objects from auth user's domain

        """
        user = request.user
        email_campaign_id = kwargs.get('id')
        if email_campaign_id:
            email_campaign = EmailCampaign.query.get(email_campaign_id)
            """:type : email_campaign_service.common.models.email_campaign.EmailCampaign"""

            if not email_campaign:
                raise NotFoundError("Email campaign with id: %s does not exist"
                                    % email_campaign_id)
            if not email_campaign.user.domain_id == user.domain_id:
                raise ForbiddenError("Email campaign doesn't belongs to user's domain")
            email_campaign_object = email_campaign.to_dict()
            return {"email_campaign": email_campaign_object}
        else:
            # Get all email campaigns from logged in user's domain
            email_campaigns = EmailCampaign.query.filter(EmailCampaign.user_id == user.id)
            return {"email_campaigns": [email_campaign.to_dict()
                                        for email_campaign in email_campaigns]}

    def post(self):
        """
            POST /email-campaigns
            Required parameters:
            email_campaign_name: Name of email campaign
            email_subject: subject of email
            email_body_html: email body
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
                                         email_campaign_name=data['campaign_name'],
                                         email_subject=data['email_subject'],
                                         email_from=data['email_from'],
                                         email_reply_to=data['reply_to'],
                                         email_body_html=data['email_body_html'],
                                         email_body_text=data['email_body_text'],
                                         list_ids=data['list_ids'],
                                         email_client_id=data['email_client_id'],
                                         template_id=data['template_id'],
                                         send_time=data['send_datetime'],
                                         stop_time=data['stop_datetime'],
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


@email_campaign_blueprint.route(EmailCampaignEndpoints.URL_REDIRECT, methods=['GET'])
def url_redirect(url_conversion_id):
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
    if destination_url.lower().startswith("www."):
        destination_url = "http://" + destination_url

    if destination_url == '#':
        # redirect(HOST_NAME + str(URL(a='web', c='dashboard', f='index')))
        destination_url = 'http://www.gettalent.com/'  # Todo
    return redirect(destination_url)


@api.route(EmailCampaignEndpoints.BLASTS)
class EmailCampaignBlasts(Resource):
    """
    Endpoint looks like /v1/email-campaigns/:id/blasts.
    This class returns all the blast objects associated with given campaign.
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
        >>> blast_id = 1
        >>> response = requests.get(EmailCampaignUrl.BLASTS % campaign_id, headers=headers)

        .. Response::

           {
              "count": 2,
              "blasts": [
                            {
                              "sent_time": "2016-02-19 00:49:21",
                              "sends": 1,
                              "bounces": 0,
                              "updated_time": "2016-02-19 00:53:53",
                              "text_clicks": 0,
                              "email_campaign_id": 1230,
                              "html_clicks": 0,
                              "complaints": 0,
                              "id": 4811,
                              "opens": 1
                            },
                            {
                              "sent_time": "2016-02-19 00:50:24",
                              "sends": 1,
                              "bounces": 0,
                              "updated_time": "2016-02-19 00:50:27",
                              "text_clicks": 0,
                              "email_campaign_id": 1230,
                              "html_clicks": 0,
                              "complaints": 0,
                              "id": 4812,
                              "opens": 0
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
        # Serialize blasts of a campaign
        blasts = [blast.to_json() for blast in campaign.blasts]
        response = dict(blasts=blasts, count=len(blasts))
        return response, 200

