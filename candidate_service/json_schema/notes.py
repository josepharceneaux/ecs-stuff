notes_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "additionalProperties": False,
    "required": ["notes"],
    "properties": {
        "notes": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["comment"],
                "properties": {
                    "comment": {"type": "string"}
                }
            }
        }
    }
}
