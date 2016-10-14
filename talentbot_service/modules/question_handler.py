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
        :rtype: int|None
        """
        try:
            word_index = [message_tokens.index(temp_word) for temp_word
                          in message_tokens if word in temp_word.lower()][0]
            return word_index
        except IndexError:
            return None

    @staticmethod
    def append_list_with_spaces(_list):
        """
        Append a list elements with spaces between then
        :param _list: list
        :rtype: str
        """
        return ' '.join(_list)

    @classmethod
    def question_0_handler(cls, message_tokens, user_id):
        """
        Handles question 'how many users are there in my domain'
        :param int user_id: User Id
        :param message_tokens: User message tokens
        :return: Response message
        :rtype: str
        """
        users, domain_name = User.get_users_in_domain(user_id)
        if not users:
            return None
        candidate_index = cls.find_word_in_message('cand', message_tokens)
        if candidate_index is not None:
            number_of_candidates = len(users[0].candidates)
            return "Candidates in domain %s : %d" % (domain_name, number_of_candidates)
        return "Users in domain %s : %d" % (domain_name, len(users))

    @classmethod
    def question_1_handler(cls, message_tokens, user_id):
        """
        Handles question 'how many candidates are there with skills [x,y and z]'
        :param int user_id: User Id
        :param message_tokens: User message tokens
        :rtype: str
        """
        skill_index = cls.find_word_in_message('skill', message_tokens)
        if not skill_index:
            skill_index = cls.find_word_in_message('know', message_tokens)
            if not skill_index:
                skill_index = cls.find_word_in_message('grasp', message_tokens)
                if skill_index:
                    if len(message_tokens) > skill_index:
                        if message_tokens[skill_index+1].lower() == 'on':
                            skill_index += 1
        if not skill_index:
            raise IndexError
        if len(message_tokens) <= skill_index+1:
            return 'Please mention skills'
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
        :rtype: str
        """
        zip_index = cls.find_word_in_message('zip', message_tokens)
        if not zip_index:
            raise IndexError
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
        :rtype: str
        """
        campaign_index = self.find_word_in_message('camp', message_tokens)
        if not campaign_index:
            raise IndexError
        campaign_type = message_tokens[campaign_index-1].lower()
        user_specific_date = message_tokens[-1]
        is_valid_year = self.is_valid_year(user_specific_date)
        campaign_method = CAMPAIGN_TYPES.get(campaign_type)
        response_message = ""
        if is_valid_year == -1:
            return "Please enter a valid year greater than 1900 and smaller than current year."
        if is_valid_year is False:
            user_specific_date = None
        last_index = self.find_word_in_message('last', message_tokens)
        if last_index:
            if len(message_tokens) > last_index + 1:
                user_specific_date = self.extract_datetime_from_question(last_index, message_tokens)
        if not campaign_method:
            campaign_list = ['Top Campaigns are following:']
            campaign_blast = CAMPAIGN_TYPES.get("email")(user_specific_date, user_id)
            if campaign_blast:
                open_rate = self.calculate_percentage(campaign_blast.opens, campaign_blast.sends)
                response_message = 'Email Campaign: "%s", open rate %d%% (%d/%d)"' \
                                   % (campaign_blast.campaign.name, open_rate,
                                      campaign_blast.opens, campaign_blast.sends)
                campaign_list.append(response_message)
            campaign_blast = CAMPAIGN_TYPES.get("sms")(user_specific_date, user_id)
            if campaign_blast:
                click_rate = self.calculate_percentage(campaign_blast.clicks, campaign_blast.sends)
                reply_rate = self.calculate_percentage(campaign_blast.replies, campaign_blast.sends)
                response_message = 'SMS Campaign: "%s" with click rate %d%% (%d/%d)' \
                                   ' and reply rate %d%% (%d/%d)"' \
                                   % (campaign_blast.campaign.name, click_rate,
                                      campaign_blast.clicks, campaign_blast.sends, reply_rate,
                                      campaign_blast.replies, campaign_blast.sends)
                campaign_list.append(response_message)
            campaign_blast = CAMPAIGN_TYPES.get("push")(user_specific_date, user_id)
            if campaign_blast:
                click_rate = self.calculate_percentage(campaign_blast.clicks, campaign_blast.sends)
                response_message = 'Push Campaign: "%s" with click rate %d%% (%d/%d)"' \
                                   % (campaign_blast.campaign.name, click_rate,
                                      campaign_blast.clicks, campaign_blast.sends)
                campaign_list.append(response_message)
            if len(campaign_list) < 2:
                campaign_list[0] = "Looks like you don't have any campaigns"
            return '\n'.join(campaign_list)
        campaign_blast = campaign_method(user_specific_date, user_id)
        timespan = self.append_list_with_spaces(message_tokens[last_index::])
        if campaign_blast:
            if isinstance(user_specific_date, datetime.datetime):
                user_specific_date = user_specific_date.date()
            if campaign_type == 'email':
                open_rate = self.calculate_percentage(campaign_blast.opens, campaign_blast.sends)
                response_message = 'Top performing %s campaign from %s is "%s" with open rate %d%% (%d/%d)"' \
                                   % (campaign_type, user_specific_date, campaign_blast.campaign.name, open_rate,
                                      campaign_blast.opens, campaign_blast.sends)
            if campaign_type == 'sms':
                click_rate = self.calculate_percentage(campaign_blast.clicks, campaign_blast.sends)
                reply_rate = self.calculate_percentage(campaign_blast.replies, campaign_blast.sends)
                response_message = 'Top performing %s campaign from %s is "%s" with click rate %d%% (%d/%d)' \
                                   ' and reply rate %d%% (%d/%d)"' \
                                   % (campaign_type, user_specific_date, campaign_blast.campaign.name, click_rate,
                                      campaign_blast.clicks, campaign_blast.sends, reply_rate,
                                      campaign_blast.replies, campaign_blast.sends)
            if campaign_type == 'push':
                click_rate = self.calculate_percentage(campaign_blast.clicks, campaign_blast.sends)
                response_message = 'Top performing %s campaign from %s is "%s" with click rate %d%% (%d/%d)"' \
                                   % (campaign_type, user_specific_date, campaign_blast.campaign.name, click_rate,
                                      campaign_blast.clicks, campaign_blast.sends)
        else:
            response_message = "Oops! looks like you don't have %s campaign from %s" % \
                                    (campaign_type, timespan)

        return response_message.replace("None", "all the times")

    def question_4_handler(self, message_tokens, user_id):
        """
        Handles question 'how many candidate leads did [user name] import into the
        [talent pool name] in last n months'
        :param int user_id: User Id
        :param message_tokens: User message tokens
        :rtype: str
        """
        talent_index = self.find_word_in_message('talent', message_tokens)
        import_index = self.find_word_in_message('import', message_tokens)
        if not import_index:
            import_index = self.find_word_in_message('add', message_tokens)
        if not talent_index or not import_index:
            return "Your question is vague"
        # Extracting talent pool name from user's message
        if message_tokens[import_index + 2].lower() != 'the':
            talent_pool_name = message_tokens[import_index + 2:talent_index:]
        else:
            talent_pool_name = message_tokens[import_index + 3:talent_index:]
        # Extracting username from user message
        user_name = message_tokens[import_index - 1]
        spaced_talent_pool_name = self.append_list_with_spaces(talent_pool_name)
        year = message_tokens[-1]
        is_valid_year = self.is_valid_year(year)
        if is_valid_year is True:
            count = TalentPoolCandidate.candidates_added_last_month(user_name, spaced_talent_pool_name,
                                                                    year, user_id)
            response_message = "%s added %d candidates in %s talent pool" % \
                               (user_name.title(), count, spaced_talent_pool_name)
            return response_message
        if is_valid_year == -1:
            return "Please enter a valid year greater than 1900 and smaller than current year."
        last_index = self.find_word_in_message('last', message_tokens)
        if last_index:
            if len(message_tokens) > last_index + 1:
                user_specific_date = self.extract_datetime_from_question(last_index, message_tokens)
                count = TalentPoolCandidate.candidates_added_last_month(user_name, spaced_talent_pool_name,
                                                                        user_specific_date, user_id)
                response_message = "%s added %d candidates in %s talent pool" % \
                                   (user_name.title(), count, spaced_talent_pool_name)
                return response_message
        count = TalentPoolCandidate.candidates_added_last_month(user_name, spaced_talent_pool_name,
                                                                None, user_id)
        response_message = "%s added %d candidates in %s talent pool" % (user_name.title(), count,
                                                                         spaced_talent_pool_name)
        return response_message

    @classmethod
    def question_5_handler(cls, *args):
        """
        Handles question 'what is your name'
        :param list args: List of args
        :rtype: str|None
        """
        if args:
            return "My name is " + BOT_NAME

    @classmethod
    def question_6_handler(cls, *args):
        """
        Handles if user types 'hint'
        :param list args: List of args
        :rtype: str|None
        """
        if args:
            return HINT

    @staticmethod
    def is_valid_year(year):
        """
        Validates that string is a valid year
        :param str year: User's entered year string
        :rtype: True|False|-1
        """
        if year.isdigit():
            year_in_number = int(year)
            current_year = datetime.datetime.utcnow().year
            if 1900 < year_in_number <= current_year:
                return True
            return -1
        return False

    @staticmethod
    def calculate_percentage(scored, total):
        """
        This function calculates percentage value
        :param int scored:
        :param int total:
        :rtype: float
        """
        return (scored / float(total)) * 100

    @classmethod
    def extract_datetime_from_question(cls, last_index, message_tokens):
        duration = 1
        user_specific_date = None
        duration_type = message_tokens[last_index + 1].lower()
        if message_tokens[last_index + 1].isdigit():
            duration = int(message_tokens[last_index + 1])
            duration_type = message_tokens[last_index + 2]
        if duration_type.lower() in 'years':
            user_specific_date = datetime.datetime.utcnow() - relativedelta(years=duration)
        if duration_type.lower() in 'months':
            user_specific_date = datetime.datetime.utcnow() - relativedelta(months=duration)
        if duration_type.lower() in 'weeks':
            user_specific_date = datetime.datetime.utcnow() - relativedelta(weeks=duration)
        if duration_type.lower() in 'days':
            user_specific_date = datetime.datetime.utcnow() - relativedelta(days=duration)
        return user_specific_date
