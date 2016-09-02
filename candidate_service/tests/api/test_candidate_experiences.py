"""
Test cases for adding, retrieving, updating, and deleting candidate work experiences
"""
# Candidate Service app instance
from candidate_service.candidate_app import app

# Conftest
from candidate_service.common.tests.conftest import *
from ..conftest import test_candidate_1

# Helper functions
from candidate_service.common.utils.test_utils import send_request, response_info
from candidate_service.common.routes import CandidateApiUrl

# Custom errors
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error


class TestUpdateCandidateExperienceSuccessfully(object):
    """
    Class contains functional tests that will update facets of candidate's work experiences
    """
    def test_update_start_and_end_dates(self, test_candidate_1, access_token_first):
        """
        Test: will update the start date & end date of one of candidate's work experience
        """
        candidate_id = test_candidate_1['candidate']['id']
        work_experience = test_candidate_1['candidate']['work_experiences'][0]
        updated_start_year = int(work_experience['start_date'][:4]) - 5
        updated_end_year = int(work_experience['end_date'][:4]) - 3

        update_data = {
            "candidates": [
                {
                    'work_experiences': [
                        {
                            'id': work_experience['id'],
                            'start_year': updated_start_year,
                            'end_year': updated_end_year
                        }
                    ]
                }
            ]
        }

        # Update candidate
        update_resp = send_request('patch', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first, update_data)
        print response_info(update_resp)
        assert update_resp.status_code == requests.codes.OK

        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        assert update_resp.status_code == requests.codes.OK
        candidate_experiences = get_resp.json()['candidate']['work_experiences']
        updated_experience = [exp for exp in candidate_experiences if exp['id'] == work_experience['id']][0]
        assert updated_experience['start_date'][:4] == str(updated_start_year)
        assert updated_experience['end_date'][:4] == str(updated_end_year)
