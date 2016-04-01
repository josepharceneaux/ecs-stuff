from boto.exception import BotoServerError

from email_campaign_service.common.talent_config_manager import TalentConfigKeys

__author__ = 'basit'

import json
import boto
import requests
from flask import request
from apis.email_campaigns import email_campaign_blueprint
from apis.email_templates import template_blueprint
from email_campaign_service.email_campaign_app import app, logger

# Register API endpoints
app.register_blueprint(email_campaign_blueprint)
app.register_blueprint(template_blueprint)

AWS_ACCESS_KEY_ID = app.config[TalentConfigKeys.ENV_KEY]
AWS_SECRET_ACCESS_KEY = app.config[TalentConfigKeys.ENV_KEY]


@app.route('/amazon_sns_endpoint', methods=['GET', 'POST'])
def ses_bounces():
    print 'Bounce detected'
    data = json.loads(request.data)
    if request.headers['X_AMZ_SNS_MESSAGE_TYPE'] == 'SubscriptionConfirmation':
        try:
            response = requests.get(data['SubscribeURL'])
            assert data['TopicArn'] in response.text, 'Could not verify topic subscription'
        except BotoServerError as e:
            logger.error('ses_bounces: Error accured while  SNS subscription. Error: %s' % str(e))
    elif request.headers['X_AMZ_SNS_MESSAGE_TYPE'] == 'Notification':
        pass
    else:
        pass
    return 'Great'
