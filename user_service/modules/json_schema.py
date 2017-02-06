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
                },
                "details": {
                    "type": ["string", "null"],
                    "maxLength": 255
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
                    },
                    "category_id": {
                        "type": "integer"
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

cf_categories_schema_post = {
    "type": "object",
    "properties": {
        "custom_field_categories": {
            "type": "array",
            "items": {
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
        }
    },
    "required": [
        "custom_field_categories"
    ]
}

cf_categories_schema_put = {
    "type": "object",
    "properties": {
        "custom_field_categories": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "id": {
                        "type": "integer"
                    }
                },
                "required": [
                    "name",
                    "id"
                ]
            }
        }
    },
    "required": [
        "custom_field_categories"
    ]
}

cf_category_schema_put = {
    "type": "object",
    "properties": {
        "custom_field_category": {
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
        "custom_field_category"
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

source_product_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "source_products": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "notes": {
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
        "source_products"
    ]
}

"""
This script adds the simple hash column which is used by the emailed resume to candidate code.
"""
