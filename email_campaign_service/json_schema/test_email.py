"""
This modules contains json schema for test email.

Authors:
    Zohaib Ijaz <mzohaib.qc@gmail.com>
"""
TEST_EMAIL_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "email_address_list": {
            "type": "array",
            "minItems": 1,
            "maxItems": 10,
            "uniqueItems": True,
            "items": {
                "type": "string"
            }
        },
        "subject": {
            "type": "string",
            "pattern": "\S",
        },
        "body_html": {
            "type": "string",
            "pattern": "\S",
        },
        "body_text": {
            "type": "string",
            "pattern": "\S",
        },
        "from": {
            "type": "string",
            "pattern": "\S",
        },
        "reply_to": {
            "type": "string",
            "format": "email",
        }
    },
    "required": [
        "email_address_list", "subject", "body_html", "from"
    ]
}
