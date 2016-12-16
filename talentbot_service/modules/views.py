"""
This module contains talentbot service's endpoints to receive webhook calls from
Facebook, Email, SMS and Slack
"""
# Common utils
from talentbot_service.common.error_handling import InvalidUsage
from talentbot_service.common.models.user import TalentbotAuth
from talentbot_service.common.routes import TalentBotApi
from talentbot_service.common.utils.api_utils import ApiResponse
from talentbot_service.common.utils.handy_functions import send_request
# Service specific
from talentbot_service.modules.email_bot import EmailBot
from talentbot_service.modules.sms_bot import SmsBot
from constants import TWILIO_NUMBER, ERROR_MESSAGE, STANDARD_MSG_LENGTH, QUESTIONS, BOT_NAME, BOT_IMAGE,\
    TWILIO_AUTH_TOKEN, TWILIO_ACCOUNT_SID, SLACK_AUTH_URI
from talentbot_service import app, logger
from talentbot_service.tasks import run_slack_communication_handler, run_facebook_communication_handler
# 3rd party imports
from flask import request
from urllib import quote
from slackclient import SlackClient

sms_bot = SmsBot(bot_name=BOT_NAME, error_messages=ERROR_MESSAGE,
                 standard_sms_length=STANDARD_MSG_LENGTH, twilio_account_sid=TWILIO_ACCOUNT_SID,
                 twilio_auth_token=TWILIO_AUTH_TOKEN, twilio_number=TWILIO_NUMBER, questions=QUESTIONS)
email_bot = EmailBot(QUESTIONS, BOT_NAME, BOT_IMAGE, ERROR_MESSAGE)


@app.route(TalentBotApi.HOME)
def index():
    """
    Just returns Add to Slack button for testing purpose
    :rtype: str
    """
    return '<a href="https://slack.com/oauth/authorize?scope=bot+users%3Aread+users%3Awrite+chat%3Awrite%3Abot&' \
           'client_id='+app.config["SLACK_APP_CLIENT_ID"]+'"><img alt="Add to Slack" height="40" width="139" ' \
           'src="https://platform.slack-edge.com/img/add_to_slack.png" srcset="https://platform.slack-edge.com/img/' \
           'add_to_slack.png 1x, https://platform.slack-edge.com/img/add_to_slack@2x.png 2x" /></a>'


@app.route(TalentBotApi.SLACK_LISTEN, methods=['POST'])
def listen_slack():
    """
    Listens to the slack callback and if it is a Slack event then processes it and extracts chanel_id,
    slack_user_id, timestamp, message and calls desired method in a thread.
    If it's not a Slack event then method considers the callback as a Slack callback authentication and returns
    the quoted challenge code if exists.
    :rtype: str
    """
    event = request.json.get('event')
    if event:
        current_timestamp = event.get('ts')
        channel_id = request.json.get('event').get('channel')
        slack_user_id = request.json.get('event').get('user')
        message = request.json.get('event').get('text')
        if message and channel_id and slack_user_id:
            logger.info("Message slack:%s, Current_timestamp: %s, Slack User ID: %s"
                        % (message, current_timestamp, slack_user_id))
            run_slack_communication_handler.delay(channel_id, message, slack_user_id, current_timestamp)
            return 'HTTP_200_OK'
    challenge = request.json.get('challenge')
    if challenge:
        if request.json.get('token') == app.config['SLACK_VERIFICATION_TOKEN']:
            return quote(challenge)
    return 'HTTP_200_OK'


@app.route(TalentBotApi.SMS_LISTEN, methods=['GET', 'POST'])
def handle_twilio_webhook():
    """
    Listens to the twilio callbacks
    :rtype: str
    """
    recipient = request.form.get('From')
    message_body = request.form.get('Body')
    if recipient and message_body:
        sms_bot.handle_communication(message_body, recipient)
    return 'HTTP_200_OK'


@app.route(TalentBotApi.EMAIL_LISTEN, methods=['POST'])
def receive_mail():
    """
    End point which listens mail gun callbacks
    :rtype: str
    """
    message = request.form.get('stripped-text')
    sender = request.form.get('sender')
    subject = request.form.get('subject')
    if message and sender:
        logger.info('Received email body: ' + message + ', Sender: ' + sender)
        email_bot.handle_communication(sender, subject, message)
    return 'HTTP_200_OK'


@app.route(TalentBotApi.FACEBOOK_LISTEN, methods=['GET'])
def handle_verification():
    """
    End point which handles facebook challenge code
    :rtype: str
    """
    challenge = request.args['hub.challenge']
    return quote(challenge)


@app.route(TalentBotApi.FACEBOOK_LISTEN, methods=['POST'])
def handle_incoming_messages():
    """
    End point to listen facebook web hooks
    :rtype: str
    """
    data = request.json
    sender = data['entry'][0]['messaging'][0]['sender']['id']
    msg = data['entry'][0]['messaging'][0].get('message')
    if msg and sender:
        message = data['entry'][0]['messaging'][0]['message']['text']
        run_facebook_communication_handler.delay(sender, message)
    return 'HTTP_200_OK'


@app.route(TalentBotApi.SLACK_AUTH, methods=['GET', 'POST'])
def get_new_user_credentials():
    """
    Receives user data when he installs talentbot on slack and saves in db
    :rtype: str
    """
    code = request.args.get('code')
    client_id = app.config['SLACK_APP_CLIENT_ID']
    client_secret = app.config['SLACK_APP_CLIENT_SECRET']
    response = send_request('POST', SLACK_AUTH_URI, access_token=None,
                            params={'client_id': client_id, 'client_secret': client_secret, 'code': code})
    json_result = response.json()
    if json_result.get('ok'):
        access_token = json_result['access_token']
        team_id = json_result['team_id']
        team_name = json_result['team_name']
        user_id = json_result['user_id']
        auth_entry = TalentbotAuth.query.filter_by(slack_user_id=user_id).first()
        bot_id = json_result['bot']['bot_user_id']
        bot_token = json_result['bot']['bot_access_token']

        if not auth_entry:

            talent_bot_auth = TalentbotAuth(slack_user_token=access_token, slack_team_id=team_id,
                                            slack_user_id=user_id, slack_team_name=team_name, bot_id=bot_id,
                                            bot_token=bot_token)
            talent_bot_auth.save()
            return "Your Slack credentials have been saved"
        auth_entry.slack_user_token = access_token
        auth_entry.bot_id = bot_id
        auth_entry.bot_token = bot_token
        TalentbotAuth.save(auth_entry)
        return "Your slack token has been updated"
    return "Your slack id already exists"


@app.route(TalentBotApi.SLACK_BOT_STATUS, methods=['POST'])
def set_bot_state_active():
    """
    Receives bot_token and perform an activity using that token to let Slack servers know
    that bot is online
    :rtype: json
    """
    bot_token = request.json.get('bot_token')
    if bot_token:
        print bot_token
        slack_client = SlackClient(bot_token)
        slack_client.rtm_connect()
        logger.info('Slack bot status online for token %s' % bot_token)
        return ApiResponse({"response": "OK"})
    raise InvalidUsage("No token found in request body")
