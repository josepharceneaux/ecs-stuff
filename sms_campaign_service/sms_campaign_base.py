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
     - send_sms_campaign_to_candidate()
     - send_sms()
     - process_url_redirect()
     - process_candidate_reply() etc.

It also contains private methods for this module as
    - _get_valid_user_phone_value()
    - _get_valid_user_phone_value()
"""

# Standard Library
from datetime import datetime

# Database Models
from sms_campaign_service.common.models.user import UserPhone
from sms_campaign_service.common.models.misc import UrlConversion
from sms_campaign_service.common.models.candidate import (PhoneLabel, Candidate, CandidatePhone)
from sms_campaign_service.common.models.sms_campaign import (SmsCampaign, SmsCampaignSend,
                                                             SmsCampaignBlast, SmsCampaignSmartlist,
                                                             SmsCampaignSendUrlConversion,
                                                             SmsCampaignReply)
# common utils
from sms_campaign_service.common.common_config import IS_DEV
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.utils.campaign_utils import CampaignBase
from sms_campaign_service.common.utils.activity_utils import ActivityMessageIds
from sms_campaign_service.common.utils.common_functions import (find_missing_items,
                                                                url_conversion)
from sms_campaign_service.common.error_handling import (ResourceNotFound, ForbiddenError,
                                                        InvalidUsage)

# Service Specific
from sms_campaign_service import logger, db
from sms_campaign_service.sms_campaign_app.app import celery_app, app
from sms_campaign_service.utilities import (TwilioSMS, search_urls_in_text,
                                            replace_localhost_with_ngrok, validate_url)
from sms_campaign_service.sms_campaign_app_constants import (MOBILE_PHONE_LABEL, TWILIO,
                                                             TWILIO_TEST_NUMBER)
from sms_campaign_service.custom_exceptions import (EmptySmsBody, MultipleTwilioNumbersFoundForUser,
                                                    EmptyDestinationUrl, MissingRequiredField,
                                                    MultipleUsersFound, MultipleCandidatesFound,
                                                    ErrorSavingSMSCampaign,
                                                    NoCandidateAssociatedWithSmartlist,
                                                    NoSmartlistAssociatedWithCampaign,
                                                    NoSMSCampaignSentToCandidate,
                                                    ErrorUpdatingBodyText,
                                                    NoCandidateFoundForPhoneNumber,
                                                    NoUserFoundForPhoneNumber,
                                                    GoogleShortenUrlAPIError, TwilioAPIError)


class SmsCampaignBase(CampaignBase):
    """
    - This is the base class for sending SMS campaign to candidates and to keep track
        of their responses. It uses Twilio API to send SMS.

    - This is inherited from CampaignBase defined inside
        flask_common/common/utils/campaign_utils.py. It implements abstract
        methods of base class and defines its own methods also.

    This class contains following methods:

    * __init__()

        - It takes "user_id" as keyword argument.
        - It calls super class __init__ to set user_id.
        - It then gets the user_phone obj from "user_phone" db table using
            provided "user_id".
        - Sets total_sends to 0.

    *  get_all_campaigns(self)
        This gets all the campaigns created by current user.

    * save(self, form_data)
        This method is used to save the campaign in db table 'sms_campaign' and
        returns the ID of fresh record in db.

    * create_or_update_sms_campaign(self, form_data, campaign_id=None)
        This saves/updates SMS campaign in database table sms_campaign

    * create_or_update_sms_campaign_smartlist(campaign, smartlist_ids): [static]
        This saves/updates smartlist ids associated with an SMS campaign in database
        table "sms_campaign_smartlist"

    * campaign_create_activity(self, sms_campaign)
        This creates activity that (e.g)
            " 'Smith' created an SMS campaign "Job Opening at getTalent".

    * get_user_phone(self)
        This gets the Twilio number of current user from database table "user_phone"

    * buy_twilio_mobile_number(self, phone_label_id=None)
        To send sms_campaign, we need to reserve a unique number for each user.
        This method is used to reserve a unique number for getTalent user.

    * create_or_update_user_phone(user_id, phone_number, phone_label_id): [static]
        This method is used to create/update user_phone record.

    * process_send(self, campaign_id=None)
        This method is used to send the campaign to candidates.

    * filter_candidate_for_valid_phone(self, candidate)
        This filter out candidate who have no mobile number associated with them.

    * send_campaign_to_candidate(self, candidate)
        This does the sending part and updates database tables "sms_campaign_blast" and
         "sms_campaign_send".

    * callback_campaign_sent(send_result, user_id, campaign, auth_header, candidate)
        Once the campaign is sent to all candidates of a particular smartlists, we crate an
        activity in Activity table that (e.g)
                " "Job opening at getTalent" campaign has been sent to "100" candidates"

    * celery_error(error)
        If we get any error on celery task, we here we catch it and log the error.

    * process_urls_in_sms_body_text(self, candidate_id)
        If "body_text" contains any link in it, then we need to transform the
        "body_text" by replacing long URL with shorter version using Google's Shorten
        URL API. If body text does not contain any link, it returns the body_text
        as it is.

    * transform_body_text(self, link_in_body_text, short_url)
        This replaces the original URL present in "body_text" with the shortened URL.

    * create_or_update_sms_campaign_blast(campaign_id, send=0, clicks=0, replies=0,
                            increment_sends=False, increment_clicks=False,
                            increment_replies=False): [static]
        For each campaign, here we create/update stats of that particular campaign.

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

    * create_campaign_send_activity(self, num_candidates)
        Once the campaign has been sent to all candidates, here we set params and type
        to be saved in db table 'Activity' that campaign has been sent to (say)
        40(num_candidates) candidates.
        Activity will appear as (e.g) "'Job opening at getTalent' has been sent to 40 candidates.".

    * pre_process_url_redirect(campaign_id, url_conversion_id, candidate_id)
        This does the validation of all the fields provided before processing the
        URL redirection.

    * process_url_redirect(self, campaign_id=None, url_conversion_id=None)
        When a candidate clicks on the link present in the body text of SMS, this code is
        hit and it updates "clicks" in "sms_campaign_blast" table and "hit_count" in
        "url_conversion" table. Finally it returns the destination URL to redirect the
        candidate to actual link provided by recruiter.

    *  create_campaign_url_click_activity(self, candidate)
        If candidate clicks on link present in SMS body text, we create an activity in
        database table "Activity".
        Activity will appear as (e.g)
            "'Muller' clicked on SMS Campaign 'Job opening at getTalent'."

    * process_candidate_reply(cls, candidate)
        When a candidate replies to a recruiter's number, here we do the necessary processing.

    * save_candidate_reply(cls, campaign_blast_id, candidate_phone_id, body_text)
        In this method, we save the reply of candidate in db table 'sms_campaign_reply".

    * create_campaign_reply_activity(cls,sms_campaign_reply, campaign_blast, candidate_id, user_id)
        When a candidate replies to a recruiter's phone number, we create an activity in
        database table "Activity" that (e.g)
            "'William Lyles' replied "Intrested" on SMS campaign 'Job opening at getTalent'.".

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
        .. see also:: CampaignBase class in flask_common/common/utils/campaign_utils.py.
    """

    def __init__(self, user_id):
        """
        Here we set the "user_id" by calling super constructor and "user_phone" by
        calling get_user_phone() method,
        :param args:
        :param kwargs:
        :return:
        """
        # sets the user_id
        super(SmsCampaignBase, self).__init__(user_id)
        self.user_phone = self.get_user_phone()
        if not self.user_phone:
            raise ForbiddenError(error_message='User(id:%s) has no phone number' % self.user_id)
        # If sms_body_test has some URL present in it, we process to make short URL
        # and this contains the updated text to be sent via SMS.
        # This is the id of record in sms_campaign_blast" database table
        self.sms_campaign_blast_id = None

    def get_all_campaigns(self):
        """
        This gets all the campaigns created by current user
        :return: all campaigns associated to with user
        :rtype: list
        """
        return SmsCampaign.get_by_user_phone_id(self.user_phone.id)

    def save(self, form_data):
        """
        This saves the campaign in database table sms_campaign in following steps:

            1- Save campaign in database
            2- Create activity that (e,g)
                "'Harvey Specter' created an SMS campaign: 'Hiring at getTalent'"

        :param form_data: data from UI
        :type form_data: dict
        :return: id of sms_campaign in db
        :rtype: int
        """
        if not form_data:
            logger.error('save: No data received from UI. (User(id:%s))' % self.user_id)
        else:
            # Save Campaign in database table "sms_campaign"
            sms_campaign = self.create_or_update_sms_campaign(form_data)
            # Create record in database table "sms_campaign_smartlist"
            self.create_or_update_sms_campaign_smartlist(sms_campaign,
                                                         form_data.get('smartlist_ids'))
            # Create Activity
            self.campaign_create_activity(sms_campaign)
            return sms_campaign.id

    def create_or_update_sms_campaign(self, form_data, campaign_id=None):
        """
        - Here we save/update sms_campaign in database table "sms_campaign".

        - This method is called from save() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param form_data: data of SMS campaign from UI to save
        :param campaign_id: id of "sms_campaign" obj, default None
        :type form_data: dict
        :type campaign_id: int
        :exception: ResourceNotFound
        :exception: ErrorSavingSMSCampaign
        :return: "sms_campaign" obj
        :rtype: SmsCampaign

        **See Also**
        .. see also:: save() method in SmsCampaignBase class.
        """
        sms_campaign_data = dict(name=form_data.get('name'),
                                 user_phone_id=self.user_phone.id,
                                 body_text=form_data.get('body_text'),
                                 frequency_id=form_data.get('frequency_id'),
                                 added_datetime=datetime.now(),
                                 send_datetime=form_data.get('send_datetime'),
                                 stop_datetime=form_data.get('stop_datetime'))
        if campaign_id:
            sms_campaign_obj = SmsCampaign.get_by_id(campaign_id)
            if not sms_campaign_obj:
                raise ResourceNotFound(error_message='SMS Campaign(id=%s) not found.' % campaign_id)
            for key, value in sms_campaign_data.iteritems():
                # update old values with new ones if provided, else preserve old ones.
                sms_campaign_data[key] = value if value else getattr(sms_campaign_obj, key)
            sms_campaign_obj.update(**sms_campaign_data)
        else:
            try:
                sms_campaign_obj = SmsCampaign(**sms_campaign_data)
                SmsCampaign.save(sms_campaign_obj)
            except Exception as error:
                raise ErrorSavingSMSCampaign(error_message=error.message)
        return sms_campaign_obj

    @staticmethod
    def create_or_update_sms_campaign_smartlist(campaign, smartlist_ids):
        """
        - Here we save/update the smartlist ids for an SMS campaign in database table
        "sms_campaign_smartlist".

        - This method is called from save() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param campaign: sms_campaign obj
        :param smartlist_ids: ids of smartlists
        :exception: InvalidUsage
        :type campaign: SmsCampaign
        :type smartlist_ids: list

        **See Also**
        .. see also:: save() method in SmsCampaignBase class.
        """
        if not isinstance(campaign, SmsCampaign):
            raise InvalidUsage(error_message='create_or_update_sms_campaign_smartlist: '
                                             'Given campaign is not instance '
                                             'of model sms_campaign.')
        for smartlist_id in smartlist_ids:
            data = {'smartlist_id': smartlist_id,
                    'sms_campaign_id': campaign.id}
            db_record = SmsCampaignSmartlist.get_by_campaign_id_and_smartlist_id(campaign.id,
                                                                                 smartlist_id)
            if not db_record:
                new_record = SmsCampaignSmartlist(**data)
                SmsCampaignSmartlist.save(new_record)

    def campaign_create_activity(self, source):
        """
        - Here we set "params" and "type" of activity to be stored in db table "Activity"
            for created Campaign.

        - Activity will appear as (e.g)
           "'Harvey Specter' created an SMS campaign: 'Hiring at getTalent'"

        - This method is called from save() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param source: "sms_campaign" obj
        :type source: SmsCampaign
        :exception: InvalidUsage

        **See Also**
        .. see also:: save() method in SmsCampaignBase class.
        """
        if not isinstance(source, SmsCampaign):
            raise InvalidUsage(error_message='source should be an instance of model sms_campaign')
        # set params
        params = {'user_name': self.user_phone.user.name,
                  'campaign_name': source.name}

        self.create_activity(self.user_id,
                             _type=ActivityMessageIds.CAMPAIGN_SMS_CREATE,
                             source_id=source.id,
                             source_table=SmsCampaign.__tablename__,
                             params=params,
                             headers=self.oauth_header)

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
        # TWILIO is a name defined in config
        phone_label_id = PhoneLabel.phone_label_id_from_phone_label(TWILIO)
        user_phone = UserPhone.get_by_user_id_and_phone_label_id(self.user_id,
                                                                 phone_label_id)
        if len(user_phone) == 1:
            if user_phone[0].value:
                return user_phone[0]
        elif len(user_phone) > 1:
            raise MultipleTwilioNumbersFoundForUser(
                error_message='User(id:%s) has multiple phone numbers for phone label: %s'
                              % (self.user_id, TWILIO))
        else:
            # User has no associated twilio number, need to buy one
            logger.debug('get_user_phone: User(id:%s) has no Twilio number associated.'
                         % self.user_id)
            return self.buy_twilio_mobile_number(phone_label_id)

    def buy_twilio_mobile_number(self, phone_label_id):
        """
        Here we use Twilio API to first get list of available numbers by calling
        get_available_numbers() of class TwilioSMS inside utilities.py. We select first available number
        from the result of get_available_numbers() and call purchase_twilio_number() to
        buy that number.

        - This method is called from get_user_phone() method of class SmsCampaignBase inside
            sms_campaign_service/sms_campaign_base.py.

        :param phone_label_id: id of phone label
        :type phone_label_id: int
        :exception: TwilioAPIError
        :return: UserPhone obj
        :rtype: UserPhone
        """
        twilio_obj = TwilioSMS()
        if IS_DEV:
            # Buy Twilio TEST number so that we won't be charged
            number_to_buy = TWILIO_TEST_NUMBER
        else:
            logger.debug('buy_twilio_mobile_number: Going to buy Twilio number for '
                         'user(id:%s).' % self.user_id)
            available_phone_numbers = twilio_obj.get_available_numbers()
            # We get a list of 30 available numbers and we pick very first phone number to buy.
            number_to_buy = available_phone_numbers[0].phone_number
        twilio_obj.purchase_twilio_number(number_to_buy)
        user_phone = self.create_or_update_user_phone(self.user_id, number_to_buy,
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
        user_phone_obj = UserPhone.get_by_user_id_and_phone_label_id(user_id,
                                                                     phone_label_id)
        if user_phone_obj:
            user_phone_obj.update(**data)
        else:
            user_phone_obj = UserPhone(**data)
            UserPhone.save(user_phone_obj)
        return user_phone_obj

    def process_send(self, campaign):
        """
        :param campaign: SMS campaign obj
        :type campaign: SmsCampaign
        :exception: TwilioAPIError
        :exception: InvalidUsage
        :exception: EmptySmsBody
        :exception: NoSmartlistAssociatedWithCampaign
        :exception: NoCandidateAssociatedWithSmartlist
        :return: number of sends
        :rtype: int

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
            raise InvalidUsage(error_message='campaign should be instance of SmsCampaign model')
        self.campaign = campaign
        logger.debug('process_send: SMS Campaign(id:%s) is being sent. User(id:%s)'
                     % (campaign.id, self.user_id))
        if not self.campaign.body_text:
            # SMS body text is empty
            raise EmptySmsBody(error_message='SMS Body text is empty for Campaign(id:%s)'
                                             % campaign.id)
        self.body_text = self.campaign.body_text.strip()
        # Get smartlists associated to this campaign
        smartlists = SmsCampaignSmartlist.get_by_campaign_id(campaign.id)
        if not smartlists:
            raise NoSmartlistAssociatedWithCampaign(
                error_message='No smartlist is associated with SMS '
                              'Campaign(id:%s). (User(id:%s))' % (campaign.id, self.user_id))
        # get candidates from search_service and filter the None records
        candidates_list = sum(filter(None, map(self.get_smartlist_candidates, smartlists)), [])
        if not candidates_list:
            raise NoCandidateAssociatedWithSmartlist(
                error_message='No candidate is associated to smartlist(s). SMS Campaign(id:%s). '
                              'smartlist ids are %s' % (campaign.id, smartlists))
        # create SMS campaign blast
        self.sms_campaign_blast_id = self.create_or_update_sms_campaign_blast(self.campaign.id)
        # Filtering candidates that have one unique mobile phone and log the error for invalid ones.
        filtered_candidates_and_phones = \
            filter(
                lambda obj: obj is not None, map(self.filter_candidate_for_valid_phone,
                                                 candidates_list)
            )
        logger.debug('process_send: SMS Campaign(id:%s) will be sent to %s candidate(s). '
                     '(User(id:%s))' % (campaign.id, len(filtered_candidates_and_phones),
                                        self.user_id))
        self.send_campaign_to_candidates(filtered_candidates_and_phones, logger)
        return len(filtered_candidates_and_phones)

    def filter_candidate_for_valid_phone(self, candidate):
        """
        Here we validate that candidate has one unique mobile number associated.
        If candidate has only one unique mobile number associated, we return that candidate and
        its phone value.
        Otherwise we log the error.

        - This method is used in process_send() method.

        :param candidate: candidates' mobile phone
        :exception: InvalidUsage
        :return: Candidate obj and its phone value
        :rtype: tuple
        **See Also**
        .. see also:: process_send() method in SmsCampaignBase class.
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
                         % (candidate.id, self.campaign.id, self.user_id))
        else:
            logger.error('filter_candidates_for_valid_phone: SMS cannot be sent as '
                         'candidate(id:%s) has no phone number associated. Campaign(id:%s). '
                         '(User(id:%s))' % (candidate.id, self.campaign.id, self.user_id))

    @celery_app.task(name='send_campaign_to_candidate')
    def send_campaign_to_candidate(self, candidate_and_phone):
        """
        This is a task of celery. We need to make sure that if any exception is raised, we
        handle it here gracefully. Otherwise, exception will be raised to chord and callback
        function will not be called as we expect. In callback function we create an activity
        that
            'SMS campaign 'Job opening at plan 9' has been sent to 400 candidates'

        For each candidate with associated phone, we do the following:
            1- Send SMS
            2- Create SMS campaign send
            3- Update SMS campaign blast
            4- Add activity e.g.('Vincent' received SMS of campaign 'Hiring senior SE'")

        - This method is called from send_sms_campaign_to_candidates() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param candidate_and_phone: candidate obj (at 0 index) and candidate's phone value (at 1st
                                    index)
        :type candidate_and_phone: tuple
        :exception: ErrorUpdatingBodyText
        :exception: TwilioAPIError
        :exception: GoogleShortenUrlAPIError
        :return: True if SMS is sent otherwise False.
        :rtype: bool

        **See Also**
        .. see also:: send_sms_campaign_to_candidates() method in SmsCampaignBase class.
        """
        # Need to commit the session because Celery session does not know about the changes
        # that some other session has made.
        db.session.commit()
        candidate, candidate_phone = candidate_and_phone

        # Transform body text to be sent in SMS
        try:
            modified_body_text, url_conversion_ids = \
                self.process_urls_in_sms_body_text(candidate.id)
        except Exception:
            logger.exception('send_campaign_to_candidate: Error processing URLs in SMS body')
            return False

        # send SMS
        try:
            message_sent_datetime = self.send_sms(candidate_phone, modified_body_text)
        except TwilioAPIError or InvalidUsage:
            logger.exception('send_campaign_to_candidate: Cannot send SMS.')
            return False

        # Create sms_campaign_send i.e. it will record that an SMS has been sent
        # to the candidate
        try:
            sms_campaign_send_obj = \
                self.create_or_update_sms_campaign_send(self.sms_campaign_blast_id,
                                                        candidate.id,
                                                        message_sent_datetime)
        except Exception:
            logger.exception('send_campaign_to_candidate: Error saving record in sms_campaign_send')
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

        # update SMS campaign blast
        try:
            self.create_or_update_sms_campaign_blast(self.campaign.id, increment_sends=True)
        except Exception:
            logger.exception('send_campaign_to_candidate: Error updating campaign blasts')
            return False
        # Create SMS sent activity
        try:
            self.create_sms_send_activity(candidate, sms_campaign_send_obj)
        except Exception:
            logger.exception('send_campaign_to_candidate: Error creating SMS send activity.')
            return False

        logger.info('send_sms_campaign_to_candidate: SMS has been sent to candidate(id:%s).'
                    ' Campaign(id:%s). (User(id:%s))' % (candidate.id, self.campaign.id,
                                                         self.user_id))
        return True

    @staticmethod
    @celery_app.task(name='callback_campaign_sent')
    def callback_campaign_sent(sends_result, user_id, campaign, auth_header):
        """
        Once SMS campaign has been sent to all candidates, this function is hit, and here we

        add activity e.g. (SMS Campaign "abc" was sent to "1000" candidates")

        :param sends_result: Result of executed task
        :param user_id: id of user (owner of campaign)
        :param campaign: sms_campaign obj
        :param auth_header: auth header of current user to make HTTP request to other services
        :type sends_result: list
        :type user_id: int
        :type campaign: SmsCampaign
        :type auth_header: dict

        **See Also**
        .. see also:: send_campaign_to_candidates() method in CampaignBase class inside
                        common/utils/campaign_utils.py
        """
        if isinstance(sends_result, list):
            total_sends = sends_result.count(True)
            SmsCampaignBase.create_campaign_send_activity(user_id,
                                                          campaign, auth_header, total_sends) \
                if total_sends else ''
            logger.debug('process_send: SMS Campaign(id:%s) has been sent to %s candidate(s).'
                         '(User(id:%s))' % (campaign.id, total_sends, user_id))
        else:
            logger.error('callback_campaign_sent: Result is not a list')

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
                     % (self.campaign.id, candidate_id, self.user_id))
        urls_in_body_text = search_urls_in_text(self.body_text)
        short_urls = []
        url_conversion_ids = []
        for url in urls_in_body_text:
            validate_url(url)
            # We have only one link in body text which needs to shortened.
            url_conversion_id = self.create_or_update_url_conversion(destination_url=url,
                                                                     source_url='')
            # URL to redirect candidates to our end point
            # TODO: remove this when app is up
            app_redirect_url = replace_localhost_with_ngrok(SmsCampaignApiUrl.APP_REDIRECTION_URL)
            # long_url looks like
            # http://127.0.0.1:8011/v1/campaigns/1/redirect/1?candidate_id=1
            long_url = str(app_redirect_url % (self.campaign.id, str(url_conversion_id)
                                               + '?candidate_id=%s') % candidate_id)
            # Use Google's API to shorten the long Url
            with app.app_context():
                short_url, error = url_conversion(long_url)
            if error:
                raise GoogleShortenUrlAPIError(error_message=error)
            # update the source_url in "url_conversion" record
            self.create_or_update_url_conversion(url_conversion_id=url_conversion_id,
                                                 source_url=long_url)
            short_urls.append(short_url)
            url_conversion_ids.append(url_conversion_id)
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
        logger.debug('transform_body_text: Replacing original URL with shorted URL. (User(id:%s))'
                     % self.user_id)
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
                error_message='Error while updating body text. Error is %s' % error.message)
        return modified_body_text

    @staticmethod
    def create_or_update_sms_campaign_blast(campaign_id,
                                            sends=0, clicks=0, replies=0,
                                            increment_clicks=False, increment_sends=False,
                                            increment_replies=False):
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
        :param increment_sends: True if sends to be updated ,False otherwise
        :param increment_clicks: True if clicks to be updated ,False otherwise
        :param increment_replies: True if replies to be updated ,False otherwise
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
        record_in_db = SmsCampaignBlast.get_by_campaign_id(campaign_id)
        data = {'sms_campaign_id': campaign_id,
                'sends': sends,
                'clicks': clicks,
                'replies': replies,
                'sent_datetime': datetime.now()}
        if record_in_db:
            data['sends'] = record_in_db.sends + 1 if increment_sends else record_in_db.sends
            data['clicks'] = record_in_db.clicks + 1 if increment_clicks else record_in_db.clicks
            data['replies'] = record_in_db.replies + 1 if increment_replies else record_in_db.replies
            record_in_db.update(**data)
            sms_campaign_blast_id = record_in_db.id
        else:
            new_record = SmsCampaignBlast(**data)
            SmsCampaignBlast.save(new_record)
            sms_campaign_blast_id = new_record.id
        return sms_campaign_blast_id

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
        if IS_DEV:
            # send SMS using Twilio Test Credentials
            sender_phone = TWILIO_TEST_NUMBER
        else:
            sender_phone = self.user_phone.value
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
            raise InvalidUsage('First param shoould be instance of SmsCampaignSend model')

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
                error_message='Candidate should be instance of model Candidate')
        if not isinstance(source, SmsCampaignSend):
            raise InvalidUsage(
                error_message='Source should be instance of model SmsCampaignSend')
        params = {'candidate_name': candidate.first_name + ' ' + candidate.last_name,
                  'campaign_name': self.campaign.name}
        self.create_activity(self.user_id,
                             _type=ActivityMessageIds.CAMPAIGN_SMS_SEND,
                             source_id=source.id,
                             source_table=SmsCampaignSend.__tablename__,
                             params=params,
                             headers=self.oauth_header)

    @classmethod
    def create_campaign_send_activity(cls, user_id, source, auth_header, num_candidates):
        """
        - Here we set "params" and "type" of activity to be stored in db table "Activity"
            for Campaign sent.

        - Activity will appear as " 'Jobs at Oculus' has been sent to '50' candidates".

        - This method is called from send_sms_campaign_to_candidates() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param user_id: id of user
        :param source: sms_campaign obj
        :param auth_header: Authorization header
        :param num_candidates: number of candidates to which campaign is sent
        :type user_id: int
        :type source: SmsCampaign
        :type auth_header: dict
        :type num_candidates: int
        :exception: InvalidUsage

        **See Also**
        .. see also:: send_sms_campaign_to_candidates() method in SmsCampaignBase class.
        """
        if not isinstance(source, SmsCampaign):
            raise InvalidUsage(error_message='source should be an instance of model sms_campaign')
        params = {'name': source.name,
                  'num_candidates': num_candidates}
        cls.create_activity(user_id,
                            _type=ActivityMessageIds.CAMPAIGN_SEND,
                            source_id=source.id,
                            source_table=SmsCampaign.__tablename__,
                            params=params,
                            headers=auth_header)

    @staticmethod
    def pre_process_url_redirect(campaign_id, url_conversion_id, candidate_id):
        """
        This method is used for the pre-processing of URL redirection
            It checks if candidate and campaign is present in database. If both are
            present, returns them otherwise raise ResourceNotFound.

        :param campaign_id: id of SMS campaign
        :param url_conversion_id: id of URL conversion record
        :param candidate_id: id of Candidate
        :exception: MissingRequiredField
        :exception: ResourceNotFound
        :return: SMS Campaign and Candidate obj
        :rtype: tuple (sms_campaign, candidate)

        **See Also**
        .. see also:: sms_campaign_url_redirection() function in sms_campaign_app/app.py
        """
        url_redirect_data = {'campaign_id': campaign_id,
                             'url_conversion_id': url_conversion_id,
                             'candidate_id': candidate_id}
        missing_items = find_missing_items(url_redirect_data, verify_values_of_all_keys=True)
        if missing_items:
            raise MissingRequiredField(
                error_message='pre_process_url_redirect: Missing required fields are: %s'
                              % missing_items)
        # check if candidate exists in database
        candidate = Candidate.get_by_id(candidate_id)
        if not candidate:
            raise ResourceNotFound(
                error_message='pre_process_url_redirect: Candidate(id:%s) not found.'
                              % candidate_id, error_code=ResourceNotFound.http_status_code())
        # check if campaign exists in database
        campaign = SmsCampaign.get_by_id(campaign_id)
        if not campaign:
            raise ResourceNotFound(
                error_message='pre_process_url_redirect: SMS Campaign(id=%s) Not found.'
                              % campaign_id, error_code=ResourceNotFound.http_status_code())
        # check if url_conversion record exists in database
        url_conversion_record = UrlConversion.get_by_id(url_conversion_id)
        if not url_conversion_record:
            raise ResourceNotFound(
                error_message='pre_process_url_redirect: Url Conversion(id=%s) Not found.'
                              % url_conversion_id,
                error_code=ResourceNotFound.http_status_code())
        return campaign, url_conversion_record, candidate

    def process_url_redirect(self, campaign, url_conversion_db_record, candidate):
        """
        This does the following steps to send campaign to candidates.

        1- Get the "url_conversion" obj from db.
        2- Get the "sms_campaign_blast" obj from db.
        3- Increase "hit_count" by 1 for "url_conversion" record.
        4- Increase "clicks" by 1 for "sms_campaign_blast" record.
        5- Add activity that abc candidate clicked on xyz campaign.
            "'Alvaro Oliveira' clicked URL of campaign 'Jobs at Google'"
        6- return the destination URL (actual URL provided by recruiter(user)
            where we want our candidate to be redirected.

        :Example:

            1- Create class object
                from sms_campaign_service.sms_campaign_base import SmsCampaignBase
                camp_obj = SmsCampaignBase(1)

            2- Call method process_send with campaign_id
                redirection_url = camp_obj.process_url_redirect(campaign_id=1, url_conversion_id=1)

        .. Status:: 200 (OK)
                    404 (Resource not found)
                    500 (Internal Server Error)
                    5005 (EmptyDestinationUrl)

        :param campaign: sms_campaign record
        :param url_conversion_db_record: url_conversion record
        :param candidate: Campaign object form db
        :type campaign: SmsCampaign
        :type url_conversion_db_record: UrlConversion
        :type candidate: Candidate
        :exception: EmptyDestinationUrl
        :return: URL where to redirect the candidate
        :rtype: str

        **See Also**
        .. see also:: sms_campaign_url_redirection() function in sms_campaign_app/app.py
        """
        logger.debug('process_url_redirect: Processing for URL redirection. (User(id:%s))'
                     % self.user_id)
        self.campaign = campaign
        # Update SMS campaign blast
        self.create_or_update_sms_campaign_blast(campaign.id,
                                                 increment_clicks=True)
        # Update hit count
        self.create_or_update_url_conversion(url_conversion_id=url_conversion_db_record.id,
                                             hit_count_update=True)
        # Create Activity
        self.create_campaign_url_click_activity(candidate)
        logger.info('process_url_redirect: candidate(id:%s) clicked on SMS '
                    'campaign(id:%s). (User(id:%s))'
                    % (candidate.id, self.campaign.id, self.user_id))
        # Get URL to redirect candidate to actual URL
        if not url_conversion_db_record.destination_url:
            raise EmptyDestinationUrl(
                error_message='process_url_redirect: Destination_url is empty for '
                              'url_conversion(id:%s)' % url_conversion_db_record.id)
        return url_conversion_db_record.destination_url


    def create_campaign_url_click_activity(self, source):
        """
        - Here we set "params" and "type" of activity to be stored in db table "Activity"
            for Campaign URL click.

        - Activity will appear as
            "Michal Jordan clicked on SMS Campaign "abc". "

        - This method is called from process_url_redirect() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param source: Candidate obj
        :type source: Candidate
        :exception: InvalidUsage

        **See Also**
        .. see also:: process_url_redirect() method in SmsCampaignBase class.
        """
        if not isinstance(source, Candidate):
            raise InvalidUsage(error_message='source should be an instance of model candidate')
        params = {'candidate_name': source.first_name + ' ' + source.last_name,
                  'campaign_name': self.campaign.name}
        self.create_activity(self.user_id,
                             _type=ActivityMessageIds.CAMPAIGN_SMS_CLICK,
                             source_id=self.campaign.id,
                             source_table=SmsCampaign.__tablename__,
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
                     MissingRequiredField (5006)
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
            raise MissingRequiredField(
                error_message='process_candidate_reply: Missing items are %s' % missing_items)

        # get "user_phone" obj
        user_phone = _get_valid_user_phone_value(reply_data.get('To'))
        # get "candidate_phone" obj
        candidate_phone = _validate_candidate_phone_value(reply_data.get('From'))
        # get latest campaign send
        sms_campaign_send = SmsCampaignSend.get_by_candidate_id(candidate_phone.candidate_id)
        if not sms_campaign_send:
            raise NoSMSCampaignSentToCandidate(
                error_message='No SMS campaign sent to candidate(id:%s)'
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
        # get/update SMS campaign blast
        cls.create_or_update_sms_campaign_blast(sms_campaign_blast.sms_campaign_id,
                                                increment_replies=True)
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
                error_message='create_campaign_reply_activity: Candidate(id:%s) not found.'
                              % candidate_id, error_code=ResourceNotFound.http_status_code())
        campaign = SmsCampaign.get_by_id(campaign_blast.sms_campaign_id)
        if not campaign:
            raise ResourceNotFound(
                error_message='create_campaign_reply_activity: SMS Campaign(id=%s) Not found.'
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
            error_message='%s phone number is associated with %s users. User ids are %s'
                          % (user_phone_value,
                             len(user_phones_obj),
                             [user_phone.user_id for user_phone in user_phones_obj]))
    else:
        raise NoUserFoundForPhoneNumber(error_message='No User is associated with '
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
            error_message='%s phone number is associated with %s candidates. Candidate ids are %s'
                          % (candidate_phone_value,
                             len(candidate_phone_records),
                             [candidate_phone.candidate_id for candidate_phone
                              in candidate_phone_records]))
    else:
        raise NoCandidateFoundForPhoneNumber(
            error_message='No Candidate is associated with %s phone number' % candidate_phone_value)
    return candidate_phone
