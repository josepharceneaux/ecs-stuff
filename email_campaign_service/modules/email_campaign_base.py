"""
This module contains EmailCampaignBase class
"""
from email_campaign_service.common.campaign_services.campaign_base import CampaignBase
from email_campaign_service.common.campaign_services.campaign_utils import CampaignUtils
from email_campaign_service.common.custom_errors.campaign import (EMAIL_CAMPAIGN_FORBIDDEN,
                                                                  EMAIL_CAMPAIGN_BLAST_FORBIDDEN,
                                                                  EMAIL_CAMPAIGN_NOT_FOUND,
                                                                  EMAIL_CAMPAIGN_BLAST_NOT_FOUND,
                                                                  NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN,
                                                                  NO_VALID_CANDIDATE_FOUND)


# TODO: Will complete class base structure in GET-2500
class EmailCampaignBase(CampaignBase):
    """
    Class containing methods to create/schedule an email-campaign and send that to candidates.
    """
    CAMPAIGN_TYPE = CampaignUtils.EMAIL
    REQUIRED_FIELDS = ('name', 'subject', 'body_html', 'list_ids', 'frequency_id')

    def __init__(self, user_id, campaign_id=None):
        """
        :param positive user_id: Id of logged-in user
        :param positive|None campaign_id: Id of campaign object in database
        """
        # sets the user_id
        super(EmailCampaignBase, self).__init__(user_id, campaign_id=campaign_id)

    class CustomErrors(object):
        """
        This contains custom error codes
        """
        CAMPAIGN_FORBIDDEN = EMAIL_CAMPAIGN_FORBIDDEN
        BLAST_FORBIDDEN = EMAIL_CAMPAIGN_BLAST_FORBIDDEN
        CAMPAIGN_NOT_FOUND = EMAIL_CAMPAIGN_NOT_FOUND
        BLAST_NOT_FOUND = EMAIL_CAMPAIGN_BLAST_NOT_FOUND
        NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN = NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN
        NO_VALID_CANDIDATE_FOUND = NO_VALID_CANDIDATE_FOUND

    def get_campaign_type(self):
        """
        This sets the value of self.campaign_type to be 'email_campaign'.
        """
        return CampaignUtils.EMAIL

    @classmethod
    def create_activity_for_campaign_creation(cls, source, user):
        """
        TODO: Just implementing abstract methods, will complete in GET-2500
        """
        pass

    def create_activity_for_campaign_delete(self, source):
        """
        TODO: Just implementing abstract methods, will complete in GET-2500
        """
        pass

    def get_smartlist_candidates_via_celery(self, smartlist_id):
        """
        TODO: Just implementing abstract methods, will complete in GET-2500
        """
        pass

    @staticmethod
    def send_callback(celery_result, campaign_obj):
        """
        TODO: Just implementing abstract methods, will complete in GET-2500
        """
        pass

    def send_campaign_to_candidate(self, data_to_send_campaign):
        """
        TODO: Just implementing abstract methods, will complete in GET-2500
        """
        pass

    @staticmethod
    def celery_error_handler(uuid):
        """
        TODO: Just implementing abstract methods, will complete in GET-2500
        """
        pass

    @staticmethod
    def callback_campaign_sent(sends_result, user_id, campaign_type, blast_id, oauth_header):
        """
        TODO: Just implementing abstract methods, will complete in GET-2500
        """
        pass
