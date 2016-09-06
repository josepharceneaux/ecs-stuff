# Common utils
from talentbot_service.common.talent_config_manager import TalentConfigKeys
# Service specific
from talentbot_service.modules.emailbot import EmailBot
from talentbot_service.modules.facebookbot import FacebookBot
from talentbot_service.modules.slackbot import SlackBot
from talentbot_service.modules.smsbot import SmsBot
# App specific
from constants import TWILIO_NUMBER, ERROR_MESSAGE, STANDARD_MSG_LENGTH, QUESTIONS, BOT_NAME, \
    MAILGUN_SENDING_ENDPOINT, BOT_IMAGE
from talentbot_service import app
# 3rd party imports
from flask import request

slack_bot = SlackBot(app.config[TalentConfigKeys.SLACK_BOT_TOKEN], QUESTIONS, BOT_NAME, ERROR_MESSAGE)
sms_bot = SmsBot(bot_name=BOT_NAME, error_messages=ERROR_MESSAGE, standard_sms_length=STANDARD_MSG_LENGTH,
                 twilio_account_sid=app.config[TalentConfigKeys.TWILIO_ACCOUNT_SID],
                 twilio_auth_token=app.config[TalentConfigKeys.TWILIO_AUTH_TOKEN],
                 twilio_number=TWILIO_NUMBER, questions=QUESTIONS)
email_bot = EmailBot(app.config[TalentConfigKeys.MAILGUN_API_KEY], MAILGUN_SENDING_ENDPOINT, QUESTIONS,
                     BOT_NAME, BOT_IMAGE, ERROR_MESSAGE)
facebook_bot = FacebookBot(QUESTIONS, BOT_NAME, ERROR_MESSAGE)


@app.route('/index')
def index():
    """
    Index page
    :rtype str
    """
    return '<a href="https://slack.com/oauth/authorize?scope=bot&client_id=19996241921.72874812897">' \
           '<img alt="Add to Slack" height="40" width="139" src="https://platform.slack-edge.com/img' \
           '/add_to_slack.png" srcset="https://platform.slack-edge.com/img/add_to_slack.png 1x, https:' \
           '//platform.slack-edge.com/img/add_to_slack@2x.png 2x" /></a>'


@app.route("/slack/listen", methods=['GET', 'POST'])
def listen_slack():
    """
    Listens to the slack web hook
    :return: str
    """
    slack_bot.slack_client.rtm_connect()
    message = request.form.get('text')
    channel_id = request.form.get('channel_id')

    if slack_bot.at_bot in message or slack_bot.at_bot+':' in message:
        message = message.lstrip(slack_bot.at_bot)
        slack_bot.handle_communication(channel_id, message)
    return "OK"


@app.route("/sms/listen", methods=['GET', 'POST'])
def handle_twilio_webhook():
    """
    Listens to the twilio callbacks
    :return: str
    """
    recipient = request.form.get('From')
    message_body = request.form.get('Body')
    if recipient and message_body:
        sms_bot.handle_communication(message_body, recipient)
    return str('ok')


@app.route('/mailgun/listen', methods=['POST'])
def receive_mailgun_mail():
    """
    End point which listens mail gun callbacks
    :return: str
    """
    message = request.form.get('stripped-text')
    sender = request.form.get('sender')
    subject = request.form.get('subject')
    if message and sender and subject:
        print message, sender
        email_bot.handle_communication(sender, subject, message)
    return "OK"


@app.route('/facebook/listen', methods=['GET'])
def handle_verification():
    """
    End point which handles facebook challenge code
    :return: str
    """
    return request.args['hub.challenge']


@app.route('/facebook/listen', methods=['POST'])
def handle_incoming_messages():
    """
    End point to listen facebook web hooks
    :return: str
    """
    data = request.json
    sender = data['entry'][0]['messaging'][0]['sender']['id']
    msg = data['entry'][0]['messaging'][0].get('message')
    current_timestamp = data['entry'][0]['messaging'][0]['timestamp']
    print 'current timestamp:', current_timestamp, 'old timestamp:', facebook_bot.time_stamp
    if msg and current_timestamp != facebook_bot.time_stamp:
        facebook_bot.time_stamp = current_timestamp
        message = data['entry'][0]['messaging'][0]['message']['text']
        facebook_bot.handle_communication(sender, message)
    return "ok"


@app.route('/slack/auth', methods=['GET', 'POST'])
def get_new_user_credentials():
    """
    Receives user data when he installs talentbot on slack
    :rtype str
    """
    code = request.args.get('code')
    response = slack_bot.slack_client.api_call('oauth.access',
                                               client_id="19996241921.72874812897",
                                               code=code,
                                               client_secret='828075991780611788b18212ab209678')
    return "ok"
