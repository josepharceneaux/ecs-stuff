# Candidate Service app instance
from candidate_service.candidate_app import app

# Conftest
from candidate_service.common.tests.conftest import *

# Helper functions
from polling import poll
from helpers import AddUserRoles
from candidate_service.common.routes import CandidateApiUrl, CandidatePoolApiUrl
from candidate_service.common.utils.test_utils import send_request, response_info
from candidate_service.common.inter_service_calls.candidate_service_calls import search_candidates_from_params as search
from candidate_service.common.utils.handy_functions import add_role_to_test_user


class TestSearchCandidatePipeline(object):
    CANDIDATE_URL = CandidateApiUrl.CANDIDATES
    PIPELINE_INCLUSION_URL = CandidateApiUrl.PIPELINES
    PIPELINE_URL = CandidatePoolApiUrl.TALENT_PIPELINES

    def test_search_for_candidate_in_pipeline(self, user_first, access_token_first, talent_pool):
        AddUserRoles.add_and_get(user_first)
        add_role_to_test_user(user_first, [DomainRole.Roles.CAN_ADD_TALENT_PIPELINES])

        # Create candidate
        data = {"candidates": [
            {
                "talent_pool_ids": {"add": [talent_pool.id]},
                "full_name": fake.name(), 'skills': [{'name': 'Java'}, {'name': 'Python'}]
            }
        ]}
        create_resp = send_request('post', self.CANDIDATE_URL, access_token_first, data)
        print response_info(create_resp)

        candidate_id = create_resp.json()['candidates'][0]['id']

        # Add Pipelines
        data = {"talent_pipelines": [
            {
                "talent_pool_id": talent_pool.id,
                "name": "testing",
                "date_needed": "2017-11-30",
                "search_params": {"user_ids": str(user_first.id)}
            }
        ]}
        create_resp = send_request('post', self.PIPELINE_URL, access_token_first, data)
        print response_info(create_resp)

        params = data['talent_pipelines'][0]['search_params']
        if poll(lambda: len(search(params, access_token_first)['candidates']) >= 1, step=1, timeout=100):
            get_resp = send_request('get', self.PIPELINE_INCLUSION_URL % candidate_id, access_token_first)
            print response_info(get_resp)
            assert get_resp.status_code == 200
            assert len(get_resp.json()['candidate_pipelines']) == len(data['talent_pipelines'])
