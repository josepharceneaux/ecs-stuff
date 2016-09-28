"""
This module has class QuestionHandler which handles questions and generates an appropriate
response
 - find_word_in_message()
 - append_list_withs_paces()
 - question_0_handler()
 - question_1_handler()
 - question_2_handler()
 - question_3_handler()
 - question_4_handler()
 - question_5_handler()
 - question_6_handler()
"""
# Builtin imports
import datetime
from dateutil.relativedelta import relativedelta
# Common utils
from talentbot_service.common.models.user import User
from talentbot_service.common.models.candidate import Candidate
from talentbot_service.common.models.talent_pools_pipelines import TalentPoolCandidate
from talentbot_service.modules.constants import HINT, BOT_NAME, CAMPAIGN_TYPES


class QuestionHandler(object):
    """
    This class contains question handlers against questions and some helping methods
    """
    def __init__(self):
        pass

    @staticmethod
    def find_word_in_message(word, message_tokens):
        """
        Finds a specific word in user message and returns it's index
        :param str word: Word to be found in message_tokens
        :param list message_tokens: Tokens of user message
        :return: int word_index
        """
        word_index = [message_tokens.index(temp_word) for temp_word
                      in message_tokens if word in temp_word.lower()][0]
        return word_index

    @staticmethod
    def append_list_with_spaces(_list):
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
    def question_0_handler(cls, message_tokens, user_id):
        """
        Handles question 'how many users are there with domain [x]'
        :param int user_id: User Id
        :param message_tokens: User message tokens
        :return: str response_message
        """
        count, domain_name = User.get_user_count_in_domain(user_id)
        response_message = "Users in domain %s : %d" % (domain_name, count)
        return response_message

    @classmethod
    def question_1_handler(cls, message_tokens, user_id):
        """
            Handles question 'how many candidates are there with skills [x,y and z]'
            :param int user_id: User Id
            :param message_tokens: User message tokens
            :return: str response_message
        """
        skill_index = cls.find_word_in_message('skill', message_tokens)
        extracted_skills = message_tokens[skill_index + 1::]
        count = Candidate.get_candidate_count_with_skills(extracted_skills, user_id)
        response_message = "There are %d candidates with skills %s"
        response_message = response_message % (count, ' '.join(extracted_skills))
        if count == 1:
            response_message = response_message.replace('are', 'is'). \
                replace('candidates', 'candidate')
        return response_message

    @classmethod
    def question_2_handler(cls, message_tokens, user_id):
        """
            Handles question 'how many candidates are there from zipcode [x]'
            :param int user_id: User Id
            :param message_tokens: User message tokens
            :return: str response_message
        """
        zip_index = cls.find_word_in_message('zip', message_tokens)
        zipcode = message_tokens[zip_index + 1]
        count = Candidate.get_candidate_count_from_zipcode(zipcode, user_id)
        response_message = "Number of candidates from zipcode %s : %d" % \
                           (message_tokens[zip_index + 1], count)
        return response_message

    def question_3_handler(self, message_tokens, user_id):
        """
            Handles question 'what's the top performing [campaign name] campaign from [year]'
            :param int user_id: User Id
            :param message_tokens: User message tokens
            :return: str response_message
        """
        campaign_type_index = self.find_word_in_message('campaign', message_tokens)
        campaign_type = message_tokens[campaign_type_index-1].lower()
        year = message_tokens[-1]
        is_valid_year = self.is_valid_year(year)
        campaign_method = CAMPAIGN_TYPES.get(campaign_type)
        if not campaign_method:
            return "Wrong campaign type specified"
        if is_valid_year or year.lower() in 'campaigns' or year.lower() == 'from':
            if year.lower() in 'campaigns' or year.lower() == 'from':
                year = None
            campaign_blast = campaign_method(year, user_id)
            if campaign_blast:
                response_message = 'Top performing %s campaign from %s is "%s"' \
                                       % (campaign_type, year, campaign_blast.campaign.name)
            else:
                response_message = "Oops! looks like you don't have %s campaign from %s" % \
                                       (campaign_type, year)
        else:
            response_message = "Please enter a valid year greater than 1900"

        return response_message.replace("None", "all the times")

    def question_4_handler(self, message_tokens, user_id):
        """
            Handles question 'how many candidate leads did [user name] import into the
            [talent pool name] in last n months'
            :param int user_id: User Id
            :param message_tokens: User message tokens
            :return: str response_message
        """
        talent_index = self.find_word_in_message('talent', message_tokens)
        import_index = self.find_word_in_message('import', message_tokens)
        # Extracting talent pool name from user's message
        if message_tokens[import_index + 2].lower() != 'the':
            talent_pool_name = message_tokens[import_index + 2:talent_index:]
        else:
            talent_pool_name = message_tokens[import_index + 3:talent_index:]
        # Extracting username from user message
        user_name = message_tokens[import_index - 1]
        spaced_talent_pool_name = self.append_list_with_spaces(talent_pool_name)
        try:
            last_index = self.find_word_in_message('last', message_tokens)
        except IndexError:  # Word 'last' not found in message
            last_index = len(message_tokens)
        user_specific_date = None
        if len(message_tokens) > last_index + 2:
            if message_tokens[last_index + 1].isdigit():
                months = int(message_tokens[last_index + 1])
                user_specific_date = datetime.datetime.utcnow() - relativedelta(months=months)
        count = TalentPoolCandidate.candidates_added_last_month(user_name, spaced_talent_pool_name,
                                                                user_specific_date, user_id)
        response_message = "%s added %d candidates in %stalent pool" %\
                           (user_name.title(), count, spaced_talent_pool_name)
        return response_message

    @classmethod
    def question_5_handler(cls, message_tokens=None, user_id=None):
        """
            Handles question 'what is your name'
            :param int user_id: User Id
            :param message_tokens: User message tokens
            :return: str bot name
        """
        return "My name is " + BOT_NAME

    @classmethod
    def question_6_handler(cls, message_tokens=None, user_id=None):
        """
        Handles if user types 'hint'
        :param int user_id: User Id
        :param message_tokens: User message tokens
        :rtype: str
        """
        return HINT

    @staticmethod
    def is_valid_year(year):
        """
        Validates that string is a valid year
        :param str year: User's entered year string
        :return: True|False
        """
        if year.isdigit():
            year_in_number = int(year)
            if year_in_number > 1900:
                return True
            return False
        return False
