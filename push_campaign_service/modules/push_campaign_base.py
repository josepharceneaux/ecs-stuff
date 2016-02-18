"""
This module contain PushCampaignVase class which is sub class of CamapignBase.

    PushCampaignBase class contains method that do following actions:
        - __init__():
            Constructor calls supper method to intiliaze default values for a push campaign

        - get_all_campaigns():
            This method retrieves all push campaigns from getTalent push_campaign table.

        - schedule():
            This method schedules a campaign using Scheduler Service

        - pre_process_celery_task():
            This method is to transform data required for celery tasks to run on.
            In this case, it is creating a list of candidate_ids from candidates,
            as SqlAlchemy objects do not behave well across different sessions

        - send_campaign_to_candidate():
            This method is core of the whole service. It receives a candidate id,
            retrieves candidate, campaign. It creates a blast and then updates it
            after sending a campaign.

        - callback_campaign_sent():
            This method is invoked when campaign has been sent to all associated campaigns.
            This method creates activity for campaign sent.

        - celery_error_handler():
            This method is invoked if some error occurs during sending a campaign
            in celery task. It then rollbacks that transaction.
            (Celery task has it's own scoped session)
"""

# Third Party
from dateutil.relativedelta import relativedelta

# Application Specific
from one_signal_sdk import OneSignalSdk
# Import all model classes from push_campaign module
from push_campaign_service.common.models.push_campaign import *
from push_campaign_service.common.models.misc import UrlConversion
from push_campaign_service.common.routes import PushCampaignApiUrl
from push_campaign_service.push_campaign_app import logger, celery_app, app
from push_campaign_service.common.models.candidate import CandidateDevice, Candidate
from push_campaign_service.common.campaign_services.campaign_base import CampaignBase
from push_campaign_service.common.campaign_services.campaign_utils import CampaignUtils
from constants import ONE_SIGNAL_APP_ID, ONE_SIGNAL_REST_API_KEY, CELERY_QUEUE


one_signal_client = OneSignalSdk(app_id=ONE_SIGNAL_APP_ID,
                                 rest_key=ONE_SIGNAL_REST_API_KEY)


class PushCampaignBase(CampaignBase):

    def __init__(self, user_id, *args, **kwargs):
        """
        Here we set the "user_id" by calling super constructor.
        In this method, initialize all instance attributes.
        :param args:
        :param kwargs:
        :return:
        """
        # sets the user_id
        super(PushCampaignBase, self).__init__(user_id, *args, **kwargs)
        self.campaign_blast = None
        self.campaign_blast_id = None
        self.campaign_id = None
        self.queue_name = kwargs.get('queue_name', CELERY_QUEUE)
        self.campaign_type = CampaignUtils.PUSH

    def get_all_campaigns(self):
        """
        This gets all the campaigns created by current user
        :return: all campaigns associated to with user
        :rtype: list
        """
        return PushCampaign.get_by_user_id(self.user_id)

    def get_campaign_type(self):
        """
        This sets the value of self.campaign_type to be 'sms_campaign'.
        """
        return CampaignUtils.PUSH

    def schedule(self, data_to_schedule):
        """
        This overrides the CampaignBase class method schedule().
        Here we set the value of dict "data_to_schedule" and pass it to
        super constructor to get task_id for us. Finally we update the Push campaign
        record in database table "push_campaign" with
            1- frequency_id
            2- start_datetime
            3- end_datetime
            4- task_id (Task created on APScheduler)
        Finally we return the "task_id".

        - This method is called from the endpoint /v1/campaigns/:id/schedule on HTTP method POST/PUT

        :param data_to_schedule: required data to schedule an Push campaign
        :type data_to_schedule: dict
        :return: task_id (Task created on APScheduler), and status of task(already scheduled
                            or new scheduled)
        :rtype: tuple

        **See Also**
        .. see also:: SchedulePushCampaignResource  in v1_push_campaign_api.py.
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

    def pre_process_celery_task(self, candidates):
        """
        Here we do any necessary processing before assigning task to Celery. Child classes
        will override this if needed.
        :param candidates: list of candidates
        :type candidates: list
        :return:
        """
        return (candidate.id for candidate in candidates)

    @celery_app.task(name='send_campaign_to_candidate')
    def send_campaign_to_candidate(self, candidate_id):
        """
        This method sends campaign to a single candidate. It gets the devices associated with
        the candidate and sends this campaign to all devices using OneSignal Restful Api.
        Destination url is first converted to something like http://127.0.0.1:8012/redirect/1
        which is then signed
            http://127.0.0.1:8012/v1/redirect/1052?valid_until=1453990099.0
            #           &auth_user=no_user&extra=&signature=cWQ43J%2BkYetfmE2KmR85%2BLmvuIw%3D

        This url is sent to candidate in push notification and when user clicks on notification
        he is redirected to our url redirection endpoint, which after updating campaign stats,
        redirected to original url given for campaign owner.
        :param candidate_id: id of candidate in candidate table in getTalent database
        :return:
        """
        with app.app_context():
            candidate = Candidate.get_by_id(candidate_id)
            self.campaign = PushCampaign.get_by_id(self.campaign_id)
            assert isinstance(candidate, Candidate), \
                'candidate should be instance of Candidate Model'
            logger.info('Going to send campaign to candidate')
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
                    # expiry duration is of one year
                    expiry_time = datetime.datetime.now() + relativedelta(years=+1)
                    signed_url = CampaignUtils.sign_redirect_url(redirect_url, expiry_time)
                    if CampaignUtils.IS_DEV:
                        # update the 'source_url' in "url_conversion" record.
                        # Source URL should not be saved in database. But we have tests written
                        # for Redirection endpoint. That's why in case of DEV,
                        # I am saving source URL here.
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
                                     'Errors: %s' % (candidate_id, errors))
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
        :param campaign_type: type of campaign. i.e. push_campaign
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
            CampaignUtils.post_campaign_sent_processing(CampaignBase, sends_result, user_id, campaign_type,
                                          blast_id, auth_header)

    @staticmethod
    @celery_app.task(name='celery_error_handler')
    def celery_error_handler(uuid):
        """
        This method is invoked whenever some error occurs.
        It rollbacks the transaction otherwise it will cause other transactions (if any) to fail.
        :param uuid:
        :return:
        """
        db.session.rollback()

    def save(self, form_data):
        """
        This overrides tha CampaignBase class method. This appends user_phone_id in
        form_data and calls super constructor to save the campaign in database.
        :param form_data: data from UI
        :type form_data: dict
        :return: id of sms_campaign in db, invalid_smartlist_ids and not_found_smartlist_ids
        :rtype: tuple
        """
        form_data['user_id'] = self.user.id
        return super(PushCampaignBase, self).save(form_data)

