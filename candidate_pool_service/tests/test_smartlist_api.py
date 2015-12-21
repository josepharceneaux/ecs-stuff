from candidate_pool_service.candidate_pool_app import app
from candidate_pool_service.common.tests.conftest import *
from candidate_pool_service.common.helper.api_calls import create_candidates_from_candidate_api
from candidate_pool_service.common.tests.fake_testing_data_generator import FakeCandidatesData
from candidate_pool_service.modules.smartlists import save_smartlist
from candidate_pool_service.common.models.smartlist import Smartlist
import json
import random
import time
import requests
from faker import Faker

__author__ = 'jitesh'

fake = Faker()

# TODO: Use routes.py once it is ready
SMARTLIST_URL = 'http://localhost:8008/v1/smartlists'
SMARTLIST_CANDIDATES_URL = 'http://localhost:8008/v1/smartlists/%s/candidates'


class TestSmartlistResource(object):
    class TestSmartlistResourcePOST(object):
        def call_post_api(self, data, access_token):
            return requests.post(
                url=SMARTLIST_URL,
                data=json.dumps(data),
                headers={'Authorization': 'Bearer %s' % access_token,
                         'content-type': 'application/json'}
            )

        def test_create_smartlist_with_search_params(self, sample_user, user_auth):
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            name = fake.word()
            search_params = {"maximum_years_experience": "5", "location": "San Jose, CA", "minimum_years_experience": "2"}
            data = {'name': name, 'search_params': search_params}
            resp = self.call_post_api(data, auth_token_row['access_token'])
            assert resp.status_code == 201  # Successfully created
            response = json.loads(resp.content)
            assert 'smartlist' in response
            assert 'id' in response['smartlist']

        def test_create_smartlist_with_candidate_ids(self, sample_user, user_auth):
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            data = FakeCandidatesData.create(count=5)
            candidate_id_list = create_candidates_from_candidate_api(auth_token_row['access_token'], data)
            candidate_ids = ','.join(map(str, candidate_id_list))
            name = fake.word()
            data = {'name': name,
                    'candidate_ids': candidate_ids}
            resp = self.call_post_api(data, auth_token_row['access_token'])
            assert resp.status_code == 201  # Successfully created
            response = json.loads(resp.content)
            assert 'smartlist' in response
            assert 'id' in response['smartlist']
            smartlist_id = response['smartlist']['id']
            # Get candidate_ids from SmartlistCandidates and assert with candidate ids used to create the smartlist
            smartlist_candidates_api = TestSmartlistCandidatesApi()
            response = smartlist_candidates_api.call_smartlist_candidates_get_api(smartlist_id,
                                                                                  {'fields': 'candidate_ids_only'},
                                                                                  auth_token_row['access_token'])
            smartlist_candidate_ids = [row['id'] for row in response.json()['candidates']]
            assert sorted(candidate_id_list) == sorted(smartlist_candidate_ids)

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
            data = {'name': fake.word(), 'candidate_ids': '1', 'search_params': {"maximum_years_experience": "5"}}
            resp = self.call_post_api(data, auth_token_row['access_token'])
            assert resp.status_code == 400
            assert json.loads(resp.content)['error']['message'] == "Bad input: `search_params` and `candidate_ids` both are present. Service accepts only one"

        def test_create_smartlist_with_invalid_search_params(self, access_token_first):
            data = {'name': fake.word(), 'search_params': "location=San Jose, CA"}
            resp = self.call_post_api(data, access_token_first)
            assert resp.status_code == 400
            assert json.loads(resp.content)['error']['message'] == "`search_params` should in dictionary format."

        def test_create_smartlist_with_string_search_params(self, access_token_first):
            data2 = {'name': fake.word(), 'search_params': "'example'"}
            resp = self.call_post_api(data2, access_token_first)
            assert resp.status_code == 400
            assert json.loads(resp.content)['error']['message'] == "`search_params` should in dictionary format."

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

        def test_create_smartlist_from_candidates_not_in_users_domain(self, access_token_first, access_token_second):
            # User_second creates candidates
            data = FakeCandidatesData.create(count=3)
            candidate_id_list = create_candidates_from_candidate_api(access_token_second, data)
            candidate_ids = ','.join(map(str, candidate_id_list))
            data = {'name': fake.word(), 'candidate_ids': candidate_ids}
            # first user (access_token_first) trying to create smartlist with second user's candidates.
            resp = self.call_post_api(data, access_token_first)
            assert resp.status_code == 403
            assert json.loads(resp.content)['error']['message'] == "Provided list of candidates does not belong to user's domain"

    class TestSmartlistResourceGET(object):
        def call_get_api(self, access_token, list_id=None):
            """Calls GET API of SmartlistResource"""
            return requests.get(
                url=SMARTLIST_URL + '/%s' % list_id if list_id else SMARTLIST_URL,
                headers={'Authorization': 'Bearer %s' % access_token}
            )

        def test_get_api_with_candidate_ids(self, sample_user, user_auth):
            """
            Test GET API for smartlist (with candidate ids)
            """
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            list_name = fake.name()
            num_of_candidates = 4
            data = FakeCandidatesData.create(count=num_of_candidates)
            candidate_ids = create_candidates_from_candidate_api(auth_token_row['access_token'], data)
            smartlist = save_smartlist(user_id=auth_token_row['user_id'], name=list_name,
                                       candidate_ids=candidate_ids)
            resp = self.call_get_api(auth_token_row['access_token'], smartlist.id)
            assert resp.status_code == 200
            response = json.loads(resp.content)
            assert response['smartlist']['name'] == list_name
            assert response['smartlist']['total_found'] == num_of_candidates
            assert response['smartlist']['user_id'] == auth_token_row["user_id"]

        def test_get_api_with_search_params(self, sample_user, user_auth):
            """
            Test GET API for smartlist (with search_params)
            """
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            list_name = fake.name()
            search_params = json.dumps({"location": "San Jose, CA"})
            smartlist = save_smartlist(user_id=auth_token_row['user_id'],
                                       name=list_name,
                                       search_params=search_params)
            resp = self.call_get_api(auth_token_row['access_token'], smartlist.id)
            assert resp.status_code == 200
            response = json.loads(resp.content)
            assert response['smartlist']['name'] == list_name
            assert response['smartlist']['user_id'] == auth_token_row["user_id"]
            assert response['smartlist']['search_params'] == search_params

        def test_get_smartlist_from_outside_domain(self, user_first, access_token_first, access_token_second):
            """Test for validate_list_belongs_to_domain"""
            list_name = fake.name()
            search_params = json.dumps({"location": "San Jose, CA"})
            # user 1 of domain 1 saving smartlist
            smartlist = save_smartlist(user_id=user_first.id,
                                       name=list_name,
                                       search_params=search_params)
            # user 1 of domain 1 getting smartlist
            resp = self.call_get_api(access_token_first, smartlist.id)
            assert resp.status_code == 200
            # user 2 of domain 2 getting smartlist
            resp = self.call_get_api(access_token_second, smartlist.id)
            assert resp.status_code == 403

        def test_presence_of_oauth_decorator(self):
            resp = self.call_get_api(access_token='', list_id=1)
            assert resp.status_code == 401

    class TestSmartlistResourceDELETE(object):
        def call_delete_api(self, access_token, list_id=None):
            """Calls DELETE API of SmartlistResource"""
            return requests.delete(
                url=SMARTLIST_URL + '/%s' % list_id if list_id else SMARTLIST_URL,
                headers={'Authorization': 'Bearer %s' % access_token}
            )

        def test_delete_smartlist(self, sample_user, user_auth):
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            list_name = fake.name()
            data = FakeCandidatesData.create(count=1)
            candidate_ids = create_candidates_from_candidate_api(auth_token_row['access_token'], data)
            smartlist = save_smartlist(user_id=auth_token_row['user_id'], name=list_name,
                                       candidate_ids=candidate_ids)
            db.session.commit()
            smartlist_obj = Smartlist.query.get(smartlist.id)
            assert smartlist_obj.is_hidden is False
            response = self.call_delete_api(auth_token_row['access_token'], smartlist.id)
            assert response.status_code == 200
            resp = response.json()
            assert 'smartlist' in resp
            assert resp['smartlist']['id'] == smartlist.id
            db.session.commit()
            smartlist_after_deletion = Smartlist.query.get(smartlist.id)
            assert smartlist_after_deletion.is_hidden is True  # Verify smartlist is hidden
            # Try calling GET method with deleted (hidden) list id and it should give 404 Not found
            output = requests.get(
                url=SMARTLIST_URL + '/%s' % smartlist_after_deletion.id,
                headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
            )
            assert output.status_code == 404  # Get method should give 404 for hidden smartlist

        def test_delete_smartlist_from_other_domain(self, user_first, access_token_first, access_token_second):
            list_name = fake.name()
            data = FakeCandidatesData.create(count=1)
            candidate_ids = create_candidates_from_candidate_api(access_token_first, data)
            # User 1 from domain 1 created smartlist
            smartlist = save_smartlist(user_id=user_first.id, name=list_name, candidate_ids=candidate_ids)
            # User 2 from domain 2 trying to delete smartlist
            response = self.call_delete_api(access_token_second, smartlist.id)
            assert response.status_code == 403

        def test_delete_smartlist_without_int_id(self, access_token_first):
            response = self.call_delete_api(access_token_first, 'abcd')
            assert response.status_code == 404

        def test_delete_deleted_smartlist(self, user_first, access_token_first):
            list_name = fake.name()
            search_params = json.dumps({"location": "San Jose, CA"})
            smartlist = save_smartlist(user_id=user_first.id,
                                       name=list_name,
                                       search_params=search_params)
            response = self.call_delete_api(access_token_first, smartlist.id)
            assert response.status_code == 200
            # Now try to delete this deleted smartlist
            response2 = self.call_delete_api(access_token_first, smartlist.id)
            assert response2.status_code == 404


class TestSmartlistCandidatesApi(object):
    def call_smartlist_candidates_get_api(self, smartlist_id, params, access_token):
        return requests.get(
                url=SMARTLIST_CANDIDATES_URL % smartlist_id,
                params=params,
                headers={'Authorization': 'Bearer %s' % access_token})

    def test_return_candidate_ids_only(self, sample_user, user_auth):
        auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
        num_of_candidates = random.choice(range(1, 10))
        data = FakeCandidatesData.create(count=num_of_candidates)
        candidate_ids = create_candidates_from_candidate_api(auth_token_row['access_token'], data)
        smartlist = save_smartlist(user_id=auth_token_row['user_id'], name=fake.name(),
                                   candidate_ids=candidate_ids)
        params = {'fields': 'candidate_ids_only'}
        resp = self.call_smartlist_candidates_get_api(smartlist.id, params, auth_token_row['access_token'])
        assert resp.status_code == 200
        response = json.loads(resp.content)
        assert response['total_found'] == num_of_candidates
        output_candidate_ids = [candidate['id'] for candidate in response['candidates']]
        assert sorted(output_candidate_ids) == sorted(candidate_ids)

    def test_return_count_only(self, sample_user, user_auth):
        auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
        num_of_candidates = random.choice(range(1, 10))
        data = FakeCandidatesData.create(count=num_of_candidates)
        candidate_ids = create_candidates_from_candidate_api(auth_token_row['access_token'], data)
        smartlist = save_smartlist(user_id=auth_token_row['user_id'], name=fake.name(),
                                   candidate_ids=candidate_ids)
        params = {'fields': 'count_only'}
        resp = self.call_smartlist_candidates_get_api(smartlist.id, params, auth_token_row['access_token'])
        assert resp.status_code == 200
        response = json.loads(resp.content)
        assert response['total_found'] == num_of_candidates
        assert response['candidates'] == []

    def test_return_all_fields(self, sample_user, user_auth):
        auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
        num_of_candidates = random.choice(range(1, 10))
        data = FakeCandidatesData.create(count=num_of_candidates)
        candidate_ids = create_candidates_from_candidate_api(auth_token_row['access_token'], data)
        smartlist = save_smartlist(user_id=auth_token_row['user_id'], name=fake.name(),
                                   candidate_ids=candidate_ids)
        params = {'fields': 'all'}
        resp = self.call_smartlist_candidates_get_api(smartlist.id, params, auth_token_row['access_token'])
        assert resp.status_code == 200
        response = json.loads(resp.content)
        assert response['total_found'] == num_of_candidates
        assert 'emails' in response['candidates'][0]

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

    def test_get_candidates_from_search_params(self, sample_user, user_auth):
        city = 'San Jose'
        state = 'CA'
        auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
        address = [{'address_line_1': fake.street_address(), 'city': city,
                    'state': state, 'zip_code': '95132', 'country': 'US'}]
        no_of_candidates = 2
        first_name = 'special'
        data = FakeCandidatesData.create(count=no_of_candidates, first_name=first_name, address_list=address)
        candidate_ids = create_candidates_from_candidate_api(auth_token_row['access_token'], data)
        # Wait for cloudsearch to upload candidate documents
        time.sleep(20)
        search_params = json.dumps({"query": "%s" % first_name})
        smartlist = save_smartlist(user_id=auth_token_row['user_id'], name=fake.name(),
                                   search_params=search_params)

        resp = self.call_smartlist_candidates_get_api(smartlist.id, {}, auth_token_row['access_token'])
        assert resp.status_code == 200
        response = resp.json()
        output_candidate_ids = [long(candidate['id']) for candidate in response['candidates']]
        assert response['total_found'] == no_of_candidates
        assert sorted(candidate_ids) == sorted(output_candidate_ids)

    def test_get_candidates_from_deleted_smartlist(self, user_first, access_token_first):
        list_name = fake.name()
        search_params = json.dumps({"location": "San Jose, CA"})
        smartlist = save_smartlist(user_id=user_first.id,
                                   name=list_name,
                                   search_params=search_params)
        # Delete (hide) this smartlist
        response = requests.delete(url=SMARTLIST_URL + '/%s' % smartlist.id,
                                   headers={'Authorization': 'Bearer %s' % access_token_first})
        assert response.status_code == 200
        # Now try getting candidates from this deleted(hidden) smartlist
        response = self.call_smartlist_candidates_get_api(smartlist.id, {'fields': 'all'}, access_token_first)
        assert response.status_code == 404
