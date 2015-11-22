import json

from flask import Blueprint
from flask import current_app as app
from flask import request
from flask.ext.cors import CORS
from ..modules.email_marketing import create_email_campaign
from ..modules.validations import validate_lists_belongs_to_domain, validate_and_format_request_data
from email_campaign.common.error_handling import UnprocessableEntity, ForbiddenError
from email_campaign.common.utils.auth_utils import require_oauth

__author__ = 'jitesh'

mod = Blueprint('email_campaign', __name__)


@mod.route('/email_campaign', methods=['POST'])
@require_oauth
def email_campaigns():
    user_id = request.user.id  # 1553
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


@mod.errorhandler(UnprocessableEntity)
def handle_invalid_usage(error):
    response = json.dumps(error.to_dict())
    # response.status_code = error.status_code TODO check why this is not working
    return response
