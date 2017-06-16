# Candidate Service app instance
from candidate_service.candidate_app import app

# Conftest
from candidate_service.common.tests.conftest import *

# Helper functions
from redo import retry

from candidate_service.common.tests.fake_testing_data_generator import FakeCandidatesData
from candidate_service.tests.modules.test_talent_cloud_search import populate_candidates
from candidate_service.common.routes import CandidateApiUrl, CandidatePoolApiUrl
from candidate_service.common.utils.test_utils import send_request, response_info
from candidate_service.common.inter_service_calls.candidate_service_calls import create_candidates_from_candidate_api
from candidate_service.common.models.user import Role

# Define urls used in this file
CANDIDATE_URL = CandidateApiUrl.CANDIDATES
TALENT_POOL_URL = CandidatePoolApiUrl.TALENT_POOLS
PIPELINE_URL = CandidatePoolApiUrl.TALENT_PIPELINES
PIPELINE_INCLUSION_URL = CandidateApiUrl.PIPELINES


class TestSearchCandidatePipeline(object):
    def test_search_for_candidate_in_pipeline(self, user_first, access_token_first, talent_pool):
        """
        Test: Use Pipeline search params to search for a candidate
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()
        skill_name = fake.word()

        # Create multiple candidates
        data = FakeCandidatesData.create(talent_pool=talent_pool, count=16, skill_name=skill_name)
        candidate_ids = create_candidates_from_candidate_api(access_token_first, data,
                                                             return_candidate_ids_only=True)
        number_of_talent_pipelines = 15
        candidate_id = candidate_ids[-1]

        # Add Pipelines
        pipeline_data = {"talent_pipelines": [
            {
                "talent_pool_id": talent_pool.id,
                "name": 'testing_{}'.format(str(fake.uuid4())[:5]),
                "date_needed": "2017-11-30",
                "search_params": {"skills": [skill_name]}
            } for _ in range(number_of_talent_pipelines)
            ]}

        create_resp = send_request('post', PIPELINE_URL, access_token_first, pipeline_data)
        print response_info(create_resp)

        # Ensure talent pipelines were created
        get_resp = send_request('get', PIPELINE_URL, access_token_first)
        assert set([tp['id'] for tp in get_resp.json()['talent_pipelines']]).issubset(
            create_resp.json()['talent_pipelines']
        )
        # Assert on results
        retry(assert_result, sleeptime=3, attempts=10, sleepscale=1,
              args=(candidate_id, access_token_first),
              kwargs=dict(expected_count=number_of_talent_pipelines),
              retry_exceptions=(AssertionError,))

    def test_search_for_last_candidate_in_pipeline(self, user_first, access_token_first, talent_pool):
        """
        This function will:
            1. create 16 candidates to ensure multiple pages will return from the search result
            2. search using pipeline search params for the first candidate created
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        # Create 16 candidates
        count = 16
        candidate_ids = populate_candidates(access_token=access_token_first, talent_pool=talent_pool, count=count)
        assert len(candidate_ids) == count

        # Add pipelines
        data = {"talent_pipelines": [
            {
                "talent_pool_id": talent_pool.id,
                "name": str(uuid.uuid4())[:5],
                "date_needed": "2017-11-30",
                "search_params": {"user_ids": str(user_first.id)}
            },
            {
                "talent_pool_id": talent_pool.id,
                "name": str(uuid.uuid4())[:5],
                "date_needed": "2017-11-30",
                "search_params": {"user_ids": str(user_first.id)}
            }
        ]}
        create_resp = send_request('post', PIPELINE_URL, access_token_first, data)
        print response_info(create_resp)

        # Search & assert result with first candidate created
        candidate_id = candidate_ids[-1]
        retry(assert_result, sleeptime=3, attempts=10, sleepscale=1,
              args=(candidate_id, access_token_first),
              retry_exceptions=(AssertionError,))

        # Search & assert result with middle candidate created
        candidate_id = candidate_ids[len(candidate_ids) / 2]
        retry(assert_result, sleeptime=3, attempts=10, sleepscale=1,
              args=(candidate_id, access_token_first),
              retry_exceptions=(AssertionError,))

        # # Search & assert result with last candidate created
        candidate_id = candidate_ids[0]
        # Assert on results
        retry(assert_result, sleeptime=3, attempts=20, sleepscale=1,
              args=(candidate_id, access_token_first),
              retry_exceptions=(AssertionError,))

    def test_search_for_non_existing_candidate_in_pipeline(self, access_token_first, candidate_first):
        """
        Test:  Use Pipeline search params to search for a candidate that is not found via pipeline's search params
        Expect:  200 status code but should just return an empty list
        """
        # Search
        get_resp = send_request('get', PIPELINE_INCLUSION_URL % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.OK
        assert get_resp.json()['candidate_pipelines'] == []

    def test_search_for_candidate_in_pipeline_without_auth_token(self, candidate_first):
        """
        Test:  Access resource without sending in a valid access token
        """

        # Search
        get_resp = send_request('get', PIPELINE_INCLUSION_URL % candidate_first.id, None)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.UNAUTHORIZED


def assert_result(candidate_id, access_token_first, expected_count=2):
    get_resp = send_request('get', PIPELINE_INCLUSION_URL % candidate_id, access_token_first)
    print response_info(get_resp)
    assert get_resp.ok
    assert len(get_resp.json()['candidate_pipelines']) == expected_count
    found_candidate_ids = [pipeline['candidate_id'] for pipeline in get_resp.json()['candidate_pipelines']]
    assert candidate_id in found_candidate_ids
