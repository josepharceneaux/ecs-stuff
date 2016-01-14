"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

This module contains SmsCampaignBase class inherited from CampaignBase.
This is used to send SMS campaign to candidates.
This implements abstract methods of CampaignBase class and defines its own
methods like
     - save()
     - buy_twilio_mobile_number()
     - create_or_update_user_phone()
     - process_send()
     - process_link_in_body_text()
     - transform_body_text()
     - send_campaign_to_candidate()
     - send_sms()
     - process_candidate_reply() etc.

It also contains private methods for this module as
    - _get_valid_user_phone_value()
    - _validate_candidate_phone_value()
"""

# Standard Library
from datetime import datetime, timedelta

# Third party
from dateutil.relativedelta import relativedelta

# Database Models
from sms_campaign_service.common.models.db import db
from sms_campaign_service.common.models.user import UserPhone
from sms_campaign_service.common.models.candidate import (PhoneLabel, Candidate, CandidatePhone)
from sms_campaign_service.common.models.sms_campaign import (SmsCampaign, SmsCampaignSend,
                                                             SmsCampaignBlast, SmsCampaignSmartlist,
                                                             SmsCampaignSendUrlConversion,
                                                             SmsCampaignReply)
# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.utils.validators import format_phone_number
from sms_campaign_service.common.talent_config_manager import TalentConfigKeys
from sms_campaign_service.common.utils.activity_utils import ActivityMessageIds
from sms_campaign_service.common.campaign_services.campaign_base import CampaignBase
from sms_campaign_service.common.error_handling import (ResourceNotFound, ForbiddenError,
                                                        InvalidUsage, InternalServerError)
from sms_campaign_service.common.utils.handy_functions import (find_missing_items, url_conversion)

# Service Specific
from sms_campaign_service.sms_campaign_app import celery_app, app, logger
from sms_campaign_service.common.campaign_services.campaign_utils import \
    (sign_redirect_url, CampaignType, processing_after_campaign_sent)
from sms_campaign_service.modules.validators import (validate_url_format, search_urls_in_text,
                                                     validate_urls_in_body_text,
                                                     get_formatted_phone_number)
from sms_campaign_service.modules.handy_functions import (TwilioSMS, replace_localhost_with_ngrok)
from sms_campaign_service.modules.sms_campaign_app_constants import (MOBILE_PHONE_LABEL, TWILIO,
                                                                     TWILIO_TEST_NUMBER)
from sms_campaign_service.modules.custom_exceptions import (EmptySmsBody,
                                                            MultipleTwilioNumbersFoundForUser,
                                                            MultipleUsersFound,
                                                            MultipleCandidatesFound,
                                                            NoCandidateAssociatedWithSmartlist,
                                                            NoSmartlistAssociatedWithCampaign,
                                                            NoSMSCampaignSentToCandidate,
                                                            ErrorUpdatingBodyText,
                                                            NoCandidateFoundForPhoneNumber,
                                                            NoUserFoundForPhoneNumber,
                                                            GoogleShortenUrlAPIError,
                                                            TwilioAPIError, InvalidUrl,
                                                            SmsCampaignApiException)


class SmsCampaignBase(CampaignBase):
    """
    - This is the base class for sending SMS campaign to candidates and to keep track
        of their responses. It uses Twilio API to send SMS.

    - This is inherited from CampaignBase defined inside
        flask_common/common/utils/campaign_base.py. It implements abstract
        methods of base class and defines its own methods also.

    This class contains following methods:

    * __init__()

        - It takes "user_id" as keyword argument.
        - It calls super class __init__ to get user obj and set it in self.user..
        - It then gets the user_phone obj from "user_phone" db table using
            provided "user_id".

    * get_user_phone(self)
        This gets the Twilio number of current user from database table "user_phone"

    * buy_twilio_mobile_number(self, phone_label_id=None)
        To send sms_campaign, we need to reserve a unique number for each user.
        This method is used to reserve a unique number for getTalent user.

    * create_or_update_user_phone(user_id, phone_number, phone_label_id): [static]
        This method is used to create/update user_phone record.

    * get_all_campaigns(self)
        This gets all the campaigns created by current user.

    * validate_form_data(cls, form_data)
        This overrides CampaignBase class method to do any further validation.

    * process_save_or_update(self, form_data, campaign_id=None)
        This overrides tha CampaignBase class method.
        This appends user_phone_id in form_data and calls super constructor to save/update
        the campaign in database.

    * schedule(self, data_to_schedule)
        This overrides the base class method and set the value of data_to_schedule.
        It then calls super constructor to get task_id for us. Then we will update
        SMS campaign record in sms_campaign table with frequency_id, start_datetime,
        end_datetime and "task_id"(Task created on APScheduler).

    * validate_ownership_of_campaign(campaign_id, current_user_id)
        This implements CampaignBase class method and returns True if the current user is
        an owner for given campaign_id. Otherwise it raises the Forbidden error.

    * process_send(self, campaign_id=None)
        This method is used to send the campaign to candidates.

    * is_candidate_have_unique_mobile_phone(self, candidate)
        This validates if candidate have unique mobile number associated with it.

    * pre_process_celery_task(self, candidate)
        This filter out the candidates who have no unique mobile number associated,

    * send_campaign_to_candidate(self, candidate)
        This does the sending part and updates database tables "sms_campaign_blast" and
         "sms_campaign_send".

    * callback_campaign_sent(send_result, user_id, campaign, oauth_header, candidate)
        Once the campaign is sent to all candidates of a particular smartlists, we crate an
        activity in Activity table that (e.g)
                " "Job opening at getTalent" campaign has been sent to "100" candidates"

    * celery_error_handler(uuid):
        If we get any error on celery task, we here we catch it and log the error.

    * process_urls_in_sms_body_text(self, candidate_id)
        If "body_text" contains any link in it, then we need to transform the
        "body_text" by replacing long URL with shorter version using Google's Shorten
        URL API. If body text does not contain any link, it returns the body_text
        as it is.

    * transform_body_text(self, link_in_body_text, short_url)
        This replaces the original URL present in "body_text" with the shortened URL.

    * create_sms_campaign_blast(campaign_id, send=0, clicks=0, replies=0): [static]
        For each campaign, here we create/update stats of that particular campaign.

    * create_campaign_blast(campaign_id, sends=0, clicks=0, replies=0)
        Every time we send a campaign, we create a new blast for that campaign here.

    * send_sms(self, candidate_phone_value)
        This finally sends the SMS to candidate using Twilio API.

    * create_or_update_sms_campaign_send(campaign_blast_id, candidate_id, sent_datetime): [static]
        For each SMS sent to the candidate, here we add an entry that particular campaign e.g.
         "Job opening at getTalent" campaign has been sent to "Waqar Younas""

    * create_or_update_sms_send_url_conversion(campaign_send_obj, url_conversion_id): [static]
        This adds an entry in db table "sms_campaign_send_url_conversion" for each SMS send.

    * create_sms_send_activity(self, candidate, source)
        Here we set "params" and "type" to be saved in db table 'Activity' for each sent SMS.
        Activity will appear as (e.g)
            "SMS Campaign "Job opening at getTalent" has been sent to 'Adam Jr'.".

    * process_candidate_reply(cls, candidate)
        When a candidate replies to a recruiter's number, here we do the necessary processing.

    * save_candidate_reply(cls, campaign_blast_id, candidate_phone_id, body_text)
        In this method, we save the reply of candidate in db table 'sms_campaign_reply".

    * create_campaign_reply_activity(cls,sms_campaign_reply, campaign_blast, candidate_id, user_id)
        When a candidate replies to a recruiter's phone number, we create an activity in
        database table "Activity" that (e.g)
            "'William Lyles' replied "Interested" on SMS campaign 'Job opening at getTalent'.".

    - An example of sending campaign to candidates will be like this.
        :Example:

        1- Create class object
            from sms_campaign_service.sms_campaign_base import SmsCampaignBase
            camp_obj = SmsCampaignBase(1)

        2- Get SMS campaign to send
            from sms_campaign_service.common.models.sms_campaign import SmsCampaign
            campaign = SmsCampaign.get(1)

        3- Call method process_send
            camp_obj.process(campaign)

    **See Also**
        .. see also:: CampaignBase class in flask_common/common/utils/campaign_base.py.
    """

    def __init__(self, user_id):
        """
        Here we set the "user_id" by calling super constructor and "user_phone" by
        calling get_user_phone() method,
        :return:
        """
        # sets the user_id
        super(SmsCampaignBase, self).__init__(user_id)
        self.user_phone = self.get_user_phone()
        if not self.user_phone:
            raise ForbiddenError('User(id:%s) has no phone number' % self.user.id)
        # If sms_body_test has some URL present in it, we process to make short URL
        # and this contains the updated text to be sent via SMS.
        # This is the id of record in sms_campaign_blast" database table
        self.campaign_type = CampaignType.SMS

    def get_user_phone(self):
        """
        Here we check if current user has Twilio number in "user_phone" table.
        If user has no Twilio number associated, we buy a new number for this user,
        saves it in database and returns it.

        - This method is called from __int__() method of class SmsCampaignBase inside
            sms_campaign_service/sms_campaign_base.py.
        :exception: MultipleTwilioNumbersFoundForUser
        :return: UserPhone obj
        :rtype: UserPhone
        """
        if not self.user:
            raise InvalidUsage('User can not be None to get user_phone record')
        # TWILIO is a name defined in config
        phone_label_id = PhoneLabel.phone_label_id_from_phone_label(TWILIO)
        user_phone = UserPhone.get_by_user_id_and_phone_label_id(self.user.id,
                                                                 phone_label_id)
        if len(user_phone) == 1:
            user_phone_value = user_phone[0].value
            if user_phone_value:
                get_formatted_phone_number(user_phone_value)
                return user_phone[0]
        elif len(user_phone) > 1:
            raise MultipleTwilioNumbersFoundForUser(
                'User(id:%s) has multiple phone numbers for phone label: %s'
                % (self.user.id, TWILIO))
        else:
            # User has no associated twilio number, need to buy one
            logger.debug('get_user_phone: User(id:%s) has no Twilio number associated.'
                         % self.user.id)
            return self.buy_twilio_mobile_number(phone_label_id)

    def buy_twilio_mobile_number(self, phone_label_id):
        """
        Here we use Twilio API to first get list of available numbers by calling
        get_available_numbers() of class TwilioSMS inside modules/handy_functions.py.
        We select first available number from the result of get_available_numbers() and call
        purchase_twilio_number() to buy that number.

        - This method is called from get_user_phone() method of class SmsCampaignBase inside
            sms_campaign_service/sms_campaign_base.py.

        :param phone_label_id: id of phone label
        :type phone_label_id: int
        :exception: TwilioAPIError
        :return: UserPhone obj
        :rtype: UserPhone
        """
        if not phone_label_id:
            raise InvalidUsage('phone_label_id must be an integer.')
        twilio_obj = TwilioSMS()
        if app.config[TalentConfigKeys.IS_DEV]:
            # Buy Twilio TEST number so that we won't be charged
            number_to_buy = TWILIO_TEST_NUMBER
        else:
            logger.debug('buy_twilio_mobile_number: Going to buy Twilio number for '
                         'user(id:%s).' % self.user.id)
            available_phone_numbers = twilio_obj.get_available_numbers()
            # We get a list of 30 available numbers and we pick very first phone number to buy.
            number_to_buy = available_phone_numbers[0].phone_number
        twilio_obj.purchase_twilio_number(number_to_buy)
        user_phone = self.create_or_update_user_phone(self.user.id, number_to_buy,
                                                      phone_label_id)
        return user_phone

    @staticmethod
    def create_or_update_user_phone(user_id, phone_number, phone_label_id):
        """
        - For each user (recruiter) we need to reserve a unique phone number to send
            SMS campaign. Here we create a new user_phone record or update the previous
            record.

        - This method is called from buy_twilio_mobile_number() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param phone_label_id: id of "phone_label" record
        :param phone_number: The number we want to reserve for user
        :type phone_label_id: int
        :type phone_number: str
        :return: "user_phone" obj
        :rtype: UserPhone

        **See Also**
        .. see also:: __int__() method of SmsCampaignBase class.
        """
        data = {'user_id': user_id,
                'phone_label_id': phone_label_id,
                'value': phone_number}
        empty_items = find_missing_items(data, verify_values_of_all_keys=True)
        if empty_items:
            raise InvalidUsage('Missing fields to save user_phone are %s.' % empty_items)
        user_phone_obj = UserPhone.get_by_user_id_and_phone_label_id(user_id,
                                                                     phone_label_id)
        if user_phone_obj:
            user_phone_obj.update(**data)
        else:
            user_phone_obj = UserPhone(**data)
            UserPhone.save(user_phone_obj)
        return user_phone_obj

    def get_all_campaigns(self):
        """
        This gets all the campaigns created by current user
        :return: all campaigns associated to with user
        :rtype: list
        """
        return SmsCampaign.get_by_user_phone_id(self.user_phone.id)

    @classmethod
    def validate_form_data(cls, form_data):
        """
        This overrides the CampaignBase class method.
        It calls super constructor to do the common validation. It then validates if body_text
        has valid URLs in it (if there are any)
        :param form_data: data from UI
        :return: validation_result
        :rtype: tuple
        :exception: Invalid URL
        """
        validation_result = super(SmsCampaignBase, cls).validate_form_data(form_data)
        # validate URLs present in SMS body text
        invalid_urls = validate_urls_in_body_text(form_data['body_text'])
        if invalid_urls:
            raise InvalidUrl('Invalid URL(s) in body_text. %s' % invalid_urls)
        return validation_result

    def process_save_or_update(self, form_data, campaign_id=None):
        """
        This overrides tha CampaignBase class method. This appends user_phone_id in
        form_data and calls super constructor to save the campaign in database.
        :param form_data: data from UI
        :type form_data: dict
        :return: id of sms_campaign in db, invalid_smartlist_ids and not_found_smartlist_ids
        :rtype: tuple
        """
        if not form_data:
            raise InvalidUsage('save: No data received from UI. (User(id:%s))' % self.user.id)
        form_data['user_phone_id'] = self.user_phone.id
        print 'in sms_base' + self.user.name
        return super(SmsCampaignBase, self).process_save_or_update(form_data,
                                                                   campaign_id=campaign_id)

    def schedule(self, data_to_schedule):
        """
        This overrides the CampaignBase class method schedule().
        Here we set the value of dict "data_to_schedule" and pass it to
        super constructor to get task_id for us. Finally we update the SMS campaign
        record in database table "sms_campaign" with
            1- frequency_id
            2- start_datetime
            3- end_datetime
            4- task_id (Task created on APScheduler)
        Finally we return the "task_id".

        - This method is called from the endpoint /v1/campaigns/:id/schedule on HTTP method DELETE

        :param data_to_schedule: required data to schedule an SMS campaign
        :type data_to_schedule: dict
        :return: task_id (Task created on APScheduler), and status of task(already scheduled
                            or new scheduled)
        :rtype: tuple

        **See Also**
        .. see also:: ScheduleSmsCampaign() method in v1_sms_campaign_api.py.
        """
        if not data_to_schedule or not isinstance(data_to_schedule, dict):
            raise InvalidUsage('Data to schedule a task cannot be empty. It should be a dict.')
        data_to_schedule.update(
            {'url_to_run_task': SmsCampaignApiUrl.SEND % self.campaign.id}
        )
        # get scheduler task_id created on scheduler_service
        scheduler_task_id = super(SmsCampaignBase, self).schedule(data_to_schedule)
        # update sms_campaign record with task_id
        self.campaign.update(scheduler_task_id=scheduler_task_id)
        return scheduler_task_id

    @staticmethod
    def validate_ownership_of_campaign(campaign_id, current_user_id):
        """
        This function returns True if the current user is an owner for given
        campaign_id. Otherwise it raises the Forbidden error.
        :param campaign_id: id of campaign form getTalent database
        :param current_user_id: Id of current user
        :exception: InvalidUsage
        :exception: ResourceNotFound
        :exception: ForbiddenError
        :return: Campaign obj if current user is an owner for given campaign.
        :rtype: SmsCampaign
        """
        if not isinstance(campaign_id, (int, long)):
            raise InvalidUsage('Include campaign_id as int|long.')
        if not isinstance(current_user_id, (int, long)):
            raise InvalidUsage('Include current_user_id as int|long.')
        campaign_obj = SmsCampaign.get_by_id(campaign_id)
        if not campaign_obj:
            raise ResourceNotFound('SMS Campaign(id=%s) not found.' % campaign_id)
        campaign_user_id = UserPhone.get_by_id(campaign_obj.user_phone_id).user_id
        if campaign_user_id == current_user_id:
            return campaign_obj
        else:
            raise ForbiddenError('User(id:%s) are not the owner of SMS campaign(id:%s)'
                                 % (current_user_id, campaign_id))

    def process_send(self, campaign):
        """
        :param campaign: SMS campaign obj
        :type campaign: SmsCampaign
        :exception: TwilioAPIError
        :exception: InvalidUsage
        :exception: EmptySmsBody
        :exception: NoSmartlistAssociatedWithCampaign
        :exception: NoCandidateAssociatedWithSmartlist

        This does the following steps to send campaign to candidates.

        1- Get body_text from sms_campaign obj
        2- Get selected smart lists for the campaign to be sent from sms_campaign_smartlist.
        3- Loop over all the smart lists and do the following:

            3.1- Get candidates and their phone number(s) to which we need to send the SMS.
            3.2- Transform the body text to be sent in SMS (convert URls), add entry in
                    url_conversion and sms_campaign_url_conversion db tables.
            3.3- Create SMS campaign blast
            3.4- Loop over list of candidate_ids found in step 3.1 and do the following:
                3.3.1- Send SMS
                3.3.2- Create SMS campaign send
                3.3.3- Update SMS campaign blast
                3.3.4- Add activity e.g.("Roger Federer" received SMS of campaign "Keep winning"")
        4- Add activity e.g. (SMS Campaign "abc" was sent to "1000" candidates")

        :Example:

            1- Create class object
                from sms_campaign_service.sms_campaign_base import SmsCampaignBase
                camp_obj = SmsCampaignBase(1)

            2- Get SMS campaign to send
                from sms_campaign_service.common.models.sms_campaign import SmsCampaign
                campaign = SmsCampaign.get(1)

            3- Call method process_send
                camp_obj.process(campaign)
        """
        if not isinstance(campaign, SmsCampaign):
            raise InvalidUsage('campaign should be instance of SmsCampaign model')
        self.campaign = campaign
        logger.debug('process_send: SMS Campaign(id:%s) is being sent. User(id:%s)'
                     % (campaign.id, self.user.id))
        if not self.campaign.body_text:
            # SMS body text is empty
            raise EmptySmsBody('SMS Body text is empty for Campaign(id:%s)'
                               % campaign.id)
        self.body_text = self.campaign.body_text.strip()
        # Get smartlists associated to this campaign
        smartlists = SmsCampaignSmartlist.get_by_campaign_id(campaign.id)
        if not smartlists:
            raise NoSmartlistAssociatedWithCampaign(
                'No smartlist is associated with SMS '
                'Campaign(id:%s). (User(id:%s))' % (campaign.id, self.user.id))
        # get candidates from search_service and filter the None records
        candidates = sum(filter(None, map(self.get_smartlist_candidates, smartlists)), [])
        if not candidates:
            raise NoCandidateAssociatedWithSmartlist(
                'No candidate is associated to smartlist(s). SMS Campaign(id:%s). '
                'smartlist ids are %s' % (campaign.id, smartlists))
        # create SMS campaign blast
        self.campaign_blast_id = self.create_sms_campaign_blast(self.campaign.id)
        self.send_campaign_to_candidates(candidates)

    def is_candidate_have_unique_mobile_phone(self, candidate):
        """
        Here we validate that candidate has one unique mobile number associated.
        If candidate has only one unique mobile number associated, we return that candidate and
        its phone value.
        Otherwise we log the error.

        - This method is used in send_campaign_to_candidate() method.

        :param candidate: candidates obj
        :type candidate: Candidate
        :exception: InvalidUsage
        :exception: MultipleCandidatesFound
        :exception: NoCandidateFoundForPhoneNumber
        :return: Candidate obj and Candidate's mobile phone
        :rtype: tuple

        **See Also**
        .. see also:: send_campaign_to_candidate() method in SmsCampaignBase class.
        """
        if not isinstance(candidate, Candidate):
            raise InvalidUsage('parameter must be an instance of model Candidate')
        candidate_phones = candidate.candidate_phones
        phone_label_id = PhoneLabel.phone_label_id_from_phone_label(MOBILE_PHONE_LABEL)

        # filter only mobile numbers
        candidate_mobile_phone = filter(lambda candidate_phone:
                                        candidate_phone.phone_label_id == phone_label_id,
                                        candidate_phones)
        if len(candidate_mobile_phone) == 1:
            # If this number is associated with multiple candidates, raise exception
            _validate_candidate_phone_value(candidate_mobile_phone[0].value)
            return candidate, candidate_mobile_phone[0].value
        elif len(candidate_mobile_phone) > 1:
            logger.error('filter_candidates_for_valid_phone: SMS cannot be sent as '
                         'candidate(id:%s) has multiple mobile phone numbers. '
                         'Campaign(id:%s). (User(id:%s))'
                         % (candidate.id, self.campaign.id, self.user.id))
        else:
            logger.error('filter_candidates_for_valid_phone: SMS cannot be sent as '
                         'candidate(id:%s) has no phone number associated. Campaign(id:%s). '
                         '(User(id:%s))' % (candidate.id, self.campaign.id, self.user.id))

    def pre_process_celery_task(self, candidates):
        """
        This overrides the CampaignBase class method and filter only those candidates who
        have one unique mobile number associated.
        :param candidates:
        :type candidates: list
        :return:
        """
        filtered_candidates_and_phones = \
            filter(lambda obj: obj is not None, map(self.is_candidate_have_unique_mobile_phone,
                                                    candidates)
                   )
        logger.debug('process_send: SMS Campaign(id:%s) will be sent to %s candidate(s). '
                     '(User(id:%s))' % (self.campaign.id, len(filtered_candidates_and_phones),
                                        self.user.id))
        return filtered_candidates_and_phones

    @celery_app.task(name='send_campaign_to_candidate')
    def send_campaign_to_candidate(self, candidate_and_phone):
        """
        This is a task of celery. We need to make sure that if any exception is raised, we
        handle it here gracefully. Otherwise, exception will be raised to chord and callback
        function will not be called as we expect. In callback function we create an activity
        that
            'SMS campaign 'Job opening at plan 9' has been sent to 400 candidates'

        For each candidate with associated phone, we do the following:
            1- Replace URLs in SMS body text with short URLs(to redirect candidate to our app)
            2- Send SMS
            3- Create SMS campaign send
            4- Update sms_campaign_send_url_conversion
            5- Update SMS campaign blast
            6- Add activity e.g.('Vincent' received SMS of campaign 'Hiring senior SE'")

        - This method is called from send_sms_campaign_to_candidates() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param candidate_and_phone: candidate obj at index 0 and candidate phone value at index 1
        :type candidate_and_phone: tuple
        :exception: ErrorUpdatingBodyText
        :exception: TwilioAPIError
        :exception: GoogleShortenUrlAPIError
        :return: True if SMS is sent otherwise False.
        :rtype: bool

        **See Also**
        .. see also:: send_sms_campaign_to_candidates() method in SmsCampaignBase class.
        """
        # Celery app is not configured with flask app, so need to use app.app_context() here
        # so that Celery tasks know the config of flask app.
        with app.app_context():
            candidate, candidate_phone_value = candidate_and_phone
            candidate_phone_value = get_formatted_phone_number(candidate_phone_value)
            try:
                modified_body_text, url_conversion_ids = \
                    self.process_urls_in_sms_body_text(candidate.id)
            except Exception:
                logger.exception('send_campaign_to_candidate: Error processing URLs in SMS body')
                return False
            # send SMS
            try:
                message_sent_datetime = self.send_sms(str(candidate_phone_value),
                                                      modified_body_text)
            except TwilioAPIError or InvalidUsage:
                logger.exception('send_campaign_to_candidate: Cannot send SMS.')
                return False
            # Create sms_campaign_send i.e. it will record that an SMS has been sent
            # to the candidate
            try:
                sms_campaign_send_obj = \
                    self.create_or_update_sms_campaign_send(self.campaign_blast_id,
                                                            candidate.id,
                                                            message_sent_datetime)
            except Exception:
                logger.exception('send_campaign_to_candidate: Error saving '
                                 'record in sms_campaign_send')
                return False
            # We keep track of all URLs sent, in sms_send_url_conversion table,
            # so we can later retrieve that to perform some tasks
            try:
                for url_conversion_id in url_conversion_ids:
                    self.create_or_update_sms_send_url_conversion(sms_campaign_send_obj,
                                                                  url_conversion_id)
            except Exception:
                logger.exception('send_campaign_to_candidate: Error adding entry in '
                                 'sms_campaign_send_url_conversion.')
                return False
            # Create SMS sent activity
            try:
                self.create_sms_send_activity(candidate, sms_campaign_send_obj)
            except Exception:
                logger.exception('send_campaign_to_candidate: Error creating SMS send activity.')
                return False

            logger.info('send_sms_campaign_to_candidate: SMS has been sent to candidate(id:%s).'
                        ' Campaign(id:%s). (User(id:%s))' % (candidate.id,
                                                             self.campaign.id,
                                                             self.user.id))
            return True

    @staticmethod
    @celery_app.task(name='callback_campaign_sent')
    def callback_campaign_sent(sends_result, user_id, campaign_type, blast_id, oauth_header):
        """
        Once SMS campaign has been sent to all candidates, this function is hit. This is
        a Celery task. Here we

        1) Update number of sends in campaign blast
        2) Add activity e.g. (SMS Campaign "abc" was sent to "1000" candidates")

        This uses processing_after_campaign_sent() function defined in
            common/campaign_services/campaign_utils.py

        :param sends_result: Result of executed task
        :param user_id: id of user (owner of campaign)
        :param campaign_type: type of campaign. i.e. sms_campaign or push_campaign
        :param blast_id: id of blast object
        :param oauth_header: auth header of current user to make HTTP request to other services
        :type sends_result: list
        :type user_id: int
        :type campaign_type: str
        :type blast_id: int
        :type oauth_header: dict

        **See Also**
        .. see also:: send_campaign_to_candidates() method in CampaignBase class inside
                        common/utils/campaign_base.py
        """
        with app.app_context():
            processing_after_campaign_sent(CampaignBase, sends_result, user_id, campaign_type,
                                           blast_id, oauth_header)

    @staticmethod
    @celery_app.task(name='celery_error_handler')
    def celery_error_handler(uuid):
        db.session.rollback()

    def process_urls_in_sms_body_text(self, candidate_id):
        """
        We use "url_conversion" table fields:
            1- 'destination_url' as URL provided by recruiter
            2- 'source_url' as URL to redirect candidate to our app
        - Once we have the body text of SMS campaign provided by recruiter(user),
            We check if it contains any URL in it.
            If it has any link, we do the following:

                1- Save that URL in db table "url_conversion" as destination_url with  empty
                    source_url.
                2- Create a URL (using id of url_conversion record created in step 1) to redirect
                    candidate to our app and save that as source_url
                    (for the same database record we created in step 1). This source_url looks like
                     http://127.0.0.1:8011/v1/campaigns/1/redirect/1?candidate_id=1
                3- Convert the source_url into shortened URL using Google's shorten URL API.
                4- Replace the link in original body text with the shortened URL
                    (which we created in step 2)
                5- Set the updated body text in self.transform_body_text

            Otherwise we save the body text in modified_body_text

        - This method is called from process_send() method of class SmsCampaignBase inside
            sms_campaign_service/sms_campaign_base.py.

        :param candidate_id: id of Candidate
        :type candidate_id: int | long
        :exception: GoogleShortenUrlAPIError
        :return: list of URL conversion records
        :rtype: list

        **See Also**
        .. see also:: process_send() method in SmsCampaignBase class.
        """
        logger.debug('process_urls_in_sms_body_text: Processing any '
                     'link present in body_text for '
                     'SMS Campaign(id:%s) and Candidate(id:%s). (User(id:%s))'
                     % (self.campaign.id, candidate_id, self.user.id))
        urls_in_body_text = search_urls_in_text(self.body_text)
        short_urls = []
        url_conversion_ids = []
        for url in urls_in_body_text:
            validate_url_format(url)
            # We have only one link in body text which needs to shortened.
            url_conversion_id = self.create_or_update_url_conversion(destination_url=url,
                                                                     source_url='')
            # URL to redirect candidates to our end point
            # TODO: remove this when app is up
            app_redirect_url = replace_localhost_with_ngrok(SmsCampaignApiUrl.REDIRECT)
            # redirect URL looks like
            # http://127.0.0.1:8012/redirect/1
            redirect_url = str(app_redirect_url % url_conversion_id)
            # sign the redirect URL
            long_url = sign_redirect_url(redirect_url, datetime.now() + relativedelta(years=+1))
            # long_url looks like
            # http://127.0.0.1:8012/v1/redirect/1052?valid_until=1453990099.0
            #           &auth_user=no_user&extra=&signature=cWQ43J%2BkYetfmE2KmR85%2BLmvuIw%3D
            # Use Google's API to shorten the long Url
            short_url, error = url_conversion(long_url)
            logger.info("url_conversion: Long URL was: %s" % long_url)
            logger.info("url_conversion: Shortened URL is: %s" % short_url)
            if error:
                raise GoogleShortenUrlAPIError(error)
            short_urls.append(short_url)
            url_conversion_ids.append(url_conversion_id)
            if app.config[TalentConfigKeys.IS_DEV]:
                # update the 'source_url' in "url_conversion" record.
                # Source URL should not be saved in database. But we have tests written
                # for Redirection endpoint. That's why in case of DEV, I am saving source URL here.
                self.create_or_update_url_conversion(url_conversion_id=url_conversion_id,
                                                     source_url=long_url)
        updated_text_body = self.transform_body_text(urls_in_body_text, short_urls)
        return updated_text_body, url_conversion_ids

    def transform_body_text(self, urls_in_sms_body_text, short_urls):
        """
        - This replaces the urls provided in "body_text" (destination urls) with the
            "shortened urls" to be sent via SMS campaign. These shortened urls will
            redirect candidate to our endpoint to keep track of clicks and hit_count,
            then we redirect the candidate to actual destination urls

        - It sets the value of modified_body_text and returns it

        - This method is called from process_urls_in_sms_body_text() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param urls_in_sms_body_text: URLs present in SMS body text
        :param short_urls: shortened URL to redirect candidate to our app
        :type short_urls: list
        :type urls_in_sms_body_text: list
        :exception: ErrorUpdatingBodyText
        :return: modified_body_text, SMS body which will be actually sent to candidate
        :rtype: str

        **See Also**
        .. see also:: process_urls_in_sms_body_text() method in SmsCampaignBase class.
        """
        logger.debug('transform_body_text: Replacing original URL with shortened URL. (User(id:%s))'
                     % self.user.id)
        try:
            if urls_in_sms_body_text:
                text_split = self.body_text.split(' ')
                short_urls_index = 0
                for url in urls_in_sms_body_text:
                    text_split_index = 0
                    for word in text_split:
                        if word == url:
                            text_split[text_split_index] = short_urls[short_urls_index]
                            break
                        text_split_index += 1
                    short_urls_index += 1
                modified_body_text = ' '.join(text_split)
            else:
                modified_body_text = self.body_text
        except Exception as error:
            raise ErrorUpdatingBodyText(
                'Error while updating body text. Error is %s' % error.message)
        return modified_body_text

    @staticmethod
    def create_sms_campaign_blast(campaign_id, sends=0, clicks=0, replies=0):
        """
        - Here we create SMS blast for a campaign. We also use this to update
            record with every new send. This gives the statistics about a campaign.

        - This method is called from process_send() and send_sms_campaign_to_candidates()
            methods of class SmsCampaignBase inside
            sms_campaign_service/sms_campaign_base.py.

        :param campaign_id: id of "sms_campaign"
        :param sends: numbers of sends, default 0
        :param clicks: number of clicks on a sent SMS, default 0
        :param replies: number of replies on a sent SMS, default 0
        :type campaign_id: int
        :type sends: int
        :type clicks: int
        :type replies: int
        :return: id of "sms_campaign_blast" record
        :rtype: int

        **See Also**
        .. see also:: process_send() method in SmsCampaignBase class.

        .. see also:: send_sms_campaign_to_candidates() method in SmsCampaignBase class.
        """
        data = {'sms_campaign_id': campaign_id,
                'sends': sends,
                'clicks': clicks,
                'replies': replies,
                'sent_datetime': datetime.now()}
        blast_obj = SmsCampaignBlast(**data)
        SmsCampaignBlast.save(blast_obj)
        return blast_obj.id

    def send_sms(self, candidate_phone_value, message_body):
        """
        - This uses Twilio API to send SMS to a given phone number of candidate.

        - This method is called from send_sms_campaign_to_candidates() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param candidate_phone_value: Candidate mobile phone number.
        :type candidate_phone_value: str
        :exception: InvalidUsage
        :return: sent message time
        :rtype: datetime

        **See Also**
        .. see also:: send_sms_campaign_to_candidates() method in SmsCampaignBase class.
        """
        if not isinstance(candidate_phone_value, basestring):
            raise InvalidUsage('Include candidate_phone as str')
        if app.config[TalentConfigKeys.IS_DEV]:
            # send SMS using Twilio Test Credentials
            sender_phone = TWILIO_TEST_NUMBER
            candidate_phone_value = TWILIO_TEST_NUMBER
        else:
            # format phone number of user and candidate
            sender_phone = format_phone_number(self.user_phone.value)
        twilio_obj = TwilioSMS()
        message_response = twilio_obj.send_sms(body_text=message_body,
                                               sender_phone=sender_phone,
                                               receiver_phone=candidate_phone_value)
        return message_response.date_created

    @staticmethod
    def create_or_update_sms_campaign_send(campaign_blast_id, candidate_id, sent_datetime):
        """
        - Here we add an entry in "sms_campaign_send" db table for each SMS send.

        - This method is called from send_sms_campaign_to_candidates() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param campaign_blast_id: id of sms_campaign_blast
        :param candidate_id: id of candidate to which SMS is supposed to be sent
        :param sent_datetime: Time of sent SMS
        :type campaign_blast_id: int
        :type candidate_id: int
        :type sent_datetime: datetime
        :return: "sms_campaign_send" record
        :rtype: SmsCampaignSend

        **See Also**
        .. see also:: send_sms_campaign_to_candidates() method in SmsCampaignBase class.
        """
        data = {'sms_campaign_blast_id': campaign_blast_id,
                'candidate_id': candidate_id,
                'sent_datetime': sent_datetime}
        record_in_db = SmsCampaignSend.get_by_blast_id_and_candidate_id(campaign_blast_id,
                                                                        candidate_id)
        if record_in_db:
            record_in_db.update(**data)
            return record_in_db
        else:
            new_record = SmsCampaignSend(**data)
            SmsCampaignSend.save(new_record)
            return new_record

    @staticmethod
    def create_or_update_sms_send_url_conversion(campaign_send_obj, url_conversion_id):
        """
        - For each SMS send, here we add an entry in database table
            "sms_campaign_send_url_conversion".

        - This method is called from send_sms_campaign_to_candidates() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param campaign_send_obj: sms_campaign_send obj
        :param url_conversion_id: id of url_conversion record
        :type campaign_send_obj: SmsCampaignSend
        :type url_conversion_id: int

        **See Also**
        .. see also:: send_sms_campaign_to_candidates() method in SmsCampaignBase class.
        """
        if not isinstance(campaign_send_obj, SmsCampaignSend):
            raise InvalidUsage('First param should be instance of SmsCampaignSend model')

        data = {'sms_campaign_send_id': campaign_send_obj.id,
                'url_conversion_id': url_conversion_id}
        record_in_db = SmsCampaignSendUrlConversion.get_by_campaign_send_id_and_url_conversion_id(
            campaign_send_obj.id, url_conversion_id)
        if record_in_db:
            record_in_db.update(**data)
        else:
            new_record = SmsCampaignSendUrlConversion(**data)
            SmsCampaignSendUrlConversion.save(new_record)

    def create_sms_send_activity(self, candidate, source):
        """
        - Here we set "params" and "type" of activity to be stored in db table "Activity"
            for each send.

        - Activity will appear as
            "SMS Campaign 'Hiring at Microsoft' has been sent to 'Borko Jendras'."

        - This method is called from send_sms_campaign_to_candidates() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param candidate: Candidate obj
        :param source: sms_campaign_send obj
        :type candidate: Candidate
        :type source: SmsCampaignSend
        :exception: InvalidUsage

        **See Also**
        .. see also:: send_sms_campaign_to_candidates() method in SmsCampaignBase class.
        """
        if not isinstance(candidate, Candidate):
            raise InvalidUsage(
                'Candidate should be instance of model Candidate')
        if not isinstance(source, SmsCampaignSend):
            raise InvalidUsage(
                'Source should be instance of model SmsCampaignSend')
        params = {'candidate_name': candidate.first_name + ' ' + candidate.last_name,
                  'campaign_name': self.campaign.name}
        self.create_activity(self.user.id,
                             _type=ActivityMessageIds.CAMPAIGN_SMS_SEND,
                             source_id=source.id,
                             source_table=SmsCampaignSend.__tablename__,
                             params=params,
                             headers=self.oauth_header)

    @classmethod
    def process_candidate_reply(cls, reply_data):
        """
        - Recruiters(users) are assigned to one unique twilio number.sms_callback_url of
        that number is set to redirect request at this end point. Twilio API hits this URL
        with data like
                 {
                      "From": "+12015617985",
                      "To": "+15039255479",
                      "Body": "Dear all, we have few openings at http://www.qc-technologies.com",
                      "SmsStatus": "received",
                      "FromCity": "FELTON",
                      "FromCountry": "US",
                      "FromZip": "95018",
                      "ToCity": "SHERWOOD",
                      "ToCountry": "US",
                      "ToZip": "97132",
                 }

        - When candidate replies to user'phone number, we do the following at our App's
            endpoint '/v1/receive'

            1- Gets "user_phone" record using "To" key
            2- Gets "candidate_phone" record using "From" key
            3- Gets latest campaign sent to given candidate
            4- Gets "sms_campaign_blast" obj for "sms_campaign_send" found in step-3
            5- Saves candidate's reply in db table "sms_campaign_reply"
            6- Creates Activity that (e.g)
                    "Alvaro Oliveira" has replied "Thanks" to campaign "Jobs at Google"
            7- Updates the count of replies in "sms_campaign_blast" by 11

        :param reply_data:
        :type reply_data: dict

        .. Status:: 200 (OK)
                    403 (ForbiddenError)
                    404 (Resource not found)
                    500 (Internal Server Error)

        .. Error codes:
                     MISSING_REQUIRED_FIELD(5006)
                     MultipleUsersFound(5007)
                     MultipleCandidatesFound(5008)
                     NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN(5011)
                     NoCandidateAssociatedWithSmartlist(5012)
                     NoSMSCampaignSentToCandidate(5013)
                     NoUserFoundForPhoneNumber(5016)
                     NoCandidateFoundForPhoneNumber (5017)

        **See Also**
        .. see also:: sms_receive() function in sms_campaign_app/app.py
        """
        required_fields = ['From', 'To', 'Body']
        missing_items = find_missing_items(reply_data, required_fields)
        if missing_items:
            raise InternalServerError(
                'process_candidate_reply: Missing items are %s' % missing_items,
                error_code=SmsCampaignApiException.MISSING_REQUIRED_FIELD)
        # get "user_phone" obj
        user_phone = _get_valid_user_phone_value(reply_data.get('To'))
        # get "candidate_phone" obj
        candidate_phone = _validate_candidate_phone_value(reply_data.get('From'))
        # get latest campaign send
        sms_campaign_send = SmsCampaignSend.get_by_candidate_id(candidate_phone.candidate_id)
        if not sms_campaign_send:
            raise NoSMSCampaignSentToCandidate(
                'No SMS campaign sent to candidate(id:%s)'
                % candidate_phone.candidate_id)
        # get SMS campaign blast
        sms_campaign_blast = SmsCampaignBlast.get_by_id(
            sms_campaign_send.sms_campaign_blast_id)
        # save candidate's reply
        sms_campaign_reply = cls.save_candidate_reply(sms_campaign_blast.id,
                                                      candidate_phone.id,
                                                      reply_data.get('Body'))
        # create Activity
        cls.create_campaign_reply_activity(sms_campaign_reply,
                                           sms_campaign_blast,
                                           candidate_phone.candidate_id,
                                           user_phone.user_id)
        # get/update SMS campaign blast i.e. increase number of replies by 1
        cls.update_campaign_blast(sms_campaign_blast, replies=True)
        logger.debug('Candidate(id:%s) replied "%s" to Campaign(id:%s).(User(id:%s))'
                     % (candidate_phone.candidate_id, reply_data.get('Body'),
                        sms_campaign_blast.sms_campaign_id, user_phone.user_id))

    @classmethod
    def save_candidate_reply(cls, campaign_blast_id, candidate_phone_id, reply_body_text):
        """
        - Here we save the reply of candidate in db table "sms_campaign_reply"

        :param campaign_blast_id: id of "sms_campaign_blast" record
        :param candidate_phone_id: id of "candidate_phone" record
        :param reply_body_text: body_text
        :type campaign_blast_id: int
        :type candidate_phone_id: int
        :type reply_body_text: str
        :return:
        """
        sms_campaign_reply_obj = SmsCampaignReply(sms_campaign_blast_id=campaign_blast_id,
                                                  candidate_phone_id=candidate_phone_id,
                                                  body_text=reply_body_text,
                                                  added_datetime=datetime.now())
        SmsCampaignReply.save(sms_campaign_reply_obj)
        return sms_campaign_reply_obj

    @classmethod
    def create_campaign_reply_activity(cls, sms_campaign_reply, campaign_blast, candidate_id,
                                       user_id):
        """
        - Here we set "params" and "type" of activity to be stored in db table "Activity"
            for Campaign reply.

        - Activity will appear as

            Smith replied "Got it" on SMS campaign "abc".

        - This method is called from process_candidate_reply() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param sms_campaign_reply: "sms_campaign_reply" obj
        :param campaign_blast: "sms_campaign_blast" obj
        :param candidate_id: id of Candidate
        :type sms_campaign_reply: SmsCampaignReply
        :type campaign_blast: SmsCampaignBlast
        :type candidate_id: int | long
        :exception: ResourceNotFound

        **See Also**
        .. see also:: process_candidate_reply() method in SmsCampaignBase class.
        """
        # get Candidate
        candidate = Candidate.get_by_id(candidate_id)
        if not candidate:
            raise ResourceNotFound(
                'create_campaign_reply_activity: Candidate(id:%s) not found.'
                % candidate_id, error_code=ResourceNotFound.http_status_code())
        campaign = SmsCampaign.get_by_id(campaign_blast.sms_campaign_id)
        if not campaign:
            raise ResourceNotFound(
                'create_campaign_reply_activity: SMS Campaign(id=%s) Not found.'
                % campaign.id, error_code=ResourceNotFound.http_status_code())
        params = {'candidate_name': candidate.first_name + ' ' + candidate.last_name,
                  'reply_text': sms_campaign_reply.body_text,
                  'campaign_name': campaign.name}
        user_access_token = cls.get_authorization_header(user_id)
        cls.create_activity(user_id,
                            _type=ActivityMessageIds.CAMPAIGN_SMS_REPLY,
                            source_id=sms_campaign_reply.id,
                            source_table=SmsCampaignReply.__tablename__,
                            params=params,
                            headers=user_access_token)


def _get_valid_user_phone_value(user_phone_value):
    """
    - This ensures that given phone number is associated with only one user (i.e. recruiter).

    - This function is called from class method process_candidate_reply() of
    SmsCampaignBase class to get user_phone db record.

    :param user_phone_value: Phone number by which we want to get user.
    :type user_phone_value: str
    :exception: If Multiple users found, it raises "MultipleUsersFound".
    :exception: If no user is found, it raises "ResourceNotFound".
    :return: user_phone obj
    :rtype: UserPhone
    """
    user_phones_obj = UserPhone.get_by_phone_value(user_phone_value)
    if len(user_phones_obj) == 1:
        user_phone = user_phones_obj[0]
    elif len(user_phones_obj) > 1:
        raise MultipleUsersFound(
            '%s phone number is associated with %s users. User ids are %s'
            % (user_phone_value,
               len(user_phones_obj),
               [user_phone.user_id for user_phone in user_phones_obj]))
    else:
        raise NoUserFoundForPhoneNumber('No User is associated with '
                                        '%s phone number' % user_phone_value)
    return user_phone


def _validate_candidate_phone_value(candidate_phone_value):
    """
    - This ensures that given phone number is associated with only one candidate.

    - This function is called from class method process_candidate_reply() of
    SmsCampaignBase class to get candidate_phone db record.

    :param candidate_phone_value: Phone number by which we want to get user.
    :type candidate_phone_value: str
    :exception: If Multiple Candidates found, it raises "MultipleCandidatesFound".
    :exception: If no Candidate is found, it raises "NoCandidateFoundForPhoneNumber".
    :return: candidate obj
    :rtype: Candidate
    """
    candidate_phone_records = CandidatePhone.get_by_phone_value(candidate_phone_value)
    if len(candidate_phone_records) == 1:
        candidate_phone = candidate_phone_records[0]
    elif len(candidate_phone_records) > 1:
        raise MultipleCandidatesFound(
            '%s phone number is associated with %s candidates. Candidate ids are %s'
            % (candidate_phone_value,
               len(candidate_phone_records),
               [candidate_phone.candidate_id for candidate_phone
                in candidate_phone_records]))
    else:
        raise NoCandidateFoundForPhoneNumber(
            'No Candidate is associated with %s phone number' % candidate_phone_value)
    return candidate_phone
