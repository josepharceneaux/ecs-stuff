"""
Author: Hafiz Muhammad Basit, QC-Technologies,
        Lahore, Punjab, Pakistan <basit.gettalent@gmail.com>

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

It has delete_sms_campaign() function to delete only that campaign
    for which the current user is an owner.
"""

# Standard Library
from datetime import datetime

# Application Specific
from sms_campaign_service import logger, db
from sms_campaign_service.common.common_config import IS_DEV
from sms_campaign_service.common.models.misc import UrlConversion
from sms_campaign_service.common.models.user import (UserPhone, User)
from sms_campaign_service.sms_campaign_app.app import celery_app, app
from sms_campaign_service.common.utils.campaign_utils import CampaignBase
from sms_campaign_service.utilities import (TwilioSMS, search_urls_in_text)
from sms_campaign_service.common.models.candidate import (PhoneLabel, Candidate, CandidatePhone)
from sms_campaign_service.common.utils.common_functions import (find_missing_items,
                                                                url_conversion,
                                                                JSON_CONTENT_TYPE_HEADER)
from sms_campaign_service.common.error_handling import (ResourceNotFound, ForbiddenError,
                                                        InvalidUsage)
from sms_campaign_service.sms_campaign_app_constants import (SMS_URL_REDIRECT,
                                                             MOBILE_PHONE_LABEL,
                                                             TWILIO)
from sms_campaign_service.custom_exceptions import (EmptySmsBody, MultipleTwilioNumbers,
                                                    EmptyDestinationUrl, MissingRequiredField,
                                                    MultipleUsersFound, MultipleCandidatesFound,
                                                    ErrorSavingSMSCampaign, NoCandidateAssociated,
                                                    NoSmartlistAssociated,
                                                    NoSMSCampaignSentToCandidate)
from sms_campaign_service.common.models.sms_campaign import (SmsCampaign, SmsCampaignSend,
                                                             SmsCampaignBlast, SmsCampaignSmartlist,
                                                             SmsCampaignSendUrlConversion,
                                                             SmsCampaignReply)
from sms_campaign_service.common.utils.activity_utils import (CAMPAIGN_SMS_CLICK,
                                                              CAMPAIGN_SMS_REPLY,
                                                              CAMPAIGN_SMS_SEND, CAMPAIGN_SEND,
                                                              CAMPAIGN_SMS_CREATE)


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
        - It then gets the user_phone row from "user_phone" db table using
            provided "user_id".
        - Sets total_sends to 0.

    *  get_all_campaigns(self)
        This gets all the campaigns created by current user.

    * save(self, form_data)
        This method is used to save the campaign in db table 'sms_campaign' and
        returns the ID of fresh record in db.

    * campaign_create_activity(self, sms_campaign)
        This creates activity that "User xyz created an SMS campaign %(campaign_name)s".

    * buy_twilio_mobile_number(self, phone_label_id=None)
        To send sms_campaign, we need to reserve a unique number for each user.
        This method is used to reserve a unique number for getTalent user.

    * create_or_update_user_phone(user_id, phone_number, phone_label_id): [static]
        This method is used to create/update user_phone record.

    * process_send(self, campaign_id=None)
        This method is used to send the campaign to candidates.

    * process_urls_in_sms_body_text(self, candidate_id)
        If "body_text" contains any link in it, then we need to transform the
        "body_text" by replacing long URL with shorter version using Google's Shorten
        URL API. If body text does not contain any link, it returns the body_text
        as it is.

    * transform_body_text(self, link_in_body_text, short_url)
        This replaces the original URL present in "body_text" with the shortened URL.

    * send_sms_campaign_to_candidate(self, candidate)
        This does the sending part and updates database tables "sms_campaign_blast" and
         "sms_campaign_send".

    * create_or_update_sms_campaign_blast(campaign_id, send=0, clicks=0, replies=0,
                            sends_update=False, clicks_update=False, replies=False): [static]
        For each campaign, here we create/update stats of that particular campaign.

    * send_sms(self, candidate_phone_value)
        This finally sends the SMS to candidate using Twilio API.

    * create_or_update_sms_campaign_send(campaign_blast_id, candidate_id, sent_time): [static]
        For each SMS sent to the candidate, here we add an entry that abc campaign has been sent to
         xyz candidate at this time.

    * create_or_update_sms_send_url_conversion(campaign_send_id, url_conversion_id): [static]
        This adds an entry in db table "sms_campaign_send_url_conversion" for each SMS send.

    * create_sms_send_activity(self, candidate, source_id=None)
        Here we set "params" and "type" to be saved in db table 'Activity' for each sent SMS.
        Activity will appear as
            "SMS Campaign <b>%(campaign_name)s</b> has been sent to %(candidate_name)s.".

    * create_campaign_send_activity(self, num_candidates)
        Once the campaign has been sent to all candidates, here we set params and type
        to be saved in db table 'Activity' that campaign has been sent to (say)
        40(num_candidates) candidates.
        Activity will appear as "%(campaign_name)s has been sent to %(num_candidates)s.".

    * process_url_redirect(self, campaign_id=None, url_conversion_id=None)
        When a candidate clicks on the link present in the body text of SMS, this code is
        hit and it updates "clicks" in "sms_campaign_blast" table and "hit_count" in
        "url_conversion" table. Finally it returns the destination URL to redirect the
        candidate to actual link provided by recruiter.

    *  create_campaign_url_click_activity(self, candidate)
        If candidate clicks on link present in SMS body text, we create an activity in
        database table "Activity".
        Activity will appear as
            "%(candidate_name)s clicked on SMS Campaign <b>%(campaign_name)s</b>."

    * process_candidate_reply(cls, candidate)
        When a candidate replies to a recruiter's number, here we do the necessary processing.

    * save_candidate_reply(cls, campaign_blast_id, candidate_phone_id, reply_body_text)
        In this method, we save the reply of candidate in db table 'sms_campaign_reply".

    * create_campaign_reply_activity(cls,sms_campaign_reply, campaign_blast, candidate_id, user_id)
        When a candidate replies to a recruiter's phone number, we create an activity in
        database table "Activity" that
            "%(candidate_name)s replied <b>%(reply_text)s</b> on SMS campaign %(campaign_name)s.".

    - An example of sending campaign to candidates will be like this.
        :Example:

        1- Create class object
            from sms_campaign_service.sms_campaign_base import SmsCampaignBase
            camp_obj = SmsCampaignBase(1)

        2- Call method process_send with campaign_id
            camp_obj.process(campaign_id=1)

    **See Also**
        .. see also:: CampaignBase class in flask_common/common/utils/campaign_utils.py.
    """

    def __init__(self, user_id, *args, **kwargs):
        """
        Here we set the "user_id" by calling super constructor and "user_phone" by
        calling get_user_phone() method,
        :param args:
        :param kwargs:
        :return:
        """
        # sets the user_id
        super(SmsCampaignBase, self).__init__(user_id, *args, **kwargs)
        self.buy_new_number = kwargs.get('buy_new_number', False)
        self.user_phone = self.get_user_phone()
        if not self.user_phone:
            raise ForbiddenError(error_message='User(id:%s) has no phone number' % self.user_id)
        # If sms_body_test has some URL present in it, we process to make short URL
        # and this contains the updated text to be sent via SMS.
        self.modified_body_text = None
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
            2 Create activity that
                "%(user_name)s created an SMS campaign: '%(campaign_name)s'"

        :param form_data: data from UI
        :type form_data: dict
        :return: id of sms_campaign in db
        :rtype: int
        """
        if form_data:
            # Save Campaign in database table "sms_campaign"
            sms_campaign = self.create_or_update_sms_campaign(form_data)
            # Create Activity
            self.campaign_create_activity(sms_campaign)
            return sms_campaign.id
        else:
            logger.error('save: No data received from UI. (User(id:%s))' % self.user_id)

    def create_or_update_sms_campaign(self, form_data, campaign_id=None):
        """
        - Here we save/update sms_campaign in database table "sms_campaign".

        - This method is called from save() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param form_data: data of SMS campaign from UI to save
        :param campaign_id: id of "sms_campaign" row, default None
        :type form_data: dict
        :type campaign_id: int
        :return: "sms_campaign" row
        :rtype: row

        **See Also**
        .. see also:: save() method in SmsCampaignBase class.
        """
        sms_campaign_data = dict(name=form_data.get('name'),
                                 user_phone_id=self.user_phone.id,
                                 sms_body_text=form_data.get('sms_body_text'),
                                 frequency_id=form_data.get('frequency_id'),
                                 added_time=datetime.now(),
                                 send_time=form_data.get('send_time'),
                                 stop_time=form_data.get('stop_time'))
        required_fields = ['name', 'user_phone_id', 'sms_body_text']
        missing_items = find_missing_items(sms_campaign_data, required_fields)
        if missing_items:
            raise MissingRequiredField(error_message='Required fields are empty to save '
                                                     'sms_campaign. Empty fields are %s'
                                                     % missing_items)
        if campaign_id:
            sms_campaign_row = SmsCampaign.get_by_id(campaign_id)
            if not sms_campaign_row:
                raise ResourceNotFound(error_message='SMS Campaign(id=%s) not found.' % campaign_id)
            for key, value in sms_campaign_data.iteritems():
                # update old values with new ones if provided, else preserve old ones.
                sms_campaign_data[key] = value if value else getattr(sms_campaign_row, key)
            sms_campaign_row.update(**sms_campaign_data)
        else:
            try:
                sms_campaign_row = SmsCampaign(**sms_campaign_data)
                SmsCampaign.save(sms_campaign_row)
            except Exception as error:
                raise ErrorSavingSMSCampaign(error_message=error.message)
        return sms_campaign_row

    def campaign_create_activity(self, source):
        """
        - Here we set "params" and "type" of activity to be stored in db table "Activity"
            for Campaign create.

        - Activity will appear as
           "%(user_name)s created an SMS campaign: '%(campaign_name)s'"

        - This method is called from save() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param source: "sms_campaign" row
        :type source: row

        **See Also**
        .. see also:: save() method in SmsCampaignBase class.
        """
        if not isinstance(source, SmsCampaign):
            raise InvalidUsage(error_message='source should be an instance of model sms_campaign')
        # get User row
        user = User.get_by_id(self.user_id)
        # set params
        params = {'user_name': user.name,
                  'campaign_name': source.name}

        self.create_activity(self.user_id,
                             type_=CAMPAIGN_SMS_CREATE,
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

        :return: UserPhone row
        """
        # TODO: need to talk to osman where to implement this
        # TWILIO is a name defined in config
        phone_label_id = PhoneLabel.phone_label_id_from_phone_label(TWILIO)
        user_phone = UserPhone.get_by_user_id_and_phone_label_id(self.user_id,
                                                                 phone_label_id)
        if len(user_phone) == 1:
            # TODO: validate that user has valid US number
            if user_phone[0].value:
                return user_phone[0]
        elif len(user_phone) > 1:
            raise MultipleTwilioNumbers(error_message='User(id:%s) has multiple phone numbers '
                                                      'for phone label: %s'
                                                      % (self.user_id, TWILIO))
        else:
            # User has no associated twilio number, need to buy one
            logger.debug('get_user_phone: User(id:%s) has no Twilio number associated.'
                         % self.user_id)
            if self.buy_new_number:
                return self.buy_twilio_mobile_number(phone_label_id=phone_label_id)

    def buy_twilio_mobile_number(self, phone_label_id=None):
        """
        Here we use Twilio API to first get list of available numbers by calling
        get_available_numbers() of class TwilioSMS inside utilities.py. We select first available number
        from the result of get_available_numbers() and call purchase_twilio_number() to
        buy that number.

        - This method is called from get_user_phone() method of class SmsCampaignBase inside
            sms_campaign_service/sms_campaign_base.py.

        :param phone_label_id: id of phone label
        :type phone_label_id: int
        :return: UserPhone row
        """
        twilio_obj = TwilioSMS()
        available_phone_numbers = twilio_obj.get_available_numbers()
        if available_phone_numbers:
            if IS_DEV:
                # Do not "actually" buy a number.
                number_to_buy = '1234'
            else:
                logger.debug('buy_twilio_mobile_number: Going to buy Twilio number for '
                             'user(id:%s).' % self.user_id)
                number_to_buy = available_phone_numbers[0].phone_number
                twilio_obj.purchase_twilio_number(number_to_buy)
            user_phone = self.create_or_update_user_phone(self.user_id, number_to_buy,
                                                          phone_label_id)
            # TODO: validate that user has valid US number
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
        :return: "user_phone" row

        **See Also**
        .. see also:: __int__() method of SmsCampaignBase class.
        """
        data = {'user_id': user_id,
                'phone_label_id': phone_label_id,
                'value': phone_number}
        user_phone_row = UserPhone.get_by_user_id_and_phone_label_id(user_id,
                                                                     phone_label_id)
        if user_phone_row:
            user_phone_row.update(**data)
        else:
            user_phone_row = UserPhone(**data)
            UserPhone.save(user_phone_row)
        return user_phone_row

    def process_send(self, campaign):
        """
        :param campaign: sms campaign row
        :type campaign: Model object
        :return: number of sends
        :rtype: int

        This does the following steps to send campaign to candidates.

        1- Transform the body text to be sent in SMS, add entry in
            url_conversion and sms_campaign_url_conversion db tables.
        2- Get selected smart lists for the campaign to be sent from sms_campaign_smart_list.
        3- Loop over all the smart lists and do the followings:

            3.1- Get candidates and their phone number(s) to which we need to send the SMS.
            3.2- Create SMS campaign blast
            3.3- Loop over list of candidate_ids found in step-3-1 and do the followings:

                3.3.1- Send SMS
                3.3.2- Create SMS campaign send
                3.3.3- Update SMS campaign blast
                3.3.4- Add activity e.g.("Roger Federer" received SMS of campaign "abc"")
        4- Add activity e.g. (SMS Campaign "abc" was sent to "1000" candidates")

        :Example:

            1- Create class object
                from sms_campaign_service.sms_campaign_base import SmsCampaignBase
                camp_obj = SmsCampaignBase(1)

            2- Call method process_send with campaign_id
                camp_obj.process(campaign_id=1)
        :return:
        """
        if not isinstance(campaign, SmsCampaign):
            raise InvalidUsage(error_message='campaign should be instance of SmsCampaign model')
        self.campaign = campaign
        logger.debug('process_send: SMS Campaign(id:%s) is being sent. User(id:%s)'
                     % (campaign.id, self.user_id))
        self.body_text = self.campaign.sms_body_text.strip()
        if not self.body_text:
            # SMS body text is empty
            raise EmptySmsBody(error_message='SMS Body text is empty for Campaign(id:%s)'
                                             % campaign.id)
        # Get smart_lists associated to this campaign
        smart_lists = SmsCampaignSmartlist.get_by_campaign_id(campaign.id)
        # TODO: Use map if we can
        if smart_lists:
            all_candidates = []
            for smart_list in smart_lists:
                self.smart_list_id = smart_list.smart_list_id
                # get candidates associated with smart list
                candidates = self.get_candidates_from_candidate_service(smart_list.smart_list_id)
                if candidates:
                    all_candidates.extend(candidates)
                else:
                    logger.error('process_send: No Candidate found. smartlist id is %s. '
                                 '(User(id:%s))' % (smart_list.smart_list_id, self.user_id))
        else:
            logger.error('process_send: No smartlist is associated with SMS '
                         'Campaign(id:%s). (User(id:%s))' % (campaign.id, self.user_id))
            raise NoSmartlistAssociated(error_message='No smartlist is associated with SMS '
                                                      'Campaign(id:%s)' % campaign.id)
        if all_candidates:
            # create SMS campaign blast
            self.sms_campaign_blast_id = self.create_or_update_sms_campaign_blast(self.campaign.id)
            filtered_candidates_and_phones = filter(lambda row: row is not None,
                                                    map(self.filter_candidate_for_valid_phone,
                                                        all_candidates))
            logger.debug('process_send: SMS Campaign(id:%s) will be sent to %s candidate(s). '
                         '(User(id:%s))' % (campaign.id, len(filtered_candidates_and_phones),
                                            self.user_id))
            self.send_campaign_to_candidates(filtered_candidates_and_phones)
            return len(filtered_candidates_and_phones)
        else:
            raise NoCandidateAssociated(error_message='No candidate is associated to smartlist(s)'
                                                      'SMS Campaign(id:%s). smartlist ids are %s'
                                                      % (campaign.id, smart_lists))

    def filter_candidate_for_valid_phone(self, candidate):
        """
        Here we validate that candidate has one mobile number associated.

        - This method is used in process_send() method.

        :param candidate: candidates' mobile phone
        :return:

        **See Also**
        .. see also:: process_send() method in SmsCampaignBase class.
        """
        candidate_phones = candidate.candidate_phones
        phone_label_id = PhoneLabel.phone_label_id_from_phone_label(MOBILE_PHONE_LABEL)

        # filter only mobile numbers
        candidate_mobile_phone = filter(lambda candidate_phone:
                                        candidate_phone.phone_label_id == phone_label_id,
                                        candidate_phones)
        if len(candidate_mobile_phone) == 1:
            # If this number is associated with multiple candidates, raise exception
            _validate_candidate_phone_value(candidate_mobile_phone[0].value)
            # TODO: validate that candidate has valid US number
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
        For each candidate with associated phone, we do the followings:
            1- Send SMS
            2- Create SMS campaign send
            3- Update SMS campaign blast
            4- Add activity (%(candidate_name)s received SMS of campaign %(campaign_name)s")

        - This method is called from send_sms_campaign_to_candidates() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param candidate_and_phone: Candidate row and Candidate's phone
        :type candidate_and_phone: tuple

        **See Also**
        .. see also:: send_sms_campaign_to_candidates() method in SmsCampaignBase class.
        """
        candidate = candidate_and_phone[0]
        candidate_phone = candidate_and_phone[1]
        # Transform body text to be sent in SMS
        url_conversion_ids = self.process_urls_in_sms_body_text(candidate.id)
        assert self.modified_body_text
        # send SMS
        message_sent_time = self.send_sms(candidate_phone)
        # Create sms_campaign_send
        sms_campaign_send_id = \
            self.create_or_update_sms_campaign_send(self.sms_campaign_blast_id, candidate.id,
                                                    message_sent_time)

        for url_conversion_id in url_conversion_ids:
            # create sms_send_url_conversion entry
            self.create_or_update_sms_send_url_conversion(sms_campaign_send_id,
                                                          url_conversion_id)
        # update SMS campaign blast
        self.create_or_update_sms_campaign_blast(self.campaign.id, sends_update=True)
        self.create_sms_send_activity(candidate, sms_campaign_send_id)
        logger.info('send_sms_campaign_to_candidate: SMS has been sent to candidate(id:%s).'
                    ' Campaign(id:%s). (User(id:%s))'
                    % (candidate.id, self.campaign.id, self.user_id))
        return True

    @staticmethod
    @celery_app.task(name='callback_campaign_sent')
    def callback_campaign_sent(sends_result, user_id, campaign, auth_header):
        """
        Once SMS campaign has been sent to all candidates, this function is hit, and here we

        add activity e.g. (SMS Campaign "abc" was sent to "1000" candidates")

        :param sends_result: Result of executed task
        :param user_id: id of user (owner of campaign)
        :param campaign: id of campaign which was sent to candidates
        :param auth_header: auth header of current user to make HTTP request to other services
        :type sends_result: list
        :type user_id: int
        :type campaign: row
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
    @celery_app.task(name='celery_error')
    def celery_error(error):
        db.session.rollback()
        logger.error('celery_error: %s' % error)

    def process_urls_in_sms_body_text(self, candidate_id):
        """
        - Once we have the body text of SMS to be sent via SMS campaign,
            we check if it contains any link in it.
            If it has any link, we do the followings:

                1- Save that link in db table "url_conversion".
                2- Checks if the db record has source URL or not. If it has no source URL,
                   we convert the URL(to redirect to our app) into shortened URL using Google's
                   shorten URL API and update the db record.
                   Otherwise we move on to transform body text.
                3. Replace the link in original body text with the shortened URL
                    (which we created in step 2)
                4. Set the updated body text

            Otherwise we save the body text in self.modified_body_text

        - This method is called from process_send() method of class SmsCampaignBase inside
            sms_campaign_service/sms_campaign_base.py.

        :param candidate_id: id of Candidate
        :return: list of URL conversion records
        :rtype: list

        **See Also**
        .. see also:: process_send() method in SmsCampaignBase class.
        """
        logger.debug('process_urls_in_sms_body_text: Processing any '
                     'link present in sms_body_text for '
                     'SMS Campaign(id:%s) and Candidate(id:%s). (User(id:%s))'
                     % (self.campaign.id, candidate_id, self.user_id))
        urls_in_body_text = search_urls_in_text(self.body_text)
        short_urls = []
        url_conversion_ids = []
        for url in urls_in_body_text:
            # We have only one link in body text which needs to shortened.
            url_conversion_id = self.create_or_update_url_conversion(destination_url=url,
                                                                     source_url='')
            # URL to redirect candidates to our end point
            long_url = (SMS_URL_REDIRECT + '?candidate_id={}').format(self.campaign.id,
                                                                      url_conversion_id,
                                                                      candidate_id)
            # Use Google's API to shorten the long Url
            with app.app_context():
                short_url, _ = url_conversion(long_url)
            # update the source_url in "url_conversion" record
            self.create_or_update_url_conversion(url_conversion_id=url_conversion_id,
                                                 source_url=long_url)
            short_urls.append(short_url)
            url_conversion_ids.append(url_conversion_id)
        self.transform_body_text(urls_in_body_text, short_urls)
        return url_conversion_ids

    def transform_body_text(self, urls_in_sms_body_text, short_urls):
        """
        - This replaces the urls provided in "body_text" (destination urls) with the
            "shortened urls" to be sent via SMS campaign. These shortened urls will
            redirect candidate to our endpoint to keep track of clicks and hit_count,
            then we redirect the candidate to actual destination urls

        - It sets the value of self.modified_body_text.

        - This method is called from process_urls_in_sms_body_text() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param urls_in_sms_body_text: URLs present in SMS body text
        :param short_urls: shortened URL to redirect candidate to our app
        :type short_urls: list
        :type urls_in_sms_body_text: list

        **See Also**
        .. see also:: process_urls_in_sms_body_text() method in SmsCampaignBase class.
        """
        logger.debug('transform_body_text: Replacing original URL with shorted URL. (User(id:%s))'
                     % self.user_id)
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
            self.modified_body_text = ' '.join(text_split)
        else:
            self.modified_body_text = self.body_text

    @staticmethod
    def create_or_update_sms_campaign_blast(campaign_id,
                                            sends=0, clicks=0, replies=0,
                                            clicks_update=False, sends_update=False,
                                            replies_update=False):
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
        :param sends_update: True if sends to be updated ,False otherwise
        :param clicks_update: True if clicks to be updated ,False otherwise
        :param replies_update: True if replies to be updated ,False otherwise
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
                'sent_time': datetime.now()}
        if record_in_db:
            data['sends'] = record_in_db.sends + 1 if sends_update else record_in_db.sends
            data['clicks'] = record_in_db.clicks + 1 if clicks_update else record_in_db.clicks
            data['replies'] = record_in_db.replies + 1 if replies_update else record_in_db.replies
            record_in_db.update(**data)
            sms_campaign_blast_id = record_in_db.id
        else:
            new_record = SmsCampaignBlast(**data)
            SmsCampaignBlast.save(new_record)
            sms_campaign_blast_id = new_record.id
        return sms_campaign_blast_id

    def send_sms(self, candidate_phone_value):
        """
        - This uses Twilio API to send SMS to a given phone number of candidate.

        - This method is called from send_sms_campaign_to_candidates() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param candidate_phone_value: Candidate mobile phone number.
        :type candidate_phone_value: str
        :return: sent message time
        :rtype: datetime

        **See Also**
        .. see also:: send_sms_campaign_to_candidates() method in SmsCampaignBase class.
        """
        if IS_DEV:
            # Do not "actually" send SMS.
            return datetime.now()
        else:
            twilio_obj = TwilioSMS()
            message_response = twilio_obj.send_sms(body_text=self.modified_body_text,
                                                   sender_phone=self.user_phone.value,
                                                   receiver_phone=candidate_phone_value)
            return message_response.date_created

    @staticmethod
    def create_or_update_sms_campaign_send(campaign_blast_id, candidate_id, sent_time):
        """
        - Here we add an entry in "sms_campaign_send" db table for each SMS send.

        - This method is called from send_sms_campaign_to_candidates() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param campaign_blast_id: id of sms_campaign_blast
        :param candidate_id: id of candidate to which SMS is supposed to be sent
        :param sent_time: Time of sent SMS
        :type campaign_blast_id: int
        :type candidate_id: int
        :type sent_time: datetime
        :return: id of "sms_campaign_send" record
        :rtype: int

        **See Also**
        .. see also:: send_sms_campaign_to_candidates() method in SmsCampaignBase class.
        """
        data = {'sms_campaign_blast_id': campaign_blast_id,
                'candidate_id': candidate_id,
                'sent_time': sent_time}
        record_in_db = SmsCampaignSend.get_by_blast_id_and_candidate_id(campaign_blast_id,
                                                                        candidate_id)
        if record_in_db:
            record_in_db.update(**data)
            sms_campaign_send_id = record_in_db.id
        else:
            new_record = SmsCampaignSend(**data)
            SmsCampaignSend.save(new_record)
            sms_campaign_send_id = new_record.id
        return sms_campaign_send_id

    @staticmethod
    def create_or_update_sms_send_url_conversion(campaign_send_id, url_conversion_id):
        """
        - For each SMS send, here we add an entry in db table "sms_campaign_send_url_conversion"
            db table.

        - This method is called from send_sms_campaign_to_candidates() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param campaign_send_id: id of campaign_send record
        :param url_conversion_id: id of url_conversion record

        **See Also**
        .. see also:: send_sms_campaign_to_candidates() method in SmsCampaignBase class.
        """
        data = {'sms_campaign_send_id': campaign_send_id,
                'url_conversion_id': url_conversion_id}
        record_in_db = SmsCampaignSendUrlConversion.get_by_campaign_send_id_and_url_conversion_id(
            campaign_send_id, url_conversion_id)
        if record_in_db:
            record_in_db.update(**data)
        else:
            new_record = SmsCampaignSendUrlConversion(**data)
            SmsCampaignSendUrlConversion.save(new_record)

    def create_sms_send_activity(self, candidate, source_id):
        """
        - Here we set "params" and "type" of activity to be stored in db table "Activity"
            for each send.

        - Activity will appear as
            "SMS Campaign <b>%(campaign_name)s</b> has been sent to %(candidate_name)s."

        - This method is called from send_sms_campaign_to_candidates() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param candidate: Candidate row
        :param source_id: id of source
        :type candidate: models.candidate.Candidate
        :type source_id: int
        :return:

        **See Also**
        .. see also:: send_sms_campaign_to_candidates() method in SmsCampaignBase class.
        """
        if isinstance(source_id, (int, long)) and isinstance(candidate, Candidate):
            params = {'candidate_name': candidate.first_name + ' ' + candidate.last_name,
                      'campaign_name': self.campaign.name}
            self.create_activity(self.user_id,
                                 type_=CAMPAIGN_SMS_SEND,
                                 source_id=source_id,
                                 source_table=SmsCampaignSend.__tablename__,
                                 params=params,
                                 headers=self.oauth_header)
        else:
            raise InvalidUsage(error_message='Cannot create sms send activity')

    @classmethod
    def create_campaign_send_activity(cls, user_id, source, auth_header, num_candidates):
        """
        - Here we set "params" and "type" of activity to be stored in db table "Activity"
            for Campaign sent.

        - Activity will appear as "%(campaign_name)s has been sent to %(num_candidates)s".

        - This method is called from send_sms_campaign_to_candidates() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param user_id: id of user
        :param source: Source row
        :param auth_header: Authorization header
        :param num_candidates: number of candidates to which campaign is sent
        :type user_id: int
        :type source: row
        :type auth_header: dict
        :type num_candidates: int

        **See Also**
        .. see also:: send_sms_campaign_to_candidates() method in SmsCampaignBase class.
        """
        if not isinstance(source, SmsCampaign):
            raise InvalidUsage(error_message='source should be an instance of model sms_campaign')
        params = {'name': source.name,
                  'num_candidates': num_candidates}
        cls.create_activity(user_id,
                            type_=CAMPAIGN_SEND,
                            source_id=source.id,
                            source_table=SmsCampaign.__tablename__,
                            params=params,
                            headers=auth_header)

    @staticmethod
    def pre_process_url_redirect(campaign_id, url_conversion_id, candidate_id):
        """
        This method is used for the pre-processing of URL redirection
            It checks if candidate and campaign is present in database, If both are
            present, returns them otherwise rasie ResourceNotFound.

        :param campaign_id: id of SMS campaign
        :param url_conversion_id: id of URL conversion record
        :param candidate_id: id of Candidate
        :return: SMS Campaign and Candidate row
        :rtype: tuple (sms_campaign, candidate)

        **See Also**
        .. see also:: sms_campaign_url_redirection() function in sms_campaign_app/app.py
        """
        url_redirect_data = {'campaign_id': campaign_id,
                             'url_conversion_id': url_conversion_id,
                             'candidate_id': candidate_id}
        missing_items = find_missing_items(url_redirect_data, verify_all_keys=True)
        if not missing_items:
            candidate = Candidate.get_by_id(candidate_id)
            if candidate:
                # check if campaign exists
                campaign = SmsCampaign.get_by_id(campaign_id)
                if campaign:
                    return campaign, candidate
                else:
                    raise ResourceNotFound(error_message='pre_process_url_redirect: '
                                                         'SMS Campaign(id=%s) Not found.'
                                                         % campaign_id)
            else:
                raise ResourceNotFound(error_message='pre_process_url_redirect: '
                                                     'Candidate(id:%s) not found.' % candidate_id)
        else:
            raise MissingRequiredField(error_message='pre_process_url_redirect: '
                                                     'Missing required fields are: %s'
                                                     % missing_items)

    def process_url_redirect(self, campaign, url_conversion_id, candidate):
        """
        This does the following steps to send campaign to candidates.

        1- Get the "url_conversion" row from db.
        2- Get the "sms_campaign_blast" row from db.
        3- Increase "hit_count" by 1 for "url_conversion" record.
        4- Increase "clicks" by 1 for "sms_campaign_blast" record.
        5- Add activity that abc candidate clicked on xyz campaign.
            "%(candidate_name)s clicked URL of campaign %(campaign_name)s"
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
        :param url_conversion_id: id of url_conversion record
        :param candidate: Campaign object form db
        :type campaign: row
        :type url_conversion_id: int
        :type candidate: common.models.candidate.Candidate
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
                                                 clicks_update=True)
        # Update hit count
        self.create_or_update_url_conversion(url_conversion_id=url_conversion_id,
                                             hit_count_update=True)
        # Create Activity
        self.create_campaign_url_click_activity(candidate)
        logger.info('process_url_redirect: candidate(id:%s) clicked on SMS '
                    'campaign(id:%s). (User(id:%s))'
                    % (candidate.id, self.campaign.id, self.user_id))
        # Get Url to redirect candidate to actual URL
        url_conversion_row = UrlConversion.get_by_id(url_conversion_id)
        if url_conversion_row.destination_url:
            return url_conversion_row.destination_url
        else:
            raise EmptyDestinationUrl(
                error_message='process_url_redirect: Destination_url is empty for '
                              'url_conversion(id:%s)' % url_conversion_id)

    def create_campaign_url_click_activity(self, source):
        """
        - Here we set "params" and "type" of activity to be stored in db table "Activity"
            for Campaign URL click.

        - Activity will appear as
            "Michal Jordan clicked on SMS Campaign "abc". "

        - This method is called from process_url_redirect() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param source: Candidate row
        :type source: row

        **See Also**
        .. see also:: process_url_redirect() method in SmsCampaignBase class.
        """
        if not isinstance(source, Candidate):
            raise InvalidUsage(error_message='source should be an instance of model candidate')
        params = {'candidate_name': source.first_name + ' ' + source.last_name,
                  'campaign_name': self.campaign.name}
        self.create_activity(self.user_id,
                             type_=CAMPAIGN_SMS_CLICK,
                             source_id=self.campaign.id,
                             source_table=SmsCampaign.__tablename__,
                             params=params,
                             headers=self.oauth_header)

    @classmethod
    def process_candidate_reply(cls, reply_data):
        """
        - When candidate replies to user'phone number, we do the following at our App's
            endpoint '/receive'

            1- Gets "user_phone" record
            2- Gets "candidate_phone" record
            3- Gets latest campaign sent to given candidate
            4- Gets "sms_campaign_blast" row for "sms_campaign_send" found in step-3
            5- Saves candidate's reply in db table "sms_campaign_reply"
            6- Creates Activity that "abc" candidate has replied "123" to campaign "xyz"
            7- Updates the count of replies in "sms_campaign_blast" by 1

        :param reply_data:
        :type reply_data: dict
        :exception: MissingRequiredField (5006)
        :exception: MultipleUsersFound(5007)
        :exception: MultipleCandidatesFound(5008)
        :exception: NoSMSCampaignSentToCandidate(5013)

        **See Also**
        .. see also:: sms_receive() function in sms_campaign_app/app.py
        """
        required_fields = ['From', 'To', 'Body']
        missing_items = find_missing_items(reply_data, required_fields)
        if not missing_items:
            # get "user_phone" row
            user_phone = _get_valid_user_phone_value(reply_data.get('To'))
            # get "candidate_phone" row
            candidate_phone = _validate_candidate_phone_value(reply_data.get('From'))
            # get latest campaign send
            sms_campaign_send = SmsCampaignSend.get_by_candidate_id(candidate_phone.candidate_id)
            if sms_campaign_send:
                # get SMS campaign blast
                sms_campaign_blast = SmsCampaignBlast.get_by_id(
                    sms_campaign_send.sms_campaign_blast_id)
                # save candidate reply
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
                                                        replies_update=True)
                logger.debug('Candidate(id:%s) replied "%s" to Campaign(id:%s).(User(id:%s))'
                             % (candidate_phone.candidate_id, reply_data.get('Body'),
                                sms_campaign_blast.sms_campaign_id, user_phone.user_id))
            else:
                raise NoSMSCampaignSentToCandidate(
                    error_message='No SMS campaign sent to candidate(id:%s)'
                                  % candidate_phone.candidate_id)
        else:
            raise MissingRequiredField(error_message='%s' % missing_items)

    @classmethod
    def save_candidate_reply(cls, campaign_blast_id, candidate_phone_id, reply_body_text):
        """
        - Here we save the reply of candidate in db table "sms_campaign_reply"

        :param campaign_blast_id: id of "sms_campaign_blast" record
        :param candidate_phone_id: id of "candidate_phone" record
        :param reply_body_text: reply_body_text
        :type campaign_blast_id: int
        :type candidate_phone_id: int
        :type reply_body_text: str
        :return:
        """
        sms_campaign_reply_row = SmsCampaignReply(sms_campaign_blast_id=campaign_blast_id,
                                                  candidate_phone_id=candidate_phone_id,
                                                  reply_body_text=reply_body_text,
                                                  added_time=datetime.now())
        SmsCampaignReply.save(sms_campaign_reply_row)
        return sms_campaign_reply_row

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

        :param sms_campaign_reply: "sms_campaign_reply" row
        :param campaign_blast: "sms_campaign_blast" row
        :param candidate_id: id of Candidate
        :type sms_campaign_reply: row
        :type campaign_blast: row
        :type candidate_id: int

        **See Also**
        .. see also:: process_candidate_reply() method in SmsCampaignBase class.
        """
        # get Candidate
        candidate = Candidate.get_by_id(candidate_id)
        campaign = SmsCampaign.get_by_id(campaign_blast.sms_campaign_id)
        params = {'candidate_name': candidate.first_name + ' ' + candidate.last_name,
                  'reply_text': sms_campaign_reply.reply_body_text,
                  'campaign_name': campaign.name}
        user_access_token = cls.get_authorization_header(user_id)
        cls.create_activity(user_id,
                            type_=CAMPAIGN_SMS_REPLY,
                            source_id=sms_campaign_reply.id,
                            source_table=SmsCampaignReply.__tablename__,
                            params=params,
                            headers=user_access_token)


def _get_valid_user_phone_value(user_phone_value):
    """
    - This ensures that given phone number is associated with only one user.

    - This function is called from class method process_candidate_reply() of
    SmsCampaignBase class to get user_phone db record.

    :param user_phone_value: Phone number by which we want to get user.
    :type user_phone_value: str
    :exception: If Multiple users found, it raises "MultipleUsersFound".
    :exception: If no user is found, it raises "ResourceNotFound".
    :return: User row
    """
    user_phone_rows = UserPhone.get_by_phone_value(user_phone_value)
    if len(user_phone_rows) == 1:
        user_phone = user_phone_rows[0]
    elif len(user_phone_rows) > 1:
        raise MultipleUsersFound(
            error_message='%s phone number is associated with %s users. User ids are %s'
                          % (user_phone_value,
                             len(user_phone_rows),
                             [user_phone.user_id for user_phone in user_phone_rows]))
    else:
        raise ResourceNotFound(error_message='No User is associated with '
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
    :exception: If no Candidate is found, it raises "ResourceNotFound".
    :return: Candidate row
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
        raise ResourceNotFound(error_message='No Candidate is associated with '
                                             '%s phone number' % candidate_phone_value)
    return candidate_phone


def delete_sms_campaign(campaign_id, current_user_id):
    """
    This function is used to delete SMS campaign of a user. If current user is the
    creator of given campaign id, it will delete the campaign, otherwise it will
    raise the Forbidden error.
    :param campaign_id: id of SMS campaign to be deleted
    :param current_user_id: id of current user
    :exception: Forbidden error (status_code = 403)
    :exception: Resource not found error (status_code = 404)
    :return: True if record deleted successfully, False otherwise.
    :rtype: bool
    """
    if is_owner_of_campaign(campaign_id, current_user_id):
        return SmsCampaign.delete(campaign_id)


def is_owner_of_campaign(campaign_id, current_user_id):
    """
    This function returns True if the current user is an owner for given
    campaign_id. Otherwise it raises the Forbidden error.
    :param campaign_id: id of campaign form getTalent database
    :param current_user_id: Id of current user
    :return:
    """
    campaign_row = SmsCampaign.get_by_id(campaign_id)
    if campaign_row:
        campaign_user_id = UserPhone.get_by_id(campaign_row.user_phone_id).user_id
        if campaign_user_id == current_user_id:
            return True
        else:
            raise ForbiddenError(error_message='You are not the owner of '
                                               'SMS campaign(id:%s)' % campaign_id)
    else:
        raise ResourceNotFound(error_message='SMS Campaign(id=%s) not found.' % campaign_id)


def validate_header(request):
    """
    Proper header should be {'content-type': 'application/json'} for posting
    some data on SMS campaign API.
    If header of request is not proper, it raises InvalidUsage exception
    :return:
    """
    if not request.headers.get('CONTENT_TYPE') == JSON_CONTENT_TYPE_HEADER['content-type']:
        raise InvalidUsage(error_message='Invalid header provided')
