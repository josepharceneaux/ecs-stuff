"""
Test cases for testing jsonschema validations
"""
# Standard library
import json

# Candidate Service app instance
from candidate_service.candidate_app import app

# Models
from candidate_service.common.models.user import User

# Conftest
from candidate_service.common.tests.conftest import UserAuthentication
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import (
    response_info, post_to_candidate_resource, get_from_candidate_resource,
    request_to_candidate_preference_resource, AddUserRoles
)

# ***** JSONSCHEMA POST *****
def test_schema_validation(sample_user, user_auth):
    """
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']
    AddUserRoles.add(user=sample_user)

    # Create Candidate
    data = {'candidates': [
        {
            'emails': [{'label': None, 'address': fake.safe_email(), 'is_default': True}],
            'first_name': 'john', 'middle_name': '', 'last_name': '', 'addresses': [],
            'social_networks': [], 'skills': [], 'work_experiences': [], 'work_preference': {},
            'educations': [], 'custom_fields': [], 'preferred_locations': [], 'military_services': [],
            'areas_of_interest': [], 'phones': []
        }
    ]}
    create_resp = post_to_candidate_resource(token, data)
    print response_info(create_resp)
    assert create_resp.status_code == 201


# ***** JSONSCHEMA PATCH *****
# ***** JSONSCHEMA GET *****