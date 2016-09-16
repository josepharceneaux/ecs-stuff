"""
This module contains class SmsBot which is inherited from TalentBot class. It handles bot interaction
with SMS.
- authenticate_user()
- reply()
- handle_communication()
- get_total_sms_segments()
"""
# Builtin import
import random
#  Common utils
from talentbot_service.common.models.user import TalentbotAuth, UserPhone
# App specific imports
from talentbot_service.modules.constants import TEXT_MESSAGE_MAX_LENGTH, AUTHENTICATION_FAILURE_MSG
from twilio.rest import TwilioRestClient
from talentbot_service.modules.talent_bot import TalentBot
from talentbot_service import logger


class SmsBot(TalentBot):
    """
    This class inherits from TalentBot class and handles received SMS from user
    """
    def __init__(self, questions, bot_name, error_messages, twilio_account_sid, twilio_auth_token,
                 standard_sms_length, twilio_number):
        TalentBot.__init__(self, questions, bot_name, error_messages)
        self.standard_sms_length = standard_sms_length
        self.twilio_number = twilio_number
        self.twilio_client = TwilioRestClient(twilio_account_sid, twilio_auth_token)

    def authenticate_user(self, mobile_number):
        """
        Authenticates user
        :return: True|False
        """
        user_phone_id = UserPhone.query.with_entities(UserPhone.id).\
            filter_by(value=mobile_number).first()
        if user_phone_id:
            count = TalentbotAuth.query.filter_by(user_phone_id=user_phone_id[0]).count()
            if count > 0:
                return True
        return False

    def reply(self, response, recipient):
        """
        Replies to the user through sms
        :param str response: Response message from bot
        :param str recipient: User's mobile number
        """
        # Twilio sms text doesn't seem to support'[' and ']'
        response = response.replace('[', '(')
        response = response.replace(']', ')')
        if len(response) > self.standard_sms_length:
            tokens = response.split('\n')
            total_segments, dict_of_segments = self.get_total_sms_segments(tokens)
            for segment_indexer in dict_of_segments:
                segment = dict_of_segments.get(segment_indexer) + \
                        "("+str(segment_indexer)+"/"+str(total_segments) + ")"
                message = self.twilio_client.messages.create(to=recipient, from_=self.twilio_number,
                                                             body=segment)
                logger.info('Twilio response status: ' + message.status)
                logger.info('message body:' + segment)
        else:
            message = self.twilio_client.messages.create(to=recipient, from_=self.twilio_number,
                                                         body=response)
            logger.info('SMS Reply: ' + response)
            logger.info('Twilio response status: ' + message.status)

    def handle_communication(self, message, recipient):
        """
        Handles communication between user and bot
        :param str message: User's message
        :param str recipient: User's mobile number
        """
        is_authenticated = self.authenticate_user(recipient)
        if is_authenticated:
            try:
                response_generated = self.parse_message(message)
                self.reply(response_generated, recipient)
            except (IndexError, NameError, KeyError):
                error_response = random.choice(self.error_messages)
                self.reply(error_response, recipient)
        else:  # User not authenticated
            self.reply(AUTHENTICATION_FAILURE_MSG, recipient)

    @staticmethod
    def get_total_sms_segments(tokens):
        """
        Breaks list of string lines into message segments and appends
        these segments in a dict with segment numbers as keys
        :param tokens: list of independent string lines
        :return: total number of message segments, dict of message segments
        :rtype: tuple[int, dict]
        """
        split_response_message = ""
        dict_of_segments = {}
        segments = 0
        while len(tokens) > 0:
            try:
                while len(tokens[0]) + len(split_response_message) <= TEXT_MESSAGE_MAX_LENGTH \
                        and len(tokens) > 0:
                    split_response_message = split_response_message + tokens.pop(0) + "\n"
                segments += 1
                dict_of_segments.update({segments: split_response_message})
                split_response_message = ""
            except IndexError:
                if len(split_response_message) > 0:
                    segments += 1
                    dict_of_segments.update({segments: split_response_message})
                return segments, dict_of_segments
        return segments, dict_of_segments