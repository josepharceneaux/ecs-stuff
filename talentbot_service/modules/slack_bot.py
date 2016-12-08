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
from datetime import datetime
# Common utils
from talentbot_service.common.utils.handy_functions import http_request
from talentbot_service.common.routes import SchedulerApiUrl, TalentBotApiUrl
from talentbot_service.common.models.user import TalentbotAuth
from talentbot_service.common.models.user import User
from talentbot_service.common.error_handling import NotFoundError
# App specific import
from talentbot_service.modules.constants import I_AM_PARSING_A_RESUME, USER_DISABLED_MSG
from talentbot_service.modules.talent_bot import TalentBot
from talentbot_service import logger
# 3rd party imports
from slackclient import SlackClient
from flask import json
from dateutil.relativedelta import relativedelta


class SlackBot(TalentBot):
    """
    This class inherits from Talentbot and handles Slack messages
    """
    def __init__(self, questions, bot_name, error_messages):
        super(SlackBot, self).__init__(questions, bot_name, error_messages)
        self.timestamp = None

    def authenticate_user(self, slack_user_id, message, channel_id):
        """
        Authenticates user
        :param str slack_user_id: User's slack Id
        :param str message: User's message
        :param str channel_id: Slack channel Id
        :rtype: tuple (True|False, None|str, None|Slack_client, TalentbotAuth.slack_user_id|None)
        """
        talentbot_auth = TalentbotAuth.get_talentbot_auth(slack_user_id=slack_user_id)
        if talentbot_auth:
            slack_user_token = talentbot_auth.bot_token
            user_id = talentbot_auth.user_id
            if slack_user_token and user_id:
                slack_client = SlackClient(slack_user_token)
                user = User.get_by_id(user_id)
                if user.is_disabled == 1:
                    return True, None, slack_client, None
                try:
                    if talentbot_auth.bot_id:
                        at_bot = '<@%s>' % talentbot_auth.bot_id
                        presence = slack_client.api_call('users.getPresence')
                        if not presence.get('online'):
                            self.set_bot_state_active(talentbot_auth.bot_token)
                    else:
                        at_bot = self.get_bot_id(slack_client)
                except NotFoundError as error:
                    logger.error(error.message)
                    return False, None, None, None
                # Slack channel Id starts with 'C' if it is a channel and
                # Start's with 'D' if it's a private message
                is_channel = channel_id[0] == 'C'
                is_private_message = channel_id[0] == 'D'
                at_bot_colon = '%s:' % at_bot
                if (at_bot in message or at_bot_colon in message and is_channel) \
                        or (is_private_message and slack_user_id != at_bot):
                    return True, message.replace(at_bot, ''), slack_client, user_id
        logger.info("Not authenticated")
        return False, None, None, None

    def get_bot_id(self, slack_client):
        """
        Gets bot Id
        :param SlackClient slack_client: SlackClient object
        :rtype: str|None
        """
        api_call = slack_client.api_call("users.list")
        if api_call.get('ok'):
            # retrieve all users so we can find our bot
            users = api_call.get('members')
            for user in users:
                if 'name' in user and self.bot_name == user.get('name'):
                    logger.info("Bot ID for %s is %s" % (user['name'], user.get('id')))
                    temp_at_bot = '<@%s>' % user.get('id')
                    return temp_at_bot
        raise NotFoundError("could not find bot user with the name %s" % self.bot_name)

    def set_bot_state_active(self, bot_token):
        """
        Sets Slack bot state active
        :param str bot_token: bot token
        :rtype: None
        """
        token = User.generate_jw_token()
        header = {'Authorization': token, 'Content-Type': 'application/json'}
        job_config = {"frequency": 144,
                      "task_type": "periodic",
                      "start_datetime": datetime.utcnow(),
                      "end_datetime": datetime.utcnow() + relativedelta(days=1),
                      "url": TalentBotApiUrl.SLACK_BOT_STATUS,
                      "task_name": bot_token,
                      "post_data": {
                          "bot_token": bot_token}
                      }
        # Getting task by name
        try:
            task = http_request('get', SchedulerApiUrl.TASK_NAME % bot_token,
                                headers=header)
            if task.status_code == 200:
                task_json = json.loads(task.text)
                http_request('delete', SchedulerApiUrl.TASK % task_json['task']['id'],
                             headers=header)
        except Exception as e:
            logger.info("No Scheduler task exists with name %s creating new one" %
                        bot_token)
        response = http_request('POST', SchedulerApiUrl.TASKS, headers=header,
                                data=json.dumps(job_config))

    def reply(self, chanel_id, msg, slack_client):
        """
        Replies to user on specified slack channel
        :param SlackClient slack_client: Slack Client RTM object
        :param str chanel_id: Slack channel id
        :param str msg: Message received to bot
        :rtype: None
        """
        logger.info('slack reply: %s' % msg)
        slack_client.api_call("chat.postMessage", channel=chanel_id,
                              text=msg, set_active=True)

    def handle_communication(self, channel_id, message, slack_user_id, timestamp):
        """
        Handles the communication between user and bot
        :param str slack_user_id: Slack user id of the sender
        :param str channel_id: Slack channel Id from which message is received
        :param str message: User's message
        :param str timestamp: Current message timestamp
        :rtype: None
        """
        is_authenticated, message, slack_client, user_id = self.authenticate_user(slack_user_id, message, channel_id)
        if is_authenticated:
            self.timestamp = timestamp
            if not user_id:
                self.reply(channel_id, USER_DISABLED_MSG, slack_client)
            else:
                if self.is_response_time_more_than_usual(message):
                    self.reply(channel_id, I_AM_PARSING_A_RESUME, slack_client)
                try:
                    response_generated = self.parse_message(message, user_id)
                    if response_generated:
                        self.reply(channel_id, response_generated, slack_client)
                    else:
                        raise IndexError
                except Exception as error:
                    logger.error("Error occurred while generating response: %s" % error.message)
                    error_response = random.choice(self.error_messages)
                    self.reply(channel_id, error_response, slack_client)
