"""
This module contains class SlackBot which is inherited from TalentBot class. It handles bot interaction
with Slack.
- authenticate_user()
- get_bot_id()
- set_bot_state_active()
- reply()
- handle_communication()
"""
# Builtin imports
import random
# Common utils
from talentbot_service.common.models.user import TalentbotAuth
# App specific import
from talentbot_service.common.error_handling import NotFoundError
from talentbot_service.modules.talent_bot import TalentBot
from talentbot_service import logger
# 3rd party imports
from slackclient import SlackClient


class SlackBot(TalentBot):
    """
    This class inherits from Talentbot and handles Slack messages
    """
    def __init__(self, questions, bot_name, error_messages):
        super(SlackBot, self).__init__(questions, bot_name, error_messages)
        self.recent_channel_id = None
        self.timestamp = None
        self.recent_user_id = None

    def authenticate_user(self, slack_user_id, message, channel_id):
        """
        Authenticates user
        :param str slack_user_id: User's slack Id
        :param str message: User's message
        :param str channel_id: Slack channel Id
        :return: tuple (True|False, None|message, None|slack_client)
        """
        slack_user_token = TalentbotAuth.query.with_entities(TalentbotAuth.slack_user_token).\
            filter_by(slack_user_id=slack_user_id).first()
        if slack_user_token:
            slack_user_token = slack_user_token[0]
            slack_client = SlackClient(slack_user_token)
            try:
                at_bot = self.get_bot_id(slack_client)
                # self.set_bot_state_active(slack_client)
            except NotFoundError as error:
                logger.error(error.message)
                return False, None, None
            # Slack channel Id starts with 'C' if it is a channel and
            # Start's with 'D' if it's a private message
            if (at_bot in message or at_bot+':' in message and channel_id[0] == 'C') \
                    or (channel_id[0] == 'D' and slack_user_id != at_bot):
                return True, message.strip(at_bot), slack_client
        return False, None, None

    def get_bot_id(self, slack_client):
        """
        Gets bot Id
        :param SlackClient slack_client: SlackClient object
        :return str|None
        """
        api_call = slack_client.api_call("users.list")
        if api_call.get('ok'):
            # retrieve all users so we can find our bot
            users = api_call.get('members')
            for user in users:
                if 'name' in user and user.get('name') == self.bot_name:
                    logger.info("Bot ID for %s is %s" % (user['name'], user.get('id')))
                    temp_at_bot = '<@' + user.get('id') + '>'
                    return temp_at_bot
        raise NotFoundError("could not find bot user with the name " + self.bot_name)

    def set_bot_state_active(self, slack_client):
        """
        Sets Slack bot state active
        """
        slack_client.rtm_connect()
        api_call_response = slack_client.api_call("users.setActive")
        logger.info('bot state is active: ' + str(api_call_response.get('ok')))

    def reply(self, chanel_id, msg, slack_client):
        """
        Replies to user on specified slack channel
        :param SlackClient slack_client: Slack Client RTM object
        :param str chanel_id: Slack channel id
        :param str msg: Message received to bot
        """
        logger.info('slack reply:' + msg)
        slack_client.api_call("chat.postMessage", channel=chanel_id,
                              text=msg, as_user=True)

    def handle_communication(self, channel_id, message, slack_user_id, timestamp):
        """
        Handles the communication between user and bot
        :param str slack_user_id: Slack user id of the sender
        :param str channel_id: Slack channel Id from which message is received
        :param str message: User's message
        :param str timestamp: Current message timestamp
        """
        is_authenticated, message, slack_client = self.authenticate_user(slack_user_id, message, channel_id)
        if is_authenticated:
            self.timestamp = timestamp
            self.recent_channel_id = channel_id
            self.recent_user_id = slack_user_id
            try:
                response_generated = self.parse_message(message)
                self.reply(channel_id, response_generated, slack_client)
            except (IndexError, NameError, KeyError):
                error_response = random.choice(self.error_messages)
                self.reply(channel_id, error_response, slack_client)
