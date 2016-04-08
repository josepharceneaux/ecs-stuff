"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>
        Zohaib Ijaz, QC-Technologies, <mzohaib.qc@gmail.com>
"""
# TODO--In the top comment kindly explain what this file is and what it contains briefly
# Standard imports
import json

# 3rd party imports
import requests
from flask import request
from boto.exception import BotoServerError

# App specific imports
from apis.email_campaigns import email_campaign_blueprint
from apis.email_templates import template_blueprint
from email_campaign_service.email_campaign_app import app, logger
from email_campaign_service.modules.email_marketing import handle_email_bounce

# Register API endpoints
app.register_blueprint(email_campaign_blueprint)
app.register_blueprint(template_blueprint)

# TODO--rename the method to amazon_ses_bounces()
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
    """
    # TODO--Make a wiki article and point that here in the comment
    data = json.loads(request.data)
    # TODO--make "SubscriptionConfirmation" a constant instead of a magic constant
    if request.headers['X_AMZ_SNS_MESSAGE_TYPE'] == 'SubscriptionConfirmation':
        try:
            response = requests.get(data['SubscribeURL'])
            # TODO--I heard we don't need to do asserts in our code?
            assert data['TopicArn'] in response.text, 'Could not verify topic subscription'
        # TODO--How will the above code throw a BotoServerError--kindly double check
        except BotoServerError as e:
            logger.error('ses_bounces: Error occurred while verifying SNS subscription. Error: %s' % str(e))
    # TODO--make 'Notification' a constant. Also, please comment why do we have both SubscriptionConfirmation and 'Notification'
    elif request.headers['X_AMZ_SNS_MESSAGE_TYPE'] == 'Notification':
        data = json.loads(request.data)
        message = data['Message']
        message = json.loads(message)
        # TODO--remove the print please
        print(message)
        # TODO -- please put 'Bounce' in a constant somewhere, may be in some place central
        if message['notificationType'] == 'Bounce':
            handle_email_bounce(request, message)
            # TODO--Put 'Compliant' in some place central
        elif message['notificationType'] == 'Complaint':
            pass   # TODO: Add implementation for complaints

    return 'Thanks SNS for notification'
