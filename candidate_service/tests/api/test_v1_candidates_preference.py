"""
Test cases for CandidatePreferenceResource
"""
# Candidate Service app instance
from candidate_service.candidate_app import app

# Conftest
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import (
    response_info, request_to_candidate_preference_resource,
    request_to_candidates_resource, AddUserRoles
)
from candidate_service.tests.api.candidate_sample_data import generate_single_candidate_data


class TestCreateSubscriptionPreference(object):
    def test_access_without_auth_token(self, user_first):
        """
        Test: Access endpoint without auth token
        Expect: 401
        """
        resp = request_to_candidate_preference_resource('', 'post', 5)
        print response_info(response=resp)
        assert resp.status_code == 401 and resp.json()['error']['code'] == 11

    def test_access_endpoint_without_role(self, access_token_first, user_first):
        """
        Test: Access endpoint without required user role
        Expect: 401
        """
        resp = request_to_candidate_preference_resource(access_token_first, 'post', 5)
        print response_info(response=resp)
        assert resp.status_code == 401

    def test_add_candidate_subs_preference(self, access_token_first, user_first, talent_pool):
        """
        Test: Add subscription preference for the candidate
        Expect: 204
        """
        # Create candidate and candidate subscription preference
        AddUserRoles.add_and_get(user=user_first)
        data = generate_single_candidate_data([talent_pool.id])
        candidate_id = request_to_candidates_resource(access_token_first, 'post', data) \
            .json()['candidates'][0]['id']
        data = {'frequency_id': 1}
        resp = request_to_candidate_preference_resource(access_token_first, 'post', candidate_id, data)
        print response_info(resp)
        assert resp.status_code == 204

        # Retrieve Candidate's subscription preference
        resp = request_to_candidate_preference_resource(access_token_first, 'get', candidate_id)
        print response_info(resp)
        assert resp.status_code == 200
        assert resp.json()['candidate']['subscription_preference']['frequency_id'] == 1

    def test_add_multiple_subscription_preference(self, access_token_first, user_first,
                                                  candidate_first):
        """
        Test: Attempt to create multiple subscription preferences for candidate
        Expect: 400, only one subscription preference per candidate is permitted
        """
        # Create candidate and its subscription preference
        AddUserRoles.add(user=user_first)
        data = dict(frequency_id=1)
        resp = request_to_candidate_preference_resource(access_token_first, 'post',
                                                        candidate_first.id, data)
        print response_info(response=resp)
        assert resp.status_code == 204
        resp = request_to_candidate_preference_resource(access_token_first, 'post',
                                                        candidate_first.id, data)
        print response_info(response=resp)
        assert resp.status_code == 400 and resp.json()['error']['code'] == 3143

    def test_access_endpoint_using_non_json_data(self, access_token_first, user_first, candidate_first):
        """
        Test: Attempt to send non json data
        Expect: 400
        """
        from candidate_service.common.routes import CandidateApiUrl
        AddUserRoles.add(user=user_first)
        resp = requests.post(
            url=CandidateApiUrl.CANDIDATE_PREFERENCE % candidate_first.id,
            headers={'Authorization': 'Bearer {}'.format(access_token_first), 'content-type': 'application/json'},
            data=json.dumps({'frequency_id': 1})
        )
        print response_info(resp)


class TestGetSubscriptionPreference(object):
    def test_access_without_auth_token(self, user_first):
        """
        Test: Access endpoint without auth token
        Expect: 401
        """
        resp = request_to_candidate_preference_resource('', 'get', 5)
        print response_info(response=resp)
        assert resp.status_code == 401 and resp.json()['error']['code'] == 11

    def test_access_endpoint_without_role(self, access_token_first, user_first):
        """
        Test: Access endpoint without required user role
        Expect: 401
        """
        resp = request_to_candidate_preference_resource(access_token_first, 'get', 5)
        print response_info(response=resp)
        assert resp.status_code == 401

    def test_get_non_existing_candidate_preference(self, access_token_first, user_first, talent_pool):
        """
        Test: Retrieve candidate's preferences that don't exist in the database
        Expect:  200, should just get an empty dict for subscription_preference
        """
        # Create candidate
        AddUserRoles.add_and_get(user=user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = request_to_candidates_resource(access_token_first, 'post', data)
        candidate_id = create_resp.json()['candidates'][0]['id']

        # Retrieve subscription preference of the candidate
        resp = request_to_candidate_preference_resource(access_token_first, 'get', candidate_id)
        print response_info(resp)
        assert resp.status_code == 200
        assert resp.json()['candidate']['subscription_preference'] == {}


class TestUpdateSubscriptionPreference(object):
    def test_access_without_auth_token(self, user_first):
        """
        Test: Access endpoint without auth token
        Expect: 401
        """
        resp = request_to_candidate_preference_resource('', 'put', 5)
        print response_info(response=resp)
        assert resp.status_code == 401 and resp.json()['error']['code'] == 11

    def test_access_endpoint_without_role(self, access_token_first, user_first):
        """
        Test: Access endpoint without required user role
        Expect: 401
        """
        resp = request_to_candidate_preference_resource(access_token_first, 'put', 5)
        print response_info(response=resp)
        assert resp.status_code == 401

    def test_update_non_existing_candidate_preference(self, access_token_first, user_first, talent_pool):
        """
        Test: Attempt to update a non existing candidate subs preference
        Expect: 400, although it's "not found" it is however a misuse of the resource
        """
        AddUserRoles.add_get_edit(user=user_first)
        # Create candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = request_to_candidates_resource(access_token_first, 'post', data)
        candidate_id = create_resp.json()['candidates'][0]['id']

        # Update candidate's subscription preferences
        data = {'frequency_id': 1}  # this is arbitrary
        resp = request_to_candidate_preference_resource(access_token_first, 'put', candidate_id, data)
        print response_info(resp)
        assert resp.status_code == 400
        assert resp.json()['error']['code'] == 3142

    def test_update_candidate_pref_without_providing_adequate_data(self, access_token_first, user_first, talent_pool):
        """
        Test: Attempt to update candidate's subs pref with missing data
        Expect: 400
        """
        # Create candidate
        AddUserRoles.add_get_edit(user=user_first)
        data = generate_single_candidate_data([talent_pool.id])
        candidate_id = request_to_candidates_resource(access_token_first, 'post', data) \
            .json()['candidates'][0]['id']

        # Update candidate's subs preference with missing inputs
        data_1, data_2, data_3, data_4 = None, {}, {'': ''}, {'frequency_id': None}
        resp_1 = request_to_candidate_preference_resource(access_token_first, 'put', candidate_id, data_1)
        resp_2 = request_to_candidate_preference_resource(access_token_first, 'put', candidate_id, data_2)
        resp_3 = request_to_candidate_preference_resource(access_token_first, 'put', candidate_id, data_3)
        resp_4 = request_to_candidate_preference_resource(access_token_first, 'put', candidate_id, data_4)
        print response_info(resp_1), response_info(resp_2), response_info(resp_3), response_info(resp_4)
        assert resp_1.status_code == 400 and resp_1.json()['error']['code'] == 3000
        assert resp_2.status_code == 400 and resp_2.json()['error']['code'] == 3000
        assert resp_3.status_code == 400 and resp_3.json()['error']['code'] == 3000
        assert resp_4.status_code == 400 and resp_4.json()['error']['code'] == 3000

    def test_update_subs_pref_of_a_non_existing_candidate(self, access_token_first, user_first, talent_pool):
        """
        Test: Attempt to update the subs pref of a non existing candidate
        Expect: 404
        """
        # Update candidate's subs preference
        AddUserRoles.edit(user=user_first)
        last_candidate = Candidate.query.order_by(Candidate.id.desc()).first()
        non_existing_candidate_id = last_candidate.id * 100
        data = {'frequency_id': 1}
        resp = request_to_candidate_preference_resource(access_token_first, 'put', non_existing_candidate_id, data)
        print response_info(resp)
        assert resp.status_code == 404 and resp.json()['error']['code'] == 3010

    def test_update_subs_pref_of_candidate(self, access_token_first, user_first, talent_pool):
        """
        Test: Update candidate's subscription preference
        Expect: 200
        """
        # Create candidate and candidate's subscription preference
        AddUserRoles.all_roles(user=user_first)
        data = generate_single_candidate_data([talent_pool.id])
        candidate_id = request_to_candidates_resource(access_token_first, 'post', data) \
            .json()['candidates'][0]['id']
        request_to_candidate_preference_resource(access_token_first, 'post', candidate_id,
                                                 data={'frequency_id': 1})

        # Update candidate's subscription preference
        resp = request_to_candidate_preference_resource(access_token_first, 'put', candidate_id,
                                                        data={'frequency_id': 2})
        assert resp.status_code == 204

        # Retrieve candidate's subscription preference
        resp = request_to_candidate_preference_resource(access_token_first, 'get', candidate_id)
        print response_info(resp)
        assert resp.status_code == 200
        assert resp.json()['candidate']['id'] == candidate_id
        assert resp.json()['candidate']['subscription_preference']['frequency_id'] == 2


class TestDeleteSubscriptionPreference(object):
    def test_access_without_auth_token(self, user_first):
        """
        Test: Access endpoint without auth token
        Expect: 401
        """
        resp = request_to_candidate_preference_resource('', 'delete', 5)
        print response_info(response=resp)
        assert resp.status_code == 401 and resp.json()['error']['code'] == 11

    def test_access_endpoint_without_role(self, access_token_first, user_first):
        """
        Test: Access endpoint without required user role
        Expect: 401
        """
        resp = request_to_candidate_preference_resource(access_token_first, 'delete', 5)
        print response_info(response=resp)
        assert resp.status_code == 401

    def test_delete_candidate_preference(self, access_token_first, user_first, talent_pool):
        """
        Test: Delete candidate's subscription preference
        Expect: 200, should just get an empty dict for subscription_preference
        """
        # Create candidate and candidate's subscription preference
        AddUserRoles.all_roles(user=user_first)
        data = generate_single_candidate_data([talent_pool.id])
        candidate_id = request_to_candidates_resource(access_token_first, 'post', data) \
            .json()['candidates'][0]['id']
        request_to_candidate_preference_resource(access_token_first, 'post', candidate_id, {'frequency_id': 1})

        # Update candidate's subscription preference
        resp = request_to_candidate_preference_resource(access_token_first, 'delete', candidate_id)
        print response_info(resp)
        assert resp.status_code == 204

        # Retrieve candidate's subscription preference
        resp = request_to_candidate_preference_resource(access_token_first, 'get', candidate_id)
        print response_info(resp)
        assert resp.status_code == 200
        assert resp.json()['candidate']['subscription_preference'] == {}
