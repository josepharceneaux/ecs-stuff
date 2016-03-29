# Candidate Service app instance
from candidate_service.candidate_app import app

# Conftest
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import AddUserRoles
from candidate_service.common.routes import CandidateApiUrl
from candidate_service.common.utils.test_utils import send_request, response_info


class TestGetCandidateLanguages(object):
    def test_retrieve_candidates_languages(self, user_first, access_token_first, candidate_first):
        """
        Test:  Make a GET request to CandidateLanguageResource
        """
        AddUserRoles.add_and_get(user_first)

        data = [
            {
                'language_code': 'en',
                'read': True,
                'write': True,
                'speak': True,
            },
            {
                'language_code': 'FA',  # all caps should also work
                'read': False,
                'write': False,
                'speak': True,
            }
        ]
        create_resp = send_request('post', CandidateApiUrl.LANGUAGES % candidate_first.id, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 204

        # Retrieve candidate's languages
        get_resp = send_request('get', CandidateApiUrl.LANGUAGES % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 200
        assert len(get_resp.json()['candidate_languages']) == 2