"""
File contains json data schema used for validating request-body's json object(s)
"""
source_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "source": {
            "type": "object",
            "properties": {
                "notes": {
                    "type": ["string", "null"],
                    "maxLength": 5000
                },
                "description": {
                    "type": "string",
                    "maxLength": 1000
                }
            },
            "required": [
                "description"
            ]
        }
    },
    "required": [
        "source"
    ]
}

custom_fields_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "custom_fields": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer"
                    },
                    "name": {
                        "type": "string"
                    }
                },
                "required": [
                    "name"
                ]
            }
        }
    },
    "required": [
        "custom_fields"
    ]
}

custom_field_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "custom_field": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                }
            },
            "required": [
                "name"
            ]
        }
    },
    "required": [
        "custom_field"
    ]
}

aoi_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "areas_of_interest": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 255
                    }
                },
                "required": [
                    "description"
                ]
            }
        }
    },
    "required": [
        "areas_of_interest"
    ]
}

"""
This script adds the simple hash column which is used by the emailed resume to candidate code.
"""
