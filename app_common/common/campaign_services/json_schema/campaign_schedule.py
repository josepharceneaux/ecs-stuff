"""
This file contains JSON schema for campaigns' scheduling API.
"""
__author__ = 'basit'

campaign_schedule_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "frequency_id": {
            "type": "integer"
        },
        "start_datetime": {
            "type": "string",
            "format": "date-time"
        },
        "end_datetime": {
            "type": "string",
            "format": "date-time"
        }
    },
    "required": [
        "frequency_id",
        "start_datetime"
    ]
}
