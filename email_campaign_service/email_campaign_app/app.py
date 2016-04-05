from boto.exception import BotoServerError

from email_campaign_service.common.talent_config_manager import TalentConfigKeys

__author__ = 'basit'

import json
import requests
from flask import request
from pprint import pprint
from apis.email_campaigns import email_campaign_blueprint
from apis.email_templates import template_blueprint
from email_campaign_service.email_campaign_app import app, logger
from email_campaign_service.common.models.email_campaign import EmailCampaignSend
from email_campaign_service.common.models.candidate import CandidateEmail
from email_campaign_service.common.error_handling import InternalServerError


# Register API endpoints
app.register_blueprint(email_campaign_blueprint)
app.register_blueprint(template_blueprint)

AWS_ACCESS_KEY_ID = app.config[TalentConfigKeys.ENV_KEY]
AWS_SECRET_ACCESS_KEY = app.config[TalentConfigKeys.ENV_KEY]


@app.route('/amazon_sns_endpoint', methods=['GET', 'POST'])
def ses_bounces():
    # return 'Great'
    print 'Bounce detected'
    data = json.loads(request.data)
    if request.headers['X_AMZ_SNS_MESSAGE_TYPE'] == 'SubscriptionConfirmation':
        try:
            response = requests.get(data['SubscribeURL'])
            assert data['TopicArn'] in response.text, 'Could not verify topic subscription'
        except BotoServerError as e:
            logger.error('ses_bounces: Error occurred while  SNS subscription. Error: %s' % str(e))
    elif request.headers['X_AMZ_SNS_MESSAGE_TYPE'] == 'Notification':
        data = json.loads(request.data)
        message = data['Message']
        message = json.loads(message)
        pprint(message)
        if message['notificationType'] == 'Bounce':
            message_id = message['mail']['messageId']
            bounce = message['bounce']
            bounce_type = bounce['bounceType']
            emails = [recipient['emailAddress'] for recipient in bounce['bouncedRecipients']]
            send_obj = EmailCampaignSend.get_by_ses_message_id(message_id)
            if not send_obj:
                logger.error('Unable to find email campaign for this email bounce: %s' % request.data)
                raise InternalServerError('Unable to find email campaign for this email bounce: %s' % request.data)
            send_obj.update(is_ses_bounce=True)
            blast = send_obj.blast
            blast.update(bounces=(blast.bounces + 1))
            query = CandidateEmail.query.filter(CandidateEmail.address.in_(emails))
            query.update(dict(is_bounced=1), synchronize_session=False)
            CandidateEmail.session.commit()
            logger.warn('Marked %s email addresses as bounced' % emails)
        elif message['notificationType'] == 'Complaint':
            pass   # TODO: Add implementation for complaints
    return 'Great'
