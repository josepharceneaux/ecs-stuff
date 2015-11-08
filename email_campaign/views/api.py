from flask import Blueprint
from flask import current_app as app
from flask import request
from flask import jsonify
from flask.ext.cors import CORS
from ..modules.email_marketing import create_email_campaign, validate_lists_belongs_to_domain
import json
from common.error_handling import UnprocessableEntity, ForbiddenError

__author__ = 'jitesh'

mod = Blueprint('email_campaign', __name__)


@mod.route('/', methods=['POST'])
def email_campaigns():
    # TODO: Authentication
    user_id = 1
    # Get post data
    campaign_name = request.form.get('email_campaign_name')
    email_subject = request.form.get('email_subject')
    email_from = request.form.get('email_from')
    reply_to = request.form.get('email_reply_to')
    email_body_html = request.form.get('email_body_html')
    email_body_text = request.form.get('email_body_text')
    list_ids = request.form.get('list_ids')
    email_client_id = request.form.get('email_client_id')
    send_time = request.form.get('send_time')
    frequency = request.form.get('frequency')
    if email_client_id:
        template_id = None
    else:
        template_id = request.form.get('selected_template_id')

    # TODO: Add validations on missing inputs
    # TODO: Add validation for list id belonging to same domain
    if validate_lists_belongs_to_domain(list_ids, user_id):
        return ForbiddenError("Provided list does not belong to user's domain")

    resp_dict = create_email_campaign(user_id=user_id,
                                      email_campaign_name=campaign_name,
                                      email_subject=email_subject,
                                      email_from=email_from,
                                      email_reply_to=reply_to,
                                      email_body_html=email_body_html,
                                      email_body_text=email_body_text,
                                      list_ids=list_ids,
                                      email_client_id=email_client_id,
                                      template_id=template_id,
                                      send_time=send_time,
                                      frequency=frequency)
    print 'inserted into database, id is %s' % resp_dict

    return "Success. Your name is %s, and subject is %s \n" % (campaign_name, email_subject)


@mod.errorhandler(UnprocessableEntity)
def handle_invalid_usage(error):
    response = json.dumps(error.to_dict())
    # response.status_code = error.status_code TODO check why this is not working
    return response
