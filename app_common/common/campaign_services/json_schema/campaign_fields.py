"""
This file contains JSON schema for campaign APIs.
"""
__author__ = 'basit'

campaign_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "name": {
            "type": "string"
        },
        "body_text": {
            "type": "string"
        },
        "smartlist_ids": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": {
                "type": "integer",
            }
        }
    },
    "required": [
        "name",
        "body_text",
        "smartlist_ids"
    ]
}


def get_campaign_schema():
    """
    We usually need three fields 1)name 2)body_text and 3)smartlist_ids to create a campaign e.g. sms_campaign.
    Some other type of campaign may also have an extra required/not-required field in it. Here we return
    basic schema for campaign creation. Any other type of campaign can update this at its end.
    :rtype: dict
    """
    return campaign_schema.copy()
