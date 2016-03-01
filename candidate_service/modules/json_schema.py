"""
JSON Schemas for validating data sent to CandidatesResource
"""
from datetime import datetime
CURRENT_YEAR = datetime.now().year

candidates_resource_schema_post = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "required": ["candidates"],
    "properties": {
        "candidates": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["talent_pool_ids"],
                "additionalProperties": False,
                "properties": {
                    "first_name": {
                        "type": ["string", "null"],
                        "maxLength": 35
                    },
                    "middle_name": {
                        "type": ["string", "null"],
                        "maxLength": 35
                    },
                    "last_name": {
                        "type": ["string", "null"],
                        "maxLength": 35
                    },
                    "full_name": {
                        "type": ["string", "null"],
                        "maxLength": 150
                    },
                    "status_id": {
                        "type": ["integer", "null"]
                    },
                    "openweb_id": {
                        "type": ["string", "null"]
                    },
                    "dice_profile_id": {
                        "type": ["string", "null"]
                    },
                    "source_id": {
                        "type": ["integer", "null"]
                    },
                    "objective": {
                        "type": ["string", "null"]
                    },
                    "summary": {
                        "type": ["string", "null"]
                    },
                    "resume_url": {
                        "type": ["string", "null"]
                    },
                    "talent_pool_ids": {
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
                        "type": ["array", "null"],
                        # "minItems": 1,
                        "items": {
                            "type": "object",
                            "required": ["address"],
                            "additionalProperties": False,
                            "properties": {
                                "label": {
                                    "type": ["string", "null"],
                                    "maxLength": 50
                                },
                                "address": {
                                    "type": ["string"],
                                    "maxLength": 255
                                },
                                "is_default": {
                                    "type": ["boolean", "null"]
                                }
                            }
                        }
                    },
                    "phones": {
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "required": ["value"],
                            "additionalProperties": False,
                            "properties": {
                                "label": {
                                    "type": ["string", "null"],
                                    "maxLength": 50
                                },
                                "value": {
                                    "type": ["string", "null"],
                                    "maxLength": 20
                                },
                                "is_default": {
                                    "type": ["boolean", "null"]
                                }
                            }
                        }
                    },
                    "areas_of_interest": {
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "required": ["area_of_interest_id"],
                            "additionalProperties": False,
                            "properties": {
                                "area_of_interest_id": {
                                    "type": ["integer", "null"]
                                }
                            }
                        }
                    },
                    "custom_fields": {
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "id": {
                                    "type": ["integer", "null"]
                                },
                                "custom_field_id": {
                                    "type": ["integer", "null"]
                                },
                                "value": {
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                }
                            }
                        }
                    },
                    "text_comments": {
                        "type": ["array", "null"],
                        "additionalProperties": True,
                        "properties": {
                            "comment": {
                                "type": ["string", "null"]
                            },
                            "created_at_datetime": {
                                "type": ["string", "null"]
                            }
                        }
                    },
                    "work_preference": {
                        "type": ["object", "null"],
                        "additionalProperties": True,
                        "properties": {
                            "authorization": {
                                "type": ["string", "null"],
                                "maxLength": 250
                            },
                            "tax_terms": {
                                "type": ["string", "null"],
                                "maxLength": 250
                            },
                            "employment_type": {
                                "type": ["string", "null"],
                                "maxLength": 250
                            },
                            "relocate": {
                                "type": ["boolean", "null"]
                            },
                            "telecommute": {
                                "type": ["boolean", "null"]
                            },
                            "travel_percentage": {
                                "type": ["integer", "null"],
                                "minimum": 0, "maximum": 100
                            },
                            "security_clearance": {
                                "type": ["boolean", "null"]
                            },
                            "third_party": {
                                "type": ["boolean", "null"]
                            },
                            "hourly_rate": {
                                "type": ["string", "number", "null"],
                                "maxLength": 6,
                                "minimum": 0  # Negative values are not allowed
                            },
                            "salary": {
                                "type": ["string", "number", "integer", "null"],
                                "maxLength": 10,
                                "minimum": 0  # Negative values are not allowed
                            }
                        }
                    },
                    "addresses": {
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "additionalProperties": True,
                            "properties": {
                                "address_line_1": {
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "address_line_2": {
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "city": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "state": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "country": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "po_box": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "zip_code": {
                                    "type": ["string", "null"],
                                    "maxLength": 31
                                },
                                "is_default": {
                                    "type": ["boolean", "null"]
                                }
                            }
                        }
                    },
                    "social_networks": {
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "required": ["name", "profile_url"],
                            "additionalProperties": True,
                            "properties": {
                                "name": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "profile_url": {
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                }
                            }
                        }
                    },
                    "educations": {
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "school_name": {
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "school_type": {
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "city": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "state": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "country": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "is_current": {
                                    "type": ["boolean", "null"]
                                },
                                "degrees": {
                                    "type": ["array", "null"],
                                    "items": {
                                        "type": "object",
                                        "additionalProperties": False,
                                        "properties": {
                                            "type": {
                                                "type": ["string", "null"],
                                                "maxLength": 255
                                            },
                                            "title": {
                                                "type": ["string", "null"],
                                                "maxLength": 255
                                            },
                                            "start_year": {
                                                "type": ["integer", "null"],
                                                "minimum": 1950, "maximum": CURRENT_YEAR
                                            },
                                            "start_month": {
                                                "type": ["integer", "null"],
                                                "minimum": 1, "maximum": 12
                                            },
                                            "end_year": {
                                                "type": ["integer", "null"],
                                                "minimum": 1950, "maximum": CURRENT_YEAR
                                            },
                                            "end_month": {
                                                "type": ["integer", "null"],
                                                "minimum": 1, "maximum": 12
                                            },
                                            "gpa": {
                                                "type": ["number", "null"],
                                                "minimum": 0
                                            },
                                            "gpa_num": {
                                                "type": ["number", "null"]
                                            },
                                            "bullets": {
                                                "type": ["array", "null"],
                                                "items": {
                                                    "type": "object",
                                                    "additionalProperties": False,
                                                    "properties": {
                                                        "major": {
                                                            "type": ["string", "null"],
                                                            "maxLength": 100
                                                        },
                                                        "comments": {
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
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "address": {
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "city": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "state": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "region": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "country": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "zip_code": {
                                    "type": ["string", "null"],
                                    "maxLength": 31
                                }
                            }
                        }
                    },
                    "work_experiences": {
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "additionalProperties": True,
                            "properties": {
                                "position": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "organization": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "city": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "state": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "country": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "start_year": {
                                    "type": ["integer", "null"],
                                    "minimum": 1950, "maximum": CURRENT_YEAR
                                },
                                "end_year": {
                                    "type": ["integer", "null"],
                                    "minimum": 1950, "maximum": CURRENT_YEAR
                                },
                                "start_month": {
                                    "type": ["integer", "null"],
                                    "minimum": 1, "maximum": 12
                                },
                                "end_month": {
                                    "type": ["integer", "null"],
                                    "minimum": 1, "maximum": 12
                                },
                                "is_current": {
                                    "type": ["boolean", "null"]
                                },
                                "bullets": {
                                    "type": ["array", "null"],
                                    "items": {
                                        "type": "object",
                                        "additionalProperties": False,
                                        "properties": {
                                            "description": {
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
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "country": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "highest_rank": {
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "branch": {
                                    "type": ["string", "null"],
                                    "maxLength": 200
                                },
                                "status": {
                                    "type": ["string", "null"],
                                    "maxLength": 200
                                },
                                "highest_grade": {
                                    "type": ["string", "null"],
                                    "maxLength": 7
                                },
                                "from_date": {
                                    "type": ["string", "null"]
                                },
                                "to_date": {
                                    "type": ["string", "null"],
                                    # "format": "date-time"
                                },
                                "comments": {
                                    "type": ["string", "null"],
                                    "maxLength": 5000
                                }
                            }
                        }
                    },
                    "skills": {
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "name": {
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "months_used": {
                                    "type": ["integer", "null"],
                                    "minimum": 1, "maximum": 720
                                },
                                "last_used_date": {
                                    "type": ["string", "null"],
                                    # "format": "date-time"
                                }
                            }
                        }
                    },
                    "image_url": {
                        "type": ["string", "null"]
                    }
                }
            }
        }
    }
}

candidates_resource_schema_patch = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "required": ["candidates"],
    "properties": {
        "candidates": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["id"],
                "additionalProperties": False,
                "properties": {
                    "id": {
                        "type": ["integer", "null"]
                    },
                    "first_name": {
                        "type": ["string", "null"],
                        "maxLength": 35
                    },
                    "middle_name": {
                        "type": ["string", "null"],
                        "maxLength": 35
                    },
                    "last_name": {
                        "type": ["string", "null"],
                        "maxLength": 35
                    },
                    "full_name": {
                        "type": ["string", "null"],
                        "maxLength": 150
                    },
                    "status_id": {
                        "type": ["integer", "null"]
                    },
                    "openweb_id": {
                        "type": ["string", "null"]
                    },
                    "dice_profile_id": {
                        "type": ["string", "null"]
                    },
                    "source_id": {
                        "type": ["integer", "null"]
                    },
                    "objective": {
                        "type": ["string", "null"]
                    },
                    "summary": {
                        "type": ["string", "null"]
                    },
                    "resume_url": {
                        "type": ["string", "null"]
                    },
                    "talent_pool_ids": {
                        "type": ["object", "null"],
                        "additionalProperties": False,
                        "properties": {
                            "add": {
                                "type": "array",
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
                        "type": ["array", "null"],
                        "items": {
                            "type": ["object", "null"],
                            "additionalProperties": False,
                            "properties": {
                                "id": {
                                    "type": ["integer", "null"]
                                },
                                "label": {
                                    "type": ["string", "null"],
                                    "maxLength": 50
                                },
                                "address": {
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "is_default": {
                                    "type": ["boolean", "null"]
                                }
                            }
                        }
                    },
                    "phones": {
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "required": ["value"],
                            "additionalProperties": False,
                            "properties": {
                                "id": {
                                    "type": ["integer", "null"]
                                },
                                "label": {
                                    "type": ["string", "null"],
                                    "maxLength": 50
                                },
                                "value": {
                                    "type": ["string", "null"],
                                    "maxLength": 20
                                },
                                "is_default": {
                                    "type": ["boolean", "null"]
                                }
                            }
                        }
                    },
                    "areas_of_interest": {
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "area_of_interest_id": {
                                    "type": ["integer", "null"]
                                }
                            }
                        }
                    },
                    "custom_fields": {
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "id": {
                                    "type": ["integer", "null"]
                                },
                                "custom_field_id": {
                                    "type": ["integer", "null"]
                                },
                                "value": {
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                }
                            }
                        }
                    },
                    "work_preference": {
                        "type": ["object", "null"],
                        "additionalProperties": False,
                        "properties": {
                            "id": {
                                "type": ["integer"]
                            },
                            "authorization": {
                                "type": ["string", "null"],
                                "maxLength": 50
                            },
                            "tax_terms": {
                                "type": ["string", "null"],
                                "maxLength": 50
                            },
                            "employment_type": {
                                "type": ["string", "null"],
                                "maxLength": 50
                            },
                            "relocate": {
                                "type": ["boolean", "null"]
                            },
                            "telecommute": {
                                "type": ["boolean", "null"]
                            },
                            "travel_percentage": {
                                "type": ["integer", "null"],
                                "minimum": 0, "maximum": 100
                            },
                            "security_clearance": {
                                "type": ["boolean", "null"]
                            },
                            "third_party": {
                                "type": ["boolean", "null"]
                            },
                            "hourly_rate": {
                                "type": ["string", "number", "null"],
                                "maxLength": 6,
                                "minimum": 0  # Negative values are not permitted
                            },
                            "salary": {
                                "type": ["string", "number", "null"],
                                "maxLength": 10,
                                "minimum": 0  # Negative values are not permitted
                            }
                        }
                    },
                    "addresses": {
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "id": {
                                    "type": ["integer"]
                                },
                                "address_line_1": {
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "address_line_2": {
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "city": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "state": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "country": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "po_box": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "zip_code": {
                                    "type": ["string", "null"],
                                    "maxLength": 31
                                },
                                "is_default": {
                                    "type": ["boolean", "null"]
                                }
                            }
                        }
                    },
                    "social_networks": {
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "id": {
                                    "type": ["integer"]
                                },
                                "name": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "profile_url": {
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                }
                            }
                        }
                    },
                    "educations": {
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "additionalProperties": True,
                            "properties": {
                                "id": {
                                    "type": ["integer"]
                                },
                                "school_name": {
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "school_type": {
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "city": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "state": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "country": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "is_current": {
                                    "type": ["boolean", "null"]
                                },
                                "degrees": {
                                    "type": ["array", "null"],
                                    "items": {
                                        "type": "object",
                                        "additionalProperties": True,
                                        "properties": {
                                            "id": {
                                                "type": ["integer"]
                                            },
                                            "type": {
                                                "type": ["string", "null"],
                                                "maxLength": 255
                                            },
                                            "title": {
                                                "type": ["string", "null"],
                                                "maxLength": 255
                                            },
                                            "start_year": {
                                                "type": ["integer", "null"],
                                                "minimum": 1950, "maximum": CURRENT_YEAR
                                            },
                                            "start_month": {
                                                "type": ["integer", "null"],
                                                "minimum": 1, "maximum": 12
                                            },
                                            "end_year": {
                                                "type": ["integer", "null"],
                                                "minimum": 1950, "maximum": CURRENT_YEAR
                                            },
                                            "end_month": {
                                                "type": ["integer", "null"],
                                                "minimum": 1, "maximum": 12
                                            },
                                            "gpa": {
                                                "type": ["number", "null"]
                                            },
                                            "bullets": {
                                                "type": ["array", "null"],
                                                "items": {
                                                    "type": "object",
                                                    "additionalProperties": False,
                                                    "properties": {
                                                        "id": {
                                                            "type": ["integer"]
                                                        },
                                                        "major": {
                                                            "type": ["string", "null"],
                                                            "maxLength": 100
                                                        },
                                                        "comments": {
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
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "id": {
                                    "type": ["integer"]
                                },
                                "address": {
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "city": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "state": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "region": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "country": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "zip_code": {
                                    "type": ["string", "null"],
                                    "maxLength": 31
                                }
                            }
                        }
                    },
                    "work_experiences": {
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": ["integer"]
                                },
                                "position": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "organization": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "city": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "state": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "country": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "start_year": {
                                    "type": ["integer", "null"],
                                    "minimum": 1950, "maximum": CURRENT_YEAR
                                },
                                "end_year": {
                                    "type": ["integer", "null"],
                                    "minimum": 1950, "maximum": CURRENT_YEAR
                                },
                                "start_month": {
                                    "type": ["integer", "null"],
                                    "minimum": 1, "maximum": 12
                                },
                                "end_month": {
                                    "type": ["integer", "null"],
                                    "minimum": 1, "maximum": 12
                                },
                                "is_current": {
                                    "type": ["boolean", "null"]
                                },
                                "bullets": {
                                    "type": ["array", "null"],
                                    "items": {
                                        "type": "object",
                                        "additionalProperties": False,
                                        "properties": {
                                            "id": {
                                                "type": ["integer"]
                                            },
                                            "description": {
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
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "id": {
                                    "type": ["integer"]
                                },
                                "country": {
                                    "type": ["string", "null"],
                                    "maxLength": 100
                                },
                                "highest_rank": {
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "branch": {
                                    "type": ["string", "null"],
                                    "maxLength": 200
                                },
                                "status": {
                                    "type": ["string", "null"],
                                    "maxLength": 200
                                },
                                "highest_grade": {
                                    "type": ["string", "null"],
                                    "maxLength": 7
                                },
                                "from_date": {
                                    "type": ["string", "null"]
                                },
                                "to_date": {
                                    "type": ["string", "null"]
                                },
                                "comments": {
                                    "type": ["string", "null"],
                                    "maxLength": 5000
                                }
                            }
                        }
                    },
                    "skills": {
                        "type": ["array", "null"],
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "id": {
                                    "type": ["integer"]
                                },
                                "name": {
                                    "type": ["string", "null"],
                                    "maxLength": 255
                                },
                                "months_used": {
                                    "type": ["integer", "null"],
                                    "minimum": 1, "maximum": 720
                                },
                                "last_used_date": {
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
    "type": ["object", "null"],
    "additionalProperties": False,
    "properties": {
        "candidate_ids": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "integer"
            }
        }
    }
}


resource_schema_preferences = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "additionalProperties": False,
    "required": ["frequency_id"],
    "properties": {
        "frequency_id": {
            "type": "integer"
        }
    }
}

resource_schema_photos_post = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "additionalProperties": False,
    "required": ["photos"],
    "properties": {
        "photos": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["image_url"],
                # "additionalProperties": False,
                "properties": {
                    "image_url": {"type": "string"},
                    "is_default": {"type": ["boolean", "null"]},
                    "added_datetime": {
                        "type": ["string", "null"]
                        # "format": "date-time" #TODO uncomment this when we can get datetime.isoformat() to comply with 'date-time' format
                    }
                }
            }
        }
    }
}

resource_schema_photos_patch = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "image_url": {"type": "string"},
        "is_default": {"type": ["boolean", "null"]},
        "added_datetime": {
            "type": ["string", "null"]
            # "format": "date-time" #TODO uncomment this when we can get datetime.isoformat() to comply with 'date-time' format
        }
    }
}
