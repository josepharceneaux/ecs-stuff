"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>
        Zohaib Ijaz, QC-Technologies, <mzohaib.qc@gmail.com>

This module contains code to register api blueprints and there is one endpoint to subscribe
Amazon Simple Notification Service topic for email campaign bounces and complaints.
"""
# Standard imports
import json

# 3rd party imports
import requests
from flask import request

# App specific imports
from apis.email_campaigns import email_campaign_blueprint
from apis.email_templates import template_blueprint
from email_campaign_service.email_campaign_app import app, logger
from email_campaign_service.modules.utils import AWS_SNS_TERMS
from email_campaign_service.modules.email_marketing import handle_email_bounce

# Register API endpoints
app.register_blueprint(email_campaign_blueprint)
app.register_blueprint(template_blueprint)


@app.route('/amazon_sns_endpoint', methods=['POST'])
def ses_bounces():
    """
    This endpoint handles email bounces and complaints using Amazon Simple Email Service (SES)
     and Simple Notification Service (SNS).

     To get email bounces and complaints callback hits, we have to setup two SNS topics ,
     one for email bounces `email_bounces` and other one for email complains `email_complaints`.
     We have subscribed this HTTP endpoint (/amazon_sns_endpoint) for any notifications on `email_bounces` topic.
     When an email is bounced or someone complains about email, SES sends a JSON message with email
     information and cause of failure to our subscribed topics on SNS service which, in turn, sends an HTTP request to
     our subscribed endpoint with JSON message that can be processed to handle bounces and complaints.

     When a bounce occurs, we mark that email address as bounced and no further emails will be sent to this
     email address.

     Here is a wiki article explaining how to setup this.
     https://github.com/gettalent/talent-flask-services/wiki/Email-Bounces
    """
    data = json.loads(request.data)

    # SNS first sends a confirmation request to this endpoint, we then confirm our subscription by sending a
    # GET request to given url in subscription request body.
    if request.headers.get('X_AMZ_SNS_MESSAGE_TYPE') == AWS_SNS_TERMS.SUBSCRIPTION:
        response = requests.get(data['SubscribeURL'])
        if not data['TopicArn'] in response.text:
            logger.info('Could not verify topic subscription. TopicArn: %s, RequestData: %s' % (data['TopicArn'],
                                                                                                request.data))
    elif request.headers.get(AWS_SNS_TERMS.HEADER_KEY) == AWS_SNS_TERMS.NOTIFICATION:
        # In case of notification, check its type (bounce or complaint) and process accordingly.
        data = json.loads(request.data)
        message = data['Message']
        message = json.loads(message)
        if message['notificationType'] == AWS_SNS_TERMS.BOUNCE:
            handle_email_bounce(request, message)
        elif message['notificationType'] == AWS_SNS_TERMS.COMPLAINT:
            pass   # TODO: Add implementation for complaints

    return 'Thanks SNS for notification'
