from flask import request, Blueprint
from flask_restful import Resource
from ...modules.email_marketing import create_email_campaign, send_emails_to_campaign
from ...modules.validations import validate_and_format_request_data
from email_campaign_service.common.error_handling import InvalidUsage, NotFoundError
from email_campaign_service.common.utils.auth_utils import require_oauth
from email_campaign_service.common.utils.validators import is_number
from email_campaign_service.common.models.email_marketing import EmailCampaign
from email_campaign_service.common.talent_api import TalentApi
from email_campaign_service.common.routes import EmailCampaignEndpoints

email_campaign_blueprint = Blueprint('email_campaign_api', __name__)


class EmailCampaignApi(Resource):

    # Access token decorator
    decorators = [require_oauth()]

    def get(self, **kwargs):
        """
        GET /email-campaigns/<id>          Fetch email campaign object
        GET /email-campaigns               Fetches all email campaign objects from auth user's domain

        """
        pass

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

        return {'campaign': campaign_id}


@email_campaign_blueprint.route(EmailCampaignEndpoints.SEND_CAMPAIGNS, methods=['POST'])
@require_oauth(allow_jwt_based_auth=True, allow_null_user=True)
def send_campaign_emails():
    """
    Sends campaign emails to the candidates present in smartlists of campaign.
    Scheduler service will call this and to send emails to candidates.
    """
    data = request.get_json(silent=True)
    if not data:
        raise InvalidUsage("Received empty request body")
    campaign_id = data.get('campaign_id')
    if not campaign_id:
        raise InvalidUsage("`campaign_id` is required")
    if not is_number(campaign_id):
        raise InvalidUsage("`campaign_id` is expected to be a numeric value")
    campaign = EmailCampaign.query.get(campaign_id)
    if not campaign:
        raise NotFoundError("Given `campaign_id` does not exists")
    # remove oauth_token instead use trusted server to server calls
    oauth_token = request.oauth_token
    email_send = send_emails_to_campaign(oauth_token, campaign, new_candidates_only=False)
    # json.dumps({'campaign': {'emails_send': email_send}})
    return '', 204


api = TalentApi(email_campaign_blueprint)
api.add_resource(EmailCampaignApi, EmailCampaignEndpoints.EMAIL_CAMPAIGN, EmailCampaignEndpoints.EMAIL_CAMPAIGNS)
