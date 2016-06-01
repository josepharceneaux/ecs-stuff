ccf_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "additionalProperties": False,
    "required": ["candidate_custom_fields"],
    "properties": {
        "candidate_custom_fields": {
            "type": ["array"],
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["custom_field_id", "value"],
                "properties": {
                    "custom_field_id": {
                        "type": ["integer"],
                        "minimum": 1
                    },
                    "value": {
                        "type": ["string", "null"],
                        "minLength": 1,
                        "maxLength": 255
                    }
                }
            }
        }
    }
}
