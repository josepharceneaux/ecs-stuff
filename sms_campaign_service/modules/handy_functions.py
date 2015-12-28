"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com

    Here we have helper functions for SMS campaign service.
"""


# Service specific
from sms_campaign_service.sms_campaign_base import SmsCampaignBase
from sms_campaign_service.custom_exceptions import ErrorDeletingSMSCampaign

# Common utils
from sms_campaign_service.common.error_handling import InvalidUsage
from sms_campaign_service.common.models.sms_campaign import SmsCampaign


def delete_sms_campaign(campaign_id, current_user_id):
    """
    This function is used to delete SMS campaign of a user. If current user is the
    creator of given campaign id, it will delete the campaign, otherwise it will
    raise the Forbidden error.
    :param campaign_id: id of SMS campaign to be deleted
    :param current_user_id: id of current user
    :exception: Forbidden error (status_code = 403)
    :exception: Resource not found error (status_code = 404)
    :exception: ErrorDeletingSMSCampaign
    :exception: InvalidUsage
    :return: True if record deleted successfully, False otherwise.
    :rtype: bool
    """
    if not isinstance(campaign_id, (int, long)):
        raise InvalidUsage(error_message='Include campaign_id as int|long')
    if SmsCampaignBase.validate_ownership_of_campaign(campaign_id, current_user_id):
        deleted = SmsCampaign.delete(campaign_id)
        if not deleted:
            raise ErrorDeletingSMSCampaign("Campaign(id:%s) couldn't be deleted."
                                           % campaign_id)
    return False
