"""
Author: Zohaib Ijaz, QC-Technologies,
        Lahore, Punjab, Pakistan <mzohaib.qc@gmail.com>

This module contains json schema for Push Campaign data validation.
Required properties are "name", "body_text", "smartlist_ids", and "url".
Schema for first 3 required fields are already defined in common code. We need to add validation for "url" field here.
"""
from push_campaign_service.common.campaign_services.json_schema.campaign_fields import get_campaign_schema
from push_campaign_service.modules.push_campaign_base import PushCampaignBase

# Copy common schema for campaign
CAMPAIGN_SCHEMA = get_campaign_schema()

# Add url as required property with pattern validation.
CAMPAIGN_SCHEMA['properties'].update({
    "url": {
            "type": "string",
            "pattern": "(http[s]?:\/\/)?([^\/\s]+\/)(.*)",
        }
})

# Specify required fields
CAMPAIGN_SCHEMA['required'] = list(PushCampaignBase.REQUIRED_FIELDS)
