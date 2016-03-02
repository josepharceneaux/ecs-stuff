"""
JSON Schemas for validating data sent to Tasks
"""

# Required parameters in JSON data
from scheduler_service import SchedulerUtils

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

# Required parameters for
one_time_task_job_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "required": ["run_datetime"],
    "properties": {
        "run_datetime": [{
            "type": "string",
        }]
    }
}

# Required parameters for
periodic_task_job_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "required": ["start_datetime", "end_datetime", "frequency"],
    "properties": {
        "start_datetime": {
            "type": "date-time",
        },
        "end_datetime": {
            "type": "date-time",
        },
        "frequency": {
            "type": "number",
        }
    }
}
