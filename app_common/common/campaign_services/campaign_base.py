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
import itertools
from abc import ABCMeta
from datetime import datetime, timedelta
from abc import abstractmethod

# Third Party
from celery import chord
from flask import current_app

# Database Models
from ..models.db import db
from ..models.user import (Token, User)
from ..models.candidate import Candidate
from ..models.push_campaign import PushCampaignBlast
from ..models.email_campaign import EmailCampaignBlast
from ..models.misc import (UrlConversion, Frequency, Activity)
from ..models.sms_campaign import (SmsCampaign, SmsCampaignBlast)

# Common Utils
from ..utils.auth_utils import refresh_token
from ..utils.datetime_utils import DatetimeUtils
from ..utils.scheduler_utils import SchedulerUtils
from ..talent_config_manager import TalentConfigKeys
from campaign_utils import (get_model, CampaignUtils)
from ..utils.validators import raise_if_not_instance_of
from custom_errors import (CampaignException, EmptyDestinationUrl)
from ..routes import (ActivityApiUrl, SchedulerApiUrl)
from ..error_handling import (ForbiddenError, InvalidUsage, ResourceNotFound, InternalServerError)
from ..inter_service_calls.candidate_pool_service_calls import get_candidates_of_smartlist
from validators import (validate_form_data,
                        validation_of_data_to_schedule_campaign,
                        validate_blast_candidate_url_conversion_in_db,
                        raise_if_dict_values_are_not_int_or_long)
from ..utils.handy_functions import (http_request, find_missing_items, JSON_CONTENT_TYPE_HEADER,
                                     generate_jwt_headers)


class CampaignBase(object):
    """
    - This is the base class for sending campaign to candidates and to keep track
        of their responses.

    This class contains following methods:

    * __init__():
        This method is called by creating the class object.
        - It takes "user_id" as keyword argument, gets the user object from database and sets
            user object in self.user.
        - It also sets type of campaign in self.campaign_type.
        - If campaign_id is provided, it gets the campaign object from database for given
            campaign type by validating that campaign belongs to logged-in user's domain

    * get_campaign_type(self) [abstract]
        Child classes will implement this to set type of campaign in self.campaign_type

    * get_authorization_header(user_id, bearer_access_token=None): [static]
        This method is used to get authorization header for current user. This header is
        used to communicate with other flask micro services like candidate_service,
        activity_service etc.

    * pre_process_save_or_update(self, form_data):
        This method is used for data validation for saving and updating a campaign.

    * save(self, form_data):
        This method is used to save the campaign in database. (e.g in "sms_campaign" table)

    * update(self, form_data, campaign_id):
        This method is used update campaign in database. (e.g in "sms_campaign" table)

    * create_campaign_smartlist(campaign, smartlist_ids): [static]
        This saves/updates smartlist ids associated with a campaign in database
        table "sms_campaign_smartlist" for SMS campaign. (or some other table for
        other campaign)

    * create_activity_for_campaign_creation(self, source):
        This method is used to create an activity in database table "Activity" when user
        creates a campaign.
            e.g. in case of SMS campaign, activity will appear as
                'Nikola Tesla' created an SMS campaign "We are hiring".

    * get_campaign_and_scheduled_task(cls. campaign_id, current_user)
        This validates that the requested campaign belongs to logged-in user's domain.
        It also return the data of scheduler_task from scheduler_service if the
        campaign was scheduled.

    * get_campaign_if_domain_is_valid(cls, campaign_id, current_user, campaign_type):
        This method verifies if current campaign lies in user's domain.
        If not it raises Forbidden error, otherwise it returns campaign object.

    * get_valid_blast_obj(cls, requested_campaign_id, blast_id, current_user, campaign_type):
        Depending on campaign_type, this method:
            1) gets the campaign object from campaign_id by validating if campaign
                belongs to current user's domain,
            2) gets the valid blast object from blast_id
        and returns blast object.

    * get_domain_id_of_campaign(campaign_obj, current_user_id):[static]
        This returns id of user who created the given campaign obj

    * delete(self, campaign_id)
        This deletes a campaign. If that campaign was scheduled, it first un-schedules the
        campaign from scheduler_service and then deletes campaign from database.

    * create_activity_for_campaign_delete(self, source):
        This adds an activity when user deletes a campaign.
        Activity appears as e.g. "John deleted SMS campaign 'Jobs at getTalent'"

    * data_validation_for_campaign_schedule(cls,request, campaign_id):
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

    * create_campaign_schedule_activity(self, source):
        This adds an activity when user schedules a campaign.
        Activity appears as e.g. "John scheduled an SMS campaign 'Jobs at getTalent'"

    * unschedule(self, data_to_schedule):
        This method is used to un-schedule given campaign using scheduler_service.

    * pre_process_re_schedule(pre_processed_data)
        This method is used to do required processing before re-scheduling a campaign.
        e.g. it checks if task is not present on redis job store, return None.
        Details are given in definition of this method.

    * reschedule(self, _request, campaign_id)
        This method is used to re-schedules a campaign.

    * send(self):
        This method is used send the campaign to candidates. This has the common functionality
        for all campaigns.

    * process_campaign_send(self, celery_result)
        This method flattens candidates' lists and then sends campaign to every candidate by calling
        `send_campaign_to_candidates()`

    * get_smartlist_candidates_via_celery(self, smartlist_id)
        This is an abstract method and child classes will implement it as celery task.
        This method will retrieve smartlist candidates over celery

    * send_callback(celery_result, campaign_obj)
        This method is abstract method and child classes will implement this as celery task.
        This method is called when all celery tasks are done with retrieving candidates of all smartlists. It call
        `process_send_campaign()` method to send campaign to those candidates.

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

    * create_or_update_campaign_send(self, campaign_blast_id, candidate_id, sent_datetime,
                                        campaign_send_model=None):
        This creates a record in database table (e.g. in database table "sms_campaign_send")
        when campaign is send to a candidate.

    * create_or_update_send_url_conversion(self, campaign_send_obj, url_conversion_id):
        This creates a record in database table (e.g. in database table
        "sms_campaign_send_url_conversion") for each URL conversion when campaign is
        send to a candidate.

    * create_campaign_send_activity(cls, user_id, source, oauth_header, num_candidates):
        This method is used to create an activity in database table "Activity" when campaign
        has been sent to all of the candidates.
            e.g.
                Activity will appear as " 'Jobs at Oculus' has been sent to '50' candidates".

    * pre_process_url_redirect(cls, request_args, requested_url)
        When candidates clicks on a campaign URL, it is redirected to our app. In this
        method we verify the signature of the URL.

    * url_redirect(cls, url_conversion_id, campaign_type, verify_signature=False,
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

    * refresh_all_db_objects(self)
        When working with celery tasks, db/model objects get expired. This method attaches them to current session.
        
    """
    __metaclass__ = ABCMeta

    def __init__(self, user_id, campaign_id=None):
        """
        This gets the user object from given user_id and sets it in self.user.
        If campaign id is provided, it gets the campaign object if it belongs to logged-in
        user's domain and sets it in self.campaign.
        :param user_id: Id of logged-in user
        :param campaign_id: Id of campaign object in database
        :type user_id: int | long
        :type campaign_id: int | long | None
        """
        raise_if_dict_values_are_not_int_or_long(dict(user_id=user_id))
        user_obj = User.get_by_id(user_id)
        if not user_obj:
            raise ResourceNotFound('User does not exist in database with id %s.' % user_id)
        self.user = user_obj
        # This gets the access_token of current user to communicate with other services.
        self.oauth_header = self.get_authorization_header(user_id)
        # It will be instance of model e.g. SmsCampaign or PushNotification etc.
        self.campaign = None  # campaign model object to be processed
        self.smartlist_ids = None  # this contains smartlist ids associated with campaign to be processed
        self.campaign_blast_id = None  # Campaign's blast id in database
        self.campaign_type = self.get_campaign_type()
        CampaignUtils.raise_if_not_valid_campaign_type(self.campaign_type)
        if campaign_id:
            self.campaign = self.get_campaign_if_domain_is_valid(campaign_id, self.user,
                                                                 self.campaign_type)

    @abstractmethod
    def get_campaign_type(self):
        """
        This method will be implemented by child to set value of campaign_type.
        campaign_type will be 'sms_campaign', 'push_campaign' etc.
        :rtype: str
        """
        pass

    @property
    def auth_token(self):
        auth_header = self.get_authorization_header(self.user.id)
        return auth_header['Authorization'].replace('Bearer ', '')

    @staticmethod
    def get_authorization_header(user_id, bearer_access_token=None):
        """
        This returns the authorization header containing access token associated
        with current user. We use this access token to communicate with other services,
        like e.g. activity_service to create activity.
        If access_token is provided, we return the auth header, otherwise we get the access token
        from database table "Token" and then return the auth header.
        If access token is not found by these two methods, we raise Forbidden error.

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
            raise_if_dict_values_are_not_int_or_long(dict(user_id=user_id))
            user_token_obj = Token.get_by_user_id(user_id)
            if not user_token_obj:
                raise ResourceNotFound('No auth token record found for user(id:%s)'
                                       % user_id, error_code=ResourceNotFound.http_status_code())

            user_access_token = user_token_obj.access_token
        if not user_access_token:
            raise ForbiddenError('User(id:%s) has no auth token associated.'
                                 % user_id)
        one_minute_later = datetime.utcnow() + timedelta(seconds=60)
        if user_token_obj.expires < one_minute_later:
            user_access_token = refresh_token(user_token_obj)
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
        :return: Model class of campaign, dict of validated data
        :rtype: tuple
        """
        if not isinstance(campaign_data, dict):
            raise InvalidUsage('campaign_data must be a dictionary.')
        if not campaign_data:
            raise InvalidUsage('No data received from UI to save/update campaign.')
        logger = current_app.config[TalentConfigKeys.LOGGER]
        # if frequency_id not provided or is 0, set to id of ONCE
        if not campaign_data.get('frequency_id'):
            campaign_data.update({'frequency_id': Frequency.ONCE})
        required_fields = self.__class__.REQUIRED_FIELDS
        validate_form_data(campaign_data, self.user, required_fields=required_fields)
        logger.info('Campaign data has been validated.')
        validated_data = campaign_data.copy()
        # get respective campaign model. e.g. sms_campaign or push_campaign etc
        campaign_model = get_model(self.campaign_type, self.campaign_type)
        # 'smartlist_ids' is not a field of sms_campaign or push_campaign tables, so
        # need to remove it from data.
        del validated_data['smartlist_ids']
        # If there exists any unexpected field in data from UI, raise invalid usage error.
        unexpected_fields = campaign_model.get_invalid_fields(validated_data)
        if unexpected_fields:
            raise InvalidUsage('Unexpected field(s) `%s` found in data.' % unexpected_fields)
        return campaign_model, validated_data

    def save(self, form_data):
        """
        It gets the data from UI and saves the campaign in database in respective campaign's
        table e.g  "sms_campaign" or "push_campaign" etc. depending upon campaign type.
        It does following steps:
            1- Validates the form data, gets campaign model and invalid_smartlist_ids if any
            2- Save campaign in database
            3- Adds entries in campaign_smartlist table (e.g. "sms_campaign_smartlist" etc)
            4- Create activity that by calling create_activity_for_campaign_creation()
                (e.g "'Harvey Specter' created an SMS campaign: 'Hiring at getTalent'")
        :param form_data: data from UI
        :type form_data: dict
        :return: id of created campaign in db
        :rtype: int | long
        """
        logger = current_app.config[TalentConfigKeys.LOGGER]
        campaign_model, validated_data = self.pre_process_save_or_update(form_data)
        # Save campaign in database table e.g. "sms_campaign"
        campaign_obj = campaign_model(**validated_data)
        campaign_model.save(campaign_obj)
        # Create record in database table e.g. "sms_campaign_smartlist"
        self.create_campaign_smartlist(campaign_obj, form_data['smartlist_ids'])
        # Create activity, and If we get any error, we log it.
        try:
            self.create_activity_for_campaign_creation(campaign_obj, self.user)
        except Exception:
            logger.exception('Error creating campaign creation activity.')
        return campaign_obj.id

    def update(self, form_data, campaign_id):
        """
        Here we will update the existing record.
        This does
            1) validates if campaign belongs to logged-in user's domain and gets the
                campaign object
            2) Validates UI data
            3) Updates the respective campaign record in database

        :param form_data: data of SMS campaign or some other campaign from UI to save
        :param campaign_id: id of "sms_campaign" obj, default None
        :type form_data: dict
        :type campaign_id: int
        :exception: ResourceNotFound
        :return: invalid_smartlist_ids
        :rtype: dict
        """
        campaign_obj = self.get_campaign_if_domain_is_valid(campaign_id, self.user,
                                                            self.campaign_type)
        _, validated_data = self.pre_process_save_or_update(form_data)
        if not campaign_obj:
            raise ResourceNotFound('%s campaign(id=%s) not found.' % (self.campaign_type,
                                                                      campaign_id))
        for key, value in validated_data.iteritems():
            # update old values with new ones if provided, else preserve old ones.
            validated_data[key] = value if value else getattr(campaign_obj, key)
        campaign_obj.update(**validated_data)

    @staticmethod
    def create_campaign_smartlist(campaign, smartlist_ids):
        """
        - Here we save the smartlist ids for an SMS campaign in database table
        "sms_campaign_smartlist" or "push_campaign_smartlist".

        - This method is called from save() method of class CampaignBase.
        :param campaign: sms_campaign obj
        :param smartlist_ids: ids of smartlists
        :exception: InvalidUsage
        :type campaign: SmsCampaign | PushCampaign etc
        :type smartlist_ids: list

        **See Also**
        .. see also:: save() method in CampaignBase class.
        """
        CampaignUtils.raise_if_not_instance_of_campaign_models(campaign)
        campaign_type = campaign.__tablename__
        campaign_smartlist_model = get_model(campaign_type, campaign_type + '_smartlist')
        for smartlist_id in smartlist_ids:
            data = {'smartlist_id': smartlist_id, 'campaign_id': campaign.id}
            db_record = CampaignUtils.get_campaign_smartlist_obj_by_campaign_and_smartlist_id(
                campaign_smartlist_model, campaign.id, smartlist_id)
            if not db_record:
                new_record = campaign_smartlist_model(**data)
                campaign_smartlist_model.save(new_record)

    @classmethod
    def create_activity_for_campaign_creation(cls, source, user):
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
        CampaignUtils.raise_if_not_instance_of_campaign_models(source)
        raise_if_not_instance_of(user, User)
        # set params
        params = {'username': user.name, 'campaign_name': source.name,
                  'campaign_type': CampaignUtils.get_campaign_type_prefix(source.__tablename__)}
        cls.create_activity(user.id, _type=Activity.MessageIds.CAMPAIGN_CREATE, source=source, params=params)

    @classmethod
    def get_campaign_and_scheduled_task(cls, campaign_id, current_user, campaign_type):
        """
        1) verifies that requested campaign belongs to logged-in user's domain
        2) If campaign has scheduler_task_id, it gets the scheduled task data
            from scheduler_service
        :param campaign_id: id of campaign
        :param current_user: logged-in user's object
        :param campaign_type: type of campaign
        :type campaign_id: int | long
        :type current_user: User
        :type campaign_type: str
        :exception: Invalid usage
        :return: This returns the campaign obj, scheduled task data and oauth_header
        :rtype: tuple
        """
        raise_if_dict_values_are_not_int_or_long(dict(campaign_id=campaign_id))
        raise_if_not_instance_of(current_user, User)
        CampaignUtils.raise_if_not_valid_campaign_type(campaign_type)
        # get campaign object
        campaign_obj = cls.get_campaign_if_domain_is_valid(campaign_id, current_user, campaign_type)
        CampaignUtils.raise_if_not_instance_of_campaign_models(campaign_obj)
        # get scheduled_task object and auth headers
        scheduled_task, oauth_header = cls.get_scheduled_task_and_auth_headers(campaign_obj, current_user)
        return campaign_obj, scheduled_task, oauth_header

    @classmethod
    def get_scheduled_task_and_auth_headers(cls, campaign, current_user):
        """
        1) It gets the scheduled task data from scheduler_service
        2) It gets the auth header for logged in user

        :param campaign: Campaign object
        :param current_user: logged-in user's object
        :type campaign: SmsCampaign | PushCampaign | EmailCampaign
        :type current_user: User
        :exception: Invalid usage
        :return: This returns the scheduled task data and oauth_header
        :rtype: tuple
        """
        CampaignUtils.raise_if_not_instance_of_campaign_models(campaign)
        raise_if_not_instance_of(current_user, User)
        oauth_header = cls.get_authorization_header(current_user.id)
        # check if campaign is already scheduled
        scheduled_task = cls.is_already_scheduled(campaign.scheduler_task_id, oauth_header)
        return scheduled_task, oauth_header

    @classmethod
    def get_campaign_if_domain_is_valid(cls, campaign_id, current_user, campaign_type):
        """
        This function returns campaign object if campaign lies in the domain of logged-in user.
        Otherwise it raises the Forbidden error.
        :param campaign_id: id of campaign form getTalent database
        :param current_user: logged in user's object
        :type campaign_id: int | long
        :type current_user: User
        :exception: ForbiddenError
        :return: Campaign obj if campaign belongs to user's domain
        :rtype: SmsCampaign or some other campaign obj
        """
        raise_if_not_instance_of(campaign_id, (int, long))
        CampaignUtils.raise_if_not_valid_campaign_type(campaign_type)
        raise_if_not_instance_of(current_user, User)
        campaign_obj = CampaignUtils.get_campaign(campaign_id, current_user.domain_id,
                                                  campaign_type)
        domain_id_of_campaign = cls.get_domain_id_of_campaign(campaign_obj,
                                                              current_user.domain_id)
        if domain_id_of_campaign == current_user.domain_id:
            return campaign_obj
        else:
            raise ForbiddenError('%s(id:%s) does not belong to user(id:%s)`s domain.'
                                 % (campaign_obj.__tablename__, campaign_obj.id,
                                    current_user.id))

    @classmethod
    def get_valid_blast_obj(cls, requested_campaign_id, blast_id, current_user, campaign_type):
        """
        This gets the blast object from SmsCampaignBlast or EmailCampaignBlast database table
        depending on campaign_type. If no object is found corresponding to given blast_id,
        it raises ResourceNotFound.
        If campaign_id associated with blast_obj is not same as the requested campaign id,
        it raises forbidden error.
        :param requested_campaign_id: Id of requested campaign object
        :param blast_id: Id of blast object of a particular campaign
        :param current_user: logged-in user's object
        :param campaign_type: Type of campaign. e.g. sms_camapign | email_campaign etc
        :type requested_campaign_id: int | long
        :type blast_id: int | long
        :type current_user: User
        :type campaign_type: str
        :exception: ResourceNotFound
        :exception: ForbiddenError
        :return: campaign blast object
        :rtype: SmsCampaignBlast | EmailCampaignBlast
        """
        raise_if_dict_values_are_not_int_or_long(dict(campaign_id=requested_campaign_id,
                                                      blast_id=blast_id))
        raise_if_not_instance_of(current_user, User)
        raise_if_not_instance_of(campaign_type, basestring)
        # Validate that campaign belongs to user's domain
        campaign = cls.get_campaign_if_domain_is_valid(requested_campaign_id, current_user,
                                                       campaign_type)
        blast_model = get_model(campaign_type, campaign_type + '_blast')
        blast_obj = blast_model.get_by_id(blast_id)
        if not blast_obj:
            raise ResourceNotFound("Blast(id:%s) for %s(id:%s) does not exist in database."
                                   % (blast_id, campaign_type, campaign.id))
        if not blast_obj.campaign_id == requested_campaign_id:
            raise ForbiddenError("Blast(id:%s) is not associated with %s(id:%s)."
                                 % (blast_id, campaign_type, requested_campaign_id))
        return blast_obj

    @staticmethod
    def get_domain_id_of_campaign(campaign_obj, current_user_id):
        """
        This returns the domain id of user who created the given campaign.
        Most of the campaigns are created with user_id as foreign key(e.g. Email campaigns and
        Push campaigns). So, in this method, we return domain id of user using relationship of
        flask SQLAlchemy.
        If some other campaign (e,g. SMS campaign) has no user_id in it, then that campaign
        has to override this method as per its requirement.
        :param campaign_obj: campaign object
        :param current_user_id: id of logged-in user
        :type campaign_obj: SmsCampaign
        :type current_user_id: int | long
        :exception: Invalid Usage
        :return: id of domain of user who created given campaign
        :rtype: int | long

        **See Also**
            .. see also:: get_domain_id_of_campaign() in SmsCampaignBase class.
        """
        CampaignUtils.raise_if_not_instance_of_campaign_models(campaign_obj)
        if not campaign_obj.user_id:
            raise ForbiddenError('%s(id:%s) has no user_id associated. User(id:%s)'
                                 % (campaign_obj.__tablename__, campaign_obj.id,
                                    current_user_id))
        # using relationship
        return campaign_obj.user.domain_id

    def delete(self, commit_session=True):
        """
        This function is used to delete the campaign in following given steps.
        1- Calls get_campaign_and_scheduled_task() method to validate that requested campaign
         belongs to logged-in user's domain and gets
            1) campaign object and 2) scheduled task from scheduler_service.
        2- If campaign is scheduled, then do the following steps:
            2.1- Calls get_authorization_header() to get auth header (which is used to make
                HTTP request to scheduler_service)
            2.2- Makes HTTP DELETE request to scheduler service to remove the job from redis job
                store.
            If both of these two steps are successful, it returns True, otherwise returns False.
        3- Deletes the campaign from database and returns False if campaign is not deleted
            successfully.
        4- Finally we add an activity that (e.g)
            'Jordan deleted an SMS campaign 'Jobs at getTalent'

        :Example:

             In case of SMS campaign, this method is used as

            >>> from sms_campaign_service.modules.sms_campaign_base import SmsCampaignBase
            >>> campaign_obj =  SmsCampaignBase(int('user_id'), int('campaign_id'))
            >>> campaign_obj.delete()
        :param bool commit_session: True if we want to commit the session per deletion
        :exception: Forbidden error (status_code = 403)
        :exception: Resource not found error (status_code = 404)
        :exception: Invalid Usage (status_code = 400)
        :return: Raises InternalServerError if record is not deleted successfully from database.

        **See Also**
        .. see also:: endpoints /v1/sms-campaigns/:id in v1_sms_campaign_api.py
        """
        CampaignUtils.raise_if_not_instance_of_campaign_models(self.campaign)
        raise_if_not_instance_of(self.user, User)
        logger = current_app.config[TalentConfigKeys.LOGGER]
        # get scheduled_task data and oauth_header
        scheduled_task, oauth_header = self.get_scheduled_task_and_auth_headers(self.campaign, self.user)
        # campaign object has scheduler_task_id assigned
        if scheduled_task:
            # campaign was scheduled, remove task from scheduler_service
            unscheduled = CampaignUtils.delete_scheduled_task(scheduled_task['id'], oauth_header)
            if not unscheduled:
                return False
        campaign_model = get_model(self.campaign_type, self.campaign_type)
        if not campaign_model.delete(self.campaign, app=current_app, commit_session=commit_session):
            logger.error("%s(id:%s) couldn't be deleted." % (self.campaign_type, self.campaign.id))
            raise InternalServerError("%s(id:%s) couldn't be deleted." % (self.campaign_type, self.campaign.id),
                                      error_code=CampaignException.ERROR_DELETING_CAMPAIGN)
        try:
            self.create_activity_for_campaign_delete(self.campaign)
        except Exception:
            # In case activity_service is not running, we proceed normally and log the error.
            logger.exception('delete: Error creating campaign delete activity.')
        logger.info('delete: %s(id:%s) has been deleted successfully.' % (self.campaign_type, self.campaign.id))

    def create_activity_for_campaign_delete(self, source):
        """
        - when a user deletes a campaign, here we set "params" and "type" of activity to
            be stored in db table "Activity" when a user deletes a campaign.
        - Activity will appear as " Michal has deleted an SMS campaign 'Jobs at Oculus'.
        - This method is called from delete() method of class CampaignBase.
        :param source: sms_campaign (or some other campaign) obj
        :type source: SmsCampaign
        :exception: InvalidUsage

        **See Also**
        .. see also:: schedule() method in CampaignBase class.
        """
        # any other campaign will update this line
        CampaignUtils.raise_if_not_instance_of_campaign_models(source)
        raise_if_not_instance_of(self.user, User)
        # Activity message looks like %(username)s deleted a campaign: %(name)s"
        params = {'username': self.user.name, 'name': source.name,
                  'campaign_type': CampaignUtils.get_campaign_type_prefix(source.__tablename__)}
        self.create_activity(
            self.user.id,
            _type=Activity.MessageIds.CAMPAIGN_DELETE,
            source=source,
            params=params
        )

    @classmethod
    def data_validation_for_campaign_schedule(cls, request, campaign_id, campaign_type):
        """
        Here we have common functionality for scheduling/re-scheduling a campaign.
        Before making HTTP POST/GET call on scheduler_service, we do the following:

        1- Check if requested campaign belongs to logged-in user's domain
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
        .. see also:: endpoints /v1/sms-campaigns/:id/schedule in v1_sms_campaign_api.py
        """
        CampaignUtils.raise_if_not_valid_campaign_type(campaign_type)
        # get campaign obj, scheduled task data and oauth_header
        campaign_obj, scheduled_task, oauth_header = \
            cls.get_campaign_and_scheduled_task(campaign_id, request.user,
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
        .. see also:: get_campaign_and_scheduled_task() defined in this file.
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
        We set URL (on which scheduler_service will hit when the time comes to run that Job)
        in child class and call super constructor to make HTTP POST call to scheduler_service.

        e.g, in case of SMS campaign, we have
        data_to_schedule = {
                            'frequency': 0,
                            'frequency_id': 0,
                            'start_datetime': '2016-10-30T17:55:00Z',
                            'end_datetime': '2016-12-30T17:55:00Z',
                            'url_to_run_task': 'http://127.0.0.1:8012/v1/sms-campaigns/1/send',
                            'task_type': 'one_time',
                            'data_to_post': None
                            }
        The validation of data_to_schedule is done inside data_validation_for_campaign_schedule() class method.
        Once campaign has been scheduled, we create an activity e.g.
            SMS campaign 'Jobs at getTalent' has been scheduled

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
        logger = current_app.config[TalentConfigKeys.LOGGER]
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
            try:
                self.create_campaign_schedule_activity(self.user, self.campaign, self.oauth_header)
            except Exception:
                # In case activity_service is not running, we proceed normally and log the error.
                logger.exception('Error creating campaign clicked activity.')
            logger.info('%s(id:%s) has been scheduled.' % (self.campaign_type,
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
        - The validation of data_to_schedule is done inside data_validation_for_campaign_schedule() class method.
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
            DatetimeUtils.validate_datetime_format(data_to_schedule['start_datetime'])
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
        CampaignUtils.raise_if_not_instance_of_campaign_models(source)
        raise_if_not_instance_of(user, User)
        params = {'username': user.name,
                  'campaign_type': CampaignUtils.get_campaign_type_prefix(source.__tablename__),
                  'campaign_name': source.name}
        cls.create_activity(user.id,
                            _type=Activity.MessageIds.CAMPAIGN_SCHEDULE,
                            source=source,
                            params=params)

    @classmethod
    def unschedule(cls, campaign_id, request, campaign_type):
        """
        This function gets the campaign object, and checks if it is present on scheduler_service.
        If campaign is present on scheduler_service, we delete it there and on success we return
            campaign object, otherwise we return None.
        :param campaign_id: id of campaign
        :param request: request from UI
        :param campaign_type: type of campaign. e.g. sms_campaign etc
        :type campaign_id: int | long
        :type request: request
        :type campaign_type: str
        :return: status of deleting a task
        :rtype: bool
        :exception: Invalid usage
        """
        if not campaign_id:
            raise InvalidUsage('Campaign id is required to unschedule it.')
        if not hasattr(request, 'user'):
            raise InvalidUsage('User cannot be None for un scheduling a campaign.')
        CampaignUtils.raise_if_not_valid_campaign_type(campaign_type)
        is_deleted = False
        campaign_obj, scheduled_task, oauth_header = \
            cls.get_campaign_and_scheduled_task(campaign_id, request.user, campaign_type)
        if scheduled_task:
            is_deleted = CampaignUtils.delete_scheduled_task(scheduled_task['id'], oauth_header)
            campaign_obj.update(scheduler_task_id=None) if is_deleted else None
        return is_deleted

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
        :param pre_processed_data: It looks like

                        {
                            'campaign': campaign_obj,
                            'data_to_schedule': data_to_schedule_campaign,
                            'scheduled_task': scheduled_task,
                            'oauth_header': oauth_header
                        }

        :return: id of task on scheduler_service
        :rtype: str
        :exception: Invalid usage

        **See Also**
        .. see also:: endpoints /v1/sms-campaigns/:id/schedule in v1_sms_campaign_api.py
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
        elif scheduled_task['task_type'] == SchedulerUtils.PERIODIC:
            # Task was periodic, user wants to make it one_time
            if not data_to_schedule.get('frequency'):
                need_to_create_new_task = True
            # Task was periodic, user wants to change the parameters
            if scheduled_task['start_datetime'] != data_to_schedule.get('start_datetime') \
                    or scheduled_task['end_datetime'] != data_to_schedule.get('end_datetime') \
                    or scheduled_task['frequency'] != data_to_schedule['frequency']:
                need_to_create_new_task = True
        else:
            raise InvalidUsage("Unknown task_type provided. It should be %s or %s."
                               % (SchedulerUtils.ONE_TIME, SchedulerUtils.PERIODIC))
        if need_to_create_new_task:
            # First delete the old schedule of campaign
            unscheduled = CampaignUtils.delete_scheduled_task(scheduled_task['id'],
                                                              pre_processed_data['oauth_header'])
            if not unscheduled:
                return None
        else:
            current_app.config[TalentConfigKeys.LOGGER].info(
                'Task(id:%s) is already scheduled with given data.' % scheduled_task['id'])
            return scheduled_task['id']

    def reschedule(self, _request, campaign_id):
        """
        This re-schedules given a campaign for given campaign_id.
        It does following steps:
            1) Calls data_validation_for_campaign_schedule() to validate UI data
            2) Calls pre_process_re_schedule() to check if task is already scheduled with given
                data or we need to schedule new one.
            3) If we need to schedule again, we call schedule() method.

        :param _request: request from UI
        :param campaign_id: id of campaign
        :type campaign_id: int | long
        :return:
        """
        task_id = None
        # validate data to schedule
        pre_processed_data = self.data_validation_for_campaign_schedule(_request, campaign_id,
                                                                        self.campaign_type)
        self.campaign = pre_processed_data['campaign']
        # check if task is already present on scheduler_service
        scheduled_task_id = self.pre_process_re_schedule(pre_processed_data)
        # Task not found on scheduler_service, need to schedule the campaign
        if not scheduled_task_id:
            task_id = self.schedule(pre_processed_data['data_to_schedule'])
        return task_id

    def send(self):
        """
        This does the following steps to send campaign to candidates.

        1- Validates that campaign object belongs to valid campaign database tables e.g
            'sms_campaign or push_campaign' etc
        2- Get body_text from campaign obj e.g. sms_campaign obj. If body_text is found empty,
            we raise Invalid usage error with custom error code to be EMPTY_BODY_TEXT
        3- Get selected smartlists for the campaign to be sent from campaign_smartlist obj e.g.
            sms_campaign_smartlist obj.
            If no smartlist is found, we raise Invalid usage error with custom error code
            NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN.
        4- Loop over all the smartlists and get candidates from candidate_pool_service and
            candidate_service.
            If no candidate is found associated to all smartlists we raise Invalid usage error
            with custom error code NO_CANDIDATE_ASSOCIATED_WITH_SMARTLIST.
        5- Create campaign blast record in e.g. sms_campaign_blast database table.
        6- Call send_campaign_to_candidates() to send the campaign to candidates via Celery
            task.
        :Example:

            1- Create class object
                >>> from sms_campaign_service.modules.sms_campaign_base import SmsCampaignBase
                >>> camp_obj = SmsCampaignBase(int('user_id'), int('campaign_id'))

            2- Call method send
                >>> camp_obj.send()

        **See Also**
        .. see also:: send_campaign_to_candidates() method in CampaignBase class.
        .. see also:: callback_campaign_sent() method in CampaignBase class.

        :exception: InvalidUsage

        ..Error Codes:: 5101 (EMPTY_BODY_TEXT)
                        5102 (NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN)
                        5103 (NO_CANDIDATE_ASSOCIATED_WITH_SMARTLIST)
        """
        if not isinstance(self.campaign, CampaignUtils.MODELS):
            raise InvalidUsage('campaign object was not set properly')
        logger = current_app.config[TalentConfigKeys.LOGGER]
        logger.debug('send: %s(id:%s) is being sent. User(id:%s)' % (self.campaign_type, self.campaign.id,
                                                                     self.user.id))
        if not self.campaign.body_text:
            # body_text is empty
            raise InvalidUsage('Body text is empty for %s(id:%s)' % (self.campaign_type,
                                                                     self.campaign.id),
                               error_code=CampaignException.EMPTY_BODY_TEXT)
        # Get smartlists associated to this campaign
        campaign_smartlists = self.campaign.smartlists.all()
        if not campaign_smartlists:
            raise InvalidUsage('No smartlist is associated with %s(id:%s). (User(id:%s))' % (self.campaign_type,
                                                                                             self.campaign.id,
                                                                                             self.user.id),
                               error_code=CampaignException.NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN)
        self.smartlist_ids = [campaign_smartlist.smartlist_id for campaign_smartlist in campaign_smartlists]
        # Register function to be called after all candidates are fetched from smartlists
        callback = self.send_callback.subtask((self,), queue=self.campaign_type)

        # Get candidates present in each smartlist
        tasks = [self.get_smartlist_candidates_via_celery.subtask(
            (self, smartlist_id),
            link_error=self.celery_error_handler.subtask(queue=self.campaign_type),
            queue=self.campaign_type) for smartlist_id in self.smartlist_ids]

        # This runs all tasks asynchronously and sets callback function to be hit once all
        # tasks in list finish running without raising any error. Otherwise callback
        # results in failure status.
        chord(tasks)(callback)

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
        CampaignUtils.raise_if_not_instance_of_campaign_models(campaign)
        campaign_type = campaign.__tablename__
        blast_model = get_model(campaign_type, campaign_type + '_blast')
        blast_obj = blast_model(campaign_id=campaign.id)
        blast_model.save(blast_obj)
        return blast_obj.id

    @abstractmethod
    def get_smartlist_candidates_via_celery(self, smartlist_id):
        """
        Child classes will implement this method as celery task because in campaign base there is no celery app.
        This method will retrieve candidates of a smartlist in a celery task.
        :param int | long smartlist_id: campaign smartlist id
        """
        pass

    def get_smartlist_candidates(self, smartlist_id):
        """
        This will get the candidates associated to a provided smart list. This makes
        HTTP GET call on candidate service API to get the candidate associated candidates.

        - This method is called from send() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :Example:
                SmsCampaignBase.get_candidates(1)

        :param int | long smartlist_id: smartlist id
        rtype list[list[Candidate]]
        :return: Returns array of candidates in the campaign's smartlists.
        :rtype: list
        :exception: Invalid usage
        **See Also**
        .. see also:: send() method in SmsCampaignBase class.
        """
        candidates = []
        logger = current_app.config[TalentConfigKeys.LOGGER]
        # As this method is called per smartlist_id for all smartlist_ids associated with
        # a campaign. So, in case iteration for any smartlist_id encounters some error,
        # we just log the error and move on to next iteration. In case of any error, we return
        # empty list.
        try:
            raise_if_not_instance_of(smartlist_id, (int, long))
            candidates_ids = get_candidates_of_smartlist(smartlist_id, candidate_ids_only=True,
                                                         access_token=self.auth_token)
            candidates = [Candidate.get_by_id(candidate_id) for candidate_id in candidates_ids]
        except Exception:
            logger.exception('get_smartlist_candidates: Error while fetching candidates for '
                             'smartlist(id:%s)' % smartlist_id)
        if not candidates:
            logger.error('get_smartlist_candidates: No Candidate found. smartlist id is %s. '
                         '(User(id:%s))' % (smartlist_id, self.user.id))
        return candidates

    @staticmethod
    @abstractmethod
    def send_callback(celery_result, campaign_obj):
        """
        When all celery tasks to retrieve smartlist candidates are finished, celery chord calls respective child
         class' function with an array or data (candidates) from all tasks. Child class' function will further
         call super class method `process_campaign_send` to process this data and send campaigns to all candidates.
        :param list[list[Candidate]] celery_result: list of lists of candidates
        :param PushCampaignBase | SmsCampaignBase campaign_obj: campaign object
        """
        pass

    def process_campaign_send(self, celery_result):
        """
        This method takes `celery_result` input argument which is a list of `lists of candidate ids` and then creates
        campaign blast and sends campaign to all candidates using celery.
        :param list[list[int | long]] list celery_result: list of lists of candidates
        """
        # TODO: correct type as list[list[Candidate]]
        logger = current_app.config[TalentConfigKeys.LOGGER]
        self.refresh_all_db_objects()
        if not celery_result:
            logger.error('No candidate(s) found for smartlist_ids %s, campaign_id: %s'
                         'user_id: %s.' % (self.smartlist_ids, self.campaign.id, self.user.id))
            return

        # gather all candidates from various smartlists
        all_candidates = list(set(itertools.chain(*celery_result)))  # Unique candidates
        # create campaign blast object
        self.campaign_blast_id = self.create_campaign_blast(self.campaign)
        self.send_campaign_to_candidates(all_candidates)

    def pre_process_celery_task(self, candidates):
        """
        Here we do any necessary processing before assigning task to Celery. Child classes
        will override this if needed.

         **See Also**
        .. see also:: pre_process_celery_task() method in SmsCampaignBase class.
        :param candidates:
        """
        # TODO: Add type of param
        if not candidates:
            logger = current_app.config[TalentConfigKeys.LOGGER]
            logger.warn('No candidates with valid data found for %s(id:%s).' % (self.campaign_type, self.campaign.id))
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
            raise InvalidUsage('No candidates with valid data found for %s(id:%s).'
                               % (self.campaign_type, self.campaign.id),
                               error_code=CampaignException.NO_VALID_CANDIDATE_FOUND)
        # TODO:  As discussed with Zohaib, I think type of objects and type of model should be same
        candidates = Candidate.refresh_all(candidates)
        pre_processed_data = self.pre_process_celery_task(candidates)
        try:
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
            # http://ask.github.io/celery/userguide/tasksets.html#chords
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
        """
        pass

    @staticmethod
    @abstractmethod
    def celery_error_handler(uuid):
        """
        This function logs any error occurred for tasks running on celery.
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
        """
        pass

    def create_or_update_campaign_send(self, campaign_blast_id, candidate_id, sent_datetime,
                                       campaign_send_model=None):
        """
        Here we add an entry in campaign send model e.g. "sms_campaign_send" db table
            for campaign send to each candidate.
        This method is called from send_campaign_to_candidate() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param campaign_blast_id: id of sms_campaign_blast
        :param candidate_id: id of candidate to which SMS is supposed to be sent
        :param sent_datetime: Time of sent SMS
        :param campaign_send_model: campaign_send_model of respective campaign | None
        :type campaign_blast_id: int
        :type candidate_id: int
        :type sent_datetime: datetime
        :type campaign_send_model: SmsCampaignSend etc or None
        :return: "sms_campaign_send" record
        :rtype: SmsCampaignSend

        **See Also**
        .. see also:: send_campaign_to_candidate() method in SmsCampaignBase class.
        """
        raise_if_dict_values_are_not_int_or_long(dict(campaign_blast_id=campaign_blast_id,
                                                      candidate_id=candidate_id))
        raise_if_not_instance_of(sent_datetime, datetime)
        # If model is not passed, we import respective model here
        if not campaign_send_model:
            campaign_send_model = get_model(self.campaign_type, self.campaign_type + '_send')
        data = {'blast_id': campaign_blast_id,
                'candidate_id': candidate_id,
                'sent_datetime': sent_datetime}
        record_in_db = CampaignUtils.get_send_obj_by_blast_id_and_candidate_id(campaign_send_model,
                                                                               campaign_blast_id,
                                                                               candidate_id)
        if record_in_db:
            record_in_db.update(**data)
            return record_in_db
        else:
            new_record = campaign_send_model(**data)
            campaign_send_model.save(new_record)
            return new_record

    def create_or_update_send_url_conversion(self, campaign_send_obj, url_conversion_id):
        """
        For every campaign, we need URL conversion to redirect candidate to our app.
        So, For each campaign send, here we add an entry in campaign_send_url_conversion database
            table e.g "sms_campaign_send_url_conversion" etc.
        This method is called from send_campaign_to_candidate() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.
        :param campaign_send_obj: sms_campaign_send obj
        :param url_conversion_id: id of url_conversion record
        :type campaign_send_obj: SmsCampaignSend
        :type url_conversion_id: int

        **See Also**
        .. see also:: send_campaign_to_candidate() method in SmsCampaignBase class.
        """
        raise_if_dict_values_are_not_int_or_long(dict(url_conversion_id=url_conversion_id))
        raise_if_not_instance_of(campaign_send_obj, CampaignUtils.SEND_MODELS)
        # get campaign_send_url_conversion model
        send_url_conversion_model = CampaignUtils.get_send_url_conversion_model(self.campaign_type)
        data = {'send_id': campaign_send_obj.id, 'url_conversion_id': url_conversion_id}
        # get campaign_send_url_conversion object
        record_in_db = CampaignUtils.get_send_url_con_obj_by_send_id_and_url_conversion_id(
            send_url_conversion_model, campaign_send_obj.id, url_conversion_id)
        if not record_in_db:
            new_record = send_url_conversion_model(**data)
            send_url_conversion_model.save(new_record)

    @classmethod
    def create_campaign_send_activity(cls, user_id, source, num_candidates):
        """
        - Here we set "params" and "type" of activity to be stored in db table "Activity"
            for Campaign sent.

        - Activity will appear as " 'Jobs at Oculus' has been sent to '50' candidates".

        - Call this method when a campaign is created some subclass like SmsCampaignBase,
        PushCampaignBase etc.

        :param user_id: id of user
        :param source: sms_campaign | push_campaign obj
        :param num_candidates: number of candidates to which campaign is sent
        :type user_id: int
        :type source: SmsCampaign | PushCampaign | EmailCampaign
        :type num_candidates: int
        :exception: InvalidUsage

        **See Also**
        .. see also:: send_sms_campaign_to_candidates() method in SmsCampaignBase class.
        """
        CampaignUtils.raise_if_not_instance_of_campaign_models(source)
        raise_if_not_instance_of(num_candidates, (int, long))
        params = {'name': source.name, 'num_candidates': num_candidates}
        cls.create_activity(user_id,
                            _type=Activity.MessageIds.CAMPAIGN_SEND,
                            source=source,
                            params=params)

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
        if not CampaignUtils.if_valid_signed_url(request_args):
            raise InvalidUsage("Cannot validate the request from URL %s." % requested_url,
                               error_code=InvalidUsage.http_status_code())
        current_app.config[TalentConfigKeys.LOGGER].info("Requested URL %s has been verified."
                                                         % requested_url)

    @classmethod
    def url_redirect(cls, url_conversion_id, campaign_type, verify_signature=False,
                     request_args=None, requested_url=None):
        """
        When candidate clicks on a URL
        (which looks like http://push-campaign-service/v1/redirect/1052?valid_until=1453990099.0&
            auth_user=no_user&extra=&signature=cWQ43J%2BkYetfmE2KmR85%2BLmvuIw%3D)
        present in any campaign e.g. in SMS, Email etc, it is redirected to our app first to keep
        track of number of clicks, hit_count and to create activity
        (e.g. Mitchel clicked on SMS campaign 'Jobs'.)

        From given url_conversion_id, we
        1- Get the "url_conversion" obj from db
        2- Get the campaign_send_url_conversion obj (e.g. "sms_campaign_send_url_conversion" obj)
            from db
        3- Get the campaign_blast obj (e.g "sms_campaign_blast" obj) using SQLAlchemy relationship
            from obj found in step-2
        4- Get the candidate obj using SQLAlchemy relationship from obj found in step-2
        5- Validate if all the objects (found in steps 2,3,4)are present in database
        6- If destination URL of object found in step-1 is empty, we raise invalid usage error.
            Otherwise we move on to update the stats.
        7- Call update_stats_and_create_click_activity() class method to do the following:
            7.1- Increase "hit_count" by 1 for "url_conversion" record.
            7.2- Increase "clicks" by 1 for "sms_campaign_blast" record.
            7.3- Add activity that abc candidate clicked on xyz campaign.
                "'Alvaro Oliveira' clicked URL of campaign 'Jobs at Google'"
        6- return the destination URL (actual URL provided by recruiter(user)
            where we want our candidate to be redirected.

        In case of any exception raised, it must be caught nicely and candidate should only get
            internal server error.

    **How to use this method**
        To use this method, one need to
            1- Make sure following model classes have been defined for that particular campaign
                (e.g. for "abc" campaign, we must have following model classes defined and proper
                relationships added)
                2.1. AbcCampaign
                2.2. AbcCampaignBlast
                2.3. AbcCampaignSend
                2.4. AbcCampaignSmartlist
                2.5. AbcCampaignSendUrlConversion
            2- Need to pass url_conversion id and name of the campaign as
                    CampaignBase.url_redirect(1, 'sms_campaign')
            You can see for an example of this in models/sms_campaign.py

        :Example:
                In case of SMS campaign, this method is used as

                redirection_url = CampaignBase.url_redirect(1, 'sms_campaign')
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
        CampaignUtils.raise_if_not_valid_campaign_type(campaign_type)
        raise_if_dict_values_are_not_int_or_long(dict(url_conversion_id=url_conversion_id))
        logger = current_app.config[TalentConfigKeys.LOGGER]
        logger.debug('url_redirect: Processing for URL redirection(id:%s).'
                     % url_conversion_id)
        if verify_signature:  # Need to validate the signed URL
            cls.pre_process_url_redirect(request_args, requested_url)
        # get send_url_conversion model for respective campaign
        send_url_conversion_model = CampaignUtils.get_send_url_conversion_model(campaign_type)
        # get send_url_conversion object for respective campaign model
        send_url_conversion_obj = \
            CampaignUtils.get_send_url_conversion_obj_by_url_conversion_id(
                send_url_conversion_model, url_conversion_id)
        if not send_url_conversion_obj:
            raise ResourceNotFound(
                'url_redirect: campaign_send_url_conversion_obj not found for '
                'url_conversion(id:%s)' % url_conversion_id, ResourceNotFound.http_status_code())
        # get candidate obj, url_conversion obj, campaign_send obj and get campaign_blast obj
        # get url_conversion obj
        url_conversion_obj = send_url_conversion_obj.url_conversion
        # get campaign_send object
        campaign_send_obj = send_url_conversion_obj.send
        # get campaign_blast object
        campaign_blast_obj = campaign_send_obj.blast
        # get candidate object
        candidate_obj = campaign_send_obj.candidate
        # Validate if all the required items are present in database.
        campaign_obj = validate_blast_candidate_url_conversion_in_db(campaign_blast_obj,
                                                                     candidate_obj,
                                                                     url_conversion_obj)
        if not url_conversion_obj.destination_url:
            raise EmptyDestinationUrl('url_redirect: Destination_url is empty for '
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
        raise_if_not_instance_of(campaign_blast_obj, CampaignUtils.BLAST_MODELS)
        logger = current_app.config[TalentConfigKeys.LOGGER]
        # update hit_count
        cls.create_or_update_url_conversion(url_conversion_id=url_conversion_obj.id,
                                            increment_hit_count=True)
        # update the number of clicks
        cls.update_campaign_blast(campaign_blast_obj, clicks=True)
        # get oauth_header
        oauth_header = cls.get_authorization_header(candidate.user_id)
        # get activity type id to create activity
        _type = CampaignUtils.get_activity_message_id_from_name(
            CampaignUtils.get_activity_message_name(campaign_obj.__tablename__, 'CLICK'))
        # create_activity
        try:
            cls.create_campaign_clicked_activity(campaign_obj, candidate, _type, oauth_header)
        except Exception:
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
        raise_if_not_instance_of(candidate, Candidate)
        CampaignUtils.raise_if_not_instance_of_campaign_models(source)
        params = {'candidate_name': candidate.name, 'campaign_name': source.name}
        # call activity_service to create activity
        cls.create_activity(candidate.user_id,
                            _type=_type,
                            source=source,
                            params=params)
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
        raise_if_not_instance_of(campaign_blast_obj, CampaignUtils.BLAST_MODELS)
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
            CampaignUtils.update_blast(campaign_blast_obj, kwargs)

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
            missing_required_fields = find_missing_items(data, verify_all=True)
            if len(missing_required_fields) == len(data.keys()):
                raise ForbiddenError('destination_url/source_url cannot be None.')
            else:
                new_record = UrlConversion(**data)
                UrlConversion.save(new_record)
                url_conversion_id = new_record.id
        return url_conversion_id

    @staticmethod
    def create_activity(user_id, _type, source, params):
        """
        - Once we have all the parameters to save the activity in database table "Activity",
            we call "activity_service"'s endpoint /v1/activities/ with HTTP POST call
            to save the activity in db.
        - This makes server-to-server trusted call using JWT as system should create the
            activity, not the user.
        - This method is called from create_sms_send_activity() and
            create_campaign_send_activity() methods of class SmsCampaignBase inside
            sms_campaign_service/sms_campaign_base.py etc.

        :param user_id: id of user
        :param _type: type of activity (using underscore with type as "type" reflects built in name)
        :param source: source object. Basically it will be Model object.
        :param params: params to store for activity
        :type user_id: int
        :type _type: int,
        :type source: SmsCampaign | SmsCampaignBlast etc.
        :type params: dict
        :exception: ForbiddenError

        **See Also**
            .. see also:: create_sms_send_activity() method in SmsCampaignBase class.
        """
        if not isinstance(params, dict):
            raise InvalidUsage('params should be dictionary.')
        raise_if_dict_values_are_not_int_or_long(dict(source_id=source.id, type=_type))
        auth_header = generate_jwt_headers(content_type='application/json',
                                           user_id=user_id)
        json_data = json.dumps({'source_table': source.__tablename__,
                                'source_id': source.id,
                                'type': _type,
                                'params': params})
        # POST call to activity_service to create activity
        http_request('POST', ActivityApiUrl.ACTIVITIES, headers=auth_header,
                     data=json_data, user_id=user_id)

    @staticmethod
    def get_url_conversion_by_send_id(send_id, campaign_type, user):
        model_name = campaign_type + '_send_url_conversion'
        send_url_conversion_model = get_model(campaign_type, model_name)
        send_url_conversion = send_url_conversion_model.query.filter_by(send_id=send_id).first()
        if not send_url_conversion:
            raise ResourceNotFound('Resource not found')
        send = send_url_conversion.send
        if not send:
            raise ResourceNotFound('Resource not found')
        if send.candidate.user.domain_id == user.domain_id:
            url_conversion = send_url_conversion.url_conversion
            return url_conversion
        else:
            raise ForbiddenError("You can not get other domain's url_conversion records")

    # TODO: Maybe this will not be particular for campaigns only, so maybe move this to somewhere more appropriate place
    # TODO: say models_utils.py?
    def refresh_all_db_objects(self):
        """
        In case of celery, when we pass objects from one session to another session, model objects get detached from
        session or get expired, so we need to attach them to current session. In this method, we are getting all model
        objects that are attributes on self and attaching them to current session and updating existing with
        updated values.
        """
        for key in dir(self):
            obj = getattr(self, key)
            if isinstance(obj, db.Model):
                setattr(self, key, db.session.merge(obj))
