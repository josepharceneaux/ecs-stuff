"""
This module contain PushCampaignVase class which is sub class of CamapignBase.

    PushCampaignBase class contains method that do following actions:
        - __init__():
            Constructor calls supper method to intiliaze default values for a push campaign
        -

"""

# Third Party
from dateutil.relativedelta import relativedelta

# Application Specific
from push_campaign_service.common.error_handling import *
from push_campaign_service.common.models.push_campaign import *
from push_campaign_service.common.models.misc import UrlConversion
from push_campaign_service.common.models.candidate import CandidateDevice, Candidate
from push_campaign_service.common.talent_config_manager import TalentConfigKeys
from push_campaign_service.common.utils.activity_utils import ActivityMessageIds
from push_campaign_service.common.campaign_services.campaign_base import CampaignBase
from push_campaign_service.common.routes import PushCampaignApiUrl

from push_campaign_service.common.models.push_campaign import PushCampaign
from push_campaign_service.push_campaign_app import logger, celery_app, app
from push_campaign_service.common.campaign_services.campaign_utils import (post_campaign_sent_processing,
                                                                           CampaignUtils,
                                                                           sign_redirect_url)
from custom_exceptions import *
from constants import ONE_SIGNAL_APP_ID, ONE_SIGNAL_REST_API_KEY, CELERY_QUEUE
from one_signal_sdk import OneSignalSdk

one_signal_client = OneSignalSdk(app_id=ONE_SIGNAL_APP_ID,
                                 rest_key=ONE_SIGNAL_REST_API_KEY)


class PushCampaignBase(CampaignBase):

    def __init__(self, user_id, *args, **kwargs):
        """
        Here we set the "user_id" by calling super constructor.
        :param args:
        :param kwargs:
        :return:
        """
        # sets the user_id
        super(PushCampaignBase, self).__init__(user_id, *args, **kwargs)
        self.campaign_blast = None
        self.campaign_blast_id = None
        self.queue_name = kwargs.get('queue_name', CELERY_QUEUE)
        self.campaign_type = CampaignUtils.PUSH

    def get_all_campaigns(self):
        """
        This gets all the campaigns created by current user
        :return: all campaigns associated to with user
        :rtype: list
        """
        return PushCampaign.get_by_user_id(self.user_id)

    # @staticmethod
    # def validate_ownership_of_campaign(campaign_id, current_user_id):
    #     """
    #     This function returns True if the current user is an owner for given
    #     campaign_id. Otherwise it raises the Forbidden error.
    #     :param campaign_id: id of campaign form getTalent database
    #     :param current_user_id: Id of current user
    #     :exception: InvalidUsage
    #     :exception: ResourceNotFound
    #     :exception: ForbiddenError
    #     :return: Campaign obj if current user is an owner for given campaign.
    #     :rtype: PushNotification
    #     """
    #     if not isinstance(campaign_id, (int, long)):
    #         raise InvalidUsage(error_message='Include campaign_id as int|long')
    #     campaign_obj = PushCampaign.get_by_id(campaign_id)
    #     if not campaign_obj:
    #         raise ResourceNotFound(error_message='Push Campaign (id=%s) not found.' % campaign_id)
    #     if campaign_obj.user_id == current_user_id:
    #         return campaign_obj
    #     else:
    #         raise ForbiddenError(error_message='You are not the owner of Push campaign(id:%s)' % campaign_id)

    def schedule(self, data_to_schedule):
        """
        This method schedules a campaign by sending a POST request to scheduler service.
        :param data_to_schedule:
        :return:
        """
        data_to_schedule.update(
            {'url_to_run_task': PushCampaignApiUrl.SEND % self.campaign.id}
        )
        # get scheduler task_id
        task_id = super(PushCampaignBase, self).schedule(data_to_schedule)
        data_to_schedule.update({'task_id': task_id})
        # update push_notification_campaign record with task_id
        self.campaign.update(scheduler_task_id=task_id)
        return task_id

    def process_send(self, campaign):
        if not isinstance(campaign, PushCampaign):
            raise InvalidUsage('campaign should be instance of PushCampaign model')

        self.campaign = campaign
        self.campaign_blast = PushCampaignBlast(campaign_id=self.campaign.id)
        PushCampaignBlast.save(self.campaign_blast)
        self.campaign_blast_id = self.campaign_blast.id
        smartlists = campaign.smartlists.all()
        if not smartlists:
            raise NoSmartlistAssociated('No smartlist is associated with Push Campaign (id:%s). '
                                        '(User(id:%s))' % (campaign.id, self.user.id))
        candidates = []
        for smartlist in smartlists:
            try:
                candidates += self.get_smartlist_candidates(smartlist)
            except:
                pass
        if not candidates:
            raise InternalServerError('No candidate associated to campaign', error_code=NO_CANDIDATE_ASSOCIATED)
        print('Sending campaign to candidates')
        self.send_campaign_to_candidates(candidates)

    @celery_app.task(name='send_campaign_to_candidate')
    def send_campaign_to_candidate(self, candidate):
        with app.app_context():
            assert isinstance(candidate, Candidate), '"candidate" should be instance of Candidate Model'
            print('Sending campaign to one candidate')
            logger.info('Going to send campaign to candidate (id: %s)' % candidate.id)
            # A device is actually candidate's desktop, android or ios machine where
            # candidate will receive push notifications. Device id is given by OneSignal.
            devices = CandidateDevice.get_devices_by_candidate_id(candidate.id)
            device_ids = [device.one_signal_device_id for device in devices]
            if not device_ids:
                logger.error('Candidate has not subscribed for push notification')
            else:
                try:
                    destination_url = self.campaign.url
                    url_conversion_id = self.create_or_update_url_conversion(
                        destination_url=destination_url,
                        source_url='')
                    # url_conversion = UrlConversion(source_url='', destination_url=destination_url)
                    # UrlConversion.save(url_conversion)
                    redirect_url = PushCampaignApiUrl.REDIRECT % url_conversion_id
                    expiry_time = datetime.datetime.now() + relativedelta(years=+1)
                    # signed_url = sign_redirect_url(redirect_url, expiry_time)
                    signed_url = sign_redirect_url(redirect_url, expiry_time)
                    if app.config[TalentConfigKeys.IS_DEV]:
                        # update the 'source_url' in "url_conversion" record.
                        # Source URL should not be saved in database. But we have tests written
                        # for Redirection endpoint. That's why in case of DEV, I am saving source URL here.
                        self.create_or_update_url_conversion(url_conversion_id=url_conversion_id,
                                                             source_url=signed_url)
                    # url_conversion.update(source_url=signed_url)
                    response = one_signal_client.send_notification(signed_url,
                                                                   self.campaign.body_text,
                                                                   self.campaign.name,
                                                                   players=device_ids)
                    if response.ok:
                        campaign_send = PushCampaignSend(campaign_blast_id=self.campaign_blast_id,
                                                         candidate_id=candidate.id
                                                         )
                        PushCampaignSend.save(campaign_send)
                        push_url_conversion = PushCampaignSendUrlConversion(
                            url_conversion_id=url_conversion_id,
                            push_campaign_send_id=campaign_send.id
                        )
                        PushCampaignSendUrlConversion.save(push_url_conversion)
                        return True
                    else:
                        response = response.json()
                        errors = response['errors']
                        logger.error('Error while sending push notification to candidate (id: %s),'
                                     'Errors: %s' % errors)
                        UrlConversion.delete(url_conversion_id)

                except Exception as e:
                    logger.exception('Unable to send push  campaign (id: %s) to candidate (id: %s)'
                                     % (self.campaign.id, candidate.id))

    @staticmethod
    @celery_app.task(name='callback_campaign_sent')
    def callback_campaign_sent(sends_result, user_id, campaign_type, blast_id, auth_header):
        """
        Once Push campaign has been sent to all candidates, this function is hit. This is
        a Celery task. Here we

        1) Update number of sends in campaign blast
        2) Add activity e.g. (Push Campaign "abc" was sent to "1000" candidates")

        This uses processing_after_campaign_sent() function defined in
            common/campaign_services/campaign_utils.py

        :param sends_result: Result of executed task
        :param user_id: id of user (owner of campaign)
        :param campaign_type: type of campaign. i.e. sms_campaign or push_campaign
        :param blast_id: id of blast object
        :param auth_header: auth header of current user to make HTTP request to other services
        :type sends_result: list
        :type user_id: int
        :type campaign_type: str
        :type blast_id: int
        :type auth_header: dict

        **See Also**
        .. see also:: send_campaign_to_candidates() method in CampaignBase class inside
                        common/utils/campaign_base.py
        """
        with app.app_context():
            post_campaign_sent_processing(CampaignBase, sends_result, user_id, campaign_type,
                                          blast_id, auth_header)

    @classmethod
    def create_campaign_send_activity(cls, user_id, source, auth_header, num_candidates):
        """
        - Here we set "params" and "type" of activity to be stored in db table "Activity"
            for Campaign sent.

        - Activity will appear as "Push Notification %(campaign_name)s has been sent to %(num_candidates)s candidates".

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
        .. see also:: send_push_notification_campaign_to_candidates() method in PushNotificationCampaign class.
        """
        if not isinstance(source, PushCampaign):
            raise InvalidUsage(error_message='source should be an instance of model PushCampaign')
        params = {'campaign_name': source.name,
                  'num_candidates': num_candidates}
        cls.create_activity(user_id,
                            _type=ActivityMessageIds.CAMPAIGN_PUSH_SEND,
                            source_id=source.id,
                            source_table=PushCampaign.__tablename__,
                            params=params,
                            headers=auth_header)

    def campaign_create_activity(self, source):
        """
        - Here we set "params" and "type" of activity to be stored in db table "Activity"
            for created Campaign.

        - Activity will appear as (e.g)
           "'Harvey Specter' created an Push campaign: 'Hiring at getTalent'"

        - This method is called from save() method of class
            PushCampaignBase inside push_campaign_service/modules/push_campaign_base.py.

        :param source: "push_campaign" obj
        :type source: PushCampaign
        :exception: InvalidUsage

        **See Also**
        .. see also:: save() method in SmsCampaignBase class.
        """
        if not isinstance(source, PushCampaign):
            raise InvalidUsage('source should be an instance of model push_campaign')
        # set params
        params = {'user_name': self.user.name,
                  'campaign_name': source.name}

        self.create_activity(self.user_id,
                             _type=ActivityMessageIds.CAMPAIGN_PUSH_CREATE,
                             source_id=source.id,
                             source_table=PushCampaign.__tablename__,
                             params=params,
                             headers=self.oauth_header)

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
        pass
    #     if not form_data:
    #         logger.error('save: No data received from UI. (User(id:%s))' % self.user_id)
    #     else:
    #         # Save Campaign in database table "sms_campaign"
    #         form_data['user_phone_id'] = self.user_phone.id
    #         push_campaign = self.create_or_update_push_campaign(form_data)
    #         # Create record in database table "sms_campaign_smartlist"
    #         self.create_or_update_push_campaign_smartlist(push_campaign,
    #                                                      form_data.get('smartlist_ids'))
    #         # Create Activity
    #         self.campaign_create_activity(push_campaign)
    #         return push_campaign.id

    @staticmethod
    @celery_app.task(name='celery_error_handler')
    def celery_error_handler(uuid):
        db.session.rollback()



