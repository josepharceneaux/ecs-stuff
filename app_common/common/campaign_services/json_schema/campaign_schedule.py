"""
This file contains JSON schema for campaigns' scheduling API.
"""
__author__ = 'basit'

CAMPAIGN_SCHEDULE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "frequency_id": {
            "type": "integer"
        },
        "start_datetime": {
            "type": "string",
            "format": "date-time"  # TODO: Add custom validator to make sure start_datetime is in future
        },
        "end_datetime": {
            "type": "string",
            "format": "date-time"  # TODO: Add custom validator to make sure end_datetime is ahead of start_datetime
        }
    },
    "required": [
        "frequency_id",
        "start_datetime"
    ]
}

# TODO: I think we should add minValue in frequency_id to be 1