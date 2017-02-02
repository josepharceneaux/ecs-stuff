"""
Test cases for CandidatePreferenceResource
"""
# Conftest
from candidate_sample_data import generate_single_candidate_data
from candidate_service.common.tests.conftest import *
from candidate_service.common.utils.test_utils import send_request, response_info
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error


class TestCreateSubscriptionPreference(object):
    def test_access_without_auth_token(self):
        """
        Test: Access endpoint without auth token
        Expect: 401
        """
        resp = send_request('post', CandidateApiUrl.CANDIDATE_PREFERENCE % '5', None)
        print response_info(resp)
        assert resp.status_code == 401 and resp.json()['error']['code'] == 11

    def test_add_candidate_subscription_preference(self, access_token_first, talent_pool):
        """
        Test: Add subscription preference for the candidate
        Expect: 204
        """
        # Create candidate and candidate subscription preference
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        candidate_id = create_resp.json()['candidates'][0]['id']
        data = {'frequency_id': 1}
        resp = send_request('post', CandidateApiUrl.CANDIDATE_PREFERENCE % candidate_id, access_token_first, data)
        print response_info(resp)
        assert resp.status_code == 204

        # Retrieve Candidate's subscription preference
        resp = send_request('get', CandidateApiUrl.CANDIDATE_PREFERENCE % candidate_id, access_token_first)
        print response_info(resp)
        assert resp.status_code == 200
        assert resp.json()['candidate']['subscription_preference']['frequency_id'] == 1

    def test_add_multiple_subscription_preference(self, access_token_first, candidate_first):
        """
        Test: Attempt to create multiple subscription preferences for candidate
        Expect: 400, only one subscription preference per candidate is permitted
        """
        # Create candidate and its subscription preference
        data = dict(frequency_id=1)
        resp = send_request('post', CandidateApiUrl.CANDIDATE_PREFERENCE % candidate_first.id, access_token_first, data)
        print response_info(resp)
        assert resp.status_code == 204
        resp = send_request('post', CandidateApiUrl.CANDIDATE_PREFERENCE % candidate_first.id, access_token_first, data)
        print response_info(resp)
        assert resp.status_code == 400
        assert resp.json()['error']['code'] == custom_error.PREFERENCE_EXISTS

    def test_access_endpoint_using_non_json_data(self, access_token_first, candidate_first):
        """
        Test: Attempt to send non json data
        Expect: 400
        """
        resp = requests.post(
            url=CandidateApiUrl.CANDIDATE_PREFERENCE % candidate_first.id,
            headers={'Authorization': 'Bearer {}'.format(access_token_first), 'content-type': 'application/json'},
            data=json.dumps({'frequency_id': 1})
        )
        print response_info(resp)


class TestGetSubscriptionPreference(object):
    def test_access_without_auth_token(self):
        """
        Test: Access endpoint without auth token
        Expect: 401
        """
        resp = send_request('get', CandidateApiUrl.CANDIDATE_PREFERENCE % "5", None)
        print response_info(resp)
        assert resp.status_code == 401 and resp.json()['error']['code'] == 11

    def test_get_non_existing_candidate_preference(self, access_token_first, talent_pool):
        """
        Test: Retrieve candidate's preferences that don't exist in the database
        Expect:  200, should just get an empty dict for subscription_preference
        """
        # Create candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        candidate_id = create_resp.json()['candidates'][0]['id']

        # Retrieve subscription preference of the candidate
        resp = send_request('get', CandidateApiUrl.CANDIDATE_PREFERENCE % candidate_id, access_token_first)
        print response_info(resp)
        assert resp.status_code == 200
        assert resp.json()['candidate']['subscription_preference'] == {}


class TestUpdateSubscriptionPreference(object):
    def test_access_without_auth_token(self):
        """
        Test: Access endpoint without auth token
        Expect: 401
        """
        resp = send_request('put', CandidateApiUrl.CANDIDATE_PREFERENCE % "5", None)
        print response_info(resp)
        assert resp.status_code == 401 and resp.json()['error']['code'] == 11

    def test_update_non_existing_candidate_preference(self, access_token_first, talent_pool):
        """
        Test: Attempt to update a non existing candidate subs preference
        Expect: 400, although it's "not found" it is however a misuse of the resource
        """
        # Create candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        candidate_id = create_resp.json()['candidates'][0]['id']

        # Update candidate's subscription preferences
        data = {'frequency_id': 1}  # this is arbitrary
        resp = send_request('put', CandidateApiUrl.CANDIDATE_PREFERENCE % candidate_id, access_token_first, data)
        print response_info(resp)
        assert resp.status_code == 400
        assert resp.json()['error']['code'] == custom_error.NO_PREFERENCES

    def test_update_candidate_pref_without_providing_adequate_data(self, access_token_first, talent_pool):
        """
        Test: Attempt to update candidate's subs pref with missing data
        Expect: 400
        """
        # Create candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        candidate_id = create_resp.json()['candidates'][0]['id']

        # Update candidate's subs preference with missing inputs
        data_1, data_2, data_3, data_4 = None, {}, {'': ''}, {'frequency_id': None}
        resp_1 = send_request('put', CandidateApiUrl.CANDIDATE_PREFERENCE % candidate_id, access_token_first, data_1)
        resp_2 = send_request('put', CandidateApiUrl.CANDIDATE_PREFERENCE % candidate_id, access_token_first, data_2)
        resp_3 = send_request('put', CandidateApiUrl.CANDIDATE_PREFERENCE % candidate_id, access_token_first, data_3)
        resp_4 = send_request('put', CandidateApiUrl.CANDIDATE_PREFERENCE % candidate_id, access_token_first, data_4)
        print response_info(resp_1), response_info(resp_2), response_info(resp_3), response_info(resp_4)
        assert resp_1.status_code == 400 and resp_1.json()['error']['code'] == custom_error.INVALID_INPUT
        assert resp_2.status_code == 400 and resp_2.json()['error']['code'] == custom_error.INVALID_INPUT
        assert resp_3.status_code == 400 and resp_3.json()['error']['code'] == custom_error.INVALID_INPUT
        assert resp_4.status_code == 400 and resp_4.json()['error']['code'] == custom_error.INVALID_INPUT

    def test_update_subs_pref_of_a_non_existing_candidate(self, access_token_first, user_first):
        """
        Test: Attempt to update the subs pref of a non existing candidate
        Expect: 404
        """
        # Update candidate's subs preference
        last_candidate = Candidate.query.order_by(Candidate.id.desc()).first()
        non_existing_candidate_id = str(last_candidate.id * 100)
        data = {'frequency_id': 1}
        resp = send_request('put', CandidateApiUrl.CANDIDATE_PREFERENCE % non_existing_candidate_id,
                            access_token_first, data)
        print response_info(resp)
        assert resp.status_code == 404
        assert resp.json()['error']['code'] == custom_error.CANDIDATE_NOT_FOUND

    def test_update_subs_pref_of_candidate(self, access_token_first, talent_pool):
        """
        Test: Update candidate's subscription preference
        Expect: 200
        """
        # Create candidate and candidate's subscription preference
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        candidate_id = create_resp.json()['candidates'][0]['id']
        send_request('post', CandidateApiUrl.CANDIDATE_PREFERENCE % candidate_id, access_token_first,
                     data={'frequency_id': 1})

        # Update candidate's subscription preference
        resp = send_request('put', CandidateApiUrl.CANDIDATE_PREFERENCE % candidate_id, access_token_first,
                     data={'frequency_id': 2})
        assert resp.status_code == 204

        # Retrieve candidate's subscription preference
        resp = send_request('get', CandidateApiUrl.CANDIDATE_PREFERENCE % candidate_id, access_token_first)
        print response_info(resp)
        assert resp.status_code == 200
        assert resp.json()['candidate']['id'] == candidate_id
        assert resp.json()['candidate']['subscription_preference']['frequency_id'] == 2


class TestDeleteSubscriptionPreference(object):
    def test_access_without_auth_token(self):
        """
        Test: Access endpoint without auth token
        Expect: 401
        """
        resp = send_request('delete', CandidateApiUrl.CANDIDATE_PREFERENCE % "5", None)
        print response_info(resp)
        assert resp.status_code == 401 and resp.json()['error']['code'] == 11

    def test_delete_candidate_preference(self, access_token_first, talent_pool):
        """
        Test: Delete candidate's subscription preference
        Expect: 200, should just get an empty dict for subscription_preference
        """
        # Create candidate and candidate's subscription preference
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        candidate_id = create_resp.json()['candidates'][0]['id']
        send_request('post', CandidateApiUrl.CANDIDATE_PREFERENCE % candidate_id,
                     access_token_first, {'frequency_id': 1})

        # Update candidate's subscription preference
        resp = send_request('delete', CandidateApiUrl.CANDIDATE_PREFERENCE % candidate_id, access_token_first)
        print response_info(resp)
        assert resp.status_code == 204

        # Retrieve candidate's subscription preference
        resp = send_request('get', CandidateApiUrl.CANDIDATE_PREFERENCE % candidate_id, access_token_first)
        print response_info(resp)
        assert resp.status_code == 200
        assert resp.json()['candidate']['subscription_preference'] == {}
