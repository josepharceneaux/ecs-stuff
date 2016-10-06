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
                              '1': {'question': list_of_questions[1], 'threshold': 95,
                                    'handler': self.handler.question_1_handler},
                              '2': {'question': list_of_questions[2], 'threshold': 79,
                                    'handler': self.handler.question_2_handler},
                              '3': {'question': list_of_questions[3], 'threshold': 70,
                                    'handler': self.handler.question_3_handler},
                              '4': {'question': list_of_questions[4], 'threshold': 69,
                                    'handler': self.handler.question_4_handler},
                              '5': {'question': list_of_questions[5], 'threshold': 70,
                                    'handler': self.handler.question_5_handler},
                              '6': {'question': list_of_questions[6], 'threshold': 90,
                                    'handler': self.handler.question_6_handler},
                              '7': {'question': list_of_questions[7], 'threshold': 90,
                                    'handler': self.handler.question_6_handler},
                              '8': {'question': list_of_questions[8], 'threshold': 90,
                                    'handler': self.handler.question_6_handler},
                              '9': {'question': list_of_questions[9], 'threshold': 90,
                                    'handler': self.handler.question_6_handler},
                              # Domain question alternates
                              '10': {'question': list_of_questions[10], 'threshold': 90,
                                     'handler': self.handler.question_0_handler},
                              '11': {'question': list_of_questions[11], 'threshold': 90,
                                     'handler': self.handler.question_0_handler},
                              '28': {'question': list_of_questions[28], 'threshold': 90,
                                     'handler': self.handler.question_0_handler},
                              '29': {'question': list_of_questions[29], 'threshold': 90,
                                     'handler': self.handler.question_0_handler},
                              # Skills question alternates
                              '12': {'question': list_of_questions[12], 'threshold': 95,
                                     'handler': self.handler.question_1_handler},
                              '13': {'question': list_of_questions[13], 'threshold': 95,
                                     'handler': self.handler.question_1_handler},
                              '14': {'question': list_of_questions[14], 'threshold': 95,
                                     'handler': self.handler.question_1_handler},
                              '15': {'question': list_of_questions[15], 'threshold': 95,
                                     'handler': self.handler.question_1_handler},
                              '16': {'question': list_of_questions[16], 'threshold': 95,
                                     'handler': self.handler.question_1_handler},
                              '20': {'question': list_of_questions[20], 'threshold': 95,
                                     'handler': self.handler.question_1_handler},
                              '21': {'question': list_of_questions[21], 'threshold': 95,
                                     'handler': self.handler.question_1_handler},
                              '23': {'question': list_of_questions[23], 'threshold': 95,
                                     'handler': self.handler.question_1_handler},
                              '30': {'question': list_of_questions[30], 'threshold': 95,
                                     'handler': self.handler.question_1_handler},
                              # Top campaign alternates
                              '17': {'question': list_of_questions[17], 'threshold': 70,
                                     'handler': self.handler.question_3_handler},
                              '18': {'question': list_of_questions[18], 'threshold': 70,
                                     'handler': self.handler.question_3_handler},
                              '24': {'question': list_of_questions[24], 'threshold': 70,
                                     'handler': self.handler.question_3_handler},
                              '25': {'question': list_of_questions[25], 'threshold': 70,
                                     'handler': self.handler.question_3_handler},
                              '26': {'question': list_of_questions[26], 'threshold': 70,
                                     'handler': self.handler.question_3_handler},
                              '27': {'question': list_of_questions[27], 'threshold': 70,
                                     'handler': self.handler.question_3_handler},
                              # Import question alternates
                              '19': {'question': list_of_questions[19], 'threshold': 69,
                                     'handler': self.handler.question_4_handler},
                              # Zipcode question alternates
                              '22': {'question': list_of_questions[22], 'threshold': 79,
                                     'handler': self.handler.question_2_handler},
                              }
        self.bot_name = bot_name
        self.error_messages = error_messages

    @staticmethod
    def clean_user_message(message):
        """
        Removes '?','.',':' and spaces from user's message
        :param str message: User's message
        :rtype: str
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
        :rtype: int
        """
        match_ratio = fuzz.partial_ratio(question, message.lower())
        logger.info("%s : %d%% matched" % (message, match_ratio))
        return match_ratio

    @abstractmethod
    def authenticate_user(self, *args):
        """
        Authenticates user
        :rtype: True|False
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
