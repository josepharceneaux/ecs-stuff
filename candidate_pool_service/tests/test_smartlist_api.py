from candidate_pool_service.candidate_pool_app import app
from candidate_pool_service.common.tests.conftest import *
from common_functions import create_candidates_from_candidate_api
from candidate_pool_service.modules.smartlists import save_smartlist
from candidate_pool_service.common.routes import CandidatePoolApiUrl
from candidate_pool_service.common.tests.cloud_search_common_functions import *
from candidate_pool_service.common.models.smartlist import Smartlist, SmartlistStats
from candidate_pool_service.common.utils.handy_functions import add_role_to_test_user
from candidate_pool_service.common.tests.fake_testing_data_generator import FakeCandidatesData

import json
import random
import time
import requests
from time import sleep
from datetime import timedelta

__author__ = 'jitesh'


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
            """Test to create smartlist by passing valid search_params as parameter. It should create smartlist"""
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
            """Test to create smartlist with candidate ids (smartlist with candidate ids is dumblist)."""
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            data = FakeCandidatesData.create(count=5)
            candidate_ids = create_candidates_from_candidate_api(auth_token_row['access_token'], data)
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
            assert sorted(candidate_ids) == sorted(smartlist_candidate_ids)

        def test_create_smartlist_with_blank_search_params(self, sample_user, user_auth):
            """Test blank search params validation"""
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            name = 'smart list with blank search params'
            search_params = ''
            data = {'name': name, 'search_params': search_params}
            resp = self.call_post_api(data, auth_token_row['access_token'])
            assert resp.status_code == 400

        def test_create_smartlist_with_whitespace_search_params(self, sample_user, user_auth):
            """Test whitespaces are passed to search params, validations test"""
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            name = 'smart list with whitespace search params'
            search_params = '         '
            data = {'name': name, 'search_params': search_params}
            resp = self.call_post_api(data, auth_token_row['access_token'])
            assert resp.status_code == 400

        def test_create_smartlist_without_candidate_ids_and_search_params(self, sample_user, user_auth):
            """Test either of search_params or candidate_ids should be present.
            If not it should not create smartlist and should raise 400"""
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            name = fake.word()
            data = {'name': name}
            resp = self.call_post_api(data, auth_token_row['access_token'])
            assert resp.status_code == 400

        def test_create_smartlist_with_blank_candidate_ids(self, sample_user, user_auth):
            """Test with blank candidate_ids list, it should raise InvalidUsage error"""
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            data = {'name': fake.word(), 'candidate_ids': ''}
            resp = self.call_post_api(data, auth_token_row['access_token'])
            assert resp.status_code == 400

        def test_create_smartlist_with_characters_in_candidate_ids(self, sample_user, user_auth):
            """Test for validation that list of candidate_ids should only contain number"""
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            data = {'name': fake.word(), 'candidate_ids': [1, 2, "abcd", 5]}
            resp = self.call_post_api(data, auth_token_row['access_token'])
            assert resp.status_code == 400
            assert resp.json()['error']['message'] == "`candidate_ids` should be list of whole numbers"

        def test_create_smartlist_with_both_search_params_and_candidate_ids(self, sample_user, user_auth):
            """Test creating smartlist with both search_params and candidate_ids should not be allowed"""
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            data = {'name': fake.word(), 'candidate_ids': [1], 'search_params': {"maximum_years_experience": "5"}}
            resp = self.call_post_api(data, auth_token_row['access_token'])
            assert resp.status_code == 400
            assert json.loads(resp.content)['error']['message'] == "Bad input: `search_params` and `candidate_ids` both are present. Service accepts only one"

        def test_create_smartlist_with_invalid_search_params(self, access_token_first):
            """Test search_params should be in dictionary format"""
            data = {'name': fake.word(), 'search_params': "location=San Jose, CA"}
            resp = self.call_post_api(data, access_token_first)
            assert resp.status_code == 400
            assert json.loads(resp.content)['error']['message'] == "`search_params` should in dictionary format."

        def test_create_smartlist_with_string_search_params(self, access_token_first):
            data2 = {'name': fake.word(), 'search_params': "'example'"}
            resp = self.call_post_api(data2, access_token_first)
            assert resp.status_code == 400
            assert json.loads(resp.content)['error']['message'] == "`search_params` should in dictionary format."

        def test_create_smartlist_with_whitespaces_name(self, sample_user, user_auth):
            """Test creating smartlist with whitespaces in name"""
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            name = "    "
            data = {'name': name, 'candidate_ids': [1]}
            resp = self.call_post_api(data, auth_token_row['access_token'])
            assert resp.status_code == 400
            assert json.loads(resp.content)['error']['message'] == "Missing input: `name` is required for creating list"

        def test_create_smartlist_presence_of_oauth_decorator(self):
            """Check if no access_token is given it should raise authorization error"""
            data = {'name': fake.word(), 'candidate_ids': [1]}
            resp = self.call_post_api(data, access_token='')
            assert resp.status_code == 401

        def test_create_smartlist_from_candidates_not_in_users_domain(self, access_token_first, access_token_second):
            """Test user should not be allowed to create smartlist with candidates not belonging to his own domain"""
            # User_second creates candidates
            data = FakeCandidatesData.create(count=3)
            candidate_ids = create_candidates_from_candidate_api(access_token_second, data)
            data = {'name': fake.word(), 'candidate_ids': candidate_ids}
            # first user (access_token_first) trying to create smartlist with second user's candidates.
            resp = self.call_post_api(data, access_token_first)
            assert resp.status_code == 403
            assert json.loads(resp.content)['error']['message'] == "Provided list of candidates does not belong to user's domain"

        def test_create_smartlist_with_existing_name_in_domain(self, access_token_first):
            """Test smartlist creation with same name is not allowed"""
            smartlist_name = fake.word()
            data = {'name': smartlist_name, 'search_params': {'maximum_years_experience': '5'}}
            resp = self.call_post_api(data, access_token_first)
            assert resp.status_code == 201  # Successfully created
            # Try creating smartlist with same name
            data2 = {'name': smartlist_name, 'search_params': {"location": "San Jose, CA"}}
            resp2 = self.call_post_api(data2, access_token_first)
            assert resp2.status_code == 400
            assert json.loads(resp2.content)['error']['message'] == "Given smartlist `name` %s already exists in your domain" % smartlist_name

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
                                       candidate_ids=candidate_ids, access_token=auth_token_row['access_token'])
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
            """Test user is able to delete (hide) smartlist.
            Once it is deleted one should not be able to retrieve it from GET API
            """
            auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
            list_name = fake.name()
            data = FakeCandidatesData.create(count=1)
            candidate_ids = create_candidates_from_candidate_api(auth_token_row['access_token'], data)
            smartlist = save_smartlist(user_id=auth_token_row['user_id'], name=list_name,
                                       candidate_ids=candidate_ids, access_token=auth_token_row['access_token'])
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

        def test_get_all_smartlist_should_not_return_deleted_smartlist(self, user_first, access_token_first):
            """Test GET all smartlists in domain should not include the deleted smartlist"""
            smartlist1 = save_smartlist(user_id=user_first.id,
                                        name=fake.name(),
                                        search_params=json.dumps({"query": ""}))
            smartlist2 = save_smartlist(user_id=user_first.id, name=fake.name(),
                                        search_params=json.dumps({'maximum_years_experience': '5'}))
            # Call GET all smartlists and it should give both the smartlist ids
            resp1 = requests.get(
                url=SMARTLIST_URL,
                headers={'Authorization': 'Bearer %s' % access_token_first}
            )
            assert resp1.status_code == 200
            all_smartlists = resp1.json()['smartlists']
            all_smartlist_ids = [smartlist['id'] for smartlist in all_smartlists]
            assert sorted([smartlist1.id, smartlist2.id]) == sorted(all_smartlist_ids)
            # Delete smartlist 1
            resp2 = self.call_delete_api(access_token_first, smartlist1.id)
            assert resp2.status_code == 200
            # Call GET all smartlists and it should give single smartlist, i.e. smartlist2
            resp3 = requests.get(
                url=SMARTLIST_URL,
                headers={'Authorization': 'Bearer %s' % access_token_first}
            )
            assert resp3.status_code == 200
            smartlist_ids = [smartlist['id'] for smartlist in resp3.json()['smartlists']]
            assert len(smartlist_ids) == 1
            assert smartlist_ids[0] == smartlist2.id

        def test_delete_smartlist_from_other_domain(self, user_first, access_token_first, access_token_second):
            list_name = fake.name()
            data = FakeCandidatesData.create(count=1)
            candidate_ids = create_candidates_from_candidate_api(access_token_first, data)
            # User 1 from domain 1 created smartlist
            smartlist = save_smartlist(user_id=user_first.id, name=list_name, candidate_ids=candidate_ids,
                                       access_token=access_token_first)
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
                                   candidate_ids=candidate_ids, access_token=auth_token_row['access_token'])
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
                                   candidate_ids=candidate_ids, access_token=auth_token_row['access_token'])
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
                                   candidate_ids=candidate_ids, access_token=auth_token_row['access_token'])
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
        # Now try getting candidates from this deleted(hidden) smartlist, it should raise 404(not found)
        response = self.call_smartlist_candidates_get_api(smartlist.id, {'fields': 'all'}, access_token_first)
        assert response.status_code == 404


class TestSmartlistStatsUpdateApi(object):

    def call_smartlist_stats_update_api(self, access_token):
        headers = {'Authorization': 'Bearer %s' % access_token}
        response = requests.post(url=CandidatePoolApiUrl.SMARTLIST_STATS, headers=headers)
        return response.status_code

    def call_smartlist_stats_get_api(self, access_token, smartlist_id, params=None):
        headers = {'Authorization': 'Bearer %s' % access_token}
        response = requests.get(url=CandidatePoolApiUrl.SMARTLIST_GET_STATS % smartlist_id, headers=headers,
                                params=params)
        return response.json(), response.status_code

    def test_update_smartlists_stats(self, access_token_first, access_token_second, user_first):

        # Logged-in user trying to update statistics of all smartlists in database
        status_code = self.call_smartlist_stats_update_api(access_token_first)
        assert status_code == 401

        # Adding 'CAN_UPDATE_SMARTLISTS_STATS' role to user_first
        add_role_to_test_user(user_first, ['CAN_UPDATE_SMARTLISTS_STATS'])

        # Adding candidates with 'Apple' as current company
        populate_candidates(oauth_token=access_token_first, count=3, current_company='Apple')

        sleep(20)

        # Adding a test smartlist in database
        test_smartlist = Smartlist(name=gen_salt(5), user_id=user_first.id, search_params='{"query": "Apple"}')
        db.session.add(test_smartlist)

        # Emptying TalentPipelineStats table
        SmartlistStats.query.delete()
        db.session.commit()

        # Logged-in user trying to update statistics of all smartlists in database
        status_code = self.call_smartlist_stats_update_api(access_token_first)
        assert status_code == 204

        # Logged-in user trying to get statistics of a non-existing smartlist
        response, status_code = self.call_smartlist_stats_get_api(access_token_first, test_smartlist.id + 100)
        assert status_code == 404

        # Logged-in user trying to get statistics of a smartlist of different user
        response, status_code = self.call_smartlist_stats_get_api(access_token_second, test_smartlist.id)
        assert status_code == 403

        # Logged-in user trying to get statistics of a smartlist but with empty params
        response, status_code = self.call_smartlist_stats_get_api(access_token_first, test_smartlist.id)
        assert status_code == 400

        from_date = str(datetime.now() - timedelta(2))
        to_date = str(datetime.now() - timedelta(1))

        # Logged-in user trying to get statistics of a smartlist
        response, status_code = self.call_smartlist_stats_get_api(access_token_first, test_smartlist.id,
                                                                  {'from_date': from_date, 'to_date': to_date})
        assert status_code == 200
        assert not response.get('smartlist_data')

        from_date = str(datetime.now() - timedelta(1))
        to_date = str(datetime.now())

        # Logged-in user trying to get statistics of a smartlist
        response, status_code = self.call_smartlist_stats_get_api(access_token_first, test_smartlist.id,
                                                                  {'from_date': from_date, 'to_date': to_date})
        assert status_code == 200
        assert len(response.get('smartlist_data')) >= 1
        assert 3 in [smartlist_data.get('number_of_candidates_removed_or_added') for smartlist_data in
                     response.get('smartlist_data')]
        assert 3 in [smartlist_data.get('total_number_of_candidates') for smartlist_data in
                     response.get('smartlist_data')]