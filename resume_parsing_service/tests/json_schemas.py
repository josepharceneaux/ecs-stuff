EMAIL_SCHEMA = {
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "address": {
      "type": "string",
      "format": "email"
    }
  },
  "required": [
    "address"
  ]
}

PHONE_SCHEMA = {
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "value": {
      "type": "string"
    },
    "label": {
      "type": "string"
    }
  },
  "required": [
    "value",
    "label"
  ]
}

EXPERIENCE_SCHEMA = {
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "position": {
      "type": ["string", "null"]
    },
    "organization": {
      "type": ["string", "null"]
    },
    "city": {
      "type": ["string", "null"]
    },
    "country_code": {
      "type": ["string", "null"]
    },
    "start_year": {
      "type": ["integer", "null"]
    },
    "start_month": {
      "type": ["integer", "null"]
    },
    "end_year": {
      "type": ["integer", "null"]
    },
    "end_month": {
      "type": ["integer", "null"]
    },
    "is_current": {
      "type": "boolean"
    },
    "bullets": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "description": {
            "type": ["string", "null"]
          }
        },
        "required": [
          "description"
        ]
      }
    }
  },
  "required": [
    "position",
    "organization",
    "city",
    "country_code",
    "start_year",
    "start_month",
    "end_year",
    "end_month",
    "is_current",
    "bullets"
  ]
}

EDU_SCHEMA = {
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "school_name": {
      "type": ["string", "null"]
    },
    "city": {
      "type": ["string", "null"]
    },
    "country_code": {
      "type": ["string", "null"]
    },
    "degrees": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "type": {
            "type": ["string", "null"]
          },
          "title": {
            "type": ["string", "null"]
          },
          "start_year": {
            "type": ["integer", "null"]
          },
          "start_month": {
            "type": ["integer", "null"]
          },
          "end_year": {
            "type": ["integer", "null"]
          },
          "end_month": {
            "type": ["integer", "null"]
          },
          "gpa_num": {
            "type": ["number", "null"]
          },
          "bullets": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "major": {
                  "type": ["string", "null"]
                },
                "comments": {
                  "type": ["string", "null"]
                }
              },
              "required": [
                "major",
                "comments"
              ]
            }
          }
        },
        "required": [
          "type",
          "title",
          "start_year",
          "start_month",
          "end_year",
          "end_month",
          "gpa_num",
          "bullets"
        ]
      }
    }
  },
  "required": [
    "school_name",
    "city",
    "country_code",
    "degrees"
  ]
}

SKILL_SCHEMA = {
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "name": {
      "type": "string"
    },
    "months_used": {
      "type": ["integer", "null"]
    },
    "last_used_date": {
      "type": ["string", "null"]
    }
  },
  "required": [
    "name",
    "months_used",
    "last_used_date"
  ]
}

ADDRESS_SCHEMA = {
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "address_line_1": {
      "type": ["string", "null"]
    },
    "city": {
      "type": ["string", "null"]
    },
    "country_code": {
      "type": ["string", "null"]
    },
    "zip_code": {
      "type": ["string", "null"]
    }
  },
  "required": [
    "address_line_1",
    "city",
    "country_code",
    "zip_code"
  ]
}
