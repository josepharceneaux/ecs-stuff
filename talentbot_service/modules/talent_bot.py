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
from constants import BEST_QUESTION_MATCH_RATIO, GREETINGS, POSITIVE_MESSAGES, HINT, MIN_WORDS_IN_QUESTION
from talentbot_service.modules.question_handler import QuestionHandler
from talentbot_service import logger
# 3rd party imports
from fuzzywuzzy import fuzz
import stopwords
from contracts import contract
# TODO: There is a class TwilioSMS in sms-campaign-service, move sms related code there in future


class TalentBot(object):
    """
    This class has some common methods of our bot
    """
    def __init__(self, list_of_questions, bot_name, error_messages):
        self.handler = QuestionHandler()
        self.list_of_questions = list_of_questions
        self.question_dict = {'0': {'question': self.list_of_questions[0], 'threshold': 90,
                                    'handler': self.handler.question_0_handler},
                              '1': {'question': self.list_of_questions[1], 'threshold': 95,
                                    'handler': self.handler.question_1_handler},
                              '2': {'question': self.list_of_questions[2], 'threshold': 79,
                                    'handler': self.handler.question_2_handler},
                              '3': {'question': self.list_of_questions[3], 'threshold': 70,
                                    'handler': self.handler.question_3_handler},
                              '4': {'question': self.list_of_questions[4], 'threshold': 69,
                                    'handler': self.handler.question_4_handler},
                              '5': {'question': self.list_of_questions[5], 'threshold': 90,
                                    'handler': self.handler.question_5_handler},
                              # Domain question alternates
                              '10': {'question': self.list_of_questions[10], 'threshold': 90,
                                     'handler': self.handler.question_0_handler},
                              '11': {'question': self.list_of_questions[11], 'threshold': 90,
                                     'handler': self.handler.question_0_handler},
                              '28': {'question': self.list_of_questions[28], 'threshold': 90,
                                     'handler': self.handler.question_0_handler},
                              '29': {'question': self.list_of_questions[29], 'threshold': 90,
                                     'handler': self.handler.question_0_handler},
                              '45': {'question': self.list_of_questions[45], 'threshold': 90,
                                     'handler': self.handler.question_0_handler},
                              '46': {'question': self.list_of_questions[46], 'threshold': 90,
                                     'handler': self.handler.question_0_handler},
                              '47': {'question': self.list_of_questions[47], 'threshold': 90,
                                     'handler': self.handler.question_0_handler},
                              # Skills question alternates
                              '12': {'question': self.list_of_questions[12], 'threshold': 95,
                                     'handler': self.handler.question_1_handler},
                              '13': {'question': self.list_of_questions[13], 'threshold': 95,
                                     'handler': self.handler.question_1_handler},
                              '14': {'question': self.list_of_questions[14], 'threshold': 95,
                                     'handler': self.handler.question_1_handler},
                              '15': {'question': self.list_of_questions[15], 'threshold': 95,
                                     'handler': self.handler.question_1_handler},
                              '16': {'question': self.list_of_questions[16], 'threshold': 95,
                                     'handler': self.handler.question_1_handler},
                              '20': {'question': self.list_of_questions[20], 'threshold': 95,
                                     'handler': self.handler.question_1_handler},
                              '21': {'question': self.list_of_questions[21], 'threshold': 95,
                                     'handler': self.handler.question_1_handler},
                              '23': {'question': self.list_of_questions[23], 'threshold': 95,
                                     'handler': self.handler.question_1_handler},
                              '30': {'question': self.list_of_questions[30], 'threshold': 95,
                                     'handler': self.handler.question_1_handler},
                              # Top campaign alternates
                              '17': {'question': self.list_of_questions[17], 'threshold': 70,
                                     'handler': self.handler.question_3_handler},
                              '18': {'question': self.list_of_questions[18], 'threshold': 70,
                                     'handler': self.handler.question_3_handler},
                              '24': {'question': self.list_of_questions[24], 'threshold': 70,
                                     'handler': self.handler.question_3_handler},
                              '25': {'question': self.list_of_questions[25], 'threshold': 70,
                                     'handler': self.handler.question_3_handler},
                              '26': {'question': self.list_of_questions[26], 'threshold': 70,
                                     'handler': self.handler.question_3_handler},
                              '27': {'question': self.list_of_questions[27], 'threshold': 70,
                                     'handler': self.handler.question_3_handler},
                              '49': {'question': self.list_of_questions[49], 'threshold': 95,
                                     'handler': self.handler.question_3_handler},
                              # Import question alternates
                              '19': {'question': self.list_of_questions[19], 'threshold': 85,
                                     'handler': self.handler.question_4_handler},
                              '43': {'question': self.list_of_questions[43], 'threshold': 95,
                                     'handler': self.handler.question_4_handler},
                              '44': {'question': self.list_of_questions[44], 'threshold': 95,
                                     'handler': self.handler.question_4_handler},
                              '50': {'question': self.list_of_questions[50], 'threshold': 80,
                                     'handler': self.handler.question_4_handler},
                              # Zipcode question alternates
                              '22': {'question': self.list_of_questions[22], 'threshold': 79,
                                     'handler': self.handler.question_2_handler},
                              '48': {'question': self.list_of_questions[48], 'threshold': 90,
                                     'handler': self.handler.question_2_handler},
                              '52': {'question': self.list_of_questions[52], 'threshold': 90,
                                     'handler': self.handler.question_2_handler},
                              '53': {'question': self.list_of_questions[53], 'threshold': 90,
                                     'handler': self.handler.question_2_handler},
                              # What talent pools in my domain
                              '31': {'question': self.list_of_questions[31], 'threshold': 97,
                                     'handler': self.handler.question_6_handler},
                              '32': {'question': self.list_of_questions[32], 'threshold': 97,
                                     'handler': self.handler.question_6_handler},
                              '33': {'question': self.list_of_questions[33], 'threshold': 97,
                                     'handler': self.handler.question_6_handler},
                              '34': {'question': self.list_of_questions[34], 'threshold': 97,
                                     'handler': self.handler.question_6_handler},
                              '35': {'question': self.list_of_questions[35], 'threshold': 97,
                                     'handler': self.handler.question_6_handler},
                              '36': {'question': self.list_of_questions[36], 'threshold': 97,
                                     'handler': self.handler.question_6_handler},
                              '51': {'question': self.list_of_questions[51], 'threshold': 97,
                                     'handler': self.handler.question_6_handler},
                              # What is my group
                              '37': {'question': self.list_of_questions[37], 'threshold': 95,
                                     'handler': self.handler.question_7_handler},
                              '38': {'question': self.list_of_questions[38], 'threshold': 95,
                                     'handler': self.handler.question_7_handler},
                              '39': {'question': self.list_of_questions[39], 'threshold': 95,
                                     'handler': self.handler.question_7_handler},
                              '40': {'question': self.list_of_questions[40], 'threshold': 95,
                                     'handler': self.handler.question_7_handler},
                              '41': {'question': self.list_of_questions[41], 'threshold': 95,
                                     'handler': self.handler.question_7_handler},
                              '42': {'question': self.list_of_questions[42], 'threshold': 95,
                                     'handler': self.handler.question_7_handler},
                              # What are my campaigns
                              '54': {'question': self.list_of_questions[54], 'threshold': 95,
                                     'handler': self.handler.question_8_handler},
                              '58': {'question': self.list_of_questions[58], 'threshold': 95,
                                     'handler': self.handler.question_8_handler},
                              '59': {'question': self.list_of_questions[59], 'threshold': 95,
                                     'handler': self.handler.question_8_handler},
                              '60': {'question': self.list_of_questions[60], 'threshold': 95,
                                     'handler': self.handler.question_8_handler},
                              '61': {'question': self.list_of_questions[61], 'threshold': 95,
                                     'handler': self.handler.question_8_handler},
                              '62': {'question': self.list_of_questions[62], 'threshold': 95,
                                     'handler': self.handler.question_8_handler},
                              # Show me <x>
                              '55': {'question': self.list_of_questions[55], 'threshold': 95,
                                     'handler': self.handler.question_9_handler},
                              '56': {'question': self.list_of_questions[56], 'threshold': 95,
                                     'handler': self.handler.question_9_handler},
                              '57': {'question': self.list_of_questions[57], 'threshold': 95,
                                     'handler': self.handler.question_9_handler}
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
        split_message = cleaned_message.split()
        cleaned_message = ' '.join([message.strip() for message in split_message])
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
        is_positive_message = self.check_for_positive_messages(message)
        if is_positive_message:
            return is_positive_message
        is_hint_question = self.check_for_hint(message)
        if is_hint_question:
            return is_hint_question
        if len(message.split()) < MIN_WORDS_IN_QUESTION:
            return random.choice(self.error_messages)
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
        :param str question:
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
        Checks if user is greeting bot
        :param str message: User's message
        :rtype: str|None
        """
        if message.lower() in GREETINGS:
            return random.choice(GREETINGS)
        return None

    @staticmethod
    def check_for_positive_messages(message):
        """
        Checks if user is saying things like ok, hmm etc
        :param str message: User's message
        :rtype: str|None
        """
        if message.lower() in POSITIVE_MESSAGES:
            return random.choice(POSITIVE_MESSAGES)
        return None

    def check_for_hint(self, message):
        """
        Checks i user is asking for hint
        :param str message: User's message
        :rtype: str|None
        """
        hint_questions = self.list_of_questions[6:10]
        for question in hint_questions:
            if message.lower() in question:
                return HINT
        return None

    @classmethod
    def clean_response_message(cls, response_message):
        """
        Replaces back-ticks and asterisks from message which are only meaningful in Slack
        :param str response_message:
        :rtype: str
        """
        response_message = response_message.replace('*', '').replace('`', '"').replace('>>>', '')
        return response_message
