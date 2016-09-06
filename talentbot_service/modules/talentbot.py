"""
This module has class Talentbot which contains some common functions of bot
 - clean_user_message()
 - parse_message()
 - tokenize_message()
 - find_word_in_message()
 - authenticate_user()
"""
# Builtin imports
import datetime
import random
import re
from abc import abstractmethod
from dateutil.relativedelta import relativedelta
# Common utils
from talentbot_service.common.models.candidate import Candidate, CandidateSkill,CandidateAddress
from talentbot_service.common.models.email_campaign import EmailCampaign, EmailCampaignBlast
from talentbot_service.common.models.talent_pools_pipelines import TalentPool, TalentPoolCandidate
from talentbot_service.common.models.user import User, Domain
# App specific imports
from constants import HINT, BEST_QUESTION_MATCH_RATIO
# 3rd party imports
from fuzzywuzzy import fuzz
from sqlalchemy import desc, or_, and_
from sqlalchemy import extract
# TODO: I have some code related to Twilio. Kindly see sms_campaign_service/modeuls/handy_functions.py
# TODO: I think we can move that out of that service and put in common/ so that it is available across services.


class TalentBot:
    def __init__(self, list_of_questions, bot_name, error_messages):
        self.question_dict = {'0': {'question': list_of_questions[0], 'threshold': 70,
                                    'handler': self.question_0_handler},
                              '1': {'question': list_of_questions[1], 'threshold': 72,
                                    'handler': self.question_1_handler},
                              '2': {'question': list_of_questions[2], 'threshold': 70,
                                    'handler': self.question_2_handler},
                              '3': {'question': list_of_questions[3], 'threshold': 70,
                                    'handler': self.question_3_handler},
                              '4': {'question': list_of_questions[4], 'threshold': 70,
                                    'handler': self.question_4_handler},
                              '5': {'question': list_of_questions[5], 'threshold': 70,
                                    'handler': self.question_5_handler},
                              '6': {'question': list_of_questions[6], 'threshold': 70,
                                    'handler': self.question_6_handler}
                              }
        self.bot_name = bot_name
        self.error_messages = error_messages

    @classmethod
    def append_list_with_spaces(cls, _list):
        """
        Append a list elements with spaces between then
        :param _list: list
        :return: str result
        """
        result = ""
        for element in _list:
            result += element + " "
        return result

    @classmethod
    def clean_user_message(cls, message):
        """
        Removes '?','.',':' and spaces from user's message
        :param str message: User's message
        :return: str message
        """
        cleaned_message = message.rstrip('?. ')
        cleaned_message = cleaned_message.lstrip(': ')
        return cleaned_message

    def parse_message(self, message):
        """
        Checks which is the appropriate message handler for this message and calls that handler
        :param str message: User's message
        :return str Response generated
        """
        message = self.clean_user_message(message)
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
            return message_handler(message, message_tokens)
        return random.choice(self.error_messages)

    @classmethod
    def tokenize_message(cls, message):
        """
        Splits message using space and ',' as separators
        :param str message: User's message
        :rtype: list
        """
        return re.split(' |,', message)

    @classmethod
    def find_word_in_message(cls, word, message_tokens):
        """
        Finds a specific word in user message and returns it's index
        :param word:
        :param list message_tokens: Tokens of user message
        :return: int word_index
        """
        word_index = [message_tokens.index(temp_word) for temp_word
                      in message_tokens if word in temp_word.lower()][0]
        return word_index

    @classmethod
    def question_0_handler(cls, message, message_tokens):
        domain_index = cls.find_word_in_message('domain', message_tokens)
        domain_name = message_tokens[domain_index + 1]
        count = User.query.filter(User.domain_id == Domain.id).\
            filter(Domain.name == domain_name).count()
        response_message = "Users in domain " + message_tokens[domain_index + 1] + " : "
        response_message += str(count)
        return response_message

    @classmethod
    def question_1_handler(cls, message, message_tokens):
        skill_index = cls.find_word_in_message('skill', message_tokens)
        extracted_skills = message_tokens[skill_index + 1::]
        count = Candidate.query.filter(Candidate.id == CandidateSkill.candidate_id) \
            .filter(CandidateSkill.description.in_(extracted_skills)).distinct().count()
        response_message = "There are %d candidates with skills " + ' '.join(extracted_skills)
        response_message = response_message % count
        if count == 1:
            response_message = response_message.replace('are', 'is'). \
                replace('candidates', 'candidate')
        return response_message

    @classmethod
    def question_2_handler(cls, message, message_tokens):
        zip_index = cls.find_word_in_message('zip', message_tokens)
        count = Candidate.query.filter(CandidateAddress.candidate_id == Candidate.id). \
            filter(CandidateAddress.zip_code == message_tokens[zip_index + 1]).count()
        response_message = "Number of candidates from zipcode " + \
                           message_tokens[zip_index + 1] + " : "
        response_message += str(count)
        return response_message

    @classmethod
    def question_3_handler(cls, message, message_tokens):
        year = message_tokens[-1]
        email_campaign_blast = EmailCampaignBlast.query.filter\
            (or_(EmailCampaignBlast.updated_datetime.contains(year),
                 EmailCampaignBlast.sent_datetime.contains(year))).\
            filter(EmailCampaign.id == EmailCampaignBlast.campaign_id).\
            order_by(desc(EmailCampaignBlast.opens)).first()
        if email_campaign_blast:
            response_message = 'Top performing email campaign from ' + year +\
                               ' is "%s"' % email_campaign_blast.campaign.name
        else:
            response_message = "Sorry couldn't find top email campaign from " + year
        return response_message

    def question_4_handler(self, message, message_tokens):
        talent_index = self.find_word_in_message('talent', message_tokens)
        import_index = self.find_word_in_message('import', message_tokens)
        # Extracting talent pool name from user's message
        talent_pool_name = message_tokens[import_index + 3:talent_index:]
        # Extracting username from user message
        user_name = message_tokens[import_index - 1]
        spaced_talent_pool_name = self.append_list_with_spaces(talent_pool_name)
        previous_month = datetime.datetime.now() - relativedelta(months=1)
        count = TalentPoolCandidate.query.filter(TalentPoolCandidate.talent_pool_id == TalentPool.id) \
            .filter(or_((and_(extract("year", TalentPoolCandidate.added_time) == previous_month.year,
                              extract("month", TalentPoolCandidate.added_time) == previous_month.month)), (
                        and_(extract("year", TalentPoolCandidate.updated_time) == previous_month.year,
                             extract("month", TalentPoolCandidate.updated_time) == previous_month.month)))) \
            .filter(User.first_name == user_name).filter(TalentPool.name == spaced_talent_pool_name).distinct().count()
        response_message = user_name.title() + " added %d candidates in "\
                                             + spaced_talent_pool_name + "talent pool last month"
        response_message = response_message % count
        return response_message

    def question_5_handler(self, message, message_tokens):
        return "My name is " + self.bot_name

    @classmethod
    def question_6_handler(cls, message, message_tokens):
        return HINT[0]

    @classmethod
    def match_question(cls, message, question):
        """
        Matches user message with predefined messages and returns matched ratio
        :param str message: User message
        :param str question:
        :return: int partial_ratio
        """
        partial_ratio = fuzz.partial_ratio(message.lower(), question)
        print message + ': ', partial_ratio
        return partial_ratio

    @classmethod
    def parse_skills(cls, skills_list):
        """
        Converts space separated skills to comma separated skills
        :param list skills_list: List which contains space separated skills
        :return: str parsed_skills
        """
        parsed_skills = '('
        for skill in skills_list:
            temp = '"' + skill.lower() + '"'
            if skills_list.index(skill) < len(skills_list) - 1:
                temp += ','
            parsed_skills += temp
        parsed_skills += ')'
        return parsed_skills

    @abstractmethod
    def authenticate_user(self):
        """
        Authenticates user
        :return: True|False
        """
        pass


