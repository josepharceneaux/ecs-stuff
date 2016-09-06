"""
This module has class QuestionHandler which handles questions and generates an appropriate
response
 - find_word_in_message()
 - append_list_withs_paces()
 - question_0_handler
 - question_1_handler
 - question_2_handler
 - question_3_handler
 - question_4_handler
 - question_5_handler
 - question_6_handler
"""
# Builtin imports
import datetime
from dateutil.relativedelta import relativedelta
# Common utils
from talentbot_service.common.models.user import User
from talentbot_service.common.models.candidate import Candidate
from talentbot_service.common.models.email_campaign import EmailCampaignBlast
from talentbot_service.common.models.talent_pools_pipelines import TalentPoolCandidate
from talentbot_service.modules.constants import HINT, BOT_NAME


class QuestionHandler:
    def __init__(self):
        pass

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
    def question_0_handler(cls, message_tokens):
        """
        Handles question 'how many users are there with domain [x]'
        :param message_tokens: User message tokens
        :return: str response_message
        """
        domain_index = cls.find_word_in_message('domain', message_tokens)
        domain_name = message_tokens[domain_index + 1]
        count = User.get_user_count_in_domain(domain_name)
        response_message = "Users in domain " + message_tokens[domain_index + 1] + " : "
        response_message += str(count)
        return response_message

    @classmethod
    def question_1_handler(cls, message_tokens):
        """
            Handles question 'how many candidates are there with skills [x,y and z]'
            :param message_tokens: User message tokens
            :return: str response_message
        """
        skill_index = cls.find_word_in_message('skill', message_tokens)
        extracted_skills = message_tokens[skill_index + 1::]
        count = Candidate.get_candidate_count_with_skills(extracted_skills)
        response_message = "There are %d candidates with skills " + ' '.join(extracted_skills)
        response_message = response_message % count
        if count == 1:
            response_message = response_message.replace('are', 'is'). \
                replace('candidates', 'candidate')
        return response_message

    @classmethod
    def question_2_handler(cls, message_tokens):
        """
            Handles question 'how many candidates are there from zipcode [x]'
            :param message_tokens: User message tokens
            :return: str response_message
        """
        zip_index = cls.find_word_in_message('zip', message_tokens)
        zipcode = message_tokens[zip_index + 1]
        count = Candidate.get_candidate_count_from_zipcode(zipcode)
        response_message = "Number of candidates from zipcode " + \
                           message_tokens[zip_index + 1] + " : "
        response_message += str(count)
        return response_message

    @classmethod
    def question_3_handler(cls, message_tokens):
        """
            Handles question 'what's the top performing email campaign from [year]'
            :param message_tokens: User message tokens
            :return: str response_message
        """
        year = message_tokens[-1]
        email_campaign_blast = EmailCampaignBlast.top_performing_email_campaign(year)
        if email_campaign_blast:
            response_message = 'Top performing email campaign from ' + year + \
                               ' is "%s"' % email_campaign_blast.campaign.name
        else:
            response_message = "Sorry couldn't find top email campaign from " + year
        return response_message

    def question_4_handler(self, message_tokens):
        """
            Handles question 'how many candidate leads did [user name] import into the
            [talent pool name] last month'
            :param message_tokens: User message tokens
            :return: str response_message
        """
        talent_index = self.find_word_in_message('talent', message_tokens)
        import_index = self.find_word_in_message('import', message_tokens)
        # Extracting talent pool name from user's message
        talent_pool_name = message_tokens[import_index + 3:talent_index:]
        # Extracting username from user message
        user_name = message_tokens[import_index - 1]
        spaced_talent_pool_name = self.append_list_with_spaces(talent_pool_name)
        previous_month = datetime.datetime.now() - relativedelta(months=1)
        count = TalentPoolCandidate.candidates_added_last_month(user_name, spaced_talent_pool_name,
                                                                previous_month)
        response_message = user_name.title() + " added %d candidates in " \
                                             + spaced_talent_pool_name + "talent pool last month"
        response_message = response_message % count
        return response_message

    @classmethod
    def question_5_handler(cls, message_tokens):
        """
            Handles question 'what is your name'
            :param message_tokens: User message tokens
            :return: str bot name
        """
        return "My name is " + BOT_NAME

    @classmethod
    def question_6_handler(cls, message_tokens):
        """
        Handles if user types 'hint'
        :param message_tokens: User message tokens
        :rtype: str
        """
        return HINT[0]
