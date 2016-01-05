"""
    Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains sms_campaign_app startup.
    We register blueprints for different APIs with this app.

    This app contains endpoints for
        1- URL redirection (to redirect candidate to our app when he clicks on URL present
                            in SMS body text)
            /v1/campaigns/:id/redirect/:id?candidate_id=id

        2- SMS receive (to save the candidate's reply to a specific SMS campaign

            /v1/receive
"""

# Initializing App. This line should come before any imports from models
from sms_campaign_service.sms_campaign_app import init_sms_campaign_app_and_celery_app
app, celery_app = init_sms_campaign_app_and_celery_app()


# Third Party Imports
from flask import request
from flask.ext.cors import CORS

# Application specific Imports
from sms_campaign_service.sms_campaign_app import logger
from sms_campaign_service.sms_campaign_base import SmsCampaignBase

# Common utils
from sms_campaign_service.common.routes import SmsCampaignApi

# Imports for Blueprints
from api.v1_sms_campaign_api import sms_campaign_blueprint

# Register Blueprints for different APIs
app.register_blueprint(sms_campaign_blueprint)

# Enable CORS
CORS(app, resources={
    r'/*': {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})


@app.route('/')
def root():
    return 'Welcome to SMS Campaign Service'


@app.route(SmsCampaignApi.RECEIVE, methods=['POST'])
def sms_receive():
    """
    This end point is is /receive and is used by Twilio to notify getTalent when a candidate
     replies to an SMS.

    - Recruiters(users) are assigned to one unique Twilio number. That number is configured with
     "sms_callback_url" which redirect the request at this end point with following data:

                {
                      "From": "+12015617985",
                      "To": "+15039255479",
                      "Body": "Dear all, we have few openings at http://www.qc-technologies.com",
                      "SmsStatus": "received",
                      "FromCity": "FELTON",
                      "FromCountry": "US",
                      "FromZip": "95018",
                      "ToCity": "SHERWOOD",
                      "ToCountry": "US",
                      "ToZip": "97132",
                 }

     So whenever someone replies to that particular recruiter's SMS (from within getTalent), this
     endpoint is hit and we do the following:

            1- Search the candidate in GT database using "From" key
            2- Search the user in GT database using "To" key
            3- Stores the candidate's reply in database table "sms_campaign_reply"
            4- Create activity that 'abc' candidate has replied "Body"(key)
                on 'xyz' SMS campaign.

    :return: XML response to Twilio API
    """
    if request.values:
        try:
            logger.debug('SMS received from %(From)s on %(To)s.\n '
                         'Body text is "%(Body)s"' % request.values)
            SmsCampaignBase.process_candidate_reply(request.values)
        except Exception as error:
            logger.exception("sms_receive: Error is: %s" % error.message)
    # So in the end we need to send properly formatted XML response back to Twilio
    return """
        <?xml version="1.0" encoding="UTF-8"?>
            <Response>
            </Response>
            """

# TODO: Verify send/receive SMS to/from with actual US or CANADA number
# @app.route('/send_sms')
# def send_sms():
#     twilio_obj = TwilioSMS()
#     twilio_obj.send_sms(sender_phone='+18312221043',
#                         # receiver_phone='+44183488260',
#                         receiver_phone='+15039255479',
#                         body_text='Testing Sender"s random number')
#     return "SMS Sent"
