references_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "required": ["candidate_references"],
    "properties": {
        "candidate_references": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": ["integer", "null"]
                    },
                    "name": {
                        "type": ["string", "null"]
                    },
                    "position_title": {
                        "type": ["string", "null"]
                    },
                    "comments": {
                        "type": ["string", "null"],
                        "maxLength": 5000
                    },
                    "reference_email": {
                        "type": "object",
                        "properties": {
                            "is_default": {
                                "type": ["boolean", "null"]
                            },
                            "address": {
                                "type": ["string", "null"]
                            },
                            "label": {
                                "type": ["string", "null"]
                            }
                        }
                    },
                    "reference_phone": {
                        "type": "object",
                        "properties": {
                            "is_default": {"type": ["boolean", "null"]},
                            "value": {
                                "type": ["string", "null"]
                            },
                            "label": {
                                "type": ["string", "null"]
                            }
                        }
                    },
                    "reference_web_address": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": ["string", "null"]
                            },
                            "description": {
                                "type": ["string", "null"]
                            }
                        }
                    }
                }
            }
        }
    }
}
