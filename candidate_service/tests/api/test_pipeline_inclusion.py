# Candidate Service app instance
from candidate_service.candidate_app import app

# Conftest
from candidate_service.common.tests.conftest import *

# Helper functions
from redo import retrier
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
        """
        Test: User Pipeline search params to search for a candidate
        """
        AddUserRoles.add_and_get(user_first)
        add_role_to_test_user(user_first, [DomainRole.Roles.CAN_ADD_TALENT_PIPELINES])

        # Create candidate
        data = {"candidates": [{"talent_pool_ids": {"add": [talent_pool.id]}}]}
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
        for _ in retrier(attempts=100, sleeptime=1, sleepscale=1):
            if len(search(params, access_token_first)['candidates']) >= 1:
                get_resp = send_request('get', self.PIPELINE_INCLUSION_URL % candidate_id, access_token_first)
                print response_info(get_resp)
                if get_resp.ok and len(get_resp.json()['candidate_pipelines']) == len(data['talent_pipelines']):
                    break
        else:
            get_resp = send_request('get', self.PIPELINE_INCLUSION_URL % candidate_id, access_token_first)
            assert get_resp.ok and len(get_resp.json()['candidate_pipelines']) == len(data['talent_pipelines'])

    def test_search_for_non_existing_candidate_in_pipeline(self, user_first, access_token_first, candidate_first):
        """
        Test:  Use Pipeline search params to search for a candidate that is not found via pipeline's search params
        Expect:  200 status code but should just return an empty list
        """
        AddUserRoles.add_and_get(user_first)

        # Search
        get_resp = send_request('get', self.PIPELINE_INCLUSION_URL % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.OK
        assert get_resp.json()['candidate_pipelines'] == []

    def test_search_for_candidate_in_pipeline_without_auth_token(self, user_first, candidate_first):
        """
        Test:  Access resource without sending in a valid access token
        """
        AddUserRoles.add_and_get(user_first)

        # Search
        get_resp = send_request('get', self.PIPELINE_INCLUSION_URL % candidate_first.id, None)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.UNAUTHORIZED