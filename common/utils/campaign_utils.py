"""
This module contains CampaignBase class which provides common methods for
all campaigns like get_campaign_data(), save(), process_send() etc.
Any service can inherit from this class to implement functionality accordingly.
"""

# Standard Library
from abc import ABCMeta
from abc import abstractmethod


class CampaignBase(object):

    __metaclass__ = ABCMeta

    def __init__(self,  *args, **kwargs):
        self.campaign_id = kwargs.get('campaign_id', None)
        self.user_id = kwargs.get('user_id', None)
        self.body_text = None

    @abstractmethod
    def process_send(self):
        """
        This will be used to do the processing to send campaign to candidates
        according to specific campaign. Child class will implement this.
        :return:
        """
        pass

    @abstractmethod
    def get_campaign_data(self):
        """
        This will get the data from the UI according to specific campaign.
        Child class will implement this.
        :return:
        """
        pass

    @staticmethod
    @abstractmethod
    def save(self, form_data):
        """
        This saves the campaign in database table.
        e.g. in sms_campaign or email_campaign etc.
        Child class will implement this.
        :return:
        """
        pass

    @staticmethod
    def schedule(self):
        """
        This actually POST on scheduler_service to schedule a given task.
        This will be common for all campaigns.
        :return:
        """
        pass
