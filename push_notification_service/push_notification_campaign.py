from push_notification_service.common.error_handling import *
from push_notification_service.common.models.push_notification import PushNotification, PushNotificationSend
from push_notification_service.common.utils.activity_utils import ActivityMessageIds
from push_notification_service.common.utils.campaign_utils import CampaignBase
from push_notification_service.common.routes import PushNotificationServiceApi
from push_notification_service import logger
from push_notification_service.custom_exceptions import *
from push_notification_service.constants import ONE_SIGNAL_APP_ID, ONE_SIGNAL_REST_API_KEY
from push_notification_service.one_signal_sdk import OneSignalSdk

one_signal_client = OneSignalSdk(app_id=ONE_SIGNAL_APP_ID,
                                 rest_key=ONE_SIGNAL_REST_API_KEY)


class PushNotificationCampaign(CampaignBase):

    def __init__(self, user_id, *args, **kwargs):
        """
        Here we set the "user_id" by calling super constructor.
        :param args:
        :param kwargs:
        :return:
        """
        # sets the user_id
        super(PushNotificationCampaign, self).__init__(user_id, *args, **kwargs)
        self.push_notification = None
        self.subscribed_candidate_ids = []
        self.unsubscribed_candidate_ids = []

    def get_all_campaigns(self):
        """
        This gets all the campaigns created by current user
        :return: all campaigns associated to with user
        :rtype: list
        """
        return PushNotification.get_by_user_id(self.user_id)

    def save(self, form_data):
        """
        This saves the campaign in database table push_notification in following steps:

            1- Save push notification in database
            2 Create activity that
                "%(user_name)s created an Push Notification campaign: '%(campaign_name)s'"

        :param form_data: data from UI
        :type form_data: dict
        :return: id of sms_campaign in db
        :rtype: int
        """
        pass

    def schedule(self, data_to_schedule):
        """
        This method schedules a campaign by sending a POST request to scheduler service.
        :param data_to_schedule:
        :return:
        """
        data_to_schedule.update(
            {'url_to_run_task': PushNotificationServiceApi.SEND % self.campaign.id}
        )
        # get scheduler task_id
        task_id = super(PushNotificationCampaign, self).schedule(data_to_schedule)
        data_to_schedule.update({'task_id': task_id})
        # update push_notification_campaign record with task_id
        self.campaign.update(task_id=task_id)
        return task_id

    def process_send(self, push_notification_id):
        self.push_notification = PushNotification.get_by_id(push_notification_id)
        if self.push_notification:
            cadidates = []
            smartlists = self.push_notification.smartlists
            if not smartlists:
                raise NoSmartlistAssociated('No smartlist is associated with Push Notification '
                                            'Campaign(id:%s). (User(id:%s))' % (self.push_notification.id, self.user_id))
            for smartlist in smartlists:
                cadidates += self.get_smartlist_candidates(smartlist)
            for candidate in cadidates:
                self.send_campaign_to_candidate(candidate)
            return self.subscribed_candidate_ids, self.unsubscribed_candidate_ids
            # device_ids = map(lambda device: device.one_signal_player_id, devices)
            # req = one_signal_client.send_notification(push_notification.url,
            #                                           push_notification.message,
            #                                           push_notification.title,
            #                                           players=device_ids)
            # response = req.json()
            # if req.ok:
            #     one_signal_pn_id = response['id']
            #     push_notification.update(one_signal_id=one_signal_pn_id)
            #     recipients = response['recipients']
            #     logger.info('%s recipients received a pushed notification (id: %s)' % (recipients, push_notification.id))
            #     if 'errors' in response and 'invalid_player_ids' in response['errors']:
            #         unsubscribed_device_ids = response['errors']['invalid_player_ids']
            #         unsubscribed_devices = filter(lambda device: device.one_signal_player_id in unsubscribed_device_ids,
            #                                       devices)
            #         unsubscribed_candidate_ids = map(lambda device: device.candidate_id, unsubscribed_devices)
            #         logger.warn('Push notification (id: %s) was not sent to candidates: %s' % (push_notification.id,
            #                                                                                    unsubscribed_candidate_ids))
            #         subscribed_candidate_ids = set(candidate_ids) - set(unsubscribed_candidate_ids)
            #         return subscribed_candidate_ids, unsubscribed_candidate_ids
            #     return subscribed_candidate_ids, unsubscribed_candidate_ids
            #
            # else:
            #     errors = '\n'.join(response['errors'])
            #     raise PushNotificationNotCreated('Unable to send push notification: Errors: %s' % errors)
        else:
            raise ResourceNotFound('Push notification was not found with id : %s' % push_notification_id)

    @staticmethod
    def callback_campaign_sent(sends_result, user_id, campaign, auth_header):
        """
        This is the callback function for campaign sent.
        Child classes will implement this.
        :param sends_result: Result of executed task
        :param user_id: id of user (owner of campaign)
        :param campaign: id of campaign which was sent to candidates
        :param auth_header: auth header of current user to make HTTP request to other services
        :type sends_result: list
        :type user_id: int
        :type campaign: row
        :type auth_header: dict
        :return:
        """
        pass

    @staticmethod
    # @celery_app.task(name='callback_campaign_sent')
    def callback_campaign_sent(sends_result, user_id, campaign, auth_header):
        """
        Once a Push Notification campaign has been sent to all candidates, this function is hit, and here we

        add activity e.g. (Push Notification Campaign "abc" was sent to "200" candidates")

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
            PushNotificationCampaign.create_campaign_send_activity(user_id,
                                                          campaign, auth_header, total_sends) \
                if total_sends else ''
            logger.debug('process_send: Push Notification Campaign(id:%s) has been sent to %s candidate(s).'
                         '(User(id:%s))' % (campaign.id, total_sends, user_id))
        else:
            logger.error('callback_campaign_sent: Result is not a list')

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
        if not isinstance(source, PushNotification):
            raise InvalidUsage(error_message='source should be an instance of model PushNotification')
        params = {'campaign_name': source.title,
                  'num_candidates': num_candidates}
        cls.create_activity(user_id,
                            type_=ActivityMessageIds.CAMPAIGN_PUSH_NOTIFICATION_CREATE,
                            source_id=source.id,
                            source_table=PushNotification.__tablename__,
                            params=params,
                            headers=auth_header)

    @staticmethod
    def celery_error(error):
        """
        This function logs any error occurred for tasks running on celery,
        :return:
        """
        pass

    def campaign_create_activity(self, source):
        pass

    def send_campaign_to_candidate(self, candidate):
        device_ids = map(lambda device: device.id, candidate.devices)
        if device_ids:
            try:
                resp = one_signal_client.send_notification(self.push_notification.url,
                                                           self.push_notification.messsage,
                                                           self.push_notification.title,
                                                           players=device_ids)
                if resp.ok:
                    push_notification_send = PushNotificationSend.get_by(
                        push_notification_id=self.push_notification.id,
                        candidate_id=candidate.id
                    )
                    self.subscribed_candidate_ids.append(candidate.id)
                    if push_notification_send:
                        sends = push_notification_send.sends + 1
                        push_notification_send.update(sends=sends)
                else:
                    self.unsubscribed_candidate_ids.append(candidate.id)
                    response = resp.json()
                    errors = response['errors']
                    logger.error('Error while sending push notification to candidate (id: %s),'
                                 'Errors: %s' % errors)

            except:
                logger.error('Unable to send push  notification (id: %s) to candidate (id: %s)'
                             % (self.push_notification.id, candidate.id))
                self.unsubscribed_candidate_ids.append(candidate.id)
        else:
            logger.error('Candidate has not subscribed for push notification')
            self.unsubscribed_candidate_ids.append(candidate.id)

