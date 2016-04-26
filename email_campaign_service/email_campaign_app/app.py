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
def amazon_sns_endpoint():
    """
    This endpoint handles email bounces and complaints using Amazon Simple Email Service (SES)
     and Simple Notification Service (SNS).

     To get email bounces and complaints callback hits, we have to setup two SNS topics,
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
    headers = request.headers

    logger.info('SNS Callback: Headers: %s\nRequest Data: %s', headers, data)

    # SNS first sends a confirmation request to this endpoint, we then confirm our subscription by sending a
    # GET request to given url in subscription request body.
    if request.headers.get(AWS_SNS_TERMS.HEADER_KEY) == AWS_SNS_TERMS.SUBSCRIBE:
        response = requests.get(data[AWS_SNS_TERMS.SUBSCRIBE_URL])
        if data[AWS_SNS_TERMS.TOPIC_ARN] not in response.text:
            logger.info('Could not verify topic subscription. TopicArn: %s, RequestData: %s',
                        data[AWS_SNS_TERMS.TOPIC_ARN], request.data)
            return 'Not verified', requests.codes.INTERNAL_SERVER_ERROR

        logger.info('Aws SNS topic subscription for email notifications was successful.'
                    '\nTopicArn: %s\nRequestData: %s', data[AWS_SNS_TERMS.TOPIC_ARN], request.data)

    elif request.headers.get(AWS_SNS_TERMS.HEADER_KEY) == AWS_SNS_TERMS.NOTIFICATION:
        # In case of notification, check its type (bounce or complaint) and process accordingly.
        data = json.loads(request.data)
        message = data[AWS_SNS_TERMS.MESSAGE]
        message = json.loads(message)
        message_id = message[AWS_SNS_TERMS.MAIL][AWS_SNS_TERMS.MESSAGE_ID]
        if message[AWS_SNS_TERMS.NOTIFICATION_TYPE] == AWS_SNS_TERMS.BOUNCE_NOTIFICATION:
            bounce = message[AWS_SNS_TERMS.BOUNCE]
            emails = [recipient[AWS_SNS_TERMS.EMAIL_ADDRESSES] for recipient in bounce[AWS_SNS_TERMS.BOUNCE_RECIPIENTS]]
            handle_email_bounce(message_id, bounce, emails)

        elif message[AWS_SNS_TERMS.NOTIFICATION_TYPE] == AWS_SNS_TERMS.COMPLAINT_NOTIFICATION:
            pass   # TODO: Add implementation for complaints

    elif request.headers.get(AWS_SNS_TERMS.HEADER_KEY) == AWS_SNS_TERMS.UNSUBSCRIBE:
        logger.info('SNS notifications for email campaign has been unsubscribed.'
                    '\nRequestData: %s', request.data)
    else:
        logger.info('Invalid request. Request data %s', request.data)

    return 'Thanks SNS for notification'
