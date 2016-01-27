"""
Test cases for testing jsonschema validations
"""
# Candidate Service app instance
from candidate_service.candidate_app import app

# Conftest
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import (
    response_info, request_to_candidates_resource, AddUserRoles
)

# ***** JSON Schema POST Validations *****
def test_schema_validation(access_token_first, user_first, talent_pool):
    # Create Candidate
    AddUserRoles.add(user=user_first)
    data = {'candidates': [
        {
            'talent_pool_ids': {'add': [talent_pool.id]},
            'emails': [{'label': None, 'address': fake.safe_email(), 'is_default': True}],
            'first_name': 'john', 'middle_name': '', 'last_name': '', 'addresses': [],
            'social_networks': [], 'skills': [], 'work_experiences': [], 'work_preference': {},
            'educations': [], 'custom_fields': [], 'preferred_locations': [], 'military_services': [],
            'areas_of_interest': [], 'phones': []
        }
    ]}
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)
    print response_info(create_resp)
    assert create_resp.status_code == 201


# ***** JSONSCHEMA PATCH *****
# ***** JSONSCHEMA GET *****