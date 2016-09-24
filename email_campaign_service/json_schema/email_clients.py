"""
This modules contains JSON schema for adding server-side-email-clients.

Authors:
    Hafiz Muhammad Basit <basit.gettalent@gmail.com>

"""
EMAIL_CLIENTS_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "host": {
            "type": "string",
            "pattern": "\w",
        },
        "port": {
            "type": ["string", "null"],
        },
        "email": {
            "type": "string",
            "format": "email",
        },
        "password": {
            "type": "string",
            "pattern": "\w",
        },
        "type": {
            "type": "string",
            "pattern": "\w",
        },
        "incoming_server_type": {
            "type": ["string", "null"]
        },

    },
    "required": ["host", "email", "password", "type"]
}
