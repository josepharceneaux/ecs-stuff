"""
JSON Schemas for validating data sent to Tasks
"""

# Required parameters in JSON data
from scheduler_service import SchedulerUtils

# Schema for validation of both one time and periodic tasks common fields
base_job_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "required": ["url", "task_type"],
    "properties": {
        "task_type": {
            "type": "string",
            "enum": [SchedulerUtils.PERIODIC, SchedulerUtils.ONE_TIME]
        },
        "url": {
            "type": "string"
        }
    }
}

# Required parameters for one_time job
one_time_task_job_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "additionalProperties": False,
    "required": ["url", "task_type", "run_datetime"],
    "properties": {
        "run_datetime": {
            "type": "string",
        },
        "content_type": {
            "type": "string",
            "default": "application/json"
        },
        "task_name": {
            "type": "string"
        },
        "task_type": {
            "type": "string"
        },
        "url": {
            "type": "string"
        },
        "post_data": {
            "type": "object"
        },
        "is_jwt_request": {
            "type": "boolean",
            "default": False
        }
    }
}

# Required parameters for periodic job
periodic_task_job_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "additionalProperties": False,
    "required": ["url", "task_type", "start_datetime", "end_datetime", "frequency", "post_data"],
    "properties": {
        "start_datetime": {
            "type": "string",
        },
        "end_datetime": {
            "type": "string",
        },
        "frequency": {
            "type": "number",
        },
        "content_type": {
            "type": "string",
            "default": "application/json"
        },
        "task_name": {
            "type": "string"
        },
        "task_type": {
            "type": "string"
        },
        "url": {
            "type": "string"
        },
        "post_data": {
            "type": "object"
        },
        "is_jwt_request": {
            "type": "boolean",
            "default": False
        }
    }
}
