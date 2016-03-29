"""
Test cases for CandidateViewResource/get()
"""
# Candidate Service app instance
from candidate_service.candidate_app import app

# Conftest
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import AddUserRoles
from candidate_service.common.utils.test_utils import send_request, response_info
from candidate_service.common.routes import CandidateApiUrl
from candidate_service.tests.api.candidate_sample_data import generate_single_candidate_data

# Custom errors
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error


class TestGetCandidateViewInfo(object):
    def test_user_without_appropriate_permission_to_view_candidate_info(self, access_token_first, user_first, talent_pool):
        """
        Test: User without "CAN_GET_CANDIDATES" permission to view candidate's view info
        Expect: 401
        """
        # Create Candidate
        AddUserRoles.add(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        candidate_id = create_resp.json()['candidates'][0]['id']

        # Retrieve candidate's view information
        view_resp = send_request('get', CandidateApiUrl.CANDIDATE_VIEW % candidate_id, access_token_first)
        print response_info(view_resp)
        assert view_resp.status_code == 401


    def test_retrieve_candidate_view_information(self, access_token_first, user_first, talent_pool):
        """
        Test: Get information pertaining to candidate from the CandidateView resource
        Expect: 200
        """
        # Create Candidate
        AddUserRoles.add_and_get(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        candidate_id = create_resp.json()['candidates'][0]['id']

        # View candidate twice
        send_request('post', CandidateApiUrl.CANDIDATE_VIEW % candidate_id, access_token_first)
        send_request('post', CandidateApiUrl.CANDIDATE_VIEW % candidate_id, access_token_first)

        # Retrieve candidate's view information
        view_resp = send_request('get', CandidateApiUrl.CANDIDATE_VIEW % candidate_id, access_token_first)
        print response_info(view_resp)
        assert view_resp.status_code == 200
        assert len(view_resp.json()['candidate_views']) == 2
        assert view_resp.json()['candidate_views'][0]['candidate_id'] == candidate_id
        assert view_resp.json()['candidate_views'][1]['candidate_id'] == candidate_id
        assert view_resp.json()['candidate_views'][0]['user_id'] == user_first.id
        assert view_resp.json()['candidate_views'][1]['user_id'] == user_first.id


    def test_all_users_from_domain_get_candidate_view(self, access_token_first, user_first, talent_pool,
                                                      user_same_domain, access_token_same):
        """
        Test: Users from candidate's domain to get candidate's view information
        Expect: 200
        """
        AddUserRoles.add_and_get(user_first)
        AddUserRoles.get(user_same_domain)

        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        candidate_id = create_resp.json()['candidates'][0]['id']

        # user_first and user_same_domain viewing candidate
        send_request('post', CandidateApiUrl.CANDIDATE_VIEW % candidate_id, access_token_first)
        send_request('post', CandidateApiUrl.CANDIDATE_VIEW % candidate_id, access_token_same)

        # Retrieve candidate's view information
        view_resp = send_request('get', CandidateApiUrl.CANDIDATE_VIEW % candidate_id, access_token_first)
        view_resp_2 = send_request('get', CandidateApiUrl.CANDIDATE_VIEW % candidate_id, access_token_same)
        print response_info(view_resp)
        print response_info(view_resp_2)
        assert user_first.domain_id == user_same_domain.domain_id
        assert view_resp.status_code == 200 and view_resp_2.status_code == 200
        assert len(view_resp.json()['candidate_views']) == 2
        assert len(view_resp_2.json()['candidate_views']) == 2


class TestViewAggregate(object):
    def test_get_view_aggregate_of_candidate(self, access_token_first, user_first, talent_pool,
                                             user_same_domain, access_token_same):
        """
        Test: Create a candidate and view it with two different users in the same domain
        Expect: 200, multiple view objects must be returned
        """
        # Create Candidate
        AddUserRoles.add_and_get(user_first)
        AddUserRoles.add_and_get(user_same_domain)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)

        # View candidate with user_first
        candidate_id = create_resp.json()['candidates'][0]['id']
        send_request('post', CandidateApiUrl.CANDIDATE_VIEW % candidate_id, access_token_first)
        send_request('post', CandidateApiUrl.CANDIDATE_VIEW % candidate_id, access_token_first)

        # View candidate with user_same_domain
        send_request('post', CandidateApiUrl.CANDIDATE_VIEW  % candidate_id, access_token_same)
        send_request('post', CandidateApiUrl.CANDIDATE_VIEW  % candidate_id, access_token_same)

        # Retrieve view information
        get_views_resp = requests.get(
            url=CandidateApiUrl.CANDIDATE_VIEW % candidate_id + "?aggregate_by='user_id'",
            headers={'Authorization': 'Bearer %s' % access_token_first, 'content-type': 'application/json'}
        )
        print response_info(get_views_resp)
        assert get_views_resp.status_code == 200
        assert len(get_views_resp.json()['aggregated_views']) == 2, 'Four get requests have been made, ' \
                                                'but only 2 are from unique domain users'
        assert get_views_resp.json()['aggregated_views'][0]['user_id'] == user_first.id
        assert get_views_resp.json()['aggregated_views'][-1]['user_id'] == user_same_domain.id
