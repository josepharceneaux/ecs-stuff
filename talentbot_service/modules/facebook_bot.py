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
# Common utils
from talentbot_service.modules.constants import FACEBOOK_MESSAGE_LIMIT, FACEBOOK_MESSAGE_SPLIT_COUNT
from talentbot_service.common.models.user import TalentbotAuth
# Service specific
from talentbot_service import app
from talentbot_service.common.talent_config_manager import TalentConfigKeys
from talentbot_service.common.utils.handy_functions import send_request
from talentbot_service.modules.talent_bot import TalentBot
from talentbot_service.modules.constants import FACEBOOK_API_URI
from talentbot_service import logger


class FacebookBot(TalentBot):
    """
    This class handles bot communication with user on Facebook
    """
    def __init__(self, questions, bot_name, error_messages):
        TalentBot.__init__(self, questions, bot_name, error_messages)
        self.timestamp = None

    def authenticate_user(self, fb_user_id):
        """
        Authenticates user
        :param fb_user_id:
        :rtype: (True|False, TalentbotAuth.facebook_user_id)
        """
        user_id = TalentbotAuth.get_user_id(facebook_user_id=fb_user_id)
        if user_id:
            return True, user_id[0]
        return False, None

    def handle_communication(self, fb_user_id, message):
        """
        Handles the communication between user and bot
        :param str fb_user_id: Facebook user Id of sender
        :param str message: User's message
        :rtype: None
        """
        is_authenticated, user_id = self.authenticate_user(fb_user_id)
        if is_authenticated:
            try:
                self.sender_action(fb_user_id, "mark_seen")
                self.sender_action(fb_user_id, "typing_on")
                response_generated = self.parse_message(message, user_id)
                if not response_generated:
                    raise IndexError
                if len(response_generated) > FACEBOOK_MESSAGE_LIMIT:
                    tokens = response_generated.split('\n')
                    split_response_message = ""
                    while len(tokens) > 0:
                        while len(split_response_message) < FACEBOOK_MESSAGE_SPLIT_COUNT and\
                                        len(tokens) > 0:
                            split_response_message = split_response_message + tokens.pop(0) + "\n"
                        self.reply(fb_user_id, split_response_message)
                        split_response_message = ""
                else:
                    self.reply(fb_user_id, response_generated)
                self.sender_action(fb_user_id, "typing_off")
            except (IndexError, NameError, KeyError):
                error_response = random.choice(self.error_messages)
                self.reply(fb_user_id, error_response)
                self.sender_action(fb_user_id, "typing_off")
        else:
            logger.info("Un registered user %r accessed Talentbot on Facebook" % fb_user_id)

    @staticmethod
    def sender_action(user_id, action):
        """
        Lets Facebook know what bot's doing e.g: typing_on or typing_off
        :param str user_id: Facebook user Id
        :param str action: Bot's action
        :rtype: None
        """
        data = {
            "recipient": {"id": user_id},
            "sender_action": action
        }
        send_request('POST', FACEBOOK_API_URI, access_token=None,
                     params={'access_token': app.config[TalentConfigKeys.FACEBOOK_ACCESS_TOKEN]},
                     data=data)

    @staticmethod
    def reply(fb_user_id, msg):
        """
        Replies to facebook user
        :param str fb_user_id: facebook user id who has sent us message
        :param str msg: Our response message
        :rtype: None
        """
        data = {
            "recipient": {"id": fb_user_id},
            "message": {"text": msg}
        }
        send_request('POST', FACEBOOK_API_URI, access_token=None,
                     params={'access_token': app.config[TalentConfigKeys.FACEBOOK_ACCESS_TOKEN]},
                     data=data)
        logger.info("FB reply '%s' to %s" % (msg, fb_user_id))
