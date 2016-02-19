"""File contains APIs for email campaign.
EmailCampaign is a restful resource and the endpoint which is sending out emails which is called by scheduler API is
using blueprint.
"""
import json
from flask import request, Blueprint, jsonify
from flask_restful import Resource
from werkzeug.utils import redirect
from ...email_campaign_app import logger
from email_campaign_service.common.campaign_services.campaign_base import CampaignBase
from ...modules.email_marketing import (create_email_campaign, send_emails_to_campaign, update_hit_count)
from ...modules.validations import validate_and_format_request_data
from email_campaign_service.common.error_handling import InvalidUsage, NotFoundError, ForbiddenError
from email_campaign_service.common.utils.auth_utils import require_oauth
from email_campaign_service.common.models.email_campaign import EmailCampaign
from email_campaign_service.common.models.misc import UrlConversion
from email_campaign_service.common.talent_api import TalentApi
from email_campaign_service.common.routes import EmailCampaignEndpoints
from email_campaign_service.common.campaign_services.validators import raise_if_dict_values_are_not_int_or_long

email_campaign_blueprint = Blueprint('email_campaign_api', __name__)


class EmailCampaignApi(Resource):

    # Access token decorator
    decorators = [require_oauth()]

    def get(self, **kwargs):
        """
        GET /email-campaigns/<id>          Fetch email campaign object
        GET /email-campaigns               Fetches all email campaign objects from auth user's domain

        """
        user = request.user
        email_campaign_id = kwargs.get('id')
        if email_campaign_id:
            email_campaign = EmailCampaign.query.get(email_campaign_id)
            """:type : email_campaign_service.common.models.email_campaign.EmailCampaign"""

            if not email_campaign:
                raise NotFoundError("Email campaign with id: %s does not exists" % email_campaign_id)
            if not email_campaign.user.domain_id == user.domain_id:
                raise ForbiddenError("Email campaign doesn't belongs to user's domain")
            email_campaign_object = email_campaign.to_dict()
            return {"email_campaign": email_campaign_object}
        else:
            # Get all email campaigns from logged in user's domain
            email_campaigns = EmailCampaign.query.filter(EmailCampaign.user_id == user.id)
            return {"email_campaigns": [email_campaign.to_dict() for email_campaign in email_campaigns]}

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


api = TalentApi(email_campaign_blueprint)
api.add_resource(EmailCampaignApi, EmailCampaignEndpoints.CAMPAIGN, EmailCampaignEndpoints.CAMPAIGNS)
api.add_resource(EmailCampaignSendApi, EmailCampaignEndpoints.SEND)
