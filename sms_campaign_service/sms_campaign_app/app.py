"""
    This module contains sms_campaign_app startup.
    We register blueprints for different APIs with this app.

    This app contains endpoints for
        1- URL redirection (to redirect candidate to our app when he clicks on URL present
                            in sms body text)
        2- SMS receive (to save the candidate's reply to a specific SMS campaign
"""
__author__ = 'basit.gettalent@gmail.com'

# Initializing App. This line should come before any imports from models
from sms_campaign_service import init_app
app = init_app()

# Third Party Imports
import flask
from flask import request
from flask.ext.cors import CORS
from werkzeug.utils import redirect

# Application specific Imports
from sms_campaign_service import logger
from sms_campaign_service.utilities import TwilioSMS
from sms_campaign_service.sms_campaign_base import SmsCampaignBase
from sms_campaign_service.common.models.candidate import Candidate
from sms_campaign_service.custom_exceptions import MissingRequiredField
from sms_campaign_service.common.error_handling import ResourceNotFound
from sms_campaign_service.common.utils.common_functions import find_missing_items

# Imports for Blueprints
from restful_API.sms_campaign_api import sms_campaign_blueprint
from restful_API.url_conversion_api import url_conversion_blueprint

# Register Blueprints for different APIs
app.register_blueprint(sms_campaign_blueprint)
app.register_blueprint(url_conversion_blueprint)

# Enable CORS
CORS(app, resources={
    r'/*': {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})


@app.route('/')
def hello_world():
    return 'Welcome to SMS Campaign Service'


@app.route('/campaigns/<int:campaign_id>/url_redirection/<int:url_conversion_id>/', methods=['GET'])
def sms_campaign_url_redirection(campaign_id=None, url_conversion_id=None):
    """
    When recruiter(user) adds some url in sms body text, we save the original URL as
    destination URL in "url_conversion" database table. Then we create a new url (long_url) to
    redirect the candidate to our app. This long_url looks like

            http://127.0.0.1:8008/sms_campaign/2/url_redirection/67/?candidate_id=2

    For this we first convert this long_url in shorter URL (using Google's shorten URL API) and
    send in sms body text to candidate. This is the endpoint which redirect the candidate. Short
    URL looks like

            https://goo.gl/CazBJG

    When candidate clicks on above url, it is redirected to this endpoint, where we keep track
    of number of clicks and hit_counts for a URL. We then create activity that 'this' candidate
    has clicked on 'this' campaign. Finally we redirect the candidate to destination url (Original
    URL provided by the recruiter)

    .. Status:: 200 (OK)
                404 (Resource not found)
                500 (Internal Server Error)

    ., Error codes::
                5005 (EmptyDestinationUrl)
                5006 (MissingRequiredField)

    :param campaign_id: id of sms_campaign in db
    :param url_conversion_id: id of url_conversion record in db
    :type campaign_id: int
    :type url_conversion_id: int
    :return: redirects to the destination URL else raises exception
    """
    try:
        url_redirect_data = {'campaign_id': campaign_id,
                             'url_conversion_id': url_conversion_id,
                             'candidate_id': request.args.get('candidate_id')}
        missing_items = find_missing_items(url_redirect_data, verify_all_keys=True)
        if not missing_items:
            candidate = Candidate.get_by_id(request.args.get('candidate_id'))
            if candidate:
                user_id = candidate.user_id
                camp_obj = SmsCampaignBase(user_id, buy_new_number=False)
                redirection_url = camp_obj.process_url_redirect(campaign_id=campaign_id,
                                                                url_conversion_id=url_conversion_id,
                                                                candidate=candidate)
                return redirect(redirection_url)
            else:
                ResourceNotFound(error_message='Candidate(id:%s) not found.'
                                               % request.args.get('candidate_id'))
        else:
            raise MissingRequiredField(error_message='%s' % missing_items)
    except:
        logger.exception("Error occurred while URL redirection for SMS campaign.")
        data = {'message': 'Internal Server Error'}
        return flask.jsonify(**data), 500


@app.route("/sms_receive", methods=['POST'])
def sms_receive():
    """
    This end point is used to receive sms of candidates.

    - Recruiters(users) are assigned to one unique twilio number.sms_callback_url of
        that number is set to redirect request at this end point. Twilio API hits this url
        with data like
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

        So whenever candidate replies to user's sms (that was sent as sms campaign),
        this endpoint is hit and we do the followings:

            1- Search the candidate in GT database using "From" key value
            2- Search the user in GT database using "To" key value
            3- Stores the candidate's reply in database table "sms_campaign_reply"
            4- Create's activity that 'abc' candidate has replied "Body"(key value)
                on 'xyz' SMS campaign.

    .. Status:: 200 (OK)
                403 (ForbiddenError)
                404 (Resource not found)
                500 (Internal Server Error)

    .. Error codes:
                5006 (MissingRequiredField)
                5007 (MultipleUsersFound)
                5008 (MultipleCandidatesFound)

    :return: xml response to Twilio API
    """
    if request.values:
        try:
            logger.debug('SMS received from %(From)s on %(To)s.\n '
                         'Body text is "%(Body)s"' % request.values)
            SmsCampaignBase.process_candidate_reply(request.values)
        except Exception as error:
            logger.exception("sms_receive: Error is: %s" % error.message)
    return """
        <?xml version="1.0" encoding="UTF-8"?>
            <Response>
            </Response>
            """

# import twilio.twiml
# resp = twilio.twiml.Response()
# resp.message("Thank you for your response")
# return str(resp)
# <Message> Hello </Message>


# @app.route('/send_sms')
# def send_sms():
#     twilio_obj = TwilioSMS()
#     twilio_obj.send_sms(sender_phone='+18312221043',
#                         # receiver_phone='+44183488260',
#                         receiver_phone='+15039255479',
#                         body_text='Testing Sender"s random number')
#     return "SMS Sent"
