"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

This module contains CampaignBase class which provides common methods for
all campaigns. Methods are
- schedule()
- get_smartlist_candidates()
- create_or_update_url_conversion()
- create_activity()
- get_campaign_data()
- save()
- send()
- delete() etc.
Any service can inherit from this class to implement/override functionality accordingly.
"""

# Standard Library
import json
from abc import ABCMeta
from datetime import datetime
from abc import abstractmethod

# Third Party
from celery import chord
from flask import current_app
from requests import ConnectionError

# Database Models
from ..models.db import db
from ..models.user import (Token, User)
from ..models.misc import UrlConversion
from ..models.candidate import Candidate
from ..models.email_marketing import EmailCampaignBlast
from ..models.sms_campaign import (SmsCampaign, SmsCampaignBlast, SmsCampaignSmartlist)

# Common Utils
from ..utils.scheduler_utils import SchedulerUtils
from ..talent_config_manager import TalentConfigKeys
from ..utils.activity_utils import ActivityMessageIds
from custom_errors import (CampaignException, EmptyDestinationUrl)
from ..utils.handy_functions import (http_request, find_missing_items,
                                     JSON_CONTENT_TYPE_HEADER,
                                     snake_case_to_pascal_case)
from ..routes import (ActivityApiUrl, SchedulerApiUrl, CandidatePoolApiUrl)
from ..error_handling import (ForbiddenError, InvalidUsage, ResourceNotFound)
from campaign_utils import (get_model, validate_signed_url, delete_scheduled_task,
                            get_candidate_url_conversion_campaign_send_and_blast_obj,
                            get_activity_message_name, get_activity_message_id_from_name,
                            FrequencyIds, get_campaign_type_prefix,
                            assert_is_instance_of_campaign_model,
                            assert_for_int_or_long, get_campaign_for_ownership_validation,
                            CampaignType)
from validators import (validate_datetime_format, validate_form_data,
                        validation_of_data_to_schedule_campaign,
                        validate_blast_candidate_url_conversion_in_db,
                        validate_if_current_user_is_owner)


class CampaignBase(object):
    """
    - This is the base class for sending campaign to candidates and to keep track
        of their responses.

    This class contains following methods:

    * __init__():
        This method is called by creating the class object.
        - It takes "user_id" as keyword argument, gets the user object from database and sets
            user object in self.user.

    * get_authorization_header(user_id, bearer_access_token=None): [static]
        This method is used to get authorization header for current user. This header is
        used to communicate with other flask micro services like candidate_service,
        activity_service etc.

    * process_save_or_update(self, form_data, campaign_id=None):
        This method is used to save or update a campaign. It returns the id of campaign
        object in database.

    * create_or_update_campaign(self, campaign_data, campaign_id=None)
        This saves/updates SMS campaign in database table "sms_campaign" or "push_campaign"
        depending upon type of campaign.

    * create_or_update_campaign_smartlist(campaign, smartlist_ids): [static]
        This saves/updates smartlist ids associated with a campaign in database
        table "sms_campaign_smartlist" for SMS campaign. (or some other table for
        other campaign)

    * create_activity_for_campaign_creation(self, source):
        This method is used to create an activity in database table "Activity" when user
        creates a campaign.
            e.g. in case of SMS campaign, activity will appear as
                'Nikola Tesla' created an SMS campaign "We are hiring".

    * get_authorized_campaign_obj_and_scheduled_task(cls. campaign_id, user_id)
        This validates that the current user is an owner of requested campaign.
        It also return the data of scheduler_task from scheduler_service if the
        campaign was scheduled.

    * validate_ownership_of_campaign(campaign_id, current_user_id): [abstract][static]
        This method verifies if current user is an owner of given campaign or not.
        If not it raises Forbidden error, otherwise it returns True, Child classes will
        implement this.

    * delete(cls, **kwargs)
        This is a class method used to delete a campaign. If that campaign was scheduled,
        it first un-schedules the campaign from scheduler_service and then deletes campaign
        from database.

    * pre_process_schedule(cls,request, campaign_id):
        This class method is used before scheduling/re-scheduling a campaign. It
        does the validation part. Details are given in definition of this method.

    * is_already_scheduled(scheduler_task_id, oauth_header): [static]
        For given task id, this method GETs the task object from scheduler_service.
        If task is not found there, it returns None. Otherwise it returns the task object
        received from scheduler_service.

    * schedule(self, data_to_schedule):
        This method is used to schedule given campaign using scheduler_service. Child classes
        will override this to set the value of "data_to_schedule" and update tables like
        email_campaign, sms_campaign etc, with "task_id" (Task created on APScheduler).

    * format_data_to_schedule(data_to_schedule)
        Once we have data from UI to schedule a campaign, we format the data as per
        scheduler_service requirement, and return it.

    * pre_process_re_schedule(pre_processed_data)
        This method is used to do required processing before re-scheduling a campaign.
        e.g. it checks if task is not present on redis job store, return None.
        Details are given in definition of this method.

    * send(self, campaign):
        This method is used send the campaign to candidates. This has the common functionality
        for all campaigns.

    * create_campaign_blast(campaign): [static]
        For each campaign, here we create blast obj for given campaign

    * get_smartlist_candidates(self, campaign_smartlist):
        This method gets the candidates associated with the given smartlist_id.
        It may search candidates in database/cloud. It is common for all the campaigns. It uses
        candidate_service/candidate_pool_service to do the job.

    * pre_process_celery_task(self, candidates):
        This method is used to do any necessary processing before assigning task to Celery
        worker if required. For example in case of SMS campaign, we filter valid candidates
        (those candidates who have one unique phone number associated).

    * send_campaign_to_candidates(self, candidates):
        This loops over candidates and call send_sms_campaign_to_candidate() to send the
        campaign asynchronously.

    * send_campaign_to_candidate(self, data_to_send_campaign): [abstract]
        This is a celery task. This does the sending part and update "sms_campaign_blast"
        ,"sms_campaign_send" etc.

    * celery_error_handler(uuid):
        This method is used to catch any error of Celery task and log it.

    * callback_campaign_sent(send_result, user_id, campaign, oauth_header):
        Once a campaign has been sent to a list of candidates, Celery hits this method as
        a callback and we create an "Activity" in database table as
            SMS campaign 'We are hiring' has been sent to 500 candidates.
        We also update the number of sends in this method.

    * create_campaign_send_activity(cls, user_id, source, oauth_header, num_candidates):
        This method is used to create an activity in database table "Activity" when campaign
        has been sent to all of the candidates.
            e.g.
                Activity will appear as " 'Jobs at Oculus' has been sent to '50' candidates".

    * pre_process_url_redirect(cls, request_args, requested_url)
        When candidates clicks on a campaign URL, it is redirected to our app. In this
        method we verify the signature of the URL.

    * process_url_redirect(cls, url_conversion_id, campaign_type, verify_signature=False,
                                                request_args=None, requested_url=None)
        When candidate clicks on a URL present in any campaign e.g. in SMS, Email etc. it is
        redirected to our app> Here we keep track of number of clicks, hit_count and create
        activity e.g. Mitchel clicked on SMS campaign 'Jobs'.

    * update_stats_and_create_click_activity(cls, campaign_blast_obj, candidate, url_conversion_obj,
                                                    campaign_obj)
        In the process of redirection, here we update hit_count, increase number of clicks
        and create "campaign clicked" activity.

    *  create_campaign_clicked_activity(self, candidate)
        If candidate clicks on link present in SMS body text, we create an activity in
        database table "Activity".
        Activity will appear as (e.g)
            "'Muller' clicked on SMS Campaign 'Job opening at getTalent'."

    * update_campaign_blast(campaign_blast_obj, **kwargs)
        This is a common method to update blast entities of a campaign. e.g. to increase
        hit_count, replies (or any other entity) by 1, we can use this method.

    * create_or_update_url_conversion(destination_url=None, source_url='', hit_count=0,
                                    url_conversion_id=None, increment_hit_count=None): [static]
        Here we save/update record of url_conversion in db table "url_conversion".
        This is common for all child classes.

    * create_activity(self, type_=None, source_table=None, source_id=None, params=None):
        This makes HTTP POST call to "activity_service" to create activity in database.
    """
    __metaclass__ = ABCMeta

    def __init__(self, user_id):
        if not isinstance(user_id, (int, long)):
            raise InvalidUsage('User id must be int|long.')
        user_obj = User.get_by_id(user_id)
        if not user_obj:
            raise ResourceNotFound('User does not exist in database with id %s.' % user_id)
        self.user = user_obj
        # This gets the access_token of current user to communicate with other services.
        self.oauth_header = self.get_authorization_header(user_id)
        self.campaign = None  # It will be instance of model e.g. SmsCampaign
        # or PushNotification etc.
        self.campaign_blast_id = None  # Campaign's blast id in database
        self.campaign_type = ''  # Child classes will set this e.g. sms_campaign

    @staticmethod
    def get_authorization_header(user_id, bearer_access_token=None):
        """
        This returns the authorization header containing access token token associated
        with current user. We use this access token to communicate with other services,
        like activity_service to create activity.
        If access_token is provided, we return the auth header, otherwise we get the access token
        from database table "Token" and then return the auth header.
        If access token is not found by these two methods ,we raise Forbidden error.

        :param user_id: id of user
        :param bearer_access_token: e.g. 'Bearer IxzJAm3RWFnZENln37E3ivs2gxUfzB'
        :type user_id: int
        :type bearer_access_token: str
        :exception: ForbiddenError
        :exception: ResourceNotFound
        :return: Authorization header
        :rtype: dict
        """
        if bearer_access_token:
            return {'Authorization': bearer_access_token}
        else:
            if not isinstance(user_id, (int, long)):
                raise InvalidUsage('User id must be int|long.')
            user_token_obj = Token.get_by_user_id(user_id)
            if not user_token_obj:
                raise ResourceNotFound('No auth token record found for user(id:%s)'
                                       % user_id, error_code=ResourceNotFound.http_status_code())
            user_access_token = user_token_obj.access_token
        if not user_access_token:
            raise ForbiddenError('User(id:%s) has no auth token associated.'
                                 % user_id)
        return {'Authorization': 'Bearer %s' % user_access_token}

    def pre_process_save_or_update(self, campaign_data):
        """
        This does the processing of data from UI before saving/updating the campaign
        in database table sms_campaign or push_campaign etc. depending upon campaign type.
        It has following steps:
            1- Sets the frequency_id to ONCE if frequency_id is not provided or 0
            2- Validates the form data by calling validate_form_data() defined in validators.py
                and store it in validated_data.
            3- Imports the model of campaign e.g. SmsCampaign or PushCampaign etc.
            4- Deletes the smartlist_ids from validated_data as smartlist_ids is not a field
                of campaign models.
        :param campaign_data:
        :type campaign_data: dict
        :exception: Invalid Usage
        :return: Model class of campaign, validated_data,
                invalid_smartlist_ids, not_found_smartlist_ids
        :rtype: tuple
        """
        if not isinstance(campaign_data, dict):
            raise InvalidUsage('campaign_data must be a dictionary.')
        if not campaign_data:
            raise InvalidUsage('No data received from UI to save/update campaign.')
        logger = current_app.config[TalentConfigKeys.LOGGER]
        validated_data = campaign_data.copy()
        # if frequency_id not provided or is 0, set to id of ONCE
        if not campaign_data.get('frequency_id'):
            campaign_data.update({'frequency_id': FrequencyIds.ONCE})
        invalid_smartlist_ids, not_found_smartlist_ids = validate_form_data(campaign_data)
        logger.info('Campaign data has been validated.')
        campaign_model = get_model(self.campaign_type,
                                   snake_case_to_pascal_case(self.campaign_type))
        # 'smartlist_ids' is not a field of sms_campaign or push_campaign tables, so
        # need to remove it from data.
        del validated_data['smartlist_ids']
        return campaign_model, validated_data, invalid_smartlist_ids, not_found_smartlist_ids

    def save(self, form_data):
        """
        This saves the campaign in database table sms_campaign or push_campaign etc. depending
        upon campaign type. It has following steps:
            1- Validates the form data
            2- Sets the frequency_id to ONCE if frequency_id is not provided or 0
            3- Save campaign in database by calling create_or_update_campaign()
            4- Create activity that by calling create_activity_for_campaign_creation()
                (e,g)
                "'Harvey Specter' created an SMS campaign: 'Hiring at getTalent'"
        :param form_data: data from UI
        :type form_data: dict
        :return: id of sms_campaign in db, invalid_smartlist_ids and not_found_smartlist_ids
        :rtype: tuple
        """
        logger = current_app.config[TalentConfigKeys.LOGGER]
        campaign_model, validated_data, invalid_smartlist_ids, not_found_smartlist_ids = \
            self.pre_process_save_or_update(form_data)
        # Save campaign in database table e.g. "sms_campaign"
        campaign_obj = campaign_model(**validated_data)
        campaign_model.save(campaign_obj)
        # Create record in database table e.g. "sms_campaign_smartlist"
        self.create_campaign_smartlist(campaign_obj, form_data['smartlist_ids'])
        # Create Activity, and If we get Connection error, we log the error
        try:
            self.create_activity_for_campaign_creation(campaign_obj, self.user,
                                                       self.oauth_header)
        except ConnectionError:
            # In case activity_service is not running, we proceed normally and log the error.
            logger.exception('Error creating campaign creation activity.')
        return campaign_obj.id, invalid_smartlist_ids, not_found_smartlist_ids

    def update(self, form_data, campaign_id):
        """
        Here we will save the campaign in database or will update the existing record.
        - This method is called from
            1) save() method of CampaignBase class
            2) schedule() method of SmsCampaignBase class
            3) unschedule method of class CampaignBase.
        :param form_data: data of SMS campaign or some other campaign from UI to save
        :param campaign_id: id of "sms_campaign" obj, default None
        :type form_data: dict
        :type campaign_id: int
        :exception: ResourceNotFound
        :return: "sms_campaign" obj, invalid_smartlist_ids and not_found_smartlist_ids
        :rtype: tuple
        """
        campaign_obj = self.validate_ownership_of_campaign(campaign_id, self.user.id,
                                                           self.campaign_type)
        _, validated_data, invalid_smartlist_ids, not_found_smartlist_ids = \
            self.pre_process_save_or_update(form_data)
        if not campaign_obj:
            raise ResourceNotFound('%s campaign(id=%s) not found.' % (self.campaign_type,
                                                                      campaign_id))
        for key, value in validated_data.iteritems():
            # update old values with new ones if provided, else preserve old ones.
            validated_data[key] = value if value else getattr(campaign_obj, key)
        campaign_obj.update(**validated_data)
        return invalid_smartlist_ids, not_found_smartlist_ids

    @staticmethod
    def create_campaign_smartlist(campaign, smartlist_ids):
        """
        - Here we save the smartlist ids for an SMS campaign in database table
        "sms_campaign_smartlist" or "push_campaign_smartlist".

        - This method is called from save() method of class CampaignBase.
        :param campaign: sms_campaign obj
        :param smartlist_ids: ids of smartlists
        :exception: InvalidUsage
        :type campaign: SmsCampaign
        :type smartlist_ids: list

        **See Also**
        .. see also:: save() method in CampaignBase class.
        """
        assert_is_instance_of_campaign_model(campaign)
        campaign_smartlist_model = get_model(
            campaign.__tablename__, snake_case_to_pascal_case(campaign.__tablename__) + 'Smartlist')
        for smartlist_id in smartlist_ids:
            data = {'smartlist_id': smartlist_id, 'sms_campaign_id': campaign.id}
            db_record = campaign_smartlist_model.get_by_campaign_id_and_smartlist_id(campaign.id,
                                                                                     smartlist_id)
            if not db_record:
                new_record = campaign_smartlist_model(**data)
                campaign_smartlist_model.save(new_record)

    @classmethod
    def create_activity_for_campaign_creation(cls, source, user, oauth_header):
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
        assert_is_instance_of_campaign_model(source)
        if not isinstance(user, User):
            raise InvalidUsage('user should be instance of model User')
        # set params
        params = {'username': user.name, 'campaign_name': source.name,
                  'campaign_type': get_campaign_type_prefix(source.__tablename__)}
        cls.create_activity(user.id,
                            _type=ActivityMessageIds.CAMPAIGN_CREATE,
                            source_id=source.id,
                            source_table=source.__tablename__,
                            params=params,
                            auth_header=oauth_header)

    @classmethod
    def get_authorized_campaign_obj_and_scheduled_task(cls, campaign_id, user_id, campaign_type):
        """
        1) verifies that current user is owner of given campaign_id
        2) If campaign has scheduler_task_id, it gets the scheduled task data from scheduler_service
        :param campaign_id: id of campaign
        :param user_id: id of user
        :return: This returns the campaign obj, scheduled task data and oauth_header
        :rtype: tuple
        :exception: Invalid usage
        """
        assert_for_int_or_long(dict(campaign_id=campaign_id, user_id=user_id))
        campaign_obj = cls.validate_ownership_of_campaign(campaign_id, user_id, campaign_type)
        assert_is_instance_of_campaign_model(campaign_obj)
        oauth_header = cls.get_authorization_header(user_id)
        # check if campaign is already scheduled
        scheduled_task = cls.is_already_scheduled(campaign_obj.scheduler_task_id, oauth_header)
        return campaign_obj, scheduled_task, oauth_header

    @classmethod
    def validate_ownership_of_campaign(cls, campaign_id, current_user_id, campaign_type):
        """
        This function returns True if the current user is an owner for given
        campaign_id. Otherwise it raises the Forbidden error. Child classes will implement this
        according to their database tables.
        :param campaign_id: id of campaign form getTalent database
        :param current_user_id: Id of current user
        :exception: InvalidUsage
        :exception: ResourceNotFound
        :exception: ForbiddenError
        :return: Campaign obj if current user is an owner for given campaign.
        :rtype: SmsCampaign or some other campaign obj
        """
        campaign_obj = get_campaign_for_ownership_validation(campaign_id, current_user_id,
                                                             campaign_type)
        campaign_user_id = cls.get_owner_user_id(campaign_obj, current_user_id)
        if campaign_user_id == current_user_id:
            return campaign_obj
        else:
            raise ForbiddenError('User(id:%s) is not the owner of %s(id:%s)'
                             % (current_user_id, campaign_obj.__tablename__, campaign_obj.id))

    @staticmethod
    @abstractmethod
    def get_owner_user_id(campaign_obj, current_user_id):
        """
        This returns the id of user who created the given campaign. Child classes will implement
        this as per their requirement.
        For example in case of SMS campaign, we have user_phone_id
        in campaign table and in case of Push campaign we have user_id in campaign table.
        :param campaign_obj: campaign object
        :param current_user_id: id of logged-in user
        :type campaign_obj: SmsCampaign
        :type current_user_id: int | long
        :exception: Invalid Usage
        :return: id of owner user of given campaign
        :rtype: int | long

        **See Also**
            .. see also:: get_owner_user_id() in SmsCampaignBase class.
        """
        pass

    def delete(self, campaign_id):
        """
        This function is used to delete the campaign in following given steps.
        1- Checks if any of the required field is missing from given data. It raise Invalid usage
            exception there is any field missing from data.
        2- Calls validate_ownership_of_campaign() method to validate that current user is an
            owner of given campaign id and gets the campaign object.
        3- Checks if campaign object has any scheduler_task_id assigned. If it has any, then do
            the following steps:
            3.1- Calls get_authorization_header() to get auth header (which is used to make
                HTTP request to scheduler_service)
            3.2- Makes HTTP DELETE request to scheduler service to remove the job from redis job
                store.
            If both of these two steps are successful, it returns True, otherwise returns False.
        4- Deletes the campaign from database and returns True if campaign is deleted successfully.
            Otherwise it returns False.

        :Example:
             In case of SMS campaign, this method is used as
                SmsCampaignBase.delete(1, 1)

        :param campaign_id: id of campaign
        :type campaign_id: int | long
        :exception: Forbidden error (status_code = 403)
        :exception: Resource not found error (status_code = 404)
        :exception: Invalid Usage (status_code = 400)
        :return: True if record deleted successfully, False otherwise.
        :rtype: bool

        **See Also**
        .. see also:: endpoints /v1/campaigns/:id in v1_sms_campaign_api.py
        """
        if not campaign_id:
            raise InvalidUsage('delete: campaign_id cannot be emtpy.')
        if not self.user:
            raise InvalidUsage('delete: user cannot be emtpy.')
        if not self.campaign_type:
            raise InvalidUsage('delete: campaign_type is not set correctly.')
        campaign_type = self.campaign_type
        logger = current_app.config[TalentConfigKeys.LOGGER]
        # get campaign_obj, scheduled_task data and oauth_header
        campaign_obj, scheduled_task, oauth_header = \
            self.get_authorized_campaign_obj_and_scheduled_task(campaign_id, self.user.id,
                                                                self.campaign_type)
        # campaign object has scheduler_task_id assigned
        if scheduled_task:
            # campaign was scheduled, remove task from scheduler_service
            unscheduled = delete_scheduled_task(scheduled_task['id'], oauth_header)
            if not unscheduled:
                return False

        campaign_model = get_model(campaign_type, snake_case_to_pascal_case(campaign_type))
        if not campaign_model.delete(campaign_obj):
            logger.error("%s(id:%s) couldn't be deleted." % (campaign_type, campaign_obj.id))
            return False
        try:
            self.create_activity_for_campaign_delete(self.user, campaign_obj, oauth_header)
        except ConnectionError:
            # In case activity_service is not running, we proceed normally and log the error.
            logger.exception('delete: Error creating campaign delete activity.')
        logger.info('delete: %s(id:%s) has been deleted successfully.' % (campaign_type,
                                                                          campaign_obj.id))
        return True

    @classmethod
    def create_activity_for_campaign_delete(cls, user, source, oauth_header):
        """
        - when a user deletes a campaign, here we set "params" and "type" of activity to
            be stored in db table "Activity" when a user deletes a campaign.
        - Activity will appear as " Michal has deleted an SMS campaign 'Jobs at Oculus'.
        - This method is called from delete() method of class CampaignBase.
        :param user: user obj
        :param source: sms_campaign (or some other campaign) obj
        :param oauth_header: Authorization header
        :type user: User
        :type source: SmsCampaign
        :type oauth_header: dict
        :exception: InvalidUsage

        **See Also**
        .. see also:: schedule() method in CampaignBase class.
        """
        # any other campaign will update this line
        assert_is_instance_of_campaign_model(source)
        if not isinstance(user, User):
            raise InvalidUsage('user should be instance of model User')
        # Activity message looks like %(username)s deleted a campaign: %(name)s"
        params = {'username': user.name, 'name': source.name,
                  'campaign_type': get_campaign_type_prefix(source.__tablename__)}
        cls.create_activity(
                user.id,
                _type=ActivityMessageIds.CAMPAIGN_DELETE,
                source_id=source.id,
                source_table=source.__tablename__,
                params=params,
                auth_header=oauth_header
        )

    @classmethod
    def pre_process_schedule(cls, request, campaign_id, campaign_type):
        """
        Here we have common functionality for scheduling/re-scheduling a campaign.
        Before making HTTP POST/GET call on scheduler_service, we do the following:

        1- Check if current user is an owner of given campaign_id
        2- Check if given campaign is already scheduled or not
        3- If campaign is already scheduled and requested method is POST, we raise Forbidden error
            because updating already scheduled campaign should be through PUT request
        4- Check if request has valid JSON content-type header
        5- Get JSON data from request and raise Invalid Usage exception if no data is found or
            data is not JSON serializable.
        6- If start datetime is not provide/given in invalid format/is in past, we raise Invalid
            usage  error as start_datetime is required field for both 'periodic' and 'one_time'
            schedule.
        7- Get number of seconds by validating given frequency_id
        8- If end_datetime and frequency, both are provided then we validate same checks for
            end_datetime as we did in step 2 for start_datetime.
        9- Removes the frequency_id from given dict of data and put frequency (number of seconds)
            in it.
        :exception: Forbidden error
        :exception: Resource not found
        :exception: Bad request
        :exception: Invalid usage
        :return: dictionary containing Campaign obj, data to schedule SMS campaign,
                    scheduled_task and auth header
        :rtype: dict

        **See Also**
        .. see also:: endpoints /v1/campaigns/:id/schedule in v1_sms_campaign_api.py
        """
        # get campaign obj, scheduled task data and oauth_header
        campaign_obj, scheduled_task, oauth_header = \
            cls.get_authorized_campaign_obj_and_scheduled_task(campaign_id, request.user.id,
                                                               campaign_type)
        # Updating scheduled task should not be allowed in POST request
        if scheduled_task and request.method == 'POST':
            raise ForbiddenError('Use PUT method instead to update already scheduled task')
        # Scheduling first time should be via POST, not via PUT HTTP method
        if not scheduled_task and request.method == 'PUT':
            raise ForbiddenError('Use POST method instead to schedule campaign first time')
        # get JSON data from request
        data_to_schedule_campaign = validation_of_data_to_schedule_campaign(campaign_obj, request)
        return {'campaign': campaign_obj,
                'data_to_schedule': data_to_schedule_campaign,
                'scheduled_task': scheduled_task,
                'oauth_header': oauth_header}

    @staticmethod
    def is_already_scheduled(scheduler_task_id, oauth_header):
        """
        If the given task id  has already been scheduled on scheduler_service. It makes HTTP GET
        call on scheduler_service_api endpoint to check if given scheduler_task_id is already
        present in redis job store. If task is found, we return task obj, otherwise we return None.
        :param scheduler_task_id: Data provided from UI to schedule a campaign
        :param oauth_header: oauth_header to make HTTP GET call on scheduler_service
        :type scheduler_task_id: str
        :type oauth_header: dict
        :exception: InvalidUsage
        :return: task obj if task is already scheduled, None otherwise.
        :rtype: dict

        **See Also**
        .. see also:: get_authorized_campaign_obj_and_scheduled_task() defined in this file.
        """
        if not oauth_header:
            raise InvalidUsage('oauth_header is required param')
        if not scheduler_task_id:  # campaign has no scheduler_task_id associated
            return None
        # HTTP GET request on scheduler_service to schedule campaign
        try:
            response = http_request('GET', SchedulerApiUrl.TASK % scheduler_task_id,
                                    headers=oauth_header)
        # Task not found on APScheduler
        except ResourceNotFound:
            return None
        # Task is present on APScheduler
        if response.ok:
            return response.json()['task']

    def schedule(self, data_to_schedule):
        """
        This actually POST on scheduler_service to schedule a given task.
        we set data_to_schedule dict in child class and call super constructor
        to make HTTP POST call to scheduler_service.

        e.g, in case of SMS campaign, we have
        data_to_schedule = {
                            'frequency': 0,
                            'frequency_id': 0,
                            'start_datetime': '2016-10-30T17:55:00Z',
                            'end_datetime': '2016-12-30T17:55:00Z',
                            'url_to_run_task': 'http://127.0.0.1:8012/v1/campaigns/1/send',
                            'task_type': 'one_time',
                            'data_to_post': None
                            }
        The validation of data_to_schedule is done inside pre_process_schedule() class method.
        Once campaign has been scheduled, we create an activity e.g.


        :param data_to_schedule: This contains the required data to schedule a particular job
        :type data_to_schedule: dict
        :return: id of scheduled task
        :rtype: str
        :exception: Invalid usage

        **See Also**
        .. see also:: schedule() method in CampaignBase class.
        """
        if not self.campaign:
            raise InvalidUsage('No campaign given to schedule.')
        if not isinstance(data_to_schedule, dict):
            raise InvalidUsage('data_to_schedule must be a dict.')
        if not data_to_schedule.get('url_to_run_task'):
            raise InvalidUsage('No URL given to run the task.')
        # format data to create new task
        data_to_schedule_task = self.format_data_to_schedule(data_to_schedule.copy())
        # set content-type in header
        self.oauth_header.update(JSON_CONTENT_TYPE_HEADER)
        response = http_request('POST', SchedulerApiUrl.TASKS,
                                data=json.dumps(data_to_schedule_task),
                                headers=self.oauth_header)
        # If any error occurs on POST call, we log the error inside http_request().
        if 'id' in response.json():
            # create campaign scheduled activity
            self.create_campaign_schedule_activity(self.user, self.campaign, self.oauth_header)
            current_app.config[TalentConfigKeys.LOGGER].info('%s(id:%s) has been scheduled.'
                                                             % (self.campaign.__tablename__,
                                                                self.campaign.id))
            return response.json()['id']
        else:
            raise InvalidUsage(
                "Error occurred while scheduling a task. Error details are '%s'."
                % response.json()['error']['message'])

    @staticmethod
    def format_data_to_schedule(data_to_schedule):
        """
        Once we have data from UI to schedule a campaign, we format the data as per
        scheduler_service requirement, and return it.

        UI sends data in following format:
                    {
                    "frequency_id": 2,
                    "start_datetime": "2015-12-29T13:40:00Z",
                    "end_datetime": "2015-12-27T11:45:00Z"
                    }
        - The validation of data_to_schedule is done inside pre_process_schedule() class method.
        - This method is called from schedule() class method.

        :param data_to_schedule:  Data provided from UI to schedule a campaign
        :exception: Invalid usage
        :return: data in dict format to send to scheduler_service
        :rtype: dict

        **See Also**
        .. see also:: schedule() method in CampaignBase class.
        """
        if not isinstance(data_to_schedule, dict):
            raise InvalidUsage('data_to_schedule must be a dict.')
        frequency = data_to_schedule.get('frequency')
        if not frequency:  # This means it is a one time job
            validate_datetime_format(data_to_schedule['start_datetime'])
            task = {
                "task_type": SchedulerUtils.ONE_TIME,
                "run_datetime": data_to_schedule['start_datetime'],
            }
        else:
            # end datetime should be in valid format and in future
            if not data_to_schedule.get('end_datetime'):
                raise InvalidUsage('end_datetime is required field to create periodic task')
            task = {
                "task_type": SchedulerUtils.PERIODIC,
                "frequency": frequency,
                "start_datetime": data_to_schedule['start_datetime'],
                "end_datetime": data_to_schedule['end_datetime'],
            }
        # set URL to be hit when time comes to run that task
        task['url'] = data_to_schedule['url_to_run_task']
        # set data to POST with above URL
        task['post_data'] = data_to_schedule.get('data_to_post', dict())
        return task

    @classmethod
    def create_campaign_schedule_activity(cls, user, source, oauth_header):
        """
        - Here we set "params" and "type" of activity to be stored in db table "Activity"
            when a user schedule a campaign.

        - Activity will appear as " Michal has scheduled an SMS campaign 'Jobs at Oculus'.

        - This method is called from schedule() method of class CampaignBase.

        :param user: user obj
        :param source: sms_campaign (or some other campaign) obj
        :param oauth_header: Authorization header
        :type user: User
        :type source: SmsCampaign
        :type oauth_header: dict
        :exception: InvalidUsage

        **See Also**
        .. see also:: schedule() method in CampaignBase class.
        """
        # any other campaign will update this line
        assert_is_instance_of_campaign_model(source)
        if not isinstance(user, User):
            raise InvalidUsage('user should be instance of model User')
        params = {'username': user.name,
                  'campaign_type': get_campaign_type_prefix(source.__tablename__),
                  'campaign_name': source.name}
        cls.create_activity(user.id,
                            _type=ActivityMessageIds.CAMPAIGN_SCHEDULE,
                            source_id=source.id,
                            source_table=source.__tablename__,
                            params=params,
                            auth_header=oauth_header)

    @classmethod
    def unschedule(cls, campaign_id, request, campaign_type):
        """
        This function gets the campaign object, and checks if it is present on scheduler_service.
        If campaign is present on scheduler_service, we delete it there and on success we return
            campaign object, otherwise we return None.
        :return: status of deleting a task
        :rtype: bool
        :exception: Invalid usage
        """
        if not campaign_id:
            raise InvalidUsage('Campaign id is required to unschedule it.')
        if not hasattr(request, 'user'):
            raise InvalidUsage('User cannot be None for un scheduling a campaign.')
        delete_status = False
        campaign_obj, scheduled_task, oauth_header = \
            cls.get_authorized_campaign_obj_and_scheduled_task(campaign_id, request.user.id,
                                                               campaign_type)
        if scheduled_task:
            delete_status = delete_scheduled_task(scheduled_task['id'], oauth_header)
            campaign_obj.update(scheduler_task_id=None) if delete_status else None
        return delete_status

    @staticmethod
    def pre_process_re_schedule(pre_processed_data):
        """
        UI sends data in following format:

                    {
                    "frequency_id": 2,
                    "start_datetime": "2015-12-29T13:40:00Z",
                    "end_datetime": "2015-12-27T11:45:00Z"
                    }
        and the already scheduled task looks like

            {"tasks":
                    {
                        "id": "5das76nbv950nghg8j8-33ddd3kfdw2",
                        "post_data": {
                            "url": "http://getTalent.com/sms/send/",
                            "phone_number": "09230862348",
                            "smart_list_id": 123456,
                            "content": "text to be sent as sms"
                            "some_other_kwarg": "abc",
                            "campaign_name": "SMS Campaign"
                        },
                        "frequency": 3601,      #in seconds
                        "start_datetime": "2015-11-05T08:00:00",
                        "end_datetime": "2015-12-05T08:00:00"
                        "next_run_datetime": "2015-11-05T08:20:30",
                        "task_type": "periodic"
                    }
            }
        So, to re-schedule a task, we do the following:
        1- Check if task is not present on redis job store, return None
        2- Check if already scheduled task is one_time
            2.1- If user wants to change the start datetime OR
            2.2- If user wants to make it periodic task

            Then move on to delete already scheduled task and create new one
        Otherwise
        3- Check if already scheduled task is 'Periodic'
            3.1- If user wants to make it one_time OR
            3.2- If user wants to change any parameter from (frequency, start_datetime.
            end_datetime)
            Then move on to delete already scheduled task and create new one
        Otherwise, return the id of already scheduled task. This means task is already
        scheduled with the given parameters.
        :param pre_processed_data:
        :return: id of task on scheduler_service
        :rtype: str
        :exception: Invalid usage

        **See Also**
        .. see also:: endpoints /v1/campaigns/:id/schedule in v1_sms_campaign_api.py
        """
        if not isinstance(pre_processed_data, dict):
            raise InvalidUsage('pre_processed_data should be a dict.')
        scheduled_task = pre_processed_data.get('scheduled_task')
        # If task is not already scheduled
        if not scheduled_task:
            return None
        need_to_create_new_task = False
        # Check if all the scheduler parameters are same as saved in database
        data_to_schedule = pre_processed_data['data_to_schedule']
        # check if already created task is one_time
        if scheduled_task['task_type'] == SchedulerUtils.ONE_TIME:
            # Task was one_time, user wants to change the start datetime
            if scheduled_task['run_datetime'] != data_to_schedule.get('start_datetime'):
                need_to_create_new_task = True
            # Task was one_time, user wants to make it periodic
            elif data_to_schedule.get('frequency'):
                need_to_create_new_task = True
        if scheduled_task['task_type'] == SchedulerUtils.PERIODIC:
            # Task was periodic, user wants to make it one_time
            if not data_to_schedule.get('frequency'):
                need_to_create_new_task = True
            # Task was periodic, user wants to change the parameters
            if scheduled_task['start_datetime'] != data_to_schedule.get('start_datetime') \
                    or scheduled_task['end_datetime'] != data_to_schedule.get('end_datetime') \
                    or scheduled_task['frequency'] != data_to_schedule['frequency']:
                need_to_create_new_task = True
        if need_to_create_new_task:
            # First delete the old schedule of campaign
            unscheduled = delete_scheduled_task(scheduled_task['id'],
                                                pre_processed_data['oauth_header'])
            if not unscheduled:
                return None
        else:
            current_app.config[TalentConfigKeys.LOGGER].info(
                'Task(id:%s) is already scheduled with given data.' % scheduled_task['id'])
            return scheduled_task['id']

    def send(self, campaign_id):
        """
        :param campaign_id: id of SMS campaign obj or push campaign etc
        :type campaign_id: int | long
        :exception: InvalidUsage

        ..Error Codes:: 5101 (EMPTY_BODY_TEXT)
                        5102 (NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN)
                        5103 (NO_CANDIDATE_ASSOCIATED_WITH_SMARTLIST)

        This does the following steps to send campaign to candidates.

        1- Gets the campaign object from database.
        2- Get body_text from campaign obj e,g sms_campaign obj. If body_text is found empty,
            we raise Invalid usage error with custom error code to be EMPTY_BODY_TEXT
        3- Get selected smartlists for the campaign to be sent from campaign_smartlist obj e.g.
            sms_campaign_smartlist obj.
            If no smartlist is found, we raise Invalid usage error with custom error code
            NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN.
        4- Loop over all the smartlists and get candidates from candidate_pool_service and
            candidate_service.
            If no candidate is found associated to all smartlists we raise Invalid usage error
            with custom error code NO_CANDIDATE_ASSOCIATED_WITH_SMARTLIST.

        5- Create SMS campaign blast
        6- Call send_campaign_to_candidates() to send the campaign to candidates via Celery
            task.

        :Example:

            1- Create class object
                from sms_campaign_service.sms_campaign_base import SmsCampaignBase
                camp_obj = SmsCampaignBase(1)

            2- Call method send
                camp_obj.send(1)

        **See Also**
        .. see also:: send_campaign_to_candidates() method in CampaignBase class.
        .. see also:: callback_campaign_sent() method in CampaignBase class.
        .. see also:: callback_campaign_sent() method in CampaignBase class.

        """
        assert_for_int_or_long(dict(campaign_id=campaign_id))
        logger = current_app.config[TalentConfigKeys.LOGGER]
        campaign = self.validate_ownership_of_campaign(campaign_id, self.user.id,
                                                       self.campaign_type)
        assert_is_instance_of_campaign_model(campaign)
        self.campaign = campaign
        campaign_type = self.campaign_type
        logger.debug('send: %s(id:%s) is being sent. User(id:%s)' % (campaign_type,
                                                                             campaign.id,
                                                                             self.user.id))
        if not self.campaign.body_text:
            # body_text is empty
            raise InvalidUsage('Body text is empty for %s(id:%s)' % (campaign_type, campaign.id),
                               error_code=CampaignException.EMPTY_BODY_TEXT)
        # Get smartlists associated to this campaign
        campaign_smartlist_model = get_model(
            campaign_type, snake_case_to_pascal_case(campaign_type) + 'Smartlist')
        smartlists = campaign_smartlist_model.get_by_campaign_id(campaign.id)
        if not smartlists:
            raise InvalidUsage(
                'No smartlist is associated with %s(id:%s). (User(id:%s))'
                % (campaign_type, campaign.id, self.user.id),
                error_code=CampaignException.NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN)
        # get candidates from search_service and filter the None records
        candidates = sum(filter(None, map(self.get_smartlist_candidates, smartlists)), [])
        if not candidates:
            raise InvalidUsage(
                'No candidate is associated with smartlist(s). %s(id:%s). '
                'smartlist ids are %s' % (campaign_type, campaign.id, smartlists),
                error_code=CampaignException.NO_CANDIDATE_ASSOCIATED_WITH_SMARTLIST)
        # create SMS campaign blast
        self.campaign_blast_id = self.create_campaign_blast(self.campaign)
        self.send_campaign_to_candidates(candidates)

    @staticmethod
    def create_campaign_blast(campaign):
        """
        - Here we create blast record for a campaign. We also use this to update
            record with every new send. This gives the statistics about a campaign.
        - This method is called from send() inside CampaignBase.
        This is also called from send_campaign_to_candidate() method of class SmsCampaignBase inside
            sms_campaign_service/sms_campaign_base.py.

        :param campaign: SMS campaign or some other campaign object
        :type campaign: SmsCampaign | PushCampaign etc.
        :return: id of "campaign_blast" record
        :rtype: int

        **See Also**
        .. see also:: send() method in SmsCampaignBase class.

        .. see also:: send_sms_campaign_to_candidates() method in SmsCampaignBase class.
        """
        assert_is_instance_of_campaign_model(campaign)
        campaign_type = campaign.__tablename__
        blast_model = get_model(campaign_type, snake_case_to_pascal_case(campaign_type) + 'Blast')
        blast_obj = blast_model(campaign_id=campaign.id)
        blast_model.save(blast_obj)
        return blast_obj.id

    def get_smartlist_candidates(self, campaign_smartlist):
        """
        This will get the candidates associated to a provided smart list. This makes
        HTTP GET call on candidate service API to get the candidate associated candidates.

        - This method is called from send() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :Example:
                SmsCampaignBase.get_candidates(1)

        :param campaign_smartlist: obj (e.g record of "sms_campaign_smartlist" database table)
        :type campaign_smartlist: object e,g obj of SmsCampaignSmartlist
        :return: Returns array of candidates in the campaign's smartlists.
        :rtype: list
        :exception: Invalid usage
        **See Also**
        .. see also:: send() method in SmsCampaignBase class.
        """
        # other campaigns need to update this
        if not isinstance(campaign_smartlist, SmsCampaignSmartlist):
            raise InvalidUsage('campaign_smartlist obj should be an instance of models %s.'
                               % SmsCampaignSmartlist.__tablename__)
        logger = current_app.config[TalentConfigKeys.LOGGER]
        params = {'return': 'all'}
        # HTTP GET call to candidate_service to get candidates associated with given smartlist id.
        response = http_request('GET', CandidatePoolApiUrl.SMARTLIST_CANDIDATES
                                % campaign_smartlist.smartlist_id,
                                headers=self.oauth_header, params=params, user_id=self.user.id)
        # get candidate ids
        try:
            candidate_ids = [candidate['id'] for candidate in response.json()['candidates']]
            candidates = [Candidate.get_by_id(_id) for _id in candidate_ids]
        except KeyError:
            logger.exception('get_smartlist_candidates: Error while fetching candidates for '
                             'smartlist(id:%s)' % campaign_smartlist.smartlist_id)
            raise
        if not candidates:
            logger.error('get_smartlist_candidates: No Candidate found. smartlist id is %s. '
                         '(User(id:%s))' % (campaign_smartlist.smartlist_id, self.user.id))
        return candidates

    def pre_process_celery_task(self, candidates):
        """
        Here we do any necessary processing before assigning task to Celery. Child classes
        will override this if needed.

         **See Also**
        .. see also:: pre_process_celery_task() method in SmsCampaignBase class.
        :param candidates:
        :return:
        """
        return candidates

    def send_campaign_to_candidates(self, candidates):
        """
        Once we have the candidates, we iterate each candidate, create celery task and call
        self.send_campaign_to_candidate() to send the campaign. Celery sends campaign to all
        candidates asynchronously and if all tasks finish correctly, it hits a callback function
        (self.callback_campaign_sent() in our case) to notify us that campaign has been sent
        to all candidates.

        e.g. This method is called from send() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param candidates: This contains the objects of model Candidate
        :type candidates: list
        :exception: InvalidUsage

        **See Also**
        .. see also:: send() method in SmsCampaignBase class.
        """
        if not candidates:
            raise InvalidUsage('At least one candidate is required to send campaign.')
        try:
            pre_processed_data = self.pre_process_celery_task(candidates)
            # callback is a function which will be hit after campaign is sent to all candidates i.e.
            # once the async task is done the self.callback_campaign_sent will be called
            # When all tasks assigned to Celery complete their execution, following function
            # is called by celery as a callback function.
            # Each service will use its own queue so that tasks related to one service only
            # assign to that particular queue.
            callback = self.callback_campaign_sent.subtask((self.user.id, self.campaign_type,
                                                            self.campaign_blast_id,
                                                            self.oauth_header,),
                                                           queue=self.campaign_type)
            # Here we create list of all tasks and assign a self.celery_error_handler() as a
            # callback function in case any of the tasks in the list encounter some error.
            tasks = [self.send_campaign_to_candidate.subtask(
                (self, record), link_error=self.celery_error_handler.subtask(queue=
                                                                             self.campaign_type)
                , queue=self.campaign_type) for record in pre_processed_data]
            # This runs all tasks asynchronously and sets callback function to be hit once all
            # tasks in list finish running without raising any error. Otherwise callback
            # results in failure status.
            chord(tasks)(callback)
        except Exception:
            current_app.config[TalentConfigKeys.LOGGER].exception(
                'send_campaign_to_candidates: Error while sending tasks to Celery')

    @abstractmethod
    def send_campaign_to_candidate(self, data_to_send_campaign):
        """
        This sends the campaign to given candidate. Child classes will implement this.
        This will be called by Celery worker to send campaigns asynchronously.
        :param data_to_send_campaign: This is the data used by celery task to send campaign
        :type data_to_send_campaign: tuple
        :return:
        """
        pass

    @staticmethod
    @abstractmethod
    def celery_error_handler(uuid):
        """
        This function logs any error occurred for tasks running on celery,
        :return:
        """
        pass

    @staticmethod
    @abstractmethod
    def callback_campaign_sent(sends_result, user_id, campaign_type, blast_id, oauth_header):
        """
        This is the callback function for campaign sent.
        Child classes will implement this.
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
        :return:
        """
        pass

    @classmethod
    def create_campaign_send_activity(cls, user_id, source, oauth_header, num_candidates):
        """
        - Here we set "params" and "type" of activity to be stored in db table "Activity"
            for Campaign sent.

        - Activity will appear as " 'Jobs at Oculus' has been sent to '50' candidates".

        - This method is called from send_sms_campaign_to_candidates() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param user_id: id of user
        :param source: sms_campaign obj
        :param oauth_header: Authorization header
        :param num_candidates: number of candidates to which campaign is sent
        :type user_id: int
        :type source: SmsCampaign
        :type oauth_header: dict
        :type num_candidates: int
        :exception: InvalidUsage

        **See Also**
        .. see also:: send_sms_campaign_to_candidates() method in SmsCampaignBase class.
        """
        assert_is_instance_of_campaign_model(source)
        params = {'name': source.name,
                  'num_candidates': num_candidates}
        cls.create_activity(user_id,
                            _type=ActivityMessageIds.CAMPAIGN_SEND,
                            source_id=source.id,
                            source_table=source.__tablename__,
                            params=params,
                            auth_header=oauth_header)

    @classmethod
    def pre_process_url_redirect(cls, request_args, requested_url):
        """
        This does the validation of signed URL.
        :param request_args: arguments in request
        :param requested_url: URL on which candidate clicks
        :type request_args: dict
        :return:
        """
        if not isinstance(request_args, dict):
            raise InvalidUsage('request args must be passed as dict.',
                               error_code=InvalidUsage.http_status_code())
        missing_item = find_missing_items(request_args, ['auth_user', 'signature', 'valid_until'])
        if missing_item:
            raise InvalidUsage('Requested URL %s has required field(s) missing. %s'
                               % (requested_url, missing_item),
                               error_code=InvalidUsage.http_status_code())
        result = validate_signed_url(request_args)
        if not result:
            raise InvalidUsage("request from URL %s was not verified." % requested_url,
                               error_code=InvalidUsage.http_status_code())
        current_app.config[TalentConfigKeys.LOGGER].info("Requested URL %s has been verified."
                                                         % requested_url)

    @classmethod
    def process_url_redirect(cls, url_conversion_id, campaign_type, verify_signature=False,
                             request_args=None, requested_url=None):
        """
        When candidate clicks on a URL present in any campaign e.g. in SMS, Email etc. it is
        redirected to our app first to keep track of number of clicks, hit_count and to create
        activity e.g. Mitchel clicked on SMS campaign 'Jobs'.
        From given url_conversion_id, we

        1- Get the "url_conversion" obj from db
        2- Get the campaign_send_url_conversion obj (e.g. "sms_campaign_send_url_conversion" obj)
            from db
        3- Get the campaign_blast obj (e.g "sms_campaign_blast" obj) using SQLAlchemy relationship
            from obj found in step-2
        4- Get the candidate obj using SQLAlchemy relationship from obj found in step-2
        5- Validate if all the objects are present in database
        6- If destination URL of object found in step-1 is empty, we raise invalid usage error.
            Otherwise we move on to update the stats.
        7- Call update_stats_and_create_click_activity() class method to do the following:
            7.1- Increase "hit_count" by 1 for "url_conversion" record.
            7.2- Increase "clicks" by 1 for "sms_campaign_blast" record.
            7.3- Add activity that abc candidate clicked on xyz campaign.
                "'Alvaro Oliveira' clicked URL of campaign 'Jobs at Google'"
        6- return the destination URL (actual URL provided by recruiter(user)
            where we want our candidate to be redirected.

        In case of any exception raised, it must be catch nicely and candidate should only get
            internal server error.

    **How to use this method**
        To use this method, one need to
            1- Make sure following model classes have been defined for that campaign
                (e.g. for push campaign, we must have following model classes defined and proper
                relationships added)
                2.1. PushCampaign
                2.2. PushCampaignBlast
                2.3. PushCampaignSend
                2.4. PushCampaignSmartlist
                2.5. PushCampaignSendUrlConversion
            2- Need to pass url_conversion id and name of the campaign as
                    CampaignBase.process_url_redirect(1, 'sms_campaign')

        :Example:
                In case of SMS campaign, this method is used as

                redirection_url = CampaignBase.process_url_redirect(1, 'sms_campaign')
                return redirect(redirection_url)

        .. Status:: 200 (OK)
                    400 (Invalid Usage)
                    403 (Forbidden error)
                    404 (Resource not found)
                    500 (Internal Server Error)

        :param url_conversion_id: id of url_conversion record
        :param campaign_type: name of campaign in snake_case
        :param verify_signature: Indicator to validate signed_url
        :param request_args: arguments of request
        :param requested_url: URL at which candidate clicks
        :type url_conversion_id: int
        :type campaign_type: str
        :type request_args: dict
        :type requested_url: str
        :return: URL where to redirect the candidate
        :rtype: str

        **See Also**
        .. see also:: SmsCampaignUrlRedirection() class in
                    sms_campaign_service/sms_campaign_app/v1_sms_campaign_api.py
        """
        current_app.config[TalentConfigKeys.LOGGER].debug(
            'process_url_redirect: Processing for URL redirection(id:%s).' % url_conversion_id)
        if verify_signature:  # Need to validate the signed URL
            cls.pre_process_url_redirect(request_args, requested_url)
        campaign_send_url_conversion_model = get_model(
            campaign_type, snake_case_to_pascal_case(campaign_type) + 'SendUrlConversion')
        campaign_send_url_conversion_obj = campaign_send_url_conversion_model.query.filter_by(
            url_conversion_id=url_conversion_id).first()
        if not campaign_send_url_conversion_obj:
            raise ResourceNotFound(
                'process_url_redirect: campaign_send_url_conversion_obj not found for '
                'url_conversion(id:%s)' % url_conversion_id)
        # get candidate obj, url_conversion obj, campaign_send obj and get campaign_blast obj
        candidate_obj, url_conversion_obj, campaign_send_obj, campaign_blast_obj = \
            get_candidate_url_conversion_campaign_send_and_blast_obj(
                campaign_send_url_conversion_obj)
        # Validate if all the required items are present in database.
        campaign_obj = validate_blast_candidate_url_conversion_in_db(campaign_blast_obj,
                                                                     candidate_obj,
                                                                     url_conversion_obj)
        if not url_conversion_obj.destination_url:
            raise EmptyDestinationUrl('process_url_redirect: Destination_url is empty for '
                                      'url_conversion(id:%s)' % url_conversion_obj.id)
        # Update hit_count, number of clicks and create activity
        cls.update_stats_and_create_click_activity(campaign_blast_obj, candidate_obj,
                                                   url_conversion_obj, campaign_obj)
        # return URL to redirect candidate to actual URL
        return url_conversion_obj.destination_url

    @classmethod
    def update_stats_and_create_click_activity(cls, campaign_blast_obj, candidate,
                                               url_conversion_obj, campaign_obj):
        """
        When a candidate is redirected to our app, we use this method to

        1)  update the hit_count in 'url_conversion' table by 1
        2)  update the clicks in campaign blast table by 1
        3)  call create_campaign_clicked_activity() to create activity that
                "Jordan has clicked on SMS campaign 'Job Openings'"
        :param campaign_blast_obj: campaign blase obj
        :param candidate: candidate obj
        :param url_conversion_obj: url_conversion obj
        :param campaign_obj: campaign obj
        :type campaign_blast_obj: SmsCampaignBlast | PushCampaignBlast
        :type candidate: Candidate
        :type url_conversion_obj: UrlConversion
        :type campaign_obj: SmsCampaign | PushCampaign etc
        """
        # Any new campaign can add the entry in this statement
        if not isinstance(campaign_blast_obj, (SmsCampaignBlast, EmailCampaignBlast)):
            raise InvalidUsage('blast object should be an instance of models %s, %s etc.' %
                               (SmsCampaignBlast.__tablename__, EmailCampaignBlast.__tablename__))
        logger = current_app.config[TalentConfigKeys.LOGGER]
        # update hit_count
        cls.create_or_update_url_conversion(url_conversion_id=url_conversion_obj.id,
                                            increment_hit_count=True)
        # update the number of clicks
        cls.update_campaign_blast(campaign_blast_obj, clicks=True)
        # get oauth_header
        oauth_header = cls.get_authorization_header(candidate.user_id)
        # get activity type id to create activity
        _type = get_activity_message_id_from_name(
            get_activity_message_name(campaign_obj.__tablename__, 'CLICK'))
        # create_activity
        try:
            cls.create_campaign_clicked_activity(campaign_obj, candidate, _type, oauth_header)
        except ConnectionError:
            # In case activity_service is not running, we proceed normally and log the error.
            logger.exception('Error creating campaign clicked activity.')

    @classmethod
    def create_campaign_clicked_activity(cls, source, candidate, _type, oauth_header):
        """
        - Here we set "params" and "type" of activity to be stored in db table "Activity"
            for Campaign URL click.
        - Activity will appear as e.g.
            "Michal Jordan clicked on SMS Campaign "abc". "
        - This method is called from update_stats_and_create_click_activity() method.

        :param source: Campaign obj
        :param candidate: Candidate obj
        :param _type: id of activity message
        :param oauth_header: authorization header to make POST call to activity_service
        :type source: SmsCampaign | PushCampaign etc
        :type candidate: Candidate
        :type _type: int
        :type oauth_header: dict
        :exception: InvalidUsage

        **See Also**
        .. see also:: update_stats_and_create_click_activity() method in CampaignBase class.
        """
        if not isinstance(candidate, Candidate):
            raise InvalidUsage('candidate should be an instance of model Candidate')
        assert_is_instance_of_campaign_model(source)
        params = {'candidate_name': candidate.name, 'campaign_name': source.name}
        # call activity_service to create activity
        cls.create_activity(candidate.user_id,
                            _type=_type,
                            source_id=source.id,
                            source_table=source.__tablename__,
                            params=params,
                            auth_header=oauth_header)
        current_app.config[TalentConfigKeys.LOGGER].info(
            'create_campaign_clicked_activity: candidate(id:%s) clicked on %s(id:%s). '
            '(User(id:%s))' % (candidate.id, source.__tablename__, source.id, candidate.user_id))

    @staticmethod
    def update_campaign_blast(campaign_blast_obj, **kwargs):
        """
        - This updates the stats of a campaign for given campaign blast object.
            kwargs dict looks like e.g.
                    dict(clicks=True, sends=False, replies=False)

        - If we set any attribute say clicks=True, this will update the number of clicks of given
            campaign blast object by 1.
        - This can also update values of multiple attributes provided.

        **Usage**
            For updating clicks of a campaign, we will use this method as
                CampaignBase.update_campaign_blast(campaign_blast_obj, clicks=True)

        - This method is called from send() and send_sms_campaign_to_candidates()
            methods of class SmsCampaignBase inside
            sms_campaign_service/sms_campaign_base.py.

        :param campaign_blast_obj: campaign blast object for which we want to update stats
        :param kwargs: dictionary containing attributes of campaign object to update
        :type campaign_blast_obj: SmsCampaignBlast or EmailCampaignBlast or PushCampaignBlast
        :type kwargs: dict

        **See Also**
        .. see also:: update_stats_and_create_click_activity() method in CampaignBase class.
        """
        # Any new campaign can add the entry in this statement
        if not isinstance(campaign_blast_obj, (SmsCampaignBlast, EmailCampaignBlast)):
            raise InvalidUsage('blast object should be an instance of models %s, %s etc.' %
                               (SmsCampaignBlast.__tablename__, EmailCampaignBlast.__tablename__))
        not_found_attr = None
        for key, value in kwargs.iteritems():
            try:
                # If given attribute has value True, and campaign_obj has that attr and then
                # we update its value by 1
                if hasattr(campaign_blast_obj, key) and value is True:
                    updated_value = getattr(campaign_blast_obj, key) + 1
                    kwargs[key] = updated_value
                # If campaign_obj does not have that attr  we raise Invalid Usage.
                else:
                    not_found_attr = key
                    raise InvalidUsage('%s object has no attribute %s'
                                       % (campaign_blast_obj.__tablename__, key))
            except InvalidUsage:
                # Remove the attributes which are not part of given campaign_blast_object
                del kwargs[not_found_attr]
        if kwargs:
            # Update the campaign_blast stats like sends, clicks
            campaign_blast_obj.query.filter_by(id=campaign_blast_obj.id).update(kwargs)
            db.session.commit()

    @staticmethod
    def create_or_update_url_conversion(destination_url=None, source_url=None, hit_count=0,
                                        url_conversion_id=None, increment_hit_count=False):
        """
        - Here we save the source_url(provided in body text) and the shortened_url
            to redirect to our endpoint in db table "url_conversion".

        - This method is called from process_urls_in_sms_body_text() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param destination_url: link present in body text
        :param source_url: shortened URL of the link present in body text
        :param hit_count: Count of hits
        :param url_conversion_id: id of URL conversion record if needs to update
        :param increment_hit_count: True if needs to increase "hit_count" by 1, False otherwise
        :type destination_url: str
        :type source_url: str
        :type hit_count: int
        :type url_conversion_id: int
        :type increment_hit_count: bool
        :exception: ResourceNotFound
        :exception: ForbiddenError
        :return: id of the url_conversion record in database
        :rtype: int

        **See Also**
        .. see also:: process_urls_in_sms_body_text() method in SmsCampaignBase class.
        """
        data = {'destination_url': destination_url,
                'source_url': source_url,
                'hit_count': hit_count}
        if url_conversion_id:  # record is already present in database
            record_in_db = UrlConversion.get_by_id(url_conversion_id)
            if record_in_db:
                data['destination_url'] = record_in_db.destination_url
                data['source_url'] = source_url if source_url else record_in_db.source_url
                data['hit_count'] = record_in_db.hit_count + 1 if increment_hit_count else \
                    record_in_db.hit_count
                data.update({'last_hit_time': datetime.now()}) if increment_hit_count else ''
                record_in_db.update(**data)
                url_conversion_id = record_in_db.id
            else:
                raise ResourceNotFound(
                    'create_or_update_url_conversion: '
                    'url_conversion(id:%s) not found' % url_conversion_id)
        else:
            missing_required_fields = find_missing_items(data, verify_values_of_all_keys=True)
            if len(missing_required_fields) == len(data.keys()):
                raise ForbiddenError('destination_url/source_url cannot be None.')
            else:
                new_record = UrlConversion(**data)
                UrlConversion.save(new_record)
                url_conversion_id = new_record.id
        return url_conversion_id

    @staticmethod
    def create_activity(user_id, _type, source_table, source_id, params, auth_header):
        """
        - Once we have all the parameters to save the activity in database table "Activity",
            we call "activity_service"'s endpoint /activities/ with HTTP POST call
            to save the activity in db.

        - This method is called from create_sms_send_activity() and
            create_campaign_send_activity() methods of class SmsCampaignBase inside
            sms_campaign_service/sms_campaign_base.py.

        :param user_id: id of user
        :param _type: type of activity (using underscore with type as "type" reflects built in name)
        :param source_table: source table name of activity
        :param source_id: source id of activity
        :param params: params to store for activity
        :param auth_header: Authorization header to make HTTP POST call on activity_service
        :type user_id: int
        :type _type: int
        :type source_table: str
        :type source_id: int
        :type params: dict
        :type auth_header: dict
        :exception: ForbiddenError

        **See Also**
            .. see also:: create_sms_send_activity() method in SmsCampaignBase class.
        """
        if not isinstance(params, dict):
            raise InvalidUsage('params should be dictionary.')
        if not isinstance(auth_header, dict) or not auth_header:
            raise InvalidUsage('auth_header should be dictionary and cannot be empty.')
        assert_for_int_or_long(dict(source_id=source_id, type=_type))
        json_data = json.dumps({'source_table': source_table,
                                'source_id': source_id,
                                'type': _type,
                                'params': params})
        auth_header.update(JSON_CONTENT_TYPE_HEADER)  # Add content-type in header
        # POST call to activity_service to create activity
        http_request('POST', ActivityApiUrl.ACTIVITIES, headers=auth_header,
                     data=json_data, user_id=user_id)
