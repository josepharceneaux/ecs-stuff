"""
JSON Schemas for validating data sent to CandidatesResource
"""
from datetime import datetime
CURRENT_YEAR = datetime.now().year

candidates_resource_schema_post = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    # "id": "http://jsonschema.net",
    "type": "object",
    "required": ["candidates"],
    "properties": {
        "candidates": {
            # "id": "http://jsonschema.net/candidates",
            "type": "array",
            "minItems": 1,
            "items": {
                # "id": "http://jsonschema.net/candidates/0",
                "type": "object",
                "required": ["talent_pool_ids"],
                "additionalProperties": False,
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
                    "full_name": {
                        # "id": "http://jsonschema.net/full_name",
                        "type": ["string", "null"],
                        "maxLength": 150
                    },
                    "status_id": {
                        # "id": "http://jsonschema.net/status_id",
                        "type": ["integer", "null"]
                    },
                    "openweb_id": {
                        # "id": "http://jsonschema.net/openweb_id",
                        "type": ["integer", "null"]
                    },
                    "dice_profile_id": {
                        # "id": "http://jsonschema.net/dice_profile_id",
                        "type": ["integer", "null"]
                    },
                    "source_id": {
                        # "id": "http://jsonschema.net/source_id",
                        "type": ["integer", "null"]
                    },
                    "objective": {
                        # "id": "http://jsonschema.net/objective",
                        "type": ["string", "null"]
                    },
                    "summary": {
                        # "id": "http://jsonschema.net/summary",
                        "type": ["string", "null"]
                    },
                    "talent_pool_ids": {
                        # "id": "http://jsonschema.net/talent_pool_id",
                        "type": "object",
                        "required": ["add"],
                        "additionalProperties": False,
                        "properties": {
                            "add": {
                                "type": "array",
                                "minItems": 1,
                                "items": {
                                    "type": "integer"
                                }
                            },
                            "delete": {
                                "type": "array",
                                "items": {
                                    "type": "integer"
                                }
                            }
                        }
                    },
                    "emails": {
                        # "id": "http://jsonschema.net/emails",
                        "type": ["array", "null"],
                        # "minItems": 1,
                        "items": {
                            # "id": "http://jsonschema.net/emails/0",
                            "type": "object",
                            "required": ["address"],
                            "additionalProperties": False,
                            "properties": {
                                "label": {
                                    # "id": "http://jsonschema.net/emails/0/label",
                                    "type": ["string", "null"],
                                    "maxLength": 50
                                },
                                "address": {
                                    # "id": "http://jsonschema.net/emails/0/address",
                                    "type": ["string"],
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
                            "required": ["value"],
                            "additionalProperties": False,
                            "properties": {
                                "label": {
                                    # "id": "http://jsonschema.net/phones/0/label",
                                    "type": ["string", "null"],
                                    "maxLength": 50
                                },
                                "value": {
                                    # "id": "http://jsonschema.net/phones/0/value",
                                    "type": ["string", "null"],
                                    "maxLength": 20
                                },
                                "is_default": {
                                    # "id": "http://jsonschema.net/phones/0/is_default",
                                    "type": ["boolean", "null"]
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
                            "required": ["area_of_interest_id"],
                            "additionalProperties": False,
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
                            "additionalProperties": False,
                            "properties": {
                                "id": {
                                    # "id": "http://jsonschema.net/custom_fields/0/id",
                                    "type": ["integer", "null"]
                                },
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
                        "additionalProperties": False,
                        "properties": {
                            "authorization": {
                                # "id": "http://jsonschema.net/work_preference/authorization",
                                "type": ["string", "null"],
                                "maxLength": 50
                            },
                            "tax_terms": {
                                # "id": "http://jsonschema.net/work_preference/tax_terms",
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
                                "type": ["integer", "null"],
                                "minimum": 0, "maximum": 100
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
                                "maxLength": 6,
                                "minimum": 0  # Negative values are not allowed
                            },
                            "salary": {
                                # "id": "http://jsonschema.net/work_preference/salary",
                                "type": ["string", "number", "integer", "null"],
                                "maxLength": 10,
                                "minimum": 0  # Negative values are not allowed
                            }
                        }
                    },
                    "addresses": {
                        # "id": "http://jsonschema.net/addresses",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/addresses/0",
                            "type": "object",
                            "additionalProperties": False,
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
                            }
                        }
                    },
                    "social_networks": {
                        # "id": "http://jsonschema.net/social_networks",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/social_networks/0",
                            "type": "object",
                            "required": ["name", "profile_url"],
                            "additionalProperties": False,
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
                            "additionalProperties": False,
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
                                        "additionalProperties": False,
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
                                                "type": ["integer", "null"],
                                                "minimum": 1950, "maximum": CURRENT_YEAR
                                            },
                                            "start_month": {
                                                # "id": "http://jsonschema.net/educations/0/degrees/0/start_month",
                                                "type": ["integer", "null"],
                                                "minimum": 1, "maximum": 12
                                            },
                                            "end_year": {
                                                # "id": "http://jsonschema.net/educations/0/degrees/0/end_year",
                                                "type": ["integer", "null"],
                                                "minimum": 1950, "maximum": CURRENT_YEAR
                                            },
                                            "end_month": {
                                                # "id": "http://jsonschema.net/educations/0/degrees/0/end_month",
                                                "type": ["integer", "null"],
                                                "minimum": 1, "maximum": 12
                                            },
                                            "gpa": {
                                                # "id": "http://jsonschema.net/educations/0/degrees/0/gpa_num",
                                                "type": ["number", "null"],
                                                "minimum": 0
                                            },
                                            "bullets": {
                                                # "id": "http://jsonschema.net/educations/0/degrees/0/bullets",
                                                "type": ["array", "null"],
                                                "items": {
                                                    # "id": "http://jsonschema.net/educations/0/degrees/0/bullets/0",
                                                    "type": "object",
                                                    "additionalProperties": False,
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
                            "additionalProperties": False,
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
                                "region": {
                                    # "id": "http://jsonschema.net/preferred_locations/0/region",
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
                            "additionalProperties": False,
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
                                    "minimum": 1950, "maximum": CURRENT_YEAR
                                },
                                "end_year": {
                                    # "id": "http://jsonschema.net/work_experiences/0/end_date",
                                    "type": ["integer", "null"],
                                    "minimum": 1950, "maximum": CURRENT_YEAR
                                },
                                "start_month": {
                                    # "id": "http://jsonschema.net/work_experiences/0/start_date",
                                    "type": ["integer", "null"],
                                    "minimum": 1, "maximum": 12
                                },
                                "end_month": {
                                    # "id": "http://jsonschema.net/work_experiences/0/end_date",
                                    "type": ["integer", "null"],
                                    "minimum": 1, "maximum": 12
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
                                        "additionalProperties": False,
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
                            "additionalProperties": False,
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
                                    "type": ["string", "null"],
                                    # "format": "date-time"
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
                            "additionalProperties": False,
                            "properties": {
                                "name": {
                                    # "id": "http://jsonschema.net/skills/0/name",
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "months_used": {
                                    # "id": "http://jsonschema.net/skills/0/months_used",
                                    "type": ["integer", "null"],
                                    "minimum": 1, "maximum": 720
                                },
                                "last_used_date": {
                                    # "id": "http://jsonschema.net/skills/0/last_used_date",
                                    "type": ["string", "null"],
                                    # "format": "date-time"
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
            "minItems": 1,
            "items": {
                # "id": "http://jsonschema.net/candidates/0",
                "type": "object",
                "required": ["id"],
                "additionalProperties": False,
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
                    "full_name": {
                        # "id": "http://jsonschema.net/full_name",
                        "type": ["string", "null"],
                        "maxLength": 150
                    },
                    "status_id": {
                        # "id": "http://jsonschema.net/status_id",
                        "type": ["integer", "null"]
                    },
                    "openweb_id": {
                        # "id": "http://jsonschema.net/openweb_id",
                        "type": ["integer", "null"]
                    },
                    "dice_profile_id": {
                        # "id": "http://jsonschema.net/dice_profile_id",
                        "type": ["integer", "null"]
                    },
                    "talent_pool_id": {
                        # "id": "http://jsonschema.net/talent_pool_id",
                        "type": ["object", "null"]
                    },
                    "source_id": {
                        # "id": "http://jsonschema.net/source_id",
                        "type": ["integer", "null"]
                    },
                    "objective": {
                        # "id": "http://jsonschema.net/objective",
                        "type": ["string", "null"]
                    },
                    "summary": {
                        # "id": "http://jsonschema.net/summary",
                        "type": ["string", "null"]
                    },
                    "emails": {
                        # "id": "http://jsonschema.net/candidates/0/emails",
                        "type": "array",
                        "items": {
                            # "id": "http://jsonschema.net/candidates/0/emails/0",
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "id": {
                                    # "id": "http://jsonschema.net/candidates/0/emails/0/id",
                                    "type": ["integer"]
                                },
                                "label": {
                                    # "id": "http://jsonschema.net/candidates/0/emails/0/label",
                                    "type": ["string", "null"],
                                    "maxLength": 50
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
                            "required": ["value"],
                            "additionalProperties": False,
                            "properties": {
                                "id": {
                                    # "id": "http://jsonschema.net/candidates/0/phones/0/id",
                                    "type": ["integer"]
                                },
                                "label": {
                                    # "id": "http://jsonschema.net/candidates/0/phones/0/label",
                                    "type": ["string", "null"],
                                    "maxLength": 50
                                },
                                "value": {
                                    # "id": "http://jsonschema.net/candidates/0/phones/0/value",
                                    "type": ["string", "null"],
                                    "maxLength": 20
                                },
                                "is_default": {
                                    # "id": "http://jsonschema.net/candidates/0/phones/0/is_default",
                                    "type": ["boolean", "null"]
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
                            "additionalProperties": False,
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
                            "additionalProperties": False,
                            "properties": {
                                "id": {
                                    # "id": "http://jsonschema.net/candidates/0/custom_fields/0/id",
                                    "type": ["integer", "null"]
                                },
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
                        "additionalProperties": False,
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
                            "tax_terms": {
                                # "id": "http://jsonschema.net/work_preference/tax_terms",
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
                                "type": ["integer", "null"],
                                "minimum": 0, "maximum": 100
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
                                "maxLength": 6,
                                "minimum": 0  # Negative values are not permitted
                            },
                            "salary": {
                                # "id": "http://jsonschema.net/candidates/0/work_preference/salary",
                                "type": ["string", "number", "null"],
                                "maxLength": 10,
                                "minimum": 0  # Negative values are not permitted
                            }
                        }
                    },
                    "addresses": {
                        # "id": "http://jsonschema.net/candidates/0/addresses",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/candidates/0/addresses/0",
                            "type": "object",
                            "additionalProperties": False,
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
                            }
                        }
                    },
                    "social_networks": {
                        # "id": "http://jsonschema.net/candidates/0/social_networks",
                        "type": ["array", "null"],
                        "items": {
                            # "id": "http://jsonschema.net/candidates/0/social_networks/0",
                            "type": "object",
                            "additionalProperties": False,
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
                            "additionalProperties": False,
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
                                        "additionalProperties": False,
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
                                                "type": ["integer", "null"],
                                                "minimum": 1950, "maximum": CURRENT_YEAR
                                            },
                                            "start_month": {
                                                # "id": "http://jsonschema.net/candidates/0/educations/0/degrees/0/start_month",
                                                "type": ["integer", "null"],
                                                "minimum": 1, "maximum": 12
                                            },
                                            "end_year": {
                                                # "id": "http://jsonschema.net/candidates/0/educations/0/degrees/0/end_year",
                                                "type": ["integer", "null"],
                                                "minimum": 1950, "maximum": CURRENT_YEAR
                                            },
                                            "end_month": {
                                                # "id": "http://jsonschema.net/candidates/0/educations/0/degrees/0/end_month",
                                                "type": ["integer", "null"],
                                                "minimum": 1, "maximum": 12
                                            },
                                            "gpa": {
                                                # "id": "http://jsonschema.net/candidates/0/educations/0/degrees/0/gpa_num",
                                                "type": ["number", "null"]
                                            },
                                            "bullets": {
                                                # "id": "http://jsonschema.net/candidates/0/educations/0/degrees/0/bullets",
                                                "type": ["array", "null"],
                                                "items": {
                                                    # "id": "http://jsonschema.net/candidates/0/educations/0/degrees/0/bullets/0",
                                                    "type": "object",
                                                    "additionalProperties": False,
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
                            "additionalProperties": False,
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
                                "region": {
                                    # "id": "http://jsonschema.net/candidates/0/preferred_locations/0/region",
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
                                    "minimum": 1950, "maximum": CURRENT_YEAR
                                },
                                "end_year": {
                                    # "id": "http://jsonschema.net/candidates/0/work_experiences/0/end_date",
                                    "type": ["integer", "null"],
                                    "minimum": 1950, "maximum": CURRENT_YEAR
                                },
                                "start_month": {
                                    # "id": "http://jsonschema.net/candidates/0/work_experiences/0/start_date",
                                    "type": ["integer", "null"],
                                    "minimum": 1, "maximum": 12
                                },
                                "end_month": {
                                    # "id": "http://jsonschema.net/candidates/0/work_experiences/0/end_date",
                                    "type": ["integer", "null"],
                                    "minimum": 1, "maximum": 12
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
                                        "additionalProperties": False,
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
                            "additionalProperties": False,
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
                            "additionalProperties": False,
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
                                    "minimum": 1, "maximum": 720
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

candidates_resource_schema_get = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    # "id": "http://jsonschema.net",
    "type": ["object", "null"],
    "additionalProperties": False,
    "properties": {
        "candidate_ids": {
            # "id": "http://jsonschema.net/candidate_ids",
            "type": "array",
            "minItems": 1,
            "items": {
                # "id": "http://jsonschema.net/candidate_ids/0",
                "type": "integer"
            }
        }
    }
}

resource_schema_preferences = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    # "id": "http://jsonschema.net",
    "type": "object",
    "additionalProperties": False,
    "required": ["frequency_id"],
    "properties": {
        "frequency_id": {
            # "id": "http://jsonschema.net/frequency_id",
            "type": "integer"
        }
    }
}