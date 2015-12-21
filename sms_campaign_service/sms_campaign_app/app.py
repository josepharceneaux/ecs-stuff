"""
    Author: Hafiz Muhammad Basit, QC-Technologies,
        Lahore, Punjab, Pakistan <basit.gettalent@gmail.com>

    This module contains sms_campaign_app startup.
    We register blueprints for different APIs with this app.

    This app contains endpoints for
        1- URL redirection (to redirect candidate to our app when he clicks on URL present
                            in sms body text)
            /v1/campaigns/:id/url_redirection/:id?candidate_id=id

        2- SMS receive (to save the candidate's reply to a specific SMS campaign

            /v1/receive
"""

# Initializing App. This line should come before any imports from models
from sms_campaign_service import init_sms_campaign_app_and_celery_app
from sms_campaign_service.common.routes import SmsCampaignApiUrl

app, celery_app = init_sms_campaign_app_and_celery_app()


# Third Party Imports
import flask
from flask import request
from flask.ext.cors import CORS
from werkzeug.utils import redirect

# Application specific Imports
from sms_campaign_service import logger
from sms_campaign_service.sms_campaign_base import SmsCampaignBase

# Imports for Blueprints
from restful_API.v1_sms_campaign_api import sms_campaign_blueprint
from restful_API.v1_url_conversion_api import url_conversion_blueprint

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
def root():
    return 'Welcome to SMS Campaign Service'


@app.route(SmsCampaignApiUrl.APP_REDIRECTION, methods=['GET'])
def sms_campaign_url_redirection(campaign_id, url_conversion_id):
    """
    When recruiter(user) adds some SMS in sms body text, we save the original URL as
    destination URL in "url_conversion" database table. Then we create a new url (long_url) to
    redirect the candidate to our app. This long_url looks like

            http://127.0.0.1:8008/sms_campaign/2/url_redirection/67/?candidate_id=2

    For this we first convert this long_url in shorter URL (using Google's shorten URL API) and
    send in sms body text to candidate. This is the endpoint which redirect the candidate. Short
    URL looks like

            https://goo.gl/CazBJG

    When candidate clicks on above url, it is redirected to this flask endpoint, where we keep track
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
    environ_header = request.headers.environ
    if ('HTTP_FROM' in request.headers.environ
        and 'google' in request.headers.environ['HTTP_FROM']) \
            or ('HTTP_REFERER' in request.headers.environ
                and 'google' in request.headers.environ['HTTP_REFERER']):
        data = {'message': "Successfully verified by Google's shorten URL API"}
        logger.info(data['message'])
        # Is there any need to jsonify? maybe we can send a simple dict
        return flask.jsonify(**data), 200
    try:

        campaign_in_db, url_conversion_in_db, candidate_in_db = \
            SmsCampaignBase.pre_process_url_redirect(campaign_id,
                                                     url_conversion_id,
                                                     request.args.get('candidate_id'))

        user_id = candidate_in_db.user_id
        camp_obj = SmsCampaignBase(user_id)
        redirection_url = camp_obj.process_url_redirect(campaign_in_db,
                                                        url_conversion_in_db,
                                                        candidate_in_db)
        return redirect(redirection_url)
    except Exception:
        logger.exception("Error occurred while URL redirection for SMS campaign.")
        data = {'message': 'Internal Server Error'}
        return flask.jsonify(**data), 500


@app.route(SmsCampaignApiUrl.RECEIVE, methods=['POST'])
def sms_receive():
    """
    This end point is used by Twilio to notify getTalent when a candidate
     replies to an SMS.

    - Recruiters(users) are assigned to one unique Twilio number and sms_callback_url (which is variable
     within Twilio to config blah TODO) of
        that number is set to redirect request at this end point. So whenever some one replies to that particular
        recruiter's SMS (from within getTalent) this endpoint will be hit.
        - It searches the candiddate in getTalent's database
        - It searches the user (i.e the recruiter) in getTalent's database
        -
        Twilio API hits this URL
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

        So whenever candidate replies to user's SMS (that was sent as SMS campaign),
        this endpoint is hit and we do the following:

            1- Search the candidate in GT database using "From" key
            2- Search the user in GT database using "To" key
            3- Stores the candidate's reply in database table "sms_campaign_reply"
            4- Creates activity that 'abc' candidate has replied "Body"(key)
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
