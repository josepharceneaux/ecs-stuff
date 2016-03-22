# Candidate Service app instance
from candidate_service.candidate_app import app

# Conftest
from candidate_service.common.tests.conftest import *

# Helpers
from candidate_service.tests.api.helpers import AddUserRoles, response_info
from candidate_service.tests.api.candidate_sample_data import generate_single_candidate_data
from candidate_service.common.utils.test_utils import send_request
from candidate_service.common.routes import CandidateApiUrl


class TestGetNotes(object):
    def test_get_candidate_notes(self, user_first, access_token_first, talent_pool):
        """
        Test:  Create candidate + add some notes for the candidate
        Expect: 204 for creation and 200 after retrieving
        """
        # Create Candidate
        AddUserRoles.add_and_get(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)

        # Create notes for candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        notes_data = {'notes': [
            {'comment': 'Interested in internet security'},
            {'comment': 'Contributed to Linux OSS'}
        ]}
        resp = send_request('post', CandidateApiUrl.NOTES % candidate_id, access_token_first, notes_data)
        print response_info(resp)
        assert resp.status_code == 204

        # Retrieve candidate's notes
        get_resp = send_request('get', CandidateApiUrl.NOTES % candidate_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 200
        assert len(get_resp.json()['candidate_notes']) == len(notes_data['notes'])