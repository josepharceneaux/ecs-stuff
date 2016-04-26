"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

This module contains SmsCampaignBase class inherited from CampaignBase.
This is used to send SMS campaign to candidates.
This implements abstract methods of CampaignBase class and defines its own
methods like
     - save()
     - buy_twilio_mobile_number()
     - create_or_update_user_phone()
     - send()
     - process_link_in_body_text()
     - transform_body_text()
     - send_campaign_to_candidate()
     - send_sms()
     - process_candidate_reply() etc.

It also contains private methods for this module as
    - _get_valid_user_phone()
    - _get_valid_candidate_phone()
"""

# Standard Library
from datetime import datetime

# Third party
from dateutil.relativedelta import relativedelta

# Database Models
from sms_campaign_service.common.models.db import db
from sms_campaign_service.common.models.misc import Activity
from sms_campaign_service.common.models.user import UserPhone, User
from sms_campaign_service.common.models.candidate import (PhoneLabel, Candidate, CandidatePhone)
from sms_campaign_service.common.models.sms_campaign import (SmsCampaign, SmsCampaignSend,
                                                             SmsCampaignBlast, SmsCampaignReply
                                                             )
# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.talent_config_manager import TalentConfigKeys, TalentEnvs
from sms_campaign_service.common.campaign_services.campaign_base import CampaignBase
from sms_campaign_service.common.campaign_services.campaign_utils import CampaignUtils
from sms_campaign_service.common.error_handling import (ForbiddenError, InvalidUsage)
from sms_campaign_service.common.campaign_services.custom_errors import (MultipleCandidatesFound,
                                                                         CampaignException)
from sms_campaign_service.common.utils.handy_functions import (find_missing_items, url_conversion)
from sms_campaign_service.common.utils.validators import raise_if_not_instance_of
from sms_campaign_service.common.campaign_services.validators import \
    raise_if_dict_values_are_not_int_or_long

# Service Specific
from sms_campaign_service.sms_campaign_app import celery_app, app, logger
from sms_campaign_service.modules.validators import (validate_url_format,
                                                     validate_urls_in_body_text)
from sms_campaign_service.modules.handy_functions import (TwilioSMS, replace_localhost_with_ngrok,
                                                          get_formatted_phone_number,
                                                          search_urls_in_text)
from sms_campaign_service.modules.sms_campaign_app_constants import (MOBILE_PHONE_LABEL, TWILIO,
                                                                     TWILIO_TEST_NUMBER)
from sms_campaign_service.modules.custom_exceptions import (TwilioApiError,
                                                            MultipleUsersFound,
                                                            ErrorUpdatingBodyText,
                                                            SmsCampaignApiException,
                                                            GoogleShortenUrlAPIError,
                                                            NoUserFoundForPhoneNumber,
                                                            NoSMSCampaignSentToCandidate,
                                                            CandidateNotFoundInUserDomain,
                                                            MultipleTwilioNumbersFoundForUser)


class SmsCampaignBase(CampaignBase):
    """
    - This is the base class for sending SMS campaign to candidates and to keep track
        of their responses. It uses Twilio API to send SMS.

    - This is inherited from CampaignBase defined inside
        app_common/common/utils/campaign_base.py. It implements abstract
        methods of base class and defines its own methods also.

    This class contains following methods:

    * __init__()

        - It takes "user_id" as keyword argument.
        - It calls super class __init__ to get user obj and set it in self.user..
        - It then gets the user_phone obj from "user_phone" db table using
            provided "user_id".

    * get_campaign_type(self)
        This returns 'sms_campaign' as the type of campaign.

    * get_user_phone(self)
        This gets the Twilio number of current user from database table "user_phone".

    * buy_twilio_mobile_number(self, phone_label_id=None)
        To send sms_campaign, we need to reserve a unique number for each user.
        This method is used to reserve a unique number for getTalent user.

    * create_or_update_user_phone(user_id, phone_number, phone_label_id): [static]
        This method is used to create/update user_phone record.

    * get_all_campaigns(self)
        This gets all the campaigns created by current user.

    * pre_process_save_or_update(self, form_data)
        This overrides CampaignBase class method to do any further validation.

    * save(self, form_data)
        This overrides tha CampaignBase class method.
        This appends user_phone_id in form_data and calls super constructor to save/update
        the campaign in database.

    * schedule(self, data_to_schedule)
        This overrides the base class method and sets the value of data_to_schedule.
        It then calls super constructor to get task_id for us. Then we will update
        SMS campaign record in sms_campaign table with frequency_id, start_datetime,
        end_datetime and "task_id"(Task created on APScheduler).

    * get_domain_id_of_campaign(campaign_obj, current_user_id)
        This gets the if of user who created the given campaign object.

    * does_candidate_have_unique_mobile_phone(self, candidate)
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

    * send_sms(self, candidate_phone_value)
        This finally sends the SMS to candidate using Twilio API.

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

        >>>    from sms_campaign_service.modules.sms_campaign_base import SmsCampaignBase
        >>>    camp_obj = SmsCampaignBase(int('user_id'))

        3- Call method send
        >>>     camp_obj.send(int('sms_campaign_id_goes_here'))

    **See Also**
        .. see also:: CampaignBase class in app_common/common/utils/campaign_base.py.
    """

    def __init__(self, user_id, campaign_id=None):
        """
        Here we set the "user" by calling super constructor and "user_phone" by
        calling get_user_phone() method,
        :param user_id: Id of logged-in user
        :param campaign_id: Id of campaign object in database
        :type user_id: int | long
        :type campaign_id: int | long | None
        """
        # sets the user_id
        super(SmsCampaignBase, self).__init__(user_id, campaign_id=campaign_id)
        self.user_phone = self.get_user_phone()
        if not self.user_phone:
            raise ForbiddenError('User(id:%s) has no phone number' % self.user.id)

    def get_campaign_type(self):
        """
        This sets the value of self.campaign_type to be 'sms_campaign'.
        """
        return CampaignUtils.SMS

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
        raise_if_not_instance_of(self.user, User)
        # TWILIO is a name defined in config
        phone_label_id = PhoneLabel.phone_label_id_from_phone_label(TWILIO)
        user_phone = UserPhone.get_by_user_id_and_phone_label_id(self.user.id,
                                                                 phone_label_id)
        if len(user_phone) == 1:
            # check if Twilio number is assigned to only one user
            user_phone_value = user_phone[0].value
            _get_valid_user_phone(user_phone_value)
            if user_phone_value:
                return user_phone[0]
        elif len(user_phone) > 1:
            raise MultipleTwilioNumbersFoundForUser(
                'User(id:%s) has multiple phone numbers for phone label: %s'
                % (self.user.id, TWILIO))
        else:
            # User has no associated Twilio number, need to buy one
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
        :exception: TwilioApiError
        :return: UserPhone obj
        :rtype: UserPhone
        """
        if not phone_label_id:
            raise InvalidUsage('phone_label_id must be an integer.')
        twilio_obj = TwilioSMS()
        if CampaignUtils.IS_DEV:
            # Buy Twilio TEST number so that we won't be charged in case of dev, jenkins and QA
            number_to_buy = TWILIO_TEST_NUMBER
        else:
            logger.debug('buy_twilio_mobile_number: Going to buy Twilio number for '
                         'user(id:%s).' % self.user.id)
            available_phone_numbers = twilio_obj.get_available_numbers()
            # We get a list of 30 available numbers and we pick very first phone number to buy.
            number_to_buy = available_phone_numbers[0].phone_number
        twilio_obj.purchase_twilio_number(number_to_buy)
        formatted_number = get_formatted_phone_number(number_to_buy)
        user_phone = self.create_or_update_user_phone(self.user.id, formatted_number,
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
        empty_items = find_missing_items(data, verify_all=True)
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
        return self.user_phone.sms_campaigns

    def pre_process_save_or_update(self, form_data):
        """
        This overrides the CampaignBase class method.
        It calls super constructor to do the common validation. It then validates if body_text
        has valid URLs in it (if there are any)
        :param form_data: data from UI
        :return: validation_result
        :rtype: tuple
        :exception: Invalid URL
        """
        validation_result = super(SmsCampaignBase, self).pre_process_save_or_update(form_data)
        # validate URLs present in SMS body text
        invalid_urls = validate_urls_in_body_text(form_data['body_text'])
        if invalid_urls:
            raise InvalidUsage('Invalid URL(s) in body_text. %s' % invalid_urls,
                               error_code=SmsCampaignApiException.INVALID_URL_FORMAT)
        return validation_result

    def save(self, form_data):
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
        logger.debug("user_phone_id has been added in form data for user %s(id:%s)"
                     % (self.user.name, self.user.id))
        return super(SmsCampaignBase, self).save(form_data)

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

        - This method is called from the endpoint /v1/sms-campaigns/:id/schedule on HTTP
            methods POST/PUT

        :param data_to_schedule: required data to schedule an SMS campaign
        :type data_to_schedule: dict
        :return: task_id (Task created on APScheduler), and status of task(already scheduled
                            or new scheduled)
        :rtype: tuple

        **See Also**
        .. see also:: ScheduleSmsCampaign() resource in v1_sms_campaign_api.py.
        """
        if not data_to_schedule or not isinstance(data_to_schedule, dict):
            raise InvalidUsage('Data to schedule a task should be non-empty dictionary.')
        data_to_schedule.update(
            {'url_to_run_task': SmsCampaignApiUrl.SEND % self.campaign.id}
        )
        # get scheduler task_id created on scheduler_service
        scheduler_task_id = super(SmsCampaignBase, self).schedule(data_to_schedule)
        # update sms_campaign record with task_id
        self.campaign.update(scheduler_task_id=scheduler_task_id)
        return scheduler_task_id

    @staticmethod
    def get_domain_id_of_campaign(campaign_obj, current_user_id):
        """
        This implements the base class method and returns the id of user who created the
        given campaign.
        :param campaign_obj: campaign object
        :param current_user_id: id of logged-in user
        :type campaign_obj: SmsCampaign
        :type current_user_id: int | long
        :exception: Invalid Usage
        :return: domain_id of owner user of given campaign
        :rtype: int | long
        """
        CampaignUtils.raise_if_not_instance_of_campaign_models(campaign_obj)
        if not campaign_obj.user_phone_id:
            raise ForbiddenError('%s(id:%s) has no user_phone associated.'
                                 % (campaign_obj.__tablename__, campaign_obj.id))
        # using relationship
        user_phone = campaign_obj.user_phone
        if not user_phone:
            raise InvalidUsage('User(id:%s) has no phone number associated.' % current_user_id)
        # using relationship
        return user_phone.user.domain_id

    def does_candidate_have_unique_mobile_phone(self, candidate):
        """
        Here we validate that if candidate has one unique mobile number associated.
        If candidate has only one unique mobile number associated, we return that candidate and
        its phone value.
        Otherwise we log the error.

        - This method is used in send_campaign_to_candidate() method.

        :param candidate: candidates obj
        :type candidate: Candidate
        :exception: InvalidUsage
        :exception: MultipleCandidatesFound
        :exception: CandidateNotFoundInUserDomain
        :return: Candidate obj and Candidate's mobile phone
        :rtype: tuple

        **See Also**
        .. see also:: send_campaign_to_candidate() method in SmsCampaignBase class.
        """
        raise_if_not_instance_of(candidate, Candidate)
        candidate_phones = candidate.phones
        mobile_label_id = PhoneLabel.phone_label_id_from_phone_label(MOBILE_PHONE_LABEL)

        # filter only mobile numbers
        candidate_mobile_phone = filter(lambda candidate_phone:
                                        candidate_phone.phone_label_id == mobile_label_id,
                                        candidate_phones)
        if len(candidate_mobile_phone) == 1:
            # If this number is associated with multiple candidates, raise exception
            phone_number = candidate_mobile_phone[0].value
            _get_valid_candidate_phone(phone_number, self.user)
            return candidate, get_formatted_phone_number(phone_number)
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
        :param candidates: list of candidates to whom we want to send campaign
        :type candidates: list[Candidate]
        """
        not_owned_ids = []
        multiple_records_ids = []
        candidates_and_phones = []
        for candidate in candidates:
            try:
                # check if candidate belongs to user's domain
                if candidate.user_id != self.user.id:
                    raise CandidateNotFoundInUserDomain
                candidates_and_phones.append(self.does_candidate_have_unique_mobile_phone(candidate))
            except CandidateNotFoundInUserDomain:
                not_owned_ids.append(candidate.id)
            except MultipleCandidatesFound:
                multiple_records_ids.append(candidate.id)
        logger.debug('send: SMS Campaign(id:%s) will be sent to %s candidate(s). '
                     '(User(id:%s))' % (self.campaign.id, len(candidates_and_phones),
                                        self.user.id))
        if not_owned_ids or multiple_records_ids:
            logger.error('send: SMS Campaign(id:%s) not_owned_candidate_ids: %s. '
                         'multiple_records_against_ids:%s '
                         '(User(id:%s))' % (self.campaign.id, not_owned_ids,
                                            multiple_records_ids,
                                            self.user.id))
        logger.info('user_phone %s' % self.user_phone.value)
        candidates_and_phones = filter(lambda obj: obj is not None, candidates_and_phones)
        super(SmsCampaignBase, self).pre_process_celery_task(candidates_and_phones)
        return candidates_and_phones

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
            7- Once campaign is sent to all candidates, we create activity in callback function
                of Celery task.
                e.g. (SMS Campaign "abc" was sent to "1000" candidates")

        - This method is called from send_sms_campaign_to_candidates() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param candidate_and_phone: candidate obj at index 0 and candidate phone value at index 1
        :type candidate_and_phone: tuple
        :exception: ErrorUpdatingBodyText
        :exception: TwilioApiError
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
            try:
                modified_body_text, url_conversion_ids = \
                    self.process_urls_in_sms_body_text(candidate.id)
            except Exception:
                logger.exception('send_campaign_to_candidate: Error processing URLs in SMS body')
                return False
            # send SMS
            try:
                message_sent_datetime = self.send_sms(candidate_phone_value, modified_body_text)
            except TwilioApiError or InvalidUsage:
                logger.exception('send_campaign_to_candidate: Cannot send SMS.')
                return False
            # Create sms_campaign_send i.e. it will record that an SMS has been sent
            # to the candidate
            try:
                sms_campaign_send_obj = self.create_or_update_campaign_send(
                    self.campaign_blast_id, candidate.id, message_sent_datetime, SmsCampaignSend)
            except Exception:
                logger.exception('send_campaign_to_candidate: Error saving '
                                 'record in sms_campaign_send')
                return False
            # We keep track of all URLs sent, in sms_send_url_conversion table,
            # so we can later retrieve that to perform some tasks
            try:
                for url_conversion_id in url_conversion_ids:
                    self.create_or_update_send_url_conversion(sms_campaign_send_obj,
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

        This uses post_campaign_sent_processing() function defined in
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
            CampaignUtils.post_campaign_sent_processing(CampaignBase, sends_result, user_id,
                                                        campaign_type, blast_id, oauth_header)

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
                     http://127.0.0.1:8012/v1/redirect/1
                3- Convert the source_url into shortened URL using Google's shorten URL API.
                4- Replace the link in original body text with the shortened URL
                    (which we created in step 2)
                5- Set the updated body text in self.transform_body_text

            Otherwise we save the body text in modified_body_text

        - This method is called from send() method of class SmsCampaignBase inside
            sms_campaign_service/sms_campaign_base.py.

        :param candidate_id: id of Candidate
        :type candidate_id: int | long
        :exception: GoogleShortenUrlAPIError
        :return: list of URL conversion records
        :rtype: list

        **See Also**
        .. see also:: send() method in SmsCampaignBase class.
        """
        raise_if_dict_values_are_not_int_or_long(dict(candidate_id=candidate_id))
        logger.debug('process_urls_in_sms_body_text: Processing any '
                     'link present in body_text for '
                     'SMS Campaign(id:%s) and Candidate(id:%s). (User(id:%s))'
                     % (self.campaign.id, candidate_id, self.user.id))
        urls_in_body_text = search_urls_in_text(self.campaign.body_text)
        short_urls = []
        url_conversion_ids = []
        for url in urls_in_body_text:
            validate_url_format(url)
            # We have only one link in body text which needs to shortened.
            url_conversion_id = self.create_or_update_url_conversion(destination_url=url,
                                                                     source_url='')
            # URL to redirect candidates to our end point
            app_redirect_url = SmsCampaignApiUrl.REDIRECT
            if app.config[TalentConfigKeys.ENV_KEY] == TalentEnvs.DEV:
                app_redirect_url = replace_localhost_with_ngrok(SmsCampaignApiUrl.REDIRECT)
            # redirect URL looks like (for prod)
            # http://sms-campaing-service.gettalent.com/redirect/1
            redirect_url = str(app_redirect_url % url_conversion_id)
            # sign the redirect URL
            long_url = CampaignUtils.sign_redirect_url(redirect_url,
                                                       datetime.utcnow() + relativedelta(years=+1))
            # long_url looks like (for prod)
            # http://sms-campaing-service.gettalent.com/v1/redirect/1052?valid_until=1453990099.0
            #           &auth_user=no_user&extra=&signature=cWQ43J%2BkYetfmE2KmR85%2BLmvuIw%3D
            # Use Google's API to shorten the long URL
            short_url, error = url_conversion(long_url)
            logger.info("url_conversion: Long URL was: %s" % long_url)
            logger.info("url_conversion: Shortened URL is: %s" % short_url)
            if error:
                raise GoogleShortenUrlAPIError(error)
            short_urls.append(short_url)
            url_conversion_ids.append(url_conversion_id)
            if CampaignUtils.IS_DEV:
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
        if not urls_in_sms_body_text:
            return self.campaign.body_text
        logger.debug('transform_body_text: Replacing original URL with shortened URL. (User(id:%s))'
                     % self.user.id)
        if len(urls_in_sms_body_text) != len(short_urls):
            raise InvalidUsage('Count of URLs in SMS body and shorted URL must be same.')
        try:
            body_text = self.campaign.body_text.strip()
            url_pairs = zip(urls_in_sms_body_text, short_urls)
            for url_pair in url_pairs:
                body_text = body_text.replace(url_pair[0], url_pair[1])
            return body_text
        except Exception:
            raise ErrorUpdatingBodyText('Error while updating body text.')

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
        raise_if_not_instance_of(candidate_phone_value, basestring)
        logger.debug("candidate's phone value passed is %s" % candidate_phone_value)
        if CampaignUtils.IS_DEV:
            # send SMS using Twilio Test Credentials
            sender_phone = TWILIO_TEST_NUMBER
            candidate_phone_value = TWILIO_TEST_NUMBER
        else:
            sender_phone = self.user_phone.value
        logger.debug("user's phone value in self.user_phone is %s" % self.user_phone.value)
        logger.debug("user's phone value in sender_phone is %s" % sender_phone)
        logger.debug("candidate's phone value in receiver phone is %s" % candidate_phone_value)
        twilio_obj = TwilioSMS()
        message_response = twilio_obj.send_sms(message_body,
                                               str(sender_phone),
                                               str(candidate_phone_value))
        return message_response.date_created

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
        raise_if_not_instance_of(candidate, Candidate)
        raise_if_not_instance_of(source, SmsCampaignSend)
        params = {'candidate_name': candidate.first_name + ' ' + candidate.last_name,
                  'campaign_name': self.campaign.name}
        self.create_activity(self.user.id,
                             _type=Activity.MessageIds.CAMPAIGN_SMS_SEND,
                             source=source,
                             params=params)

    @classmethod
    def process_candidate_reply(cls, reply_data):
        """
        - Recruiters(users) are assigned to one unique Twilio number. sms_callback_url of
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

        - When candidate replies to a recruiter's phone_number, endpoint '/v1/receive' is hit by
            Twilio and this method does the following step:
            1- Gets "user_phone" record using "To" key
            2- Gets "candidate_phone" record using "From" key
            3- Gets latest campaign sent to given candidate
            4- Gets "sms_campaign_blast" obj for "sms_campaign_send" found in step-3
            5- Saves candidate's reply in db table "sms_campaign_reply"
            6- Creates Activity that (e.g)
                    "Alvaro Oliveira" has replied "Thanks" to campaign "Jobs at Google"
            7- Updates the count of replies in "sms_campaign_blast" by 11

        .. Status:: 200 (OK)
                    400 (Invalid Usage)
                    403 (ForbiddenError)
                    404 (Resource not found)
                    500 (Internal Server Error)

        .. Error codes::

                     MultipleUsersFound(5005)
                     NoSMSCampaignSentToCandidate(5006)
                     CandidateNotFoundInUserDomain(5008)
                     NoUserFoundForPhoneNumber(5009)
                     MultipleCandidatesFound(5016)
                     NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN(5102)
                     NoCandidateAssociatedWithSmartlist(5103)

        **See Also**
        .. see also:: SmsReceive() class in sms_campaign_app/v1_sms_campaign_api.py

        :param reply_data:
        :type reply_data: dict

        """
        required_fields = ['From', 'To', 'Body']
        missing_items = find_missing_items(reply_data, required_fields)
        if missing_items:
            raise InvalidUsage(
                'process_candidate_reply: Missing items are %s' % missing_items,
                error_code=CampaignException.MISSING_REQUIRED_FIELD)
        # get "user_phone" obj
        user_phone = _get_valid_user_phone(reply_data.get('To'))
        # get "candidate_phone" obj
        candidate_phone = _get_valid_candidate_phone(reply_data.get('From'), user_phone.user)
        # get latest campaign send
        sms_campaign_send = \
            SmsCampaignSend.get_latest_campaign_by_candidate_id(candidate_phone.candidate_id)
        if not sms_campaign_send:
            raise NoSMSCampaignSentToCandidate(
                'No SMS campaign sent to candidate(id:%s)'
                % candidate_phone.candidate_id)
        # get SMS campaign blast
        sms_campaign_blast = sms_campaign_send.blast
        # save candidate's reply
        sms_campaign_reply = cls.save_candidate_reply(sms_campaign_blast.id,
                                                      candidate_phone.id,
                                                      reply_data.get('Body'))
        try:
            # create Activity
            cls.create_campaign_reply_activity(sms_campaign_reply,
                                               sms_campaign_blast,
                                               candidate_phone.candidate,
                                               user_phone.user_id)
        except Exception:
            logger.exception('process_candidate_reply: Error creating SMS receive activity.')
        # get/update SMS campaign blast i.e. increase number of replies by 1
        cls.update_campaign_blast(sms_campaign_blast, replies=True)
        logger.debug('Candidate(id:%s) replied "%s" to Campaign(id:%s).(User(id:%s))'
                     % (candidate_phone.candidate_id, reply_data.get('Body'),
                        sms_campaign_blast.campaign_id, user_phone.user_id))

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
        sms_campaign_reply_obj = SmsCampaignReply(blast_id=campaign_blast_id,
                                                  candidate_phone_id=candidate_phone_id,
                                                  body_text=reply_body_text,
                                                  added_datetime=datetime.now())
        SmsCampaignReply.save(sms_campaign_reply_obj)
        return sms_campaign_reply_obj

    @classmethod
    def create_campaign_reply_activity(cls, sms_campaign_reply, campaign_blast, candidate,
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
        :param candidate: Candidate obj
        :type sms_campaign_reply: SmsCampaignReply
        :type campaign_blast: SmsCampaignBlast
        :type candidate: Candidate
        :exception: ResourceNotFound

        **See Also**
        .. see also:: process_candidate_reply() method in SmsCampaignBase class.
        """
        # get Candidate
        raise_if_not_instance_of(candidate, Candidate)
        campaign = campaign_blast.campaign
        raise_if_not_instance_of(campaign, SmsCampaign)
        params = {'candidate_name': candidate.first_name + ' ' + candidate.last_name,
                  'reply_text': sms_campaign_reply.body_text,
                  'campaign_name': campaign.name}
        auth_header = cls.get_authorization_header(user_id)
        cls.create_activity(user_id,
                            _type=Activity.MessageIds.CAMPAIGN_SMS_REPLY,
                            source=sms_campaign_reply,
                            params=params)


def _get_valid_user_phone(user_phone_value):
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
    raise_if_not_instance_of(user_phone_value, basestring)
    user_phones_obj = UserPhone.get_by_phone_value(user_phone_value)
    if len(user_phones_obj) == 1:
        user_phone = user_phones_obj[0]
        return user_phone
    elif len(user_phones_obj) > 1:
        if not user_phone_value == TWILIO_TEST_NUMBER:
            raise MultipleUsersFound('%s phone number is associated with %s users. '
                                     'User ids are %s'
                                     % (user_phone_value, len(user_phones_obj),
                                        [user_phone.user_id for user_phone in user_phones_obj]))
    else:
        raise NoUserFoundForPhoneNumber('No User is associated with '
                                        '%s phone number' % user_phone_value)


def _get_valid_candidate_phone(candidate_phone_value, current_user):
    """
    - This ensures that given phone number is associated with only one candidate.

    - This function is called from class method process_candidate_reply() of
    SmsCampaignBase class to get candidate_phone db record.

    :param candidate_phone_value: Phone number by which we want to get user.
    :type candidate_phone_value: str
    :exception: If Multiple Candidates found, it raises "MultipleCandidatesFound".
    :exception: If no Candidate is found, it raises "CandidateNotFoundInUserDomain".
    :return: candidate_phone obj
    :rtype: CandidatePhone
    """
    raise_if_not_instance_of(candidate_phone_value, basestring)
    candidate_phone_records = CandidatePhone.search_phone_number_in_user_domain(
        candidate_phone_value, [candidate.id for candidate in current_user.candidates])
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
        raise CandidateNotFoundInUserDomain(
            "Candidate(phone=%s) does not belong to user's domain." % candidate_phone_value)
    return candidate_phone
