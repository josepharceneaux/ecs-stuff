"""
This modules contains JSON schema for adding server-side-email-clients.

Authors:
    Hafiz Muhammad Basit <basit.gettalent@gmail.com>

"""
EMAIL_CLIENTS_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "host": {
            "type": "string",
            "pattern": "\S",
        },
        "port": {
            "type": ["string", "null"],
        },
        "name": {
            "type": ["string"],
            "pattern": "\S"
        },
        "email": {
            "type": "string",
            "format": "email",
        },
        "password": {
            "type": "string",
            "pattern": "\S",
        }

    },
    "required": ["host", "name", "email", "password"]
}
