"""
This modules contains utility functions that are specific to push campaign service.
"""
from push_campaign_service.common.error_handling import ResourceNotFound
from push_campaign_service.common.models.push_campaign import PushCampaignSmartlist
from push_campaign_service.common.models.smartlist import Smartlist


def associate_smart_list_with_campaign(_id, camapaign_id):
    """
    This function associates retrieves a smartlist with given id and then associates
    this smartlist with given push campaign.
    :param _id: smartlist id
    :type _id: int | long
    :param camapaign_id: push campaign id
    :type campaign_id: int | long
    :return:
    """
    smartlist = Smartlist.get_by_id(_id)
    if not smartlist:
        raise ResourceNotFound('Smartlist was not found with id %s' % _id)
    push_campaign_smartlist = PushCampaignSmartlist(smartlist_id=_id, campaign_id=camapaign_id)
    PushCampaignSmartlist.save(push_campaign_smartlist)
