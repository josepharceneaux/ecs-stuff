import requests
import json
import random
from faker import Faker
from candidate_service.common.tests.conftest import *
from candidate_service.tests import populate_candidates
from helpers import get_smartlist_candidates, create_smartlist_with_candidate_ids, create_smartlist_with_search_params
from helpers import SMARTLIST_CANDIDATES_GET_URL, SMARTLIST_GET_URL, SMARTLIST_POST_URL

__author__ = 'jitesh'

fake = Faker()


class TestSmartlistResource(object):
    class TestSmartlistResourcePOST(object):
        def call_post_api(self, data, access_token):
            return requests.post(
                url=SMARTLIST_POST_URL,
                data=data,
                headers={'Authorization': 'Bearer %s' % access_token}
            )

        def test_create_smartlist_with_search_params(self, sample_user, user_auth):
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            name = fake.word()
            search_params = '{"maximum_years_experience": "5", "location": "San Jose, CA", "minimum_years_experience": "2"}'
            data = {'name': name,
                    'search_params': search_params}
            resp = self.call_post_api(data, auth_token_row['access_token'])
            assert resp.status_code == 201  # Successfully created
            response = json.loads(resp.content)
            assert 'smartlist' in response
            assert 'id' in response['smartlist']

        def test_create_smartlist_with_candidate_ids(self, sample_user, user_auth):
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            candidate_id_list = populate_candidates(auth_token_row['user_id'], count=5)
            candidate_ids = ','.join(map(str, candidate_id_list))
            name = fake.word()
            data = {'name': name,
                    'candidate_ids': candidate_ids}
            resp = self.call_post_api(data, auth_token_row['access_token'])
            assert resp.status_code == 201  # Successfully created
            response = json.loads(resp.content)
            assert 'smartlist' in response
            assert 'id' in response['smartlist']
            # Get candidates from SmartlistCandidates and assert with candidate ids used to create the smartlist
            r = get_smartlist_candidates(access_token=auth_token_row['access_token'], list_id=response['smartlist']['id'], candidate_ids_only=True)
            output = json.loads(r.content)
            assert sorted(candidate_id_list) == sorted(output['candidate_ids'])

        def test_create_smartlist_with_blank_search_params(self, sample_user, user_auth):
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            name = 'smart list with blank search params'
            search_params = ''
            data = {'name': name, 'search_params': search_params}
            resp = self.call_post_api(data, auth_token_row['access_token'])
            assert resp.status_code == 400

        def test_create_smartlist_without_candidate_ids_and_search_params(self, sample_user, user_auth):
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            name = fake.word()
            data = {'name': name}
            resp = self.call_post_api(data, auth_token_row['access_token'])
            assert resp.status_code == 400

        def test_create_smartlist_with_blank_candidate_ids(self, sample_user, user_auth):
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            data = {'name': fake.word(), 'candidate_ids': ''}
            resp = self.call_post_api(data, auth_token_row['access_token'])
            assert resp.status_code == 400

        def test_create_smartlist_with_characters_in_candidate_ids(self, sample_user, user_auth):
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            data = {'name': fake.word(), 'candidate_ids': '1, 2, "abcd", 5'}
            resp = self.call_post_api(data, auth_token_row['access_token'])
            assert resp.status_code == 400

        def test_create_smartlist_with_both_search_params_and_candidate_ids(self, sample_user, user_auth):
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            data = {'name': fake.word(), 'candidate_ids': '1', 'search_params': '{"maximum_years_experience": "5"}'}
            resp = self.call_post_api(data, auth_token_row['access_token'])
            assert resp.status_code == 400
            assert json.loads(resp.content)['error']['message'] == "Bad input: `search_params` and `candidate_ids` both are present. Service accepts only one"

        def test_create_smartlist_without_name(self, sample_user, user_auth):
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            name = "    "
            data = {'name': name, 'candidate_ids': '1'}
            resp = self.call_post_api(data, auth_token_row['access_token'])
            assert resp.status_code == 400
            assert json.loads(resp.content)['error']['message'] == "Missing input: `name` is required for creating list"

        def test_create_smartlist_presence_of_oauth_decorator(self):
            data = {'name': fake.word(), 'candidate_ids': '1'}
            resp = self.call_post_api(data, access_token='')
            assert resp.status_code == 401

    class TestSmartlistResourceGET(object):
        def call_get_api(self, list_id, access_token):
            """Calls GET API of SmartlistResource"""
            return requests.get(
                url=SMARTLIST_GET_URL + str(list_id),
                headers={'Authorization': 'Bearer %s' % access_token}
            )

        def test_get_api_with_candidate_ids(self, sample_user, user_auth):
            """
            Create candidates => create smartlist with these candidates
            Test GET api returns correct list_name, count and user_id
            """
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            list_name = fake.name()
            num_of_candidates = 4
            candidate_ids = populate_candidates(auth_token_row['user_id'], count=num_of_candidates)
            smartlist = create_smartlist_with_candidate_ids(user_id=auth_token_row['user_id'],
                                                             list_name=list_name,
                                                             candidate_ids=candidate_ids)
            resp = self.call_get_api(smartlist.id, auth_token_row['access_token'])
            assert resp.status_code == 200
            response = json.loads(resp.content)
            assert response['smartlist']['name'] == list_name
            assert response['smartlist']['candidate_count'] == num_of_candidates
            assert response['smartlist']['user_id'] == auth_token_row["user_id"]

        def test_get_api_with_search_params(self, sample_user, user_auth):
            """
            Create candidates => create smartlist with search_params
            Test GET api returns correct list_name, user_id
            """
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            list_name = fake.name()
            search_params = '{"location": "San Jose, CA"}'
            smartlist = create_smartlist_with_search_params(user_id=auth_token_row['user_id'],
                                                            list_name=list_name,
                                                            search_params=search_params)
            resp = self.call_get_api(smartlist.id, auth_token_row['access_token'])
            assert resp.status_code == 200
            response = json.loads(resp.content)
            assert response['smartlist']['name'] == list_name
            assert response['smartlist']['user_id'] == auth_token_row["user_id"]
            assert response['smartlist']['search_params'] == search_params

        def test_presence_of_oauth_decorator(self):
            resp = self.call_get_api(list_id=1, access_token='')
            assert resp.status_code == 401


class TestSmartlistCandidatesApi(object):
    def call_smartlist_candidates_get_api(self, smartlist_id, params, access_token):
        return requests.get(
                url=SMARTLIST_CANDIDATES_GET_URL % smartlist_id,
                params=params,
                headers={'Authorization': 'Bearer %s' % access_token})

    def test_return_candidate_ids_only(self, sample_user, user_auth):
        auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
        num_of_candidates = random.choice(range(1, 10))
        candidate_ids = populate_candidates(auth_token_row['user_id'], count=num_of_candidates)
        smartlist = create_smartlist_with_candidate_ids(user_id=auth_token_row['user_id'],
                                                         list_name=fake.name(),
                                                         candidate_ids=candidate_ids)
        params = {'fields': 'candidate_ids_only'}
        resp = self.call_smartlist_candidates_get_api(smartlist.id, params, auth_token_row['access_token'])
        assert resp.status_code == 200
        response = json.loads(resp.content)
        assert response['total_found'] == num_of_candidates
        assert sorted(response['candidate_ids']) == sorted(candidate_ids)

    def test_return_count_only(self, sample_user, user_auth):
        auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
        num_of_candidates = random.choice(range(1, 10))
        candidate_ids = populate_candidates(auth_token_row['user_id'], count=num_of_candidates)
        smartlist = create_smartlist_with_candidate_ids(user_id=auth_token_row['user_id'],
                                                         list_name=fake.name(),
                                                         candidate_ids=candidate_ids)
        params = {'fields': 'count_only'}
        resp = self.call_smartlist_candidates_get_api(smartlist.id, params, auth_token_row['access_token'])
        assert resp.status_code == 200
        response = json.loads(resp.content)
        assert response['total_found'] == num_of_candidates
        assert response['candidate_ids'] == []

    def test_return_all_fields(self, sample_user, user_auth):
        auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
        num_of_candidates = random.choice(range(1, 10))
        candidate_ids = populate_candidates(auth_token_row['user_id'], count=num_of_candidates)
        smartlist = create_smartlist_with_candidate_ids(user_id=auth_token_row['user_id'],
                                                         list_name=fake.name(),
                                                         candidate_ids=candidate_ids)
        params = {'fields': 'all'}
        resp = self.call_smartlist_candidates_get_api(smartlist.id, params, auth_token_row['access_token'])
        assert resp.status_code == 200
        response = json.loads(resp.content)
        assert response['total_found'] == num_of_candidates
        assert 'emails' in response['candidates'][0]
        assert 'phone_numbers' in response['candidates'][0]
        # TODO: assert candidate emails and phone_numbers once populate_candidates function is fixed

    def test_without_list_id(self, sample_user, user_auth):
        auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
        params = {'fields': 'candidate_ids_only'}
        resp = self.call_smartlist_candidates_get_api('', params, auth_token_row['access_token'])
        assert resp.status_code == 404

    def test_string_in_list_id(self, sample_user, user_auth):
        auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
        params = {}
        resp = self.call_smartlist_candidates_get_api('123abc', params, auth_token_row['access_token'])
        assert resp.status_code == 404

    def test_incorrect_list_id(self, sample_user, user_auth):
        auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
        params = {}
        resp = self.call_smartlist_candidates_get_api('123456789', params, auth_token_row['access_token'])
        assert resp.status_code == 404

    def test_presence_of_oauth_decorator(self):
        params = {'id': 1, 'fields': 'all'}
        resp = self.call_smartlist_candidates_get_api(2, params, access_token='')
        assert resp.status_code == 401

    def test_get_candidates_from_search_params(self):
        # TODO
        pass







