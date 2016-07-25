"""
This file contains JSON schema for campaigns' scheduling API.
"""
__author__ = 'basit'

campaign_schedule_schema = {
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
