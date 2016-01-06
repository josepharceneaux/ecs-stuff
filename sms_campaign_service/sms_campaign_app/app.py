"""
    Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains sms_campaign_app startup.
    We register blueprints for different APIs with this app.
"""

# Third Party Imports

from flask.ext.cors import CORS

# Imports for Blueprints
from api.v1_sms_campaign_api import sms_campaign_blueprint

# Register Blueprints for different APIs
from sms_campaign_service.sms_campaign_app import app
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


# TODO: Verify send/receive SMS to/from with actual US or CANADA number
# @app.route('/send_sms')
# def send_sms():
#     twilio_obj = TwilioSMS()
#     twilio_obj.send_sms(sender_phone='+18312221043',
#                         # receiver_phone='+44183488260',
#                         receiver_phone='+15039255479',
#                         body_text='Testing Sender"s random number')
#     return "SMS Sent"
