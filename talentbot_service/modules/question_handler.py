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
 - question_7_handler()
 - question_8_handler()
"""
# Builtin imports
import datetime
from dateutil.relativedelta import relativedelta
import sys
# Common utils
from talentbot_service.common.models.user import User
from talentbot_service.common.models.candidate import Candidate
from talentbot_service.common.models.talent_pools_pipelines import TalentPoolCandidate
from talentbot_service.common.models.talent_pools_pipelines import TalentPool
# App specific imports
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
    def find_exact_word_in_message(word, message_tokens):
        """
        Finds a specific exact word in user message and returns it's index
        :param str word: Word to be found in message_tokens
        :param list message_tokens: Tokens of user message
        :rtype: int|None
        """
        try:
            word_index = [message_tokens.index(temp_word) for temp_word
                          in message_tokens if word == temp_word.lower()][0]
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
            user = [user for user in users if user.id == user_id]
            number_of_candidates = len(user[0].candidates)
            return "Candidates in domain `%s` : %d" % (domain_name, number_of_candidates)
        return "Users in domain `%s` : %d" % (domain_name, len(users))

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
        response_message = "There are `%d` candidates with skills %s"
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
        response_message = "Number of candidates from zipcode `%s` : `%d`" % \
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
            return "Please enter a valid year greater than `1900` and smaller than `current year`."
        if is_valid_year is False:
            user_specific_date = None
        last_index = self.find_word_in_message('last', message_tokens)
        if last_index and not is_valid_year:
            if len(message_tokens) > last_index + 1:
                user_specific_date = self.extract_datetime_from_question(last_index, message_tokens)
                if isinstance(user_specific_date, basestring):
                    return user_specific_date
        if not campaign_method:
            if not campaign_type.lower() in ['all', 'every', 'performing', 'top']:
                campaign_list = ['No valid campaign type found, all top campaigns are following:\n']
            else:
                campaign_list = ['Top Campaigns are following:\n']
            if not isinstance(user_specific_date, datetime.datetime) and not is_valid_year \
               and user_specific_date is None and message_tokens[-1].lower() not in ['campaigns']:
                campaign_list = ['No valid duration found, Top campaigns from all the times:\n']
            campaign_blast = CAMPAIGN_TYPES.get("email")(user_specific_date, user_id)
            if campaign_blast:
                open_rate = self.calculate_percentage(campaign_blast.opens, campaign_blast.sends)
                response_message = '*Email Campaign:* `%s`, open rate `%d%%` (%d/%d)' \
                                   % (campaign_blast.campaign.name, open_rate,
                                      campaign_blast.opens, campaign_blast.sends)
                campaign_list.append(response_message)
            campaign_blast = CAMPAIGN_TYPES.get("sms")(user_specific_date, user_id)
            if campaign_blast:
                click_rate = self.calculate_percentage(campaign_blast.clicks, campaign_blast.sends)
                reply_rate = self.calculate_percentage(campaign_blast.replies, campaign_blast.sends)
                response_message = '*SMS Campaign:* `%s` with click rate `%d%%` (%d/%d)' \
                                   ' and reply rate `%d%%` (%d/%d)' \
                                   % (campaign_blast.campaign.name, click_rate,
                                      campaign_blast.clicks, campaign_blast.sends, reply_rate,
                                      campaign_blast.replies, campaign_blast.sends)
                campaign_list.append(response_message)
            campaign_blast = CAMPAIGN_TYPES.get("push")(user_specific_date, user_id)
            if campaign_blast:
                click_rate = self.calculate_percentage(campaign_blast.clicks, campaign_blast.sends)
                response_message = '*Push Campaign:* `%s` with click rate `%d%%` (%d/%d)' \
                                   % (campaign_blast.campaign.name, click_rate,
                                      campaign_blast.clicks, campaign_blast.sends)
                campaign_list.append(response_message)
            if len(campaign_list) < 2:
                campaign_list[0] = "Looks like you don't have any campaigns since that time"
            return '%s%s' % (campaign_list[0], self.create_ordered_list(campaign_list[1::]))
        campaign_blast = campaign_method(user_specific_date, user_id)
        timespan = self.append_list_with_spaces(message_tokens[last_index::])
        if is_valid_year:
            timespan = user_specific_date
        if campaign_blast:
            if isinstance(user_specific_date, datetime.datetime):
                user_specific_date = user_specific_date.date()
            if campaign_type == 'email':
                open_rate = self.calculate_percentage(campaign_blast.opens, campaign_blast.sends)
                response_message = 'Top performing `%s` campaign from %s is `%s` with open rate `%d%%` (%d/%d)' \
                                   % (campaign_type, user_specific_date, campaign_blast.campaign.name, open_rate,
                                      campaign_blast.opens, campaign_blast.sends)
            if campaign_type == 'sms':
                click_rate = self.calculate_percentage(campaign_blast.clicks, campaign_blast.sends)
                reply_rate = self.calculate_percentage(campaign_blast.replies, campaign_blast.sends)
                response_message = 'Top performing `%s` campaign from %s is `%s` with click rate `%d%%` (%d/%d)' \
                                   ' and reply rate `%d%%` (%d/%d)' \
                                   % (campaign_type, user_specific_date, campaign_blast.campaign.name, click_rate,
                                      campaign_blast.clicks, campaign_blast.sends, reply_rate,
                                      campaign_blast.replies, campaign_blast.sends)
            if campaign_type == 'push':
                click_rate = self.calculate_percentage(campaign_blast.clicks, campaign_blast.sends)
                response_message = 'Top performing `%s` campaign from %s is `%s` with click rate `%d%%` (%d/%d)' \
                                   % (campaign_type, user_specific_date, campaign_blast.campaign.name, click_rate,
                                      campaign_blast.clicks, campaign_blast.sends)
        else:
            response_message = "Oops! looks like you don't have `%s` campaign from %s" % \
                                    (campaign_type, timespan)
        if not isinstance(user_specific_date, datetime.datetime) and not is_valid_year \
                and user_specific_date is None and message_tokens[-1].lower() not in ['campaigns']:
            response_message = 'No valid time duration found\n %s' % response_message
        return response_message.replace("None", "all the times")

    def question_4_handler(self, message_tokens, user_id):
        """
        Handles question 'how many candidate leads did [user name] import into the
        [talent pool name] in last n months'
        :param int user_id: User Id
        :param message_tokens: User message tokens
        :rtype: str
        """
        user_specific_date = None
        talent_index = self.find_word_in_message('talent', message_tokens)
        import_index = self.find_word_in_message('import', message_tokens)
        if not import_index:
            import_index = self.find_word_in_message('add', message_tokens)
        if not import_index:
            return "Your question is vague"
        # Extracting talent pool name from user's message
        if talent_index is not None:
            if message_tokens[import_index + 2].lower() != 'the':
                talent_pool_name = message_tokens[import_index + 2:talent_index:]
            else:
                talent_pool_name = message_tokens[import_index + 3:talent_index:]
            spaced_talent_pool_name = self.append_list_with_spaces(talent_pool_name)
        else:
            spaced_talent_pool_name = None
        # Extracting username from user message
        if spaced_talent_pool_name:
            if spaced_talent_pool_name.lower() in ['each', 'every', 'all']:
                spaced_talent_pool_name = None
        user_name = message_tokens[import_index - 1]
        is_asking_about_each_user = self.find_word_in_message('user', message_tokens)
        if is_asking_about_each_user is not None or user_name.lower() in ['all', 'every', 'each']:
            user_name = None
        else:
            is_asking_about_each_user = self.find_word_in_message('everyone', message_tokens)
            if is_asking_about_each_user is not None:
                user_name = None
            else:
                is_asking_about_each_user = self.find_word_in_message('everybody', message_tokens)
                if is_asking_about_each_user is not None:
                    user_name = None
        year = message_tokens[-1]
        is_valid_year = self.is_valid_year(year)
        if is_valid_year is True:
            count = TalentPoolCandidate.candidates_added_last_month(user_name, spaced_talent_pool_name,
                                                                    year, user_id)
            if isinstance(count, basestring):
                return count
            if not user_name:
                user_name = "Everyone totally"
            if not spaced_talent_pool_name:
                spaced_talent_pool_name = "all"
            spaced_talent_pool_name = spaced_talent_pool_name.lower().replace(' and ', '` and `')
            response_message = "`%s` added `%d` candidates in `%s` talent pool" % \
                               (user_name, count, spaced_talent_pool_name)
            if spaced_talent_pool_name in ['all']:
                response_message = response_message.replace('pool', 'pools')
            if count == 1:
                response_message = response_message.replace('candidates', 'candidate')
            if user_name == 'Everyone totally':
                response_message = response_message.replace('`Everyone totally`', '`Everyone` totally')
            return response_message
        if is_valid_year == -1:
            return "Please enter a valid year greater than 1900 and smaller than current year."
        last_index = self.find_word_in_message('last', message_tokens)
        if last_index:
            if len(message_tokens) > last_index + 1:
                user_specific_date = self.extract_datetime_from_question(last_index, message_tokens)
                if isinstance(user_specific_date, basestring):
                    return user_specific_date
                count = TalentPoolCandidate.candidates_added_last_month(user_name, spaced_talent_pool_name,
                                                                        user_specific_date, user_id)
                if isinstance(count, basestring):
                    return count
                if not user_name:
                    user_name = "Everyone totally"
                if not spaced_talent_pool_name:
                    spaced_talent_pool_name = "all"
                spaced_talent_pool_name = spaced_talent_pool_name.lower().replace(' and ', '` and `')
                response_message = "`%s` added `%d` candidates in `%s` talent pool" % \
                                   (user_name, count, spaced_talent_pool_name)
                if user_name == 'Everyone totally':
                    response_message = response_message.replace('`Everyone totally`', '`Everyone` totally')
                if spaced_talent_pool_name in ['all']:
                    response_message = response_message.replace('pool', 'pools')
                if count == 1:
                    response_message = response_message.replace('candidates', 'candidate')
                return response_message
        count = TalentPoolCandidate.candidates_added_last_month(user_name, spaced_talent_pool_name,
                                                                None, user_id)
        if isinstance(count, basestring):
            return count
        if not user_name:
            user_name = "Everyone totally"
        if not spaced_talent_pool_name:
            spaced_talent_pool_name = "all"
        spaced_talent_pool_name = spaced_talent_pool_name.lower().replace(' and ', '` and `')
        response_message = "`%s` added `%d` candidates in `%s` talent pool" % (user_name, count,
                                                                               spaced_talent_pool_name)
        if user_name == 'Everyone totally':
            response_message = response_message.replace('`Everyone totally`', '`Everyone` totally')
        if spaced_talent_pool_name in ['all']:
            response_message = response_message.replace('pool', 'pools')
        if count == 1:
            response_message = response_message.replace('candidates', 'candidate')
        if not isinstance(user_specific_date, datetime.datetime) and not is_valid_year \
                and user_specific_date is None and message_tokens[-1].lower() not in ['pool']:
            response_message = 'No valid time duration found, showing result from all the times\n %s' % response_message
        return response_message

    @classmethod
    def question_5_handler(cls, *args):
        """
        Handles question 'what is your name'
        :param list args: List of args
        :rtype: str|None
        """
        if args:
            return "My name is `%s`" % BOT_NAME

    @classmethod
    def question_6_handler(cls, *args):
        """
        Handles if user types 'hint'
        :param list args: List of args
        :rtype: str|None
        """
        if args:
            return HINT

    @classmethod
    def question_7_handler(cls, message_tokens, user_id):
        """
        This method handles question what talent are pools in my domain
        :param int user_id: User Id
        :param message_tokens: User message tokens
        :rtype: str
        """
        talent_pools = TalentPool.get_talent_pools_in_user_domain(user_id)
        _, domain_name = User.get_users_in_domain(user_id)
        if talent_pools:
            talent_pool_names = [talent_pool.name for talent_pool in talent_pools]
            talent_pool_names = cls.create_ordered_list(talent_pool_names)
            header = ["There are %d talent pools in your domain `%s`\n" % (len(talent_pools), domain_name)]
            response = '%s%s' % (header[0], talent_pool_names[::])
            return response.replace('`None`', '')
        response = "Seems like there is no talent pool in your domain `%s`" % domain_name
        return response.replace('`None`', '')

    @classmethod
    def question_8_handler(cls, message_tokens, user_id):
        """
        This method handles question What is my group and what group a user belong to
        :param message_tokens:
        :param int user_id: User Id
        :rtype: str
        """
        belong_index = cls.find_word_in_message('belong', message_tokens)
        if belong_index is None:
            belong_index = cls.find_word_in_message('part', message_tokens)
        is_user_asking_about_himslef = cls.find_exact_word_in_message('i', message_tokens)
        if belong_index is not None and is_user_asking_about_himslef is None:
            user_name = message_tokens[belong_index - 1]
            users = User.get_by_name(user_id, user_name)
            if users:
                user = users[0]
                response = "`%s's` group is `%s`" % (user_name, user.user_group.name)
                return response
            response = 'No user with name `%s` exists in your domain' % user_name
            return response
        users = User.get_by_id(user_id)
        if users:
            user = users[0]
            response = "Your group is `%s`" % user.user_group.name
            return response
        response = "Something went wrong you do not exist as a user contact the developer"
        return response

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
            if duration > sys.maxint:
                return "Number's max range exceeded"
            duration_type = message_tokens[last_index + 2]
        if message_tokens[last_index + 1][0] == '-':
            return 'Negative numbers are not acceptable'
        if duration_type.lower() in 'years':
            user_specific_date = datetime.datetime.utcnow() - relativedelta(years=duration)
        if duration_type.lower() in 'months':
            user_specific_date = datetime.datetime.utcnow() - relativedelta(months=duration)
        if duration_type.lower() in 'weeks':
            user_specific_date = datetime.datetime.utcnow() - relativedelta(weeks=duration)
        if duration_type.lower() in 'days':
            user_specific_date = datetime.datetime.utcnow() - relativedelta(days=duration)
        return user_specific_date

    @staticmethod
    def create_ordered_list(_list):
        """
        This method creates an ordered list
        :param list _list: List of same string elements
        :rtype str:
        """
        for list_element in _list:
            ordered_talent_pool_name = "%d- %s" % (_list.index(list_element) + 1, list_element)
            _list[_list.index(list_element)] = ordered_talent_pool_name
        return '\n\n'.join(_list)
