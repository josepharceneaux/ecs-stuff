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
 - question_7_handler()
 - question_8_handler()
"""
# Builtin imports
import os
import re
import urllib
import urllib2
from datetime import datetime
from os.path import splitext
from random import randint
from time import sleep
from urlparse import urlparse
from contracts import contract
from dateutil.relativedelta import relativedelta
# Common utils
from talentbot_service.common.talent_config_manager import TalentConfigKeys
from talentbot_service.common.utils.talentbot_utils import DOMAIN_SPECIFIC, OWNED
from talentbot_service.common.error_handling import NotFoundError, InvalidUsage, InternalServerError
from talentbot_service.common.models.user import User
from talentbot_service.common.models.candidate import Candidate
from talentbot_service.common.models.talent_pools_pipelines import TalentPoolCandidate, TalentPipeline
from talentbot_service.common.models.talent_pools_pipelines import TalentPool
from talentbot_service.common.models.email_campaign import EmailCampaign
from talentbot_service.common.models.sms_campaign import SmsCampaign
from talentbot_service.common.models.push_campaign import PushCampaign
from talentbot_service.common.routes import ResumeApiUrl, CandidateApiUrl
from talentbot_service.common.utils.handy_functions import send_request
from talentbot_service.common.utils.resume_utils import IMAGE_FORMATS, DOC_FORMATS
from talentbot_service.common.utils.talent_s3 import boto3_put, create_bucket_using_boto3,\
    delete_from_filepicker_using_boto3
from talentbot_service.common.redis_cache import redis_store
# App specific imports
from talentbot_service.modules.constants import BOT_NAME, CAMPAIGN_TYPES, MAX_NUMBER_FOR_DATE_GENERATION,\
    QUESTION_HANDLER_NUMBERS, EMAIL_CAMPAIGN, PUSH_CAMPAIGN, ZERO, SMS_CAMPAIGN,\
    SOMETHING_WENT_WRONG, TEN_MB, INVALID_RESUME_URL_MSG, NO_RESUME_URL_FOUND_MSG, TOO_LARGE_RESUME_MSG, \
    SUPPORTED_SOCIAL_SITES, GITHUB, STACK_OVERFLOW, LINKEDIN, INVALID_INPUT, CANDIDATE_ALREADY_EXISTS, TWITTER, FACEBOOK, \
    CLASSES, USER_CLIENTS
from talentbot_service import logger, app
# 3rd party imports
from flask import json
from requests import codes
import requests


class QuestionHandler(object):
    """
    This class contains question handlers against questions and some helping methods
    """
    def __init__(self):
        pass

    @staticmethod
    def find_word_in_message(word, message_tokens, exact_word=False):
        """
        Finds a specific word in user message and returns it's index
        :param boole exact_word: Weather find partially or completely
        :param str word: Word to be found in message_tokens
        :param list message_tokens: Tokens of user message
        :rtype: int|None
        """
        word_index = None
        for index, token in enumerate(message_tokens):
            if exact_word:
                if word == token.lower():
                    word_index = index
            else:
                if word in token.lower():
                    word_index = index
        return word_index

    @staticmethod
    def append_list_with_spaces(_list):
        """
        Append a list elements with spaces
        :param _list: list
        :rtype: str
        """
        return ' '.join(_list)

    @classmethod
    def question_0_handler(cls, message_tokens, user_id, user_client=None):
        """
        Handles question 'how many users are there in my domain'
        :param positive|None user_client: User client weather Slack, Facebook, SMS or Email
        :param int user_id: User Id
        :param message_tokens: User message tokens
        :return: Response message
        :rtype: str
        """
        users, domain_name = User.get_domain_name_and_its_users(user_id)
        if not users:
            return None
        candidate_index = cls.find_word_in_message('cand', message_tokens)
        if candidate_index is not None:
            number_of_candidates = ZERO
            if users:
                domain_id = users[0].domain_id
                candidates = Candidate.get_all_in_user_domain(domain_id, is_hidden=ZERO)
                number_of_candidates = len(candidates)
            return "Candidates in domain `%s` : %d" % (domain_name, number_of_candidates)
        return "Users in domain `%s` : %d" % (domain_name, len(users))

    @classmethod
    def question_1_handler(cls, message_tokens, user_id, user_client=None):
        """
        Handles question 'how many candidates are there with skills [x,y and z]'
        :param positive|None user_client: User client weather Slack, Facebook, SMS or Email
        :param int user_id: User Id
        :param message_tokens: User message tokens
        :rtype: str
        """
        # Finding word 'skill,know or grasp' in user's message so that we can extract actual skills from question
        # I assume that after word 'skill' in user message there are actual skills
        skill_index = cls.find_optional_word(message_tokens, ['skill', 'know', 'grasp'])
        if len(message_tokens) > skill_index + 1:
            if message_tokens[skill_index + 1].lower() == 'on':
                skill_index += 1
        if skill_index is None:
            raise IndexError
        if len(message_tokens) <= skill_index+1:
            return 'Please mention skills properly'
        extracted_skills = map(unicode.strip, [skill for skill in message_tokens[skill_index + 1::] if skill])
        count = Candidate.get_candidate_count_with_skills(extracted_skills, user_id)
        response_message = "There are `%d` candidates with skills %s"
        response_message = response_message % (count, ', '.join(extracted_skills))
        if count == 1:
            response_message = response_message.replace('are', 'is').replace('candidates', 'candidate')
        if len(extracted_skills) > 1:
            response_message = cls.append_count_with_message(response_message, extracted_skills, 1, user_id)
        # Not removing 'and' in actual skills for better response generation, just replacing 'and' with commas
        #  around it with simple 'and'.
        return response_message.replace(', and,', ' and').replace('and,', 'and')

    @classmethod
    def question_2_handler(cls, message_tokens, user_id, user_client=None):
        """
        Handles question 'how many candidates are there from zipcode [x]'
        :param positive|None user_client: User client weather Slack, Facebook, SMS or Email
        :param int user_id: User Id
        :param message_tokens: User message tokens
        :rtype: str
        """
        zip_index = cls.find_word_in_message('zip', message_tokens)
        if zip_index is None:
            raise IndexError
        code_index = cls.find_word_in_message('code', message_tokens, exact_word=True)
        if code_index is not None:
            message_tokens.pop(code_index)
        zipcode = message_tokens[zip_index + 1]
        if not zipcode.isdigit():
            return 'Invalid zipcode specified'
        count = Candidate.get_candidate_count_from_zipcode(zipcode, user_id)
        response_message = "Number of candidates from zipcode `%s` : `%d`" % (message_tokens[zip_index + 1], count)
        return response_message

    def question_3_handler(self, message_tokens, user_id, user_client=None):
        """
        Handles question 'what's the top performing [campaign name] campaign from [year]'
        :param positive|None user_client: User client weather Slack, Facebook, SMS or Email
        :param int user_id: User Id
        :param message_tokens: User message tokens
        :rtype: str
        """
        campaign_index = self.find_word_in_message('camp', message_tokens)
        if campaign_index is None:
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
        last_index = self.find_optional_word(message_tokens, ['last', 'from'])
        if last_index is not None and not is_valid_year:
            if len(message_tokens) > last_index + 1:
                user_specific_date = self.extract_datetime_from_question(last_index, message_tokens)
                if isinstance(user_specific_date, basestring):
                    return user_specific_date
        if not campaign_method:
            if not campaign_type.lower() in ['all', 'every', 'performing', 'top']:
                campaign_list = ['No valid campaign type found, all top campaigns are following:\n']
            else:
                campaign_list = ['Top Campaigns are following:\n']
            if not isinstance(user_specific_date, datetime) and not is_valid_year \
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
        timespan_starting_index = last_index if last_index is not None else len(message_tokens)
        timespan = self.append_list_with_spaces(message_tokens[timespan_starting_index::])
        if is_valid_year:
            timespan = user_specific_date
        if campaign_blast:
            if isinstance(user_specific_date, datetime):
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
            response_message = "Oops! looks like you don't have `%s` campaigns %s" % \
                                    (campaign_type, "from %s" % timespan if timespan else '')
        if not isinstance(user_specific_date, datetime) and not is_valid_year \
                and user_specific_date is None and message_tokens[-1].lower() not in ['campaigns']:
            response_message = 'No valid time duration found\n %s' % response_message
        return response_message.replace("None", "all the times").replace('from from', 'from')

    def question_4_handler(self, message_tokens, user_id, user_client=None):
        """
        Handles question 'how many candidate leads did [user name] import into the
        [talent pool name] in last n months'
        :param positive|None user_client: User client weather Slack, Facebook, SMS or Email
        :param int user_id: User Id
        :param message_tokens: User message tokens
        :rtype: str
        """
        user_specific_date = None
        talent_index = self.find_word_in_message('talent', message_tokens, exact_word=True)
        import_index = self.find_optional_word(message_tokens, ['import', 'add'])
        if import_index is None:
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
            is_asking_about_each_user = self.find_optional_word(message_tokens, ['everyone', 'everybody'])
            if is_asking_about_each_user is not None:
                user_name = None
        year = message_tokens[-1]
        is_valid_year = self.is_valid_year(year)
        if is_valid_year is True:
            talent_pool_list = self.create_list_of_talent_pools(spaced_talent_pool_name)
            try:
                count = TalentPoolCandidate.candidate_imports(user_id, user_name, talent_pool_list,
                                                              year)
            except NotFoundError:
                return 'No user exists in your domain with the name `%s`' % user_name
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
            if isinstance(talent_pool_list, list) and len(talent_pool_list) > 1 and user_name is not None \
                    and user_name != 'Everyone totally':
                response_message = self.append_count_with_message(response_message, talent_pool_list, 4, user_id,
                                                                  user_name, user_specific_date)
            return re.sub(r'`i`|`I`', '`You`', response_message)
        if is_valid_year == -1:
            return "Please enter a valid year greater than 1900 and smaller than current year."
        last_index = self.find_word_in_message('last', message_tokens)
        if last_index is not None:
            if len(message_tokens) > last_index + 1:
                user_specific_date = self.extract_datetime_from_question(last_index, message_tokens)
                if isinstance(user_specific_date, basestring):
                    return user_specific_date
                talent_pool_list = self.create_list_of_talent_pools(spaced_talent_pool_name)
                try:
                    count = TalentPoolCandidate.candidate_imports(user_id, user_name, talent_pool_list,
                                                                  user_specific_date)
                except NotFoundError:
                    return 'No user exists in your domain with the name `%s`' % user_name
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
                if isinstance(talent_pool_list, list) and len(talent_pool_list) > 1 and user_name is not None \
                        and user_name != 'Everyone totally':
                    response_message = self.append_count_with_message(response_message, talent_pool_list, 4, user_id,
                                                                      user_name, user_specific_date)
                return re.sub(r'`i`|`I`', '`You`', response_message)
        talent_pool_list = self.create_list_of_talent_pools(spaced_talent_pool_name)
        try:
            count = TalentPoolCandidate.candidate_imports(user_id, user_name, talent_pool_list)
        except NotFoundError:
            if user_name.lower() == 'i':
                return "Oops! Something went wrong"
            return 'No user exists in your domain with the name `%s`' % user_name
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
        if not isinstance(user_specific_date, datetime) and not is_valid_year \
                and user_specific_date is None and message_tokens[-1].lower() not in ['pool']:
            response_message = 'No valid time duration found, showing result from all the times\n %s' % response_message
        if isinstance(talent_pool_list, list) and len(talent_pool_list) > 1 and user_name is not None \
                and user_name != 'Everyone totally':
            response_message = self.append_count_with_message(response_message, talent_pool_list, 4, user_id,
                                                              user_name, user_specific_date)
        return re.sub(r'`i`|`I`', '`You`', response_message)

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
    def question_6_handler(cls, message_tokens, user_id, user_client=None):
        """
        This method handles question what are the talent pools in my domain
        :param positive|None user_client: User client weather Slack, Facebook, SMS or Email
        :param int user_id: User Id
        :param message_tokens: User message tokens
        :rtype: str
        """
        via_sms = True if user_client == USER_CLIENTS["SMS"] else False
        talent_pools = TalentPool.get_talent_pools_in_user_domain(user_id, 1 if via_sms else None)
        _, domain_name = User.get_domain_name_and_its_users(user_id)
        if talent_pools:
            talent_pool_number = len(talent_pools)
            is_or_are = 'is' if talent_pool_number == 1 else 'are'
            plural = '' if talent_pool_number == 1 else 's'
            header = ["There %s %d talent pool%s in your domain `%s`\n" % (is_or_are, talent_pool_number, plural,
                                                                           domain_name)]
            if via_sms:
                state = [{"class": "TalentPool", "method": "get_talent_pools_in_user_domain",
                         "params": [user_id, 1], "repr": "talent pools"}]
                redis_store.set("bot-pg-%d" % user_id, json.dumps(state))
                if talent_pool_number == 10:
                    header = ["Top 10 talent pools in your domain `%s` are following:\n"
                              " Type `next` to view next 10\n" % domain_name]
            response = cls.custom_count_appender(1, talent_pools, "talent pools", header)
            return response.replace('`None`', '')
        response = "Seems like there is no talent pool in your domain `%s`" % domain_name
        return response.replace('`None`', '')

    @classmethod
    def question_7_handler(cls, message_tokens, user_id, user_client=None):
        """
        This method handles question What is my group, what group a user belongs to and what are my group
        campaigns|pipelines
        :param positive|None user_client: User client weather Slack, Facebook, SMS or Email
        :param message_tokens:
        :param int user_id: User Id
        :rtype: str
        """
        # Checking if user's asking about group campaigns
        group_campaigns = True if cls.find_word_in_message('campa', message_tokens) is not None else False
        group_pipelines = True if cls.find_word_in_message('pipeline', message_tokens) is not None else False
        if group_campaigns:
            response = ["Campaigns in your group are following:"]
            try:
                email_campaigns = EmailCampaign.email_campaigns_in_user_group(user_id)
                push_campaigns = PushCampaign.push_campaigns_in_user_group(user_id)
                sms_campaigns = SmsCampaign.sms_campaign_in_user_group(user_id)
            except NotFoundError:
                return "Seems like you don't belong to a group"
            if email_campaigns:  # Appending email campaigns in a representable response list
                response.append("*Email Campaigns*")
                for index, email_campaign in enumerate(email_campaigns):
                    response.append("%d: `%s`" % (index + 1, email_campaign.name))
            if push_campaigns:  # Appending push campaigns in a representable response list
                response.append("*Push Campaigns*")
                for index, push_campaign in enumerate(push_campaigns):
                    response.append("%d: `%s`" % (index + 1, push_campaign.name))
            if sms_campaigns:  # Appending sms campaigns in a representable response list
                response.append("*SMS Campaigns*")
                for index, sms_campaign in enumerate(sms_campaigns):
                    response.append("%d: `%s`" % (index + 1, sms_campaign.name))
            return '\n'.join(response) if len(response) > 1 else 'No campaigns exist in your group'
        if group_pipelines:
            via_sms = True if user_client == USER_CLIENTS["SMS"] else False
            pipelines = TalentPipeline.pipelines_user_group(user_id, 1 if via_sms else None)
            response = ["Pipelines in your group are following:"]
            if pipelines:
                response.append("*Pipelines*")
                response = cls.custom_count_appender(1, pipelines, "pipelines", response)
                state = [{"class": "TalentPipeline", "method": "pipelines_user_group",
                          "params": [user_id, 1],
                          "repr": "pipelines"}]
                redis_store.set("bot-pg-%d" % user_id, json.dumps(state))
            return response
        belong_index = cls.find_optional_word(message_tokens, ['belong', 'part'])
        is_user_asking_about_himself = cls.find_word_in_message('i', message_tokens, exact_word=True)
        if belong_index is not None and is_user_asking_about_himself is None:
            user_name = message_tokens[belong_index - 1]
            domain_id = User.get_domain_id(user_id)
            users = User.get_by_domain_id_and_name(domain_id, user_name)
            if users:
                user = users[0]
                if user.user_group:
                    response = "`%s`'s group is `%s`" % (user_name, user.user_group.name)
                    return response
                return "`%s` doesn't belong to any group" % user_name
            response = 'No user with name `%s` exists in your domain' % user_name
            return response
        user = User.get_by_id(user_id)
        if user:
            response = "Your group is `%s`" % user.user_group.name
            return response
        response = "Something went wrong you do not exist as a user contact the developer"
        return response

    @classmethod
    @contract
    def question_8_handler(cls, message_tokens, user_id, user_client=None):
        """
        Handles question 'What are my campaigns, What are my campaigns in <x> talent pool'
        :param positive|None user_client: User client weather Slack, Facebook, SMS or Email
        :param list message_tokens: Tokens of User message
        :param positive user_id:
        :rtype: string
        """
        via_sms = True if user_client == USER_CLIENTS["SMS"] else False
        is_group_campaigns = True if cls.find_word_in_message('group', message_tokens, True) is not None else False
        if is_group_campaigns:  # If user's asking for campaigns in his group we already have handler for that
            return cls.question_7_handler(message_tokens, user_id)
        asking_about_his_pool = bool(re.search(r'my talent pool*|my all talent pool*',
                                               ' '.join(message_tokens).lower()))
        asking_about_all_pools = bool(re.search(r'([^m][^y][ ])(all talent pool*|our talent pool*)', ' '.
                                                join(message_tokens).lower()))
        # Checking weather user's asking about all campaigns or his/her campaigns
        asking_about_all_campaigns = not bool(re.search(r'my camp*|my all camp*', ' '.join(message_tokens).lower()))
        # Extracting talentpool names
        talent_pool_index = cls.find_word_in_message('talent', message_tokens, True)
        asking_about_specific_pool = (not asking_about_all_pools and
                                      not asking_about_his_pool and talent_pool_index is not None)
        email_campaigns, sms_campaigns, push_campaigns = (None, None, None)
        response = []
        scope = OWNED if not asking_about_all_campaigns else DOMAIN_SPECIFIC
        page_number = 1 if via_sms else None
        if asking_about_all_pools or asking_about_his_pool or asking_about_specific_pool:
            user_talent_pool_names = None
            if asking_about_his_pool:  # If user's asking about his talent pools
                user_talent_pool_names = TalentPool.get_talent_pool_owned_by_user(user_id)
                user_talent_pool_names = [pool_name[0] for pool_name in user_talent_pool_names]
            if asking_about_specific_pool:  # If user has specified some talent pool's name
                campaign_index = cls.find_word_in_message('camp', message_tokens)  # Extracting Talentpool names
                if campaign_index is not None and talent_pool_index is not None:
                    if len(message_tokens) > campaign_index:
                        if message_tokens[campaign_index + 1].lower() == 'in':
                            campaign_index += 1
                    talent_pool_names = message_tokens[campaign_index + 1:talent_pool_index:]
                    user_talent_pool_names = cls.create_list_of_talent_pools('\\'.join(talent_pool_names))
                    response.append("Campaigns in %s talent pools" %
                                    (' ,'.join(
                                        ["`%s`" % talent_pool_name for talent_pool_name in user_talent_pool_names])
                                     if user_talent_pool_names else "all"))
            state_array = []  # To store multiple methods as a single state e.g Email, Push and SMS Campaigns
            email_campaigns = EmailCampaign.email_campaigns_in_talent_pool(user_id, scope, user_talent_pool_names,
                                                                           page_number)
            push_campaigns = PushCampaign.push_campaigns_in_talent_pool(user_id, scope, user_talent_pool_names,
                                                                        page_number)
            sms_campaigns = SmsCampaign.sms_campaigns_in_talent_pool(user_id, scope, user_talent_pool_names,
                                                                     page_number)
            if via_sms:
                # Generating State object and appending it in state_array
                state_array.append(cls.create_state_object("PushCampaign", "push_campaigns_in_talent_pool",
                                                           [user_id, scope, user_talent_pool_names, 1],
                                                           "Push Campaigns"))
                state_array.append(cls.create_state_object("EmailCampaign", "email_campaigns_in_talent_pool",
                                                           [user_id, scope, user_talent_pool_names, 1],
                                                           "Email Campaigns"))
                state_array.append(cls.create_state_object("SmsCampaign", "sms_campaigns_in_talent_pool",
                                                           [user_id, scope, user_talent_pool_names, 1],
                                                           "SMS Campaigns"))
                cls.save_state(state_array, user_id)
        is_asking_for_campaigns_in_pool = not asking_about_specific_pool and not \
            asking_about_all_pools and not asking_about_his_pool
        # Appending suitable response header
        response = ["Campaigns in your domain are following:"] if (is_asking_for_campaigns_in_pool
                                                                       and asking_about_all_campaigns) else \
            ["Your Campaigns are following:"] if not asking_about_all_campaigns and is_asking_for_campaigns_in_pool\
            else ["Campaigns in all Talent pools"] if asking_about_all_pools else ["Campaigns in your Talent pools"] \
            if asking_about_his_pool else ["Campaigns in your group are following:"] if len(response) == 0 else response
        # if via_sms:
        #     response[0] = response[0].lower().replace("campaigns", "top 10 campaigns").title()
        domain_id = User.get_domain_id(user_id) if is_asking_for_campaigns_in_pool else None
        # Getting campaigns
        if is_asking_for_campaigns_in_pool:
            state_array = []
            email_campaigns = EmailCampaign.get_by_domain_id(domain_id, page_number) if asking_about_all_campaigns else\
                EmailCampaign.get_by_user_id(user_id, page_number)
            push_campaigns = PushCampaign.get_by_domain_id(domain_id, page_number) if asking_about_all_campaigns else\
                PushCampaign.get_by_user_id(user_id, page_number)
            sms_campaigns = SmsCampaign.get_by_domain_id(domain_id, page_number) if asking_about_all_campaigns else\
                SmsCampaign.get_by_user_id(user_id, page_number)
            if via_sms:
                # Generating State object and appending it in state_array
                method_name = "get_by_domain_id" if asking_about_all_campaigns else "get_by_user_id"
                parameters = [domain_id, 1] if asking_about_all_campaigns else [user_id, 1]
                state_array.append(cls.create_state_object("SmsCampaign", method_name, parameters, "Sms Campaigns"))
                state_array.append(cls.create_state_object("PushCampaign", method_name, parameters, "Push Campaigns"))
                state_array.append(cls.create_state_object("EmailCampaign", method_name, parameters, "Email Campaigns"))
                cls.save_state(state_array, user_id)

        if email_campaigns:  # Appending email campaigns in a representable response list
            counter, _index = 0, len(response)
            for index, email_campaign in enumerate(email_campaigns):
                counter += 1
                response.append("%d: `%s`" % (index + 1, email_campaign.name))
            response.insert(_index, "*Top 10 Email Campaigns*" if via_sms and counter == 10 else "*Email Campaigns*")
            if not counter:
                response.pop()
        if push_campaigns:  # Appending push campaigns in a representable response list
            counter, _index = 0, len(response)
            for index, push_campaign in enumerate(push_campaigns):
                response.append("%d: `%s`" % (index + 1, push_campaign.name))
                counter += 1
            response.insert(_index, "*Top 10 Push Campaigns*" if via_sms and counter == 10 else "*Push Campaigns*")
            if not counter:
                response.pop()
        if sms_campaigns:  # Appending sms campaigns in a representable response list
            counter, _index = 0, len(response)
            for index, sms_campaign in enumerate(sms_campaigns):
                response.append("%d: `%s`" % (index + 1, sms_campaign.name))
                counter += 1
            response.insert(_index, "*Top 10 SMS Campaigns*" if via_sms and counter == 10 else "*SMS Campaigns*")
            if not counter:
                response.pop()
        return '\n'.join(response) if len(response) > 1 else "No Campaign found"  # Returning string

    @classmethod
    @contract
    def question_9_handler(cls, message_tokens, user_id, user_client=None):
        """
        This method handles question 'show me <x>'
        :param positive|None user_client: User client weather Slack, Facebook, SMS or Email
        :param list message_tokens:
        :param positive user_id:
        :rtype: string
        """
        # Getting index before meaningful data
        name_index = cls.find_optional_word(message_tokens, ['about', 'me', 'show', 'is'], True)
        if name_index is None:
            return "No name specified"
        if message_tokens[-1].lower() in 'performing':
            message_tokens.pop(-1)
        name = ' '.join(message_tokens[name_index + 1::])  # User specified name
        # Finding (Email|SMS|Push)Campaigns and TalentPipelines against this name
        domain_id = User.get_domain_id(user_id)
        email_campaigns = EmailCampaign.get_by_domain_id_and_name(domain_id, name)
        push_campaigns = PushCampaign.get_by_domain_id_and_name(domain_id, name)
        talent_pipelines = TalentPipeline.get_by_domain_id_and_name(domain_id, name)
        sms_campaigns = SmsCampaign.get_by_domain_id_and_name(domain_id, name)
        nothing_found = not email_campaigns and not talent_pipelines and not push_campaigns and not sms_campaigns
        if nothing_found:
            return "Nothing found with name `%s`" % name
        response = []
        # Preparing response against each Entity
        response += cls.prepare_blast_results(email_campaigns, name, EMAIL_CAMPAIGN)
        response += cls.prepare_blast_results(push_campaigns, name, PUSH_CAMPAIGN)
        response += cls.prepare_blast_results(sms_campaigns, name, SMS_CAMPAIGN)
        for pipeline in talent_pipelines:  # Appending all found TalentPipelines' results
            response.append("Pipeline `%s` exists in `%s` talent pool which has `%d` candidates and this pipeline was "
                            "created by `%s`" % (pipeline.name, pipeline.talent_pool.name,
                                                 TalentPoolCandidate.candidate_imports
                                                 (user_id, talent_pool_list=[pipeline.talent_pool.name]),
                                                 pipeline.user.name))
        return '\n'.join(response)  # Converting list to string

    @classmethod
    @contract
    def question_10_handler(cls, message_tokens, user_id, user_client=None):
        """
        Handles question 'What are my|all pipelines'
        :param positive|None user_client: User client weather Slack, Facebook, SMS or Email
        :param list message_tokens: Tokens of User message
        :param positive user_id:
        :rtype: string
        """
        # Checking whether user's asking about all pipelines or his/her pipelines
        via_sms = user_client == USER_CLIENTS["SMS"]
        asking_about_all_pipelines = not bool(re.search(r'my pipe*|my all pipe*', ' '.join(message_tokens).lower()))
        response = ["Your pipelines are following:"] if not asking_about_all_pipelines else\
            ["Pipelines in your domain are following:"]
        scope = DOMAIN_SPECIFIC if asking_about_all_pipelines else OWNED
        if via_sms:  # Saving state for pagination
            state = [{"class": "TalentPipeline", "method": "get_own_or_domain_pipelines", "params": [user_id, scope, 1],
                     "repr": "pipelines"}]
            redis_store.set("bot-pg-%d" % user_id, json.dumps(state))
            pipelines = TalentPipeline.get_own_or_domain_pipelines(user_id, scope, 1)
            if len(pipelines) == 10:
                response[0] = response[0].lower().replace("pipelines", "top 10 pipelines").title()
        else:
            pipelines = TalentPipeline.get_own_or_domain_pipelines(user_id, scope)
        return cls.custom_count_appender(1, pipelines, "pipelines", response)

    @staticmethod
    @contract
    def custom_count_appender(start, _list, representative, response):
        """

        :param list response:
        :param positive start:
        :param list _list:
        :param string representative:
        :rtype: string
        """
        for index, item in enumerate(_list):
            response.append("%d- `%s`" % (start + index, item.name))
        return '\n'.join(response) if len(response) > 1 else "No %s found" % representative

    @classmethod
    @contract
    def add_candidate_handler(cls, message_tokens, user_id, user_client=None):
        """
        Adds candidate from a resume url mentioned in message by user
        :param list message_tokens: Tokens of User message
        :param positive user_id: User Id
        :rtype: string
        """
        try:
            resume_url = re.search("(?P<url>((https?)|(ftps?))://[^\s]+)", ' '.join(message_tokens)).group("url")
            resume_url = resume_url.strip('>')
            extension, hostname, resume_size_in_bytes = cls.parse_resume_url(resume_url)
            # Supported social sites' array
            supported_social_sites_array = [SUPPORTED_SOCIAL_SITES[GITHUB], SUPPORTED_SOCIAL_SITES[TWITTER],
                                            SUPPORTED_SOCIAL_SITES[STACK_OVERFLOW]]
            is_hostname_in_supported_social_sites = hostname in supported_social_sites_array \
                                                or SUPPORTED_SOCIAL_SITES[LINKEDIN] in hostname \
                                                or SUPPORTED_SOCIAL_SITES[FACEBOOK] in hostname
            # If it is social profile link it wont have an extension
            if not extension and is_hostname_in_supported_social_sites:
                response_message = cls.get_candidate_from_openweb_and_add(user_id, resume_url)
                if response_message:
                    return response_message
                else:
                    return "Sorry, I couldn't find information on %s" % resume_url
            elif int(resume_size_in_bytes) >= TEN_MB:
                resume_size_in_mbs = float(resume_size_in_bytes)/(1024*1024)
                return TOO_LARGE_RESUME_MSG % resume_size_in_mbs
            '''
            create_bucket() method checks if resume bucket exists on S3 if it does create_bucket() returns bucket
            object if it does not exist create_bucket() creates the bucket with a predefined name (stored in cfg file).
            If some error occurs while creating bucket create_bucket() raises InternalServerError
            '''
            create_bucket_using_boto3(app.config['S3_FILEPICKER_BUCKET_NAME'])
            # saving resume in S3 bucket
            filepicker_key = cls.download_resume_and_save_in_bucket(resume_url, user_id, extension)
            return cls.parse_resume_and_add_candidate(user_id, filepicker_key)
        except AttributeError as error:
            logger.error("Attribute error occurred while resolving resume url Error: %s" % error.message)
            return NO_RESUME_URL_FOUND_MSG
        except (urllib2.HTTPError, urllib2.URLError) as error:
            logger.error("HTTPError occurred while resolving resume url Error: %s" % error.message)
            return INVALID_RESUME_URL_MSG
        except InternalServerError as error:
            logger.error("Internal Server Error occured while adding candidate from URL Error: %s" % error.message)
            # return SOMETHING_WENT_WRONG  # Replying user with a response message for internal server error
            return error.message
        except InvalidUsage as error:
            return error.message
        except urllib.ContentTooShortError as error:
            logger.error("Error occurred downloading resume and saving in bucket: %s" % error.message)
            return "File size too small"
        except Exception as error:
            logger.error("Error occured while addinf candidate Error: %s" % error.message)
            # return SOMETHING_WENT_WRONG
            return error.message

    @classmethod
    @contract
    def get_candidate_from_openweb_and_add(cls, user_id, resume_url):
        """
        This method gets candidate from candidates/openweb endpoint if openweb returns a candidate then calls
        add_openweb_candidate if not then returns None
        :param positive user_id: User Id
        :param string resume_url: Resume URL
        :rtype: string|None
        """
        token = User.generate_jw_token(user_id=user_id)
        response = send_request('get', CandidateApiUrl.OPENWEB, token, params={'url': resume_url})
        if response.ok:
            openweb_candidate = json.loads(response.content)
            try:
                candidate, talent_pool = cls.add_openweb_candidate(token, openweb_candidate)
                if candidate and talent_pool:
                    return ("Your candidate `%s %s` has been added to `%s` talent pool" %
                            (candidate.get("first_name"), candidate.get("last_name"), talent_pool.name))\
                        .replace('None', '').replace(' ` `', '')  # If candidate name does not exists remove the None
                return SOMETHING_WENT_WRONG
            except InvalidUsage as error:
                return error.message
            except Exception as error:
                logger.error("Error occurred while parsing openweb candidate: %s" % error.message)
                return SOMETHING_WENT_WRONG

    @classmethod
    @contract
    def parse_resume_and_add_candidate(cls, user_id, filepicker_key):
        """
        This method sends S3 filepicker key to RPS, deletes resume when it gets parsed and returns an appropriate
        response message if candidate has been added or not
        :param positive user_id: User Id
        :param string filepicker_key: S3 filepicker key f resume
        :rtype: string
        """
        token = User.generate_jw_token(user_id=user_id)
        header = {'Authorization': token, 'Content-Type': 'application/json'}
        response = requests.post(ResumeApiUrl.PARSE, headers=header, data=json.dumps(
            {'filepicker_key': filepicker_key, 'talent_pools': [], 'create_candidate': True}))
        try:
            delete_from_filepicker_using_boto3(filepicker_key)  # Deleting saved resume from S3
            print("response from RPS %s" % response.content)
            if response.status_code == codes.OK:
                candidate = response.json()
                first_name = candidate["candidate"]["first_name"]
                talent_pool_name = TalentPool.get_by_id(candidate["candidate"]["talent_pool_ids"]).name
                last_name = candidate["candidate"]["last_name"]
                return ("Your candidate `%s %s` has been added to `%s` talent pool"
                        % (first_name, last_name, talent_pool_name)) \
                    .replace('None', '').replace(' ` `', '')  # If candidate name does not exists remove the None
        except KeyError as error:
            logger.error("Error occurred while getting candidate from RPS: %s" % error.message)
            return SOMETHING_WENT_WRONG  # Replying user with a response message for KeyError error
        except Exception as error:
            logger.warning("Error occurred while deleting S3 bucket: %s" % error.message)
            return SOMETHING_WENT_WRONG  # Replying with a response message if response code from RPS is other than OK

    @classmethod
    def add_openweb_candidate(cls, token, openweb_candidate):
        """
        This method receives scrapped openweb_candidate then appends it in candidates dict and pass this dict to
        candidate service's /candidates endpoint
        :param string token: Auth token Bearer type
        :param dict|None openweb_candidate: Candidate received from openweb against URL
        :rtype: tuple(dict|None, Talentpool|None)
        """
        assert isinstance(token, basestring) and isinstance(openweb_candidate, (dict, None))
        """
        Candidate service receives A list of CandidateObjects:
        e.g. {'candidates': [CandidateObject, CandidateObject, ...]}
        """
        candidate = openweb_candidate["candidate"]
        if "dice_profile_id" in candidate:
            candidate.pop("dice_profile_id")
        # Adding candidate in first talent pool
        if candidate["talent_pool_ids"].get("add"):
            candidate["talent_pool_ids"]["add"] = candidate["talent_pool_ids"]["add"][0:1]
        else:
            raise InvalidUsage("Candidate already exists")
        candidates = {"candidates": [candidate]}
        response = send_request('post', CandidateApiUrl.CANDIDATES, token, candidates)
        if response.ok:
            candidate_id = json.loads(response.content)["candidates"][0]["id"]
            # Getting candidate from candidate service endpoint
            resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, token)
            if resp.ok:
                recently_added_candidate = json.loads(resp.content)["candidate"]
                return recently_added_candidate, TalentPool.get_by_id(candidate["talent_pool_ids"].get("add")[0])
            raise InternalServerError("Error occurred while getting candidate which was recently added")
        error_code = json.loads(response.content)["error"]["code"]
        # When a candidate already exists in db, /openweb returns ids of address and skills etc
        # Which causes INVALID_INPUT so, we are treating INVALID_INPUT as candidate already exists
        if error_code in [INVALID_INPUT, CANDIDATE_ALREADY_EXISTS]:
            raise InvalidUsage("Candidate already exists")
        logger.error("Error occurred while adding candidate through Candidate Service endpoint: %s" % response.content)
        raise InternalServerError("Sorry! Couldn't add candidate")

    @classmethod
    @contract
    def download_resume_and_save_in_bucket(cls, resume_url, user_id, extension):
        """
        Opens url checks if it is valid and then download resume from the url and saves it in S3 gtbot-resume-bucket
        :param string extension: Resume extension
        :param positive user_id: User Id
        :param string resume_url: Resume URL
        :return: Returns saved resume's key
        :rtype: string
        """
        if extension in IMAGE_FORMATS or extension in DOC_FORMATS:
            current_datetime = datetime.utcnow()
            filename = '%d-%s%s%s' % (user_id, current_datetime.date(), current_datetime.time(), extension)
            urllib.urlretrieve(resume_url, filename)
            with open(filename, 'r') as file_reader:
                boto3_put(file_reader.read(), app.config['S3_FILEPICKER_BUCKET_NAME'], filename, 'UploadedResumes')
                os.remove(filename)  # Removing file from directory
                return '{}/{}'.format('UploadedResumes', filename)
        else:
            raise InvalidUsage("Unsupported Resume Type")

    @staticmethod
    @contract
    def parse_resume_url(resume_url):
        """
        This method parses a url and returns resume's extension, hostname and content_length of resume
        :param string resume_url: Url of resume or a social profile
        :rtype: tuple(string|None,string|None,string|None)
        """
        meta = urllib2.urlopen(resume_url)
        resume_size_in_bytes = meta.headers.get('Content-Length')
        parsed_data = urlparse(resume_url)
        host_name = parsed_data.hostname
        _, extension = splitext(parsed_data.path)
        return extension, host_name, resume_size_in_bytes

    @staticmethod
    def is_valid_year(year):
        """
        Validates that string is a valid year
        :param str year: User's entered year string
        :rtype: True|False|-1
        """
        if year.isdigit():
            year_in_number = int(year)
            current_year = datetime.utcnow().year
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
            if duration > MAX_NUMBER_FOR_DATE_GENERATION:
                return "Number's max range exceeded"
            duration_type = message_tokens[last_index + 2]
        if message_tokens[last_index + 1][0] == '-':
            return 'Negative numbers are not acceptable'
        if duration_type.lower() in 'years':
            user_specific_date = datetime.utcnow() - relativedelta(years=duration)
        if duration_type.lower() in 'months':
            user_specific_date = datetime.utcnow() - relativedelta(months=duration)
        if duration_type.lower() in 'weeks':
            user_specific_date = datetime.utcnow() - relativedelta(weeks=duration)
        if duration_type.lower() in 'days':
            user_specific_date = datetime.utcnow() - relativedelta(days=duration)
        return user_specific_date

    @staticmethod
    def create_ordered_list(_list):
        """
        This method creates an ordered list
        :param list _list: List of string elements
        :rtype: str
        """
        for index, list_element in enumerate(_list):
            ordered_talent_pool_name = "%d- %s" % (index + 1, list_element)
            _list[index] = ordered_talent_pool_name
        return '\n\n'.join(_list)

    @staticmethod
    def create_list_of_talent_pools(talent_pool_name):
        """
        This method checks if there are more than one talent pool names, and makes a list of them and removes spaces.
        :param str talent_pool_name:
        :rtype: list|None
        """
        if talent_pool_name:
            if bool(re.search(r"and|\\", talent_pool_name)):
                talent_pool_name_list = re.split(r"and|\\", talent_pool_name)
            else:
                talent_pool_name_list = [talent_pool_name]
            talent_pool_name_list = [name.strip(' ') for name in talent_pool_name_list if len(name) != 0]
            return talent_pool_name_list
        return None

    @classmethod
    def append_count_with_message(cls, message, _list, handler_number, user_id, user_name=None,
                                  user_specific_date=None):
        """
        This method appends number of imports or number of candidates with skills with the given message
        :param str message: Response message
        :param list _list: List of skills or list of talent pools
        :param int handler_number: Question handler number
        :param int|long user_id: User Id
        :param str|None user_name: User name
        :param datetime|str|None user_specific_date: User specified datetime
        :rtype: str
        """
        count_dict = {}
        if handler_number == QUESTION_HANDLER_NUMBERS.get('question_handler_4'):
            # Getting count against each talent pool and then adding it to count_dict
            for talent_pool in _list:
                _count = TalentPoolCandidate.candidate_imports(user_id, user_name, [talent_pool],
                                                               user_specific_date)
                if isinstance(_count, (int, long)):
                    count_dict.update({talent_pool: _count})
        if handler_number == QUESTION_HANDLER_NUMBERS.get('question_handler_1'):
            # Getting count against each skill and then adding it to count_dict
            for skill in _list:
                if skill.lower() != 'and':
                    _count = Candidate.get_candidate_count_with_skills([skill], user_id)
                    if isinstance(_count, (int, long)):
                        count_dict.update({skill: _count})
        # Now appending these counts with the response_message and returning it
        if len(count_dict) > 1:
            message = '%s\n%s' % (message, '\n'.join(['`%s`: %d' % (key,
                                  count_dict[key]) for key in count_dict]))
            message = message.replace('pool', 'pools')
        return message

    @classmethod
    def find_optional_word(cls, message_tokens, optional_words, exact_word=False):
        """
        This method returns the first matched word's index
        :param bool exact_word: If user wants to find exact word or partial word
        :param list message_tokens: User message tokens
        :param optional_words: list of optional words to be found
        :rtype: int|None
        """
        for word in optional_words:
            index = cls.find_word_in_message(word, message_tokens,  exact_word)
            if index is not None:
                return index
        return None

    @classmethod
    @contract
    def prepare_blast_results(cls, campaigns, name, campaign_type):
        """
        Generates a representable result of a Campaign Blast
        :param string name: Campaign name specified by User
        :param string campaign_type: Campaign Name
        :param list campaigns: list of Email|Push|Sms Campaigns
        :rtype: list
        """
        blasts = []
        for campaign in campaigns:  # Getting all blasts for all campaigns
            blasts += (campaign.blasts.all())
        response = []
        if len(blasts) < 1 and len(campaigns) > ZERO:  # If Campaign exists but has no blasts
            response.append("%s `%s` has not been sent yet" % (campaign_type.title(), name))
            return response
        # Appending all found CampaignBlasts' result
        total_sends = ZERO
        total_opens = ZERO
        for blast in blasts:  # Campaigns with more than one blasts are being summed as a single blast
            total_sends += blast.sends
            if campaign_type == EMAIL_CAMPAIGN:
                total_opens += blast.opens
            elif campaign_type == SMS_CAMPAIGN:
                total_opens += blast.replies
            else:
                total_opens += blast.clicks
        if len(blasts) > ZERO:  # Preparing representable response
            # interaction_rate means open_rate in case of EmailCampaign and reply_rate or click_rate in case of SMS
            # and Push Campaigns
            interaction_rate = cls.calculate_percentage(total_opens, total_sends if total_sends != 0 else 1)
            # What text should be displayed in response (click rate, open rate or reply rate)
            interaction_type = 'open' if campaign_type == EMAIL_CAMPAIGN else 'click' if \
                campaign_type == SMS_CAMPAIGN else 'reply'
            response.append("%s `%s` has been sent to `%d` %s with %s rate of `%d%%`"
                            % (campaign_type.title(), name, total_sends, 'candidate' if total_sends == 1 else
                               'candidates', interaction_type, interaction_rate))
        return response

    @classmethod
    @contract
    def handle_pagination(cls, user_id, number):
        """
        This method handles pagination, if user says next it gets method from state and add 1 in page number
        and returns next records
        :param int number: Add this in page number
        :param positive user_id: User Id
        :rtype: None|string
        """
        # Requesting Lock
        lock = cls.request_lock(user_id)
        while lock:
            sleep(randint(1, 2))
            lock = cls.request_lock(user_id)
        # Acquiring lock
        redis_store.set("%dredis_lock" % user_id, True)
        states = redis_store.get("bot-pg-%d" % user_id)
        try:
            if states:
                states = json.loads(states)
                # Getting state data from redis
                response = []
                new_states = []
                for state in states:
                    representative, _class, params = state["repr"], CLASSES[state["class"]], state["params"]
                    method = getattr(_class, state["method"])
                    page_number = params[-1] or 1
                    if number < 0 and page_number > 1:
                        # Decreasing page number
                        page_number += number
                    elif number > 0:
                        page_number += number
                    else:
                        # Releasing lock
                        redis_store.set("%dredis_lock" % user_id, False)
                        return None
                    params[-1] = page_number
                    _list = method(*tuple(params))
                    if _list:
                        state.update({"page_number": page_number})
                        new_states.append(state)
                        start = 1 if page_number == 1 else page_number * 10 - 9
                        response.append(cls.custom_count_appender(start, _list, representative, []))
                        redis_store.set("bot-pg-%d" % user_id, json.dumps(new_states))
                # Releasing lock
                redis_store.set("%dredis_lock" % user_id, False)
                return '\n'.join(response)
            redis_store.delete("bot-pg-%d" % user_id)
        except Exception as error:
            logger.info("No state found: %s" % error.message)
            # Releasing lock
            redis_store.set("%dredis_lock" % user_id, False)
            return None
        return None

    @staticmethod
    @contract
    def request_lock(user_id):
        """
        Returns user specific lock from redis
        :param positive user_id: User Id
        :rtype: None|bool
        """
        lock = redis_store.get("%dredis_lock" % user_id)
        if lock is not None:
            lock = eval(lock)
        return lock

    @staticmethod
    @contract
    def create_state_object(_class, method, params, representative):
        """
        This methods takes required parameters for pagination state and save them in redis as state
        :param string _class:
        :param string method:
        :param list params:
        :param string representative:
        :rtype: dict
        """
        state = {"class": _class, "method": method, "params": params, "repr": representative}
        return state

    @staticmethod
    @contract
    def save_state(state, user_id):
        """
        This method saves state dict in redis
        :param positive user_id: User Id
        :param dict|list state: dict or list of dicts of required objects for state maintenance
        """
        redis_store.set("bot-pg-%d" % user_id, json.dumps(state))
