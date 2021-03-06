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
        "content-type": {
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
            "type": "object",
            "default": {}
        },
        "is_jwt_request": {
            "type": "boolean",
            "default": False
        },
        "request_method": {
            "type": "string",
            "default": "post",
            "enum": ["post", "get", "delete", "patch", "put"]
        }
    }
}

# Required parameters for periodic job
periodic_task_job_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "additionalProperties": False,
    "required": ["url", "task_type", "start_datetime", "end_datetime", "frequency"],
    "properties": {
        "start_datetime": {
            "type": "string",
        },
        "end_datetime": {
            "type": "string",
        },
        "frequency": {
            "type": "number",
            "minimum": SchedulerUtils.MIN_ALLOWED_FREQUENCY
        },
        "content-type": {
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
            "type": "object",
            "default": {}
        },
        "is_jwt_request": {
            "type": "boolean",
            "default": False
        },
        "request_method": {
            "type": "string",
            "default": "post",
            "enum": ["post", "get", "delete", "patch", "put"]
        }
    }
}
