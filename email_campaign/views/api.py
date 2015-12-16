import json

from flask import Blueprint
from flask import current_app as app
from flask import request
from flask.ext.cors import CORS
from ..modules.email_marketing import create_email_campaign, send_emails_to_campaign
from ..modules.validations import validate_lists_belongs_to_domain, validate_and_format_request_data
from email_campaign.common.error_handling import ForbiddenError
from email_campaign.common.utils.auth_utils import require_oauth

__author__ = 'jitesh'

mod = Blueprint('email_campaign', __name__)

# Enable CORS
CORS(mod, resources={
    r'/email_campaign/*': {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})

@mod.route('/email_campaign', methods=['POST'])
@require_oauth
def email_campaigns():
    """Creates new email campaign
    Requires: Bearer token for Authorization in headers
    Input: (post data)
        email_campaign_name
        email_subject
        email_from: Name of email sender
        email_reply_to
        email_body_html
        email_body_text
        selectedTemplateId
        send_time
        frequency
        list_ids : One or more (comma separated) smartlist ids to which email campaign will be sent (Currently only supports dumblists)
    Returns: campaign id
    """
    user_id = request.user.id
    # Get and validate request data
    data = validate_and_format_request_data(request.form)

    if data['email_client_id']:
        template_id = None
    else:
        template_id = request.form.get('selected_template_id')
    # convert list_ids (unicode, separated by comma) to list
    list_ids = data['list_ids']
    if isinstance(list_ids, basestring):
        list_ids = [long(list_id) for list_id in list_ids.split(',')]
    # Validation for list ids belonging to same domain
    if not validate_lists_belongs_to_domain(list_ids, user_id):
        raise ForbiddenError("Provided list does not belong to user's domain")

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
                                        template_id=template_id,
                                        send_time=data['send_time'],
                                        stop_time=data['stop_time'],
                                        frequency=data['frequency'])

    app.logger.info('Email campaign created, campaign id is %s.' % campaign_id)

    return json.dumps({'campaign': campaign_id})


@mod.route('/send-campaign-emails', methods=['GET'])
def send_email_campaigns():
    campaign_id = request.args.get('campaign_id')
    oauth_token = request.args.get('oauth_token')
    email_send = send_emails_to_campaign(oauth_token, campaign_id, email_client_id=None, list_ids=None, new_candidates_only=False)
    return json.dumps({'campaign': {'emails send': email_send}})
