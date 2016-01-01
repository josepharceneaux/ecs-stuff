from push_notification_service.common.error_handling import ResourceNotFound
from push_notification_service.common.models.push_notification import PushCampaignSmartlist
from push_notification_service.common.models.smartlist import Smartlist


def associate_smart_list_with_campaign(_id, camapaign_id):
    smartlist = Smartlist.get_by_id(_id)
    if not smartlist:
        raise ResourceNotFound('Smartlist was not found with id %s' % _id)
    push_campaign_smartlist = PushCampaignSmartlist(smartlist_id=_id, campaign_id=camapaign_id)
    PushCampaignSmartlist.save(push_campaign_smartlist)
