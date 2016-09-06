"""
This module contains class FacebookBot which is inherited from TalentBot class. It handles bot interaction
with Facebook.
- authenticate_user()
- handle_communication()
- sender_action()
- reply()
"""
# Builtin imports
import random

from talentbot_service.modules.constants import FACEBOOK_MESSAGE_LIMIT, FACEBOOK_MESSAGE_SPLIT_COUNT

from talentbot_service import app
from talentbot_service.common.talent_config_manager import TalentConfigKeys
from talentbot_service.common.utils.handy_functions import send_request
from talentbot_service.modules.talentbot import TalentBot


class FacebookBot(TalentBot):
    def __init__(self, questions, bot_name, error_messages):
        TalentBot.__init__(self, questions, bot_name, error_messages)
        self.time_stamp = None

    def authenticate_user(self):
        """
        Authenticates user
        :return: True|False
        """
        return True

    def handle_communication(self, user_id, message):
        """
        Handles the communication between user and bot
        :param user_id: Facebook user iId of sender
        :param message: User's message
        """
        try:
            self.sender_action(user_id, "mark_seen")
            self.sender_action(user_id, "typing_on")
            response_generated = self.parse_message(message)
            if len(response_generated) > FACEBOOK_MESSAGE_LIMIT:
                tokens = response_generated.split('\n')
                split_response_message = ""
                while len(tokens) > 0:
                    while len(split_response_message) < FACEBOOK_MESSAGE_SPLIT_COUNT and\
                                    len(tokens) > 0:
                        split_response_message = split_response_message + tokens.pop(0) + "\n"
                    self.reply(user_id, split_response_message)
                    split_response_message = ""
            else:
                self.reply(user_id, response_generated)
            self.sender_action(user_id, "typing_off")
        except Exception:
            error_response = random.choice(self.error_messages)
            self.reply(user_id, error_response)
            self.sender_action(user_id, "typing_off")

    @classmethod
    def sender_action(cls, user_id, action):
        """
        Lets Facebook know what bot's doing e.g: typing_on or typing_off
        :param str user_id: Facebook user Id
        :param str action: Bot's action
        """
        data = {
            "recipient": {"id": user_id},
            "sender_action": action
        }
        send_request('POST', "https://graph.facebook.com/v2.6/me/messages", access_token=None,
                     params={'access_token': app.config[TalentConfigKeys.FACEBOOK_ACCESS_TOKEN]},
                     data=data)

    @classmethod
    def reply(cls, user_id, msg):
        """
        Replies to facebook user
        :param str user_id: facebook user id who has sent us message
        :param str msg: Our response message
        """
        data = {
            "recipient": {"id": user_id},
            "message": {"text": msg}
        }
        send_request('POST', "https://graph.facebook.com/v2.6/me/messages", access_token=None,
                     params={'access_token': app.config[TalentConfigKeys.FACEBOOK_ACCESS_TOKEN]},
                     data=data)