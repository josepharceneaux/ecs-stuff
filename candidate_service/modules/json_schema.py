"""
JSON Schemas for validating data sent to CandidatesResource/post()
"""
candidates_resource_schema_post = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    # "id": "http://jsonschema.net",
    "type": "object",
    "required": ["candidates"],
    "properties": {
        "candidates": {
            # "id": "http://jsonschema.net/candidates",
            "type": "array",
            "items": {
                # "id": "http://jsonschema.net/candidates/0",
                "type": "object",
                "required": ["first_name", "middle_name", "last_name", "addresses", "areas_of_interest",
                             "phones", "emails", "educations", "custom_fields", "preferred_locations",
                             "military_services", "social_networks", "skills", "work_experiences",
                             "work_preference"],
                "properties": {
                    "first_name": {
                        # "id": "http://jsonschema.net/first_name",
                        "type": ["string", "null"],
                        "maxLength": 35
                    },
                    "middle_name": {
                        # "id": "http://jsonschema.net/middle_name",
                        "type": ["string", "null"],
                        "maxLength": 35
                    },
                    "last_name": {
                        # "id": "http://jsonschema.net/last_name",
                        "type": ["string", "null"],
                        "maxLength": 35
                    },
                    "emails": {
                        # "id": "http://jsonschema.net/emails",
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 5,
                        "items": {
                            # "id": "http://jsonschema.net/emails/0",
                            "type": "object",
                            "required": ["label", "address", "is_default"],
                            "properties": {
                                "label": {
                                    # "id": "http://jsonschema.net/emails/0/label",
                                    "type": ["string", "null"],
                                    "maxLength": 7
                                },
                                "address": {
                                    # "id": "http://jsonschema.net/emails/0/address",
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "is_default": {
                                    # "id": "http://jsonschema.net/emails/0/id_default",
                                    "type": ["boolean", "null"]
                                }
                            }
                        }
                    },
                    "phones": {
                        # "id": "http://jsonschema.net/phones",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/phones/0",
                            "type": "object",
                            "required": ["label", "value", "is_default"],
                            "properties": {
                                "label": {
                                    # "id": "http://jsonschema.net/phones/0/label",
                                    "type": ["string", "null"],
                                    "maxLength": 10
                                },
                                "value": {
                                    # "id": "http://jsonschema.net/phones/0/value",
                                    "type": ["string", "null"],
                                    "maxLength": 20
                                },
                                "is_default": {
                                    # "id": "http://jsonschema.net/phones/0/is_default",
                                    "type": "boolean"
                                }
                            }
                        }
                    },
                    "areas_of_interest": {
                        # "id": "http://jsonschema.net/areas_of_interest",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/areas_of_interest/0",
                            "type": "object",
                            "properties": {
                                "area_of_interest_id": {
                                    # "id": "http://jsonschema.net/areas_of_interest/0/area_of_interest_id",
                                    "type": ["integer", "null"]
                                }
                            }
                        }
                    },
                    "custom_fields": {
                        # "id": "http://jsonschema.net/custom_fields",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/custom_fields/0",
                            "type": "object",
                            "required": ["value"],
                            "properties": {
                                "custom_field_id": {
                                    # "id": "http://jsonschema.net/custom_fields/0/custom_field_id",
                                    "type": ["integer", "null"]
                                },
                                "value": {
                                    # "id": "http://jsonschema.net/custom_fields/0/value",
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                }
                            }
                        }
                    },
                    "work_preference": {
                        # "id": "http://jsonschema.net/work_preference",
                        "type": ["object", "null"],
                        "required": ["authorization", "employment_type", "relocate", "telecommute",
                                     "travel_percentage", "security_clearance", "third_party", "hourly_rate",
                                     "salary"],
                        "properties": {
                            "authorization": {
                                # "id": "http://jsonschema.net/work_preference/authorization",
                                "type": ["string", "null"],
                                "maxLength": 50
                            },
                            "employment_type": {
                                # "id": "http://jsonschema.net/work_preference/employment_type",
                                "type": ["string", "null"],
                                "maxLength": 50
                            },
                            "relocate": {
                                # "id": "http://jsonschema.net/work_preference/relocate",
                                "type": ["boolean", "null"]
                            },
                            "telecommute": {
                                # "id": "http://jsonschema.net/work_preference/telecommute",
                                "type": ["boolean", "null"]
                            },
                            "travel_percentage": {
                                # "id": "http://jsonschema.net/work_preference/travel_percentage",
                                "type": ["string", "integer", "null"],
                                "maxLength": 3
                            },
                            "security_clearance": {
                                # "id": "http://jsonschema.net/work_preference/security_clearance",
                                "type": ["boolean", "null"]
                            },
                            "third_party": {
                                # "id": "http://jsonschema.net/work_preference/third_party",
                                "type": ["boolean", "null"]
                            },
                            "hourly_rate": {
                                # "id": "http://jsonschema.net/work_preference/hourly_rate",
                                "type": ["string", "number", "null"],
                                "maxLength": 6
                            },
                            "salary": {
                                # "id": "http://jsonschema.net/work_preference/salary",
                                "type": ["string", "number", "integer", "null"],
                                "maxLength": 10
                            }
                        }
                    },
                    "addresses": {
                        # "id": "http://jsonschema.net/addresses",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/addresses/0",
                            "type": "object",
                            "required": ["address_line_1", "city", "state", "country",
                                         "po_box", "zip_code", "is_default"],
                            "properties": {
                                "address_line_1": {
                                    # "id": "http://jsonschema.net/addresses/0/address_line_1",
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "address_line_2": {
                                    # "id": "http://jsonschema.net/addresses/0/address_line_2",
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "city": {
                                    # "id": "http://jsonschema.net/addresses/0/city",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "state": {
                                    # "id": "http://jsonschema.net/addresses/0/state",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "country": {
                                    # "id": "http://jsonschema.net/addresses/0/country",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "po_box": {
                                    # "id": "http://jsonschema.net/addresses/0/po_box",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "zip_code": {
                                    # "id": "http://jsonschema.net/addresses/0/zip_code",
                                    "type": ["string", "null"],
                                    "maxLength": 31
                                },
                                "is_default": {
                                    # "id": "http://jsonschema.net/addresses/0/is_default",
                                    "type": ["boolean", "null"]
                                }
                            },
                        }
                    },
                    "social_networks": {
                        # "id": "http://jsonschema.net/social_networks",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/social_networks/0",
                            "type": "object",
                            "required": ["name", "profile_url"],
                            "properties": {
                                "name": {
                                    # "id": "http://jsonschema.net/social_networks/0/name",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "profile_url": {
                                    # "id": "http://jsonschema.net/social_networks/0/profile_url",
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                }
                            }
                        }
                    },
                    "educations": {
                        # "id": "http://jsonschema.net/educations",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/educations/0",
                            "type": "object",
                            "required": ["school_name", "school_type", "city", "state", "country",
                                         "is_current", "degrees"],
                            "properties": {
                                "school_name": {
                                    # "id": "http://jsonschema.net/educations/0/school_name",
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "school_type": {
                                    # "id": "http://jsonschema.net/educations/0/school_type",
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "city": {
                                    # "id": "http://jsonschema.net/educations/0/city",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "state": {
                                    # "id": "http://jsonschema.net/educations/0/state",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "country": {
                                    # "id": "http://jsonschema.net/educations/0/country",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "is_current": {
                                    # "id": "http://jsonschema.net/educations/0/is_current",
                                    "type": ["boolean", "null"]
                                },
                                "degrees": {
                                    # "id": "http://jsonschema.net/educations/0/degrees",
                                    "type": ["array", "null"],
                                    "items": {
                                        # "id": "http://jsonschema.net/educations/0/degrees/0",
                                        "type": "object",
                                        "required": ["title", "type", "start_year", "end_year", "start_month",
                                                     "end_month", "gpa_num", "bullets"],
                                        "properties": {
                                            "type": {
                                                # "id": "http://jsonschema.net/educations/0/degrees/0/type",
                                                "type": ["string", "null"],
                                                "maxLength": 255
                                            },
                                            "title": {
                                                # "id": "http://jsonschema.net/educations/0/degrees/0/title",
                                                "type": ["string", "null"],
                                                "maxLength": 255
                                            },
                                            "start_year": {
                                                # "id": "http://jsonschema.net/educations/0/degrees/0/start_year",
                                                "type": ["string", "integer", "null"],
                                                "maxLength": 4
                                            },
                                            "start_month": {
                                                # "id": "http://jsonschema.net/educations/0/degrees/0/start_month",
                                                "type": ["string", "integer", "null"],
                                                "maxLength": 2
                                            },
                                            "end_year": {
                                                # "id": "http://jsonschema.net/educations/0/degrees/0/end_year",
                                                "type": ["string", "integer", "null"],
                                                "maxLength": 4
                                            },
                                            "end_month": {
                                                # "id": "http://jsonschema.net/educations/0/degrees/0/end_month",
                                                "type": ["string", "integer", "null"],
                                                "maxLength": 2
                                            },
                                            "gpa_num": {
                                                # "id": "http://jsonschema.net/educations/0/degrees/0/gpa_num",
                                                "type": ["number", "null"],
                                                "maxLength": 4
                                            },
                                            "bullets": {
                                                # "id": "http://jsonschema.net/educations/0/degrees/0/bullets",
                                                "type": ["array", "null"],
                                                "items": {
                                                    # "id": "http://jsonschema.net/educations/0/degrees/0/bullets/0",
                                                    "type": "object",
                                                    "required": ["major", "comments"],
                                                    "properties": {
                                                        "major": {
                                                            # "id": "http://jsonschema.net/educations/0/degrees/0/bullets/0/major",
                                                            "type": ["string", "null"],
                                                            "maxLength": 100
                                                        },
                                                        "comments": {
                                                            # "id": "http://jsonschema.net/educations/0/degrees/0/bullets/0/comments",
                                                            "type": ["string", "null"],
                                                            "maxLength": 5000
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "preferred_locations": {
                        # "id": "http://jsonschema.net/preferred_locations",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/preferred_locations/0",
                            "type": "object",
                            "required": ["city", "state", "country"],
                            "properties": {
                                "address": {
                                    # "id": "http://jsonschema.net/preferred_locations/0/address",
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "city": {
                                    # "id": "http://jsonschema.net/preferred_locations/0/city",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "state": {
                                    # "id": "http://jsonschema.net/preferred_locations/0/state",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "country": {
                                    # "id": "http://jsonschema.net/preferred_locations/0/country",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "zip_code": {
                                    # "id": "http://jsonschema.net/preferred_locations/0/zip_code",
                                    "type": ["string", "null"],
                                    "maxLength": 31
                                }
                            }
                        }
                    },
                    "work_experiences": {
                        # "id": "http://jsonschema.net/work_experiences",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/work_experiences/0",
                            "type": "object",
                            "required": ["position", "organization", "city", "state", "country", "is_current",
                                         "bullets", "start_year", "end_year", "start_month", "end_month"],
                            "properties": {
                                "position": {
                                    # "id": "http://jsonschema.net/work_experiences/0/position",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "organization": {
                                    # "id": "http://jsonschema.net/work_experiences/0/organization",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "city": {
                                    # "id": "http://jsonschema.net/work_experiences/0/city",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "state": {
                                    # "id": "http://jsonschema.net/work_experiences/0/state",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "country": {
                                    # "id": "http://jsonschema.net/work_experiences/0/country",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "start_year": {
                                    # "id": "http://jsonschema.net/work_experiences/0/start_date",
                                    "type": ["integer", "null"],
                                    "maxLength": 4
                                },
                                "end_year": {
                                    # "id": "http://jsonschema.net/work_experiences/0/end_date",
                                    "type": ["integer", "null"],
                                    "maxLength": 4
                                },
                                "start_month": {
                                    # "id": "http://jsonschema.net/work_experiences/0/start_date",
                                    "type": ["integer", "null"],
                                    "maxLength": 2
                                },
                                "end_month": {
                                    # "id": "http://jsonschema.net/work_experiences/0/end_date",
                                    "type": ["integer", "null"],
                                    "maxLength": 2
                                },
                                "is_current": {
                                    # "id": "http://jsonschema.net/work_experiences/0/is_current",
                                    "type": ["boolean", "null"]
                                },
                                "bullets": {
                                    # "id": "http://jsonschema.net/work_experiences/0/bullets",
                                    "type": ["array", "null"],
                                    "items": {
                                        # "id": "http://jsonschema.net/work_experiences/0/bullets/0",
                                        "type": "object",
                                        "required": ["description"],
                                        "properties": {
                                            "description": {
                                                # "id": "http://jsonschema.net/work_experiences/0/bullets/0/description",
                                                "type": ["string", "null"],
                                                "maxLength": 10000
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "military_services": {
                        # "id": "http://jsonschema.net/military_services",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/military_services/0",
                            "type": "object",
                            "required": ["country", "highest_rank", "branch", "status",
                                         "highest_grade", "from_date", "to_date", "comments"],
                            "properties": {
                                "country": {
                                    # "id": "http://jsonschema.net/military_services/0/country",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "highest_rank": {
                                    # "id": "http://jsonschema.net/military_services/0/highest_rank",
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "branch": {
                                    # "id": "http://jsonschema.net/military_services/0/branch",
                                    "type": ["string", "null"],
                                    "maxLength": 200
                                },
                                "status": {
                                    # "id": "http://jsonschema.net/military_services/0/status",
                                    "type": ["string", "null"],
                                    "maxLength": 200
                                },
                                "highest_grade": {
                                    # "id": "http://jsonschema.net/military_services/0/highest_grade",
                                    "type": ["string", "null"],
                                    "maxLength": 7
                                },
                                "from_date": {
                                    # "id": "http://jsonschema.net/military_services/0/from_date",
                                    "type": ["string", "null"]
                                },
                                "to_date": {
                                    # "id": "http://jsonschema.net/military_services/0/to_date",
                                    "type": ["string", "null"]
                                },
                                "comments": {
                                    # "id": "http://jsonschema.net/military_services/0/comments",
                                    "type": ["string", "null"],
                                    "maxLength": 5000
                                }
                            }
                        }
                    },
                    "skills": {
                        # "id": "http://jsonschema.net/skills",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/skills/0",
                            "type": "object",
                            "required": ["name", "months_used", "last_used_date"],
                            "properties": {
                                "name": {
                                    # "id": "http://jsonschema.net/skills/0/name",
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "months_used": {
                                    # "id": "http://jsonschema.net/skills/0/months_used",
                                    "type": ["integer", "null"],
                                    "maxLength": 3  # TODO: custom validation for setting maxLength of a number/integer
                                },
                                "last_used_date": {
                                    # "id": "http://jsonschema.net/skills/0/last_used_date",
                                    "type": ["string", "null"]
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

candidates_resource_schema_patch = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    # "id": "http://jsonschema.net",
    "type": "object",
    "required": ["candidates"],
    "properties": {
        "candidates": {
            # "id": "http://jsonschema.net/candidates",
            "type": "array",
            "items": {
                # "id": "http://jsonschema.net/candidates/0",
                "type": "object",
                "required": ["id"],
                "properties": {
                    "id": {
                        # "id": "http://jsonschema.net/candidates/0/id",
                        "type": ["integer"]
                    },
                    "first_name": {
                        # "id": "http://jsonschema.net/candidates/0/first_name",
                        "type": ["string", "null"],
                        "maxLength": 35
                    },
                    "middle_name": {
                        # "id": "http://jsonschema.net/candidates/0/middle_name",
                        "type": ["string", "null"],
                        "maxLength": 35
                    },
                    "last_name": {
                        # "id": "http://jsonschema.net/candidates/0/last_name",
                        "type": ["string", "null"],
                        "maxLength": 35
                    },
                    "emails": {
                        # "id": "http://jsonschema.net/candidates/0/emails",
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 5,
                        "items": {
                            # "id": "http://jsonschema.net/candidates/0/emails/0",
                            "type": "object",
                            "required": ["id", "label", "address", "is_default"],
                            "properties": {
                                "id": {
                                    # "id": "http://jsonschema.net/candidates/0/emails/0/id",
                                    "type": ["integer"]
                                },
                                "label": {
                                    # "id": "http://jsonschema.net/candidates/0/emails/0/label",
                                    "type": ["string", "null"],
                                    "maxLength": 7
                                },
                                "address": {
                                    # "id": "http://jsonschema.net/candidates/0/emails/0/address",
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "is_default": {
                                    # "id": "http://jsonschema.net/candidates/0/emails/0/id_default",
                                    "type": ["boolean", "null"]
                                }
                            }
                        }
                    },
                    "phones": {
                        # "id": "http://jsonschema.net/candidates/0/phones",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/candidates/0/phones/0",
                            "type": "object",
                            "required": ["id", "label", "value", "is_default"],
                            "properties": {
                                "id": {
                                    # "id": "http://jsonschema.net/candidates/0/phones/0/id",
                                    "type": ["integer"]
                                },
                                "label": {
                                    # "id": "http://jsonschema.net/candidates/0/phones/0/label",
                                    "type": ["string", "null"],
                                    "maxLength": 10
                                },
                                "value": {
                                    # "id": "http://jsonschema.net/candidates/0/phones/0/value",
                                    "type": ["string", "null"],
                                    "maxLength": 20
                                },
                                "is_default": {
                                    # "id": "http://jsonschema.net/candidates/0/phones/0/is_default",
                                    "type": "boolean"
                                }
                            }
                        }
                    },
                    "areas_of_interest": {
                        # "id": "http://jsonschema.net/candidates/0/areas_of_interest",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/candidates/0/areas_of_interest/0",
                            "type": "object",
                            "properties": {
                                "area_of_interest_id": {
                                    # "id": "http://jsonschema.net/candidates/0/areas_of_interest/0/area_of_interest_id",
                                    "type": ["integer", "null"]
                                }
                            }
                        }
                    },
                    "custom_fields": {
                        # "id": "http://jsonschema.net/candidates/0/custom_fields",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/candidates/0/custom_fields/0",
                            "type": "object",
                            "required": ["value"],
                            "properties": {
                                "custom_field_id": {
                                    # "id": "http://jsonschema.net/candidates/0/custom_fields/0/custom_field_id",
                                    "type": ["integer", "null"]
                                },
                                "value": {
                                    # "id": "http://jsonschema.net/candidates/0/custom_fields/0/value",
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                }
                            }
                        }
                    },
                    "work_preference": {
                        # "id": "http://jsonschema.net/candidates/0/work_preference",
                        "type": ["object", "null"],
                        "required": ["id", "authorization", "employment_type", "relocate", "telecommute",
                                     "travel_percentage", "security_clearance", "third_party", "hourly_rate",
                                     "salary"],
                        "properties": {
                            "id": {
                                # "id": "http://jsonschema.net/candidates/0/work_preference/id",
                                "type": ["integer"]
                            },
                            "authorization": {
                                # "id": "http://jsonschema.net/candidates/0/work_preference/authorization",
                                "type": ["string", "null"],
                                "maxLength": 50
                            },
                            "employment_type": {
                                # "id": "http://jsonschema.net/candidates/0/work_preference/employment_type",
                                "type": ["string", "null"],
                                "maxLength": 50
                            },
                            "relocate": {
                                # "id": "http://jsonschema.net/candidates/0/work_preference/relocate",
                                "type": ["boolean", "null"]
                            },
                            "telecommute": {
                                # "id": "http://jsonschema.net/candidates/0/work_preference/telecommute",
                                "type": ["boolean", "null"]
                            },
                            "travel_percentage": {
                                # "id": "http://jsonschema.net/candidates/0/work_preference/travel_percentage",
                                "type": ["string", "integer", "null"],
                                "maxLength": 3
                            },
                            "security_clearance": {
                                # "id": "http://jsonschema.net/candidates/0/work_preference/security_clearance",
                                "type": ["boolean", "null"]
                            },
                            "third_party": {
                                # "id": "http://jsonschema.net/candidates/0/work_preference/third_party",
                                "type": ["boolean", "null"]
                            },
                            "hourly_rate": {
                                # "id": "http://jsonschema.net/candidates/0/work_preference/hourly_rate",
                                "type": ["string", "number", "null"],
                                "maxLength": 6
                            },
                            "salary": {
                                # "id": "http://jsonschema.net/candidates/0/work_preference/salary",
                                "type": ["string", "number", "integer", "null"],
                                "maxLength": 10
                            }
                        }
                    },
                    "addresses": {
                        # "id": "http://jsonschema.net/candidates/0/addresses",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/candidates/0/addresses/0",
                            "type": "object",
                            "required": ["id", "address_line_1", "city", "state", "country",
                                         "po_box", "zip_code", "is_default"],
                            "properties": {
                                "id": {
                                    # "id": "http://jsonschema.net/candidates/0/addresses/0/id",
                                    "type": ["integer"]
                                },
                                "address_line_1": {
                                    # "id": "http://jsonschema.net/candidates/0/addresses/0/address_line_1",
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "address_line_2": {
                                    # "id": "http://jsonschema.net/candidates/0/addresses/0/address_line_2",
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "city": {
                                    # "id": "http://jsonschema.net/candidates/0/addresses/0/city",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "state": {
                                    # "id": "http://jsonschema.net/candidates/0/addresses/0/state",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "country": {
                                    # "id": "http://jsonschema.net/candidates/0/addresses/0/country",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "po_box": {
                                    # "id": "http://jsonschema.net/candidates/0/addresses/0/po_box",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "zip_code": {
                                    # "id": "http://jsonschema.net/candidates/0/addresses/0/zip_code",
                                    "type": ["string", "null"],
                                    "maxLength": 31
                                },
                                "is_default": {
                                    # "id": "http://jsonschema.net/candidates/0/addresses/0/is_default",
                                    "type": ["boolean", "null"]
                                }
                            },
                        }
                    },
                    "social_networks": {
                        # "id": "http://jsonschema.net/candidates/0/social_networks",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/candidates/0/social_networks/0",
                            "type": "object",
                            "required": ["id", "name", "profile_url"],
                            "properties": {
                                "id": {
                                    # "id": "http://jsonschema.net/candidates/0/social_networks/0/id",
                                    "type": ["integer"]
                                },
                                "name": {
                                    # "id": "http://jsonschema.net/candidates/0/social_networks/0/name",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "profile_url": {
                                    # "id": "http://jsonschema.net/candidates/0/social_networks/0/profile_url",
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                }
                            }
                        }
                    },
                    "educations": {
                        # "id": "http://jsonschema.net/candidates/0/educations",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/candidates/0/educations/0",
                            "type": "object",
                            "required": ["id", "school_name", "school_type", "city", "state", "country",
                                         "is_current", "degrees"],
                            "properties": {
                                "id": {
                                    # "id": "http://jsonschema.net/candidates/0/educations/0/id",
                                    "type": ["integer"]
                                },
                                "school_name": {
                                    # "id": "http://jsonschema.net/candidates/0/educations/0/school_name",
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "school_type": {
                                    # "id": "http://jsonschema.net/candidates/0/educations/0/school_type",
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "city": {
                                    # "id": "http://jsonschema.net/candidates/0/educations/0/city",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "state": {
                                    # "id": "http://jsonschema.net/candidates/0/educations/0/state",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "country": {
                                    # "id": "http://jsonschema.net/candidates/0/educations/0/country",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "is_current": {
                                    # "id": "http://jsonschema.net/candidates/0/educations/0/is_current",
                                    "type": ["boolean", "null"]
                                },
                                "degrees": {
                                    # "id": "http://jsonschema.net/candidates/0/educations/0/degrees",
                                    "type": ["array", "null"],
                                    "items": {
                                        # "id": "http://jsonschema.net/candidates/0/educations/0/degrees/0",
                                        "type": "object",
                                        "required": ["id", "title", "type", "start_year", "end_year", "start_month",
                                                     "end_month", "gpa_num", "bullets"],
                                        "properties": {
                                            "id": {
                                                # "id": "http://jsonschema.net/candidates/0/educations/0/degrees/0/id",
                                                "type": ["integer"]
                                            },
                                            "type": {
                                                # "id": "http://jsonschema.net/candidates/0/educations/0/degrees/0/type",
                                                "type": ["string", "null"],
                                                "maxLength": 255
                                            },
                                            "title": {
                                                # "id": "http://jsonschema.net/candidates/0/educations/0/degrees/0/title",
                                                "type": ["string", "null"],
                                                "maxLength": 255
                                            },
                                            "start_year": {
                                                # "id": "http://jsonschema.net/candidates/0/educations/0/degrees/0/start_year",
                                                "type": ["string", "integer", "null"],
                                                "maxLength": 4
                                            },
                                            "start_month": {
                                                # "id": "http://jsonschema.net/candidates/0/educations/0/degrees/0/start_month",
                                                "type": ["string", "integer", "null"],
                                                "maxLength": 2
                                            },
                                            "end_year": {
                                                # "id": "http://jsonschema.net/candidates/0/educations/0/degrees/0/end_year",
                                                "type": ["string", "integer", "null"],
                                                "maxLength": 4
                                            },
                                            "end_month": {
                                                # "id": "http://jsonschema.net/candidates/0/educations/0/degrees/0/end_month",
                                                "type": ["string", "integer", "null"],
                                                "maxLength": 2
                                            },
                                            "gpa_num": {
                                                # "id": "http://jsonschema.net/candidates/0/educations/0/degrees/0/gpa_num",
                                                "type": ["number", "null"],
                                                "maxLength": 4
                                            },
                                            "bullets": {
                                                # "id": "http://jsonschema.net/candidates/0/educations/0/degrees/0/bullets",
                                                "type": ["array", "null"],
                                                "items": {
                                                    # "id": "http://jsonschema.net/candidates/0/educations/0/degrees/0/bullets/0",
                                                    "type": "object",
                                                    "required": ["id", "major", "comments"],
                                                    "properties": {
                                                        "id": {
                                                            # "id": "http://jsonschema.net/candidates/0/educations/0/degrees/0/bullets/0/id",
                                                            "type": ["integer"]
                                                        },
                                                        "major": {
                                                            # "id": "http://jsonschema.net/candidates/0/educations/0/degrees/0/bullets/0/major",
                                                            "type": ["string", "null"],
                                                            "maxLength": 100
                                                        },
                                                        "comments": {
                                                            # "id": "http://jsonschema.net/candidates/0/educations/0/degrees/0/bullets/0/comments",
                                                            "type": ["string", "null"],
                                                            "maxLength": 5000
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "preferred_locations": {
                        # "id": "http://jsonschema.net/candidates/0/preferred_locations",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/candidates/0/preferred_locations/0",
                            "type": "object",
                            "required": ["id", "city", "state", "country"],
                            "properties": {
                                "id": {
                                    # "id": "http://jsonschema.net/candidates/0/preferred_locations/0/id",
                                    "type": ["integer"]
                                },
                                "address": {
                                    # "id": "http://jsonschema.net/candidates/0/preferred_locations/0/address",
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "city": {
                                    # "id": "http://jsonschema.net/candidates/0/preferred_locations/0/city",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "state": {
                                    # "id": "http://jsonschema.net/candidates/0/preferred_locations/0/state",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "country": {
                                    # "id": "http://jsonschema.net/candidates/0/preferred_locations/0/country",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "zip_code": {
                                    # "id": "http://jsonschema.net/candidates/0/preferred_locations/0/zip_code",
                                    "type": ["string", "null"],
                                    "maxLength": 31
                                }
                            }
                        }
                    },
                    "work_experiences": {
                        # "id": "http://jsonschema.net/candidates/0/work_experiences",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/candidates/0/work_experiences/0",
                            "type": "object",
                            "required": ["id", "position", "organization", "city", "state", "country", "is_current",
                                         "bullets", "start_year", "end_year", "start_month", "end_month"],
                            "properties": {
                                "id": {
                                    # "id": "http://jsonschema.net/candidates/0/work_experiences/0/id",
                                    "type": ["integer"]
                                },
                                "position": {
                                    # "id": "http://jsonschema.net/candidates/0/work_experiences/0/position",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "organization": {
                                    # "id": "http://jsonschema.net/candidates/0/work_experiences/0/organization",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "city": {
                                    # "id": "http://jsonschema.net/candidates/0/work_experiences/0/city",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "state": {
                                    # "id": "http://jsonschema.net/candidates/0/work_experiences/0/state",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "country": {
                                    # "id": "http://jsonschema.net/candidates/0/work_experiences/0/country",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "start_year": {
                                    # "id": "http://jsonschema.net/candidates/0/work_experiences/0/start_date",
                                    "type": ["integer", "null"],
                                    "maxLength": 4
                                },
                                "end_year": {
                                    # "id": "http://jsonschema.net/candidates/0/work_experiences/0/end_date",
                                    "type": ["integer", "null"],
                                    "maxLength": 4
                                },
                                "start_month": {
                                    # "id": "http://jsonschema.net/candidates/0/work_experiences/0/start_date",
                                    "type": ["integer", "null"],
                                    "maxLength": 2
                                },
                                "end_month": {
                                    # "id": "http://jsonschema.net/candidates/0/work_experiences/0/end_date",
                                    "type": ["integer", "null"],
                                    "maxLength": 2
                                },
                                "is_current": {
                                    # "id": "http://jsonschema.net/candidates/0/work_experiences/0/is_current",
                                    "type": ["boolean", "null"]
                                },
                                "bullets": {
                                    # "id": "http://jsonschema.net/candidates/0/work_experiences/0/bullets",
                                    "type": ["array", "null"],
                                    "items": {
                                        # "id": "http://jsonschema.net/candidates/0/work_experiences/0/bullets/0",
                                        "type": "object",
                                        "required": ["id", "description"],
                                        "properties": {
                                            "id": {
                                                # "id": "http://jsonschema.net/candidates/0/work_experiences/0/bullets/0/id",
                                                "type": ["integer"]
                                            },
                                            "description": {
                                                # "id": "http://jsonschema.net/candidates/0/work_experiences/0/bullets/0/description",
                                                "type": ["string", "null"],
                                                "maxLength": 10000
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "military_services": {
                        # "id": "http://jsonschema.net/candidates/0/military_services",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/candidates/0/military_services/0",
                            "type": "object",
                            "required": ["id", "country", "highest_rank", "branch", "status",
                                         "highest_grade", "from_date", "to_date", "comments"],
                            "properties": {
                                "id": {
                                    # "id": "http://jsonschema.net/candidates/0/military_services/0/id",
                                    "type": ["integer"]
                                },
                                "country": {
                                    # "id": "http://jsonschema.net/candidates/0/military_services/0/country",
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "highest_rank": {
                                    # "id": "http://jsonschema.net/candidates/0/military_services/0/highest_rank",
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "branch": {
                                    # "id": "http://jsonschema.net/candidates/0/military_services/0/branch",
                                    "type": ["string", "null"],
                                    "maxLength": 200
                                },
                                "status": {
                                    # "id": "http://jsonschema.net/candidates/0/military_services/0/status",
                                    "type": ["string", "null"],
                                    "maxLength": 200
                                },
                                "highest_grade": {
                                    # "id": "http://jsonschema.net/candidates/0/military_services/0/highest_grade",
                                    "type": ["string", "null"],
                                    "maxLength": 7
                                },
                                "from_date": {
                                    # "id": "http://jsonschema.net/candidates/0/military_services/0/from_date",
                                    "type": ["string", "null"]
                                },
                                "to_date": {
                                    # "id": "http://jsonschema.net/candidates/0/military_services/0/to_date",
                                    "type": ["string", "null"]
                                },
                                "comments": {
                                    # "id": "http://jsonschema.net/candidates/0/military_services/0/comments",
                                    "type": ["string", "null"],
                                    "maxLength": 5000
                                }
                            }
                        }
                    },
                    "skills": {
                        # "id": "http://jsonschema.net/candidates/0/skills",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/candidates/0/skills/0",
                            "type": "object",
                            "required": ["id", "name", "months_used", "last_used_date"],
                            "properties": {
                                "id": {
                                    # "id": "http://jsonschema.net/candidates/0/skills/0/id",
                                    "type": ["integer"]
                                },
                                "name": {
                                    # "id": "http://jsonschema.net/candidates/0/skills/0/name",
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "months_used": {
                                    # "id": "http://jsonschema.net/candidates/0/skills/0/months_used",
                                    "type": ["integer", "null"],
                                    "maxLength": 3  # TODO: custom validation for setting maxLength of a number/integer
                                },
                                "last_used_date": {
                                    # "id": "http://jsonschema.net/candidates/0/skills/0/last_used_date",
                                    "type": ["string", "null"]
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
