from push_campaign_service.common.campaign_services.json_schema.campaign_fields import get_campaign_schema
from push_campaign_service.modules.push_campaign_base import PushCampaignBase

CAMPAIGN_SCHEMA = get_campaign_schema()
CAMPAIGN_SCHEMA['properties'].update({
    "url": {
            "type": "string",
            "pattern": "(http[s]?:\/\/)?([^\/\s]+\/)(.*)",
        }
})

CAMPAIGN_SCHEMA['required'] = PushCampaignBase.REQUIRED_FIELDS