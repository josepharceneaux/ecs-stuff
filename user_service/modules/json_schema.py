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
