"""
This module has class Talentbot which contains some common functions of bot
 - clean_user_message()
 - parse_message()
 - tokenize_message()
 - find_word_in_message()
 - authenticate_user()
"""
# Builtin imports
import random
import re
from abc import abstractmethod
# App specific imports
from constants import BEST_QUESTION_MATCH_RATIO, GREETINGS
from talentbot_service.modules.question_handler import QuestionHandler
from talentbot_service import logger
# 3rd party imports
from fuzzywuzzy import fuzz
# TODO: There is a class TwilioSMS in sms-campaign-service, move sms related code there in future


class TalentBot(object):
    """
    This class has some common methods of our bot
    """
    def __init__(self, list_of_questions, bot_name, error_messages):
        self.handler = QuestionHandler()
        self.question_dict = {'0': {'question': list_of_questions[0], 'threshold': 70,
                                    'handler': self.handler.question_0_handler},
                              '1': {'question': list_of_questions[1], 'threshold': 72,
                                    'handler': self.handler.question_1_handler},
                              '2': {'question': list_of_questions[2], 'threshold': 70,
                                    'handler': self.handler.question_2_handler},
                              '3': {'question': list_of_questions[3], 'threshold': 70,
                                    'handler': self.handler.question_3_handler},
                              '4': {'question': list_of_questions[4], 'threshold': 70,
                                    'handler': self.handler.question_4_handler},
                              '5': {'question': list_of_questions[5], 'threshold': 70,
                                    'handler': self.handler.question_5_handler},
                              '6': {'question': list_of_questions[6], 'threshold': 70,
                                    'handler': self.handler.question_6_handler}
                              }
        self.bot_name = bot_name
        self.error_messages = error_messages

    @staticmethod
    def clean_user_message(message):
        """
        Removes '?','.',':' and spaces from user's message
        :param str message: User's message
        :return: str message
        """
        cleaned_message = message.rstrip('?. ')
        cleaned_message = cleaned_message.lstrip(': ')
        return cleaned_message

    def parse_message(self, message, user_id=None):
        """
        Checks which is the appropriate message handler for this message and calls that handler
        :param int user_id: User Id
        :param str message: User's message
        :rtype str
        """
        message = self.clean_user_message(message)
        is_greetings = self.check_for_greetings(message)
        if is_greetings:
            return is_greetings
        message_tokens = self.tokenize_message(message)
        max_match_ratio = 0
        message_handler = None
        for question_key in self.question_dict:
            question_dict_entry = self.question_dict[question_key]
            question = question_dict_entry['question']
            match_ratio = self.match_question(message, question)
            if match_ratio >= question_dict_entry['threshold'] and match_ratio > max_match_ratio:
                max_match_ratio = match_ratio
                message_handler = question_dict_entry['handler']
                if match_ratio >= BEST_QUESTION_MATCH_RATIO:
                    break
        if message_handler:
            return message_handler(message_tokens, user_id)
        return random.choice(self.error_messages)

    @staticmethod
    def tokenize_message(message):
        """
        Splits message using space and ',' as separators
        :param str message: User's message
        :rtype: list
        """
        return re.split(' |,', message)

    @staticmethod
    def match_question(message, question):
        """
        Matches user message with predefined messages and returns matched ratio
        :param str message: User message
        :param dict question:
        :return: int partial_ratio
        """
        partial_ratio = fuzz.partial_ratio(message.lower(), question)
        logger.info("%s : %d%% matched" % (message, partial_ratio))
        return partial_ratio

    @abstractmethod
    def authenticate_user(self, *args):
        """
        Authenticates user
        :return: True|False
        """
        pass

    @staticmethod
    def check_for_greetings(message):
        """
        Checks if user is greeting out bot
        :param str message: User's message
        :return: Response message|None
        :rtype: str|None
        """
        if message.lower() in GREETINGS:
            return random.choice(GREETINGS)
        return None
