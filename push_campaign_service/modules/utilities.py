from push_campaign_service.common.error_handling import ResourceNotFound, InvalidUsage
from push_campaign_service.common.models.push_campaign import PushCampaignSmartlist
from push_campaign_service.common.models.smartlist import Smartlist


def associate_smart_list_with_campaign(_id, camapaign_id):
    smartlist = Smartlist.get_by_id(_id)
    if not smartlist:
        raise ResourceNotFound('Smartlist was not found with id %s' % _id)
    push_campaign_smartlist = PushCampaignSmartlist(smartlist_id=_id, campaign_id=camapaign_id)
    PushCampaignSmartlist.save(push_campaign_smartlist)


def get_valid_json_data(req):
    data = req.get_json()
    if data is None:
        raise InvalidUsage('No valid JSON data in request. Kindly send request with JSON data and '
                           'application/json content-type header')
    if isinstance(data, dict) and not len(data):
        raise InvalidUsage('POST data is empty. Kindly send required fields.')
    return data
