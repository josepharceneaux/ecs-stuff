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

from slackclient import SlackClient

from talentbot_service.modules.talentbot import TalentBot


class SlackBot(TalentBot):
    def __init__(self, slack_bot_token, questions, bot_name, error_messages):
        TalentBot.__init__(self, questions, bot_name, error_messages)
        self.slack_client = SlackClient(slack_bot_token)
        self.at_bot = self.get_bot_id()

    def authenticate_user(self):
        """
        Authenticates user
        :return: True|False
        """
        return True

    def get_bot_id(self):
        """
        Gets bot Id
        :return str|None
        """
        api_call = self.slack_client.api_call("users.list")
        if api_call.get('ok'):
            # retrieve all users so we can find our bot
            users = api_call.get('members')
            for user in users:
                if 'name' in user and user.get('name') == self.bot_name:
                    print "Bot ID for %s is %s" % (user['name'], user.get('id'))
                    temp_at_bot = '<@' + user.get('id') + '>'
                    return temp_at_bot
        print("could not find bot user with the name " + self.bot_name)
        return None

    def set_bot_state_active(self):
        """
        Sets Slack bot state active
        """
        self.slack_client.rtm_connect()
        api_call_response = self.slack_client.api_call("users.setActive")
        print 'bot state is active: ', api_call_response.get('ok')

    def reply(self, chanel_id, msg):
        """
        Replies to user on specified slack channel
        :param str chanel_id: Slack channel id
        :param str msg: Message received to bot
        """
        print 'message:', msg
        self.slack_client.api_call("chat.postMessage", channel=chanel_id,
                                   text=msg, as_user=True)

    def handle_communication(self, channel_id, message):
        """
        Handles the communication between user and bot
        :param str channel_id: Slack channel Id from which message is received
        :param message: User's message
        """
        try:
            response_generated = self.parse_message(message)
            self.reply(channel_id, response_generated)
        except Exception:
            error_response = random.choice(self.error_messages)
            self.reply(channel_id, error_response)