# Candidate Service app instance
from candidate_service.candidate_app import app

# Conftest
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import (
    response_info, AddUserRoles, request_to_candidate_resource, request_to_candidates_resource,
    request_to_candidate_photos_resource
)

# Sample data
from candidate_sample_data import (
    generate_single_candidate_data, candidate_phones, candidate_military_service,
    candidate_preferred_locations, candidate_skills, candidate_social_network
)
from candidate_service.common.models.candidate import CandidateEmail

# Custom errors
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error
