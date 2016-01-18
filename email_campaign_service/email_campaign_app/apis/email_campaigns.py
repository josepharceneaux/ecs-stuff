import json
from flask import request, Blueprint, redirect
from flask_restful import Resource
from ...modules.email_marketing import (create_email_campaign, send_emails_to_campaign, update_hit_count, get_email_campaign_object)
from ...modules.validations import validate_and_format_request_data
from email_campaign_service.common.error_handling import InvalidUsage, NotFoundError, ForbiddenError
from email_campaign_service.common.utils.auth_utils import require_oauth
from email_campaign_service.common.models.email_marketing import EmailCampaign, UrlConversion
from email_campaign_service.common.talent_api import TalentApi
from email_campaign_service.common.routes import EmailCampaignEndpoints
from ...email_campaign_app import logger

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
            if not email_campaign:
                raise NotFoundError("Email campaign with id: %s does not exists")
            if not email_campaign.user.domain_id == user.domain_id:
                raise ForbiddenError("Email campaign doesn't belongs to user's domain")
            email_campaign_object = get_email_campaign_object(email_campaign)
            return {"email_campaign": email_campaign_object}
        else:
            # Get all email campaigns from logged in user's domain
            email_campaigns = EmailCampaign.query.filter(EmailCampaign.user_id == user.id)
            return {"email_campaigns": [get_email_campaign_object(email_campaign)
                                        for email_campaign in email_campaigns]}

    def post(self):
        user_id = request.user.id
        # Get and validate request data
        data = request.get_json(silent=True)
        if not data:
            raise InvalidUsage("Received empty request body")
        data = validate_and_format_request_data(data, user_id)

        campaign_id = create_email_campaign(user_id=user_id,
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
                                            frequency=data['frequency'])

        return {'campaign': {'id': campaign_id}}


@email_campaign_blueprint.route(EmailCampaignEndpoints.SEND_CAMPAIGN, methods=['POST'])
@require_oauth(allow_jwt_based_auth=True, allow_null_user=True)
def send_campaign_emails(campaign_id):
    """
    Sends campaign emails to the candidates present in smartlists of campaign.
    Scheduler service will call this to send emails to candidates.
    :param campaign_id: Campaign id
    """
    campaign = EmailCampaign.query.get(campaign_id)
    if not campaign:
        logger.exception("Given campaign_id: %s does not exists." % campaign_id)
        raise NotFoundError("Given `campaign_id` does not exists")
    # remove oauth_token instead use trusted server to server calls
    oauth_token = request.oauth_token
    email_send = send_emails_to_campaign(oauth_token, campaign, new_candidates_only=False)
    data = json.dumps({'campaign': {'emails_send': email_send}})
    return data


@email_campaign_blueprint.route(EmailCampaignEndpoints.URL_REDIRECT, methods=['GET'])
def url_redirect(url_conversion_id):
    # TODO: Add verification, once SMS campaign code is merged, it is already implemented.
    # if not URL.verify(request, hmac_key=HMAC_KEY):
    #     raise HTTP(403)

    url_conversion = UrlConversion.query.get(url_conversion_id)
    if not url_conversion:
        logger.exception('No record of url_conversion found for id: %s' % url_conversion_id)
        return
    # Update hitcount
    update_hit_count(url_conversion)
    # response.title = "getTalent.com: Redirecting to %s" % url_conversion.destinationUrl
    destination_url = url_conversion.destination_url
    if destination_url.lower().startswith("www."):
        destination_url = "http://" + destination_url

    if destination_url == '#':
        # redirect(HOST_NAME + str(URL(a='web', c='dashboard', f='index')))
        # TODO: redirect to dashboard url?
        # redirect('/')
        destination_url = 'gettalent.com'
    # else:
    redirect(destination_url)
    #return json.dumps({'redirect_url': destination_url})


api = TalentApi(email_campaign_blueprint)
api.add_resource(EmailCampaignApi, EmailCampaignEndpoints.EMAIL_CAMPAIGN, EmailCampaignEndpoints.EMAIL_CAMPAIGNS)
