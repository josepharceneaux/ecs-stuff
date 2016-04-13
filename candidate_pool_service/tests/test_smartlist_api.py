from candidate_pool_service.candidate_pool_app import logger
from candidate_pool_service.common.tests.conftest import *
from common_functions import create_candidates_from_candidate_api
from candidate_pool_service.modules.smartlists import save_smartlist
from candidate_pool_service.common.models.smartlist import Smartlist
from candidate_pool_service.common.tests.cloud_search_common_functions import *
from candidate_pool_service.common.tests.fake_testing_data_generator import FakeCandidatesData
from candidate_pool_service.common.utils.handy_functions import (add_role_to_test_user,
                                                                 poll)
from candidate_pool_service.common.routes import CandidatePoolApiUrl
from candidate_pool_service.common.utils.api_utils import DEFAULT_PAGE
from candidate_pool_service.common.inter_service_calls.candidate_pool_service_calls import \
    assert_smartlist_candidates

__author__ = 'jitesh'


class TestSmartlistResource(object):
    class TestSmartlistResourcePOST(object):
        @staticmethod
        def call_post_api(data, access_token):
            return requests.post(
                url=CandidatePoolApiUrl.SMARTLISTS,
                data=json.dumps(data),
                headers={'Authorization': 'Bearer %s' % access_token,
                         'content-type': 'application/json'}
            )

        # TODO: move this function to common as one copy is also there in email-campaign-service
        @classmethod
        def create_and_return_smartlist_with_candidates(cls, access_token_first, user_first,
                                                        talent_pool, talent_pipeline, count,
                                                        timeout=30, smartlist_name=fake.name()):
            """
            Creates and returns the id of a smartlist with candidate ids (dumb list).
            :param access_token_first: Token for authorization.
            :param user_first: User of first domain.
            :param talent_pool: Valid talent pool.
            :param talent_pipeline: valid talent pipeline.
            :param count: Number of candidates.
            :return: smartlist_id and candidate_ids.
            """
            data = FakeCandidatesData.create(talent_pool=talent_pool, count=count)
            add_role_to_test_user(user_first, [DomainRole.Roles.CAN_ADD_CANDIDATES,
                                               DomainRole.Roles.CAN_GET_CANDIDATES])
            candidate_ids = create_candidates_from_candidate_api(access_token_first, data)
            time.sleep(10)
            data = {'name': smartlist_name,
                    'candidate_ids': candidate_ids,
                    'talent_pipeline_id': talent_pipeline.id}
            resp = cls.call_post_api(data, access_token_first)
            assert resp.status_code == 201  # Successfully created
            response = json.loads(resp.content)
            assert 'smartlist' in response
            assert 'id' in response['smartlist']
            smartlist_id = response['smartlist']['id']
            assert poll(assert_smartlist_candidates, [smartlist_id, len(candidate_ids), access_token_first],
                        timeout=timeout, default_result=False), 'Candidates not found for smartlist'
            logger.info('%s candidate(s) found for smartlist(id:%s)'
                        % (len(candidate_ids), smartlist_id))
            return smartlist_id, candidate_ids

        def test_create_smartlist_with_search_params(self, access_token_first, talent_pipeline):
            """Test to create smartlist by passing valid search_params as parameter. It should create smartlist"""
            name = fake.word()
            search_params = {"maximum_years_experience": "5", "location": "San Jose, CA", "minimum_years_experience": "2"}
            data = {'name': name, 'search_params': search_params, 'talent_pipeline_id': talent_pipeline.id}
            resp = self.call_post_api(data, access_token_first)

            assert resp.status_code == 201  # Successfully created

            response = json.loads(resp.content)
            assert 'smartlist' in response
            assert 'id' in response['smartlist']

        def test_create_smartlist_with_candidate_ids(self, access_token_first, user_first, talent_pool,
                                                     talent_pipeline):
            """Test to create smartlist with candidate ids (smartlist with candidate ids is dumblist)."""
            smartlist_id, candidate_ids = self.create_and_return_smartlist_with_candidates(
                access_token_first, user_first, talent_pool, talent_pipeline,
                count=20, timeout=60)
            # Get candidate_ids from SmartlistCandidates and assert with candidate ids used to create the smartlist
            smartlist_candidates_api = TestSmartlistCandidatesApi()
            response = smartlist_candidates_api.call_smartlist_candidates_get_api(smartlist_id,
                                                                                  {'fields': 'id'},
                                                                                  access_token_first)
            candidates = response.json()['candidates']
            assert len(candidates) == 15

            total_found = response.json()['total_found']
            assert total_found == 20

        def test_create_smartlist_with_candidate_ids_using_pagination_params(self, access_token_first,
                                                                             user_first, talent_pool, talent_pipeline):
            """
            Test to create smartlist with candidate ids (dumb list) and get candidates from that
            smartlist using pagination params.
            :param user_first: User from first domain
            :param access_token_first: Token for authentication.
            :param talent_pool: valid talent pool object.
            :param talent_pipeline: valid talent pipeline
            """
            smartlist_id, candidate_ids = self.create_and_return_smartlist_with_candidates(
                access_token_first, user_first, talent_pool, talent_pipeline, count=20,
                timeout=60)
            # Get candidate_ids from SmartlistCandidates and assert with candidate ids used to create the smartlist
            smartlist_candidates_api = TestSmartlistCandidatesApi()
            response = smartlist_candidates_api.call_smartlist_candidates_get_api_with_pagination_params(
                smartlist_id, {'fields': 'id'}, access_token_first, page=DEFAULT_PAGE, per_page=2)
            response_body = response.json()
            no_of_pages = int(response_body['max_pages'])
            assert no_of_pages == 10
            total = int(response_body['total_found'])
            assert total == 20
            candidates = response_body['candidates']
            assert len(candidates) == 2

            if no_of_pages > 1:
                for current_page in range(1, int(no_of_pages)):
                    next_page = current_page + 1
                    response = smartlist_candidates_api.call_smartlist_candidates_get_api_with_pagination_params(
                        smartlist_id, {'fields': 'id'}, access_token_first, page=next_page,
                        per_page=2)
                    response_body = json.loads(response.content)
                    candidates.extend(response_body['candidates'])
            assert len(candidates) == 20
            smartlist_candidate_ids = [row['id'] for row in candidates]
            assert sorted(candidate_ids) == sorted(map(int, smartlist_candidate_ids))

            # Checking by sending pagination param "page" as total number of pages plus 1, it should return total_found
            # and an empty candidates list.
            response = smartlist_candidates_api.call_smartlist_candidates_get_api_with_pagination_params(
                               smartlist_id, {'fields': 'id'}, access_token_first,
                               page=no_of_pages + DEFAULT_PAGE, per_page=2)
            response_body = json.loads(response.content)
            candidates = response_body['candidates']
            assert candidates == []
            total_found = response_body['total_found']
            assert total_found == 20

        def test_create_smartlist_with_blank_search_params(self, access_token_first):
            """Test blank search params validation"""
            name = 'smart list with blank search params'
            search_params = ''
            data = {'name': name, 'search_params': search_params}
            resp = self.call_post_api(data, access_token_first)

            assert resp.status_code == 400

        def test_create_smartlist_with_whitespace_search_params(self, access_token_first):
            """Test whitespaces are passed to search params, validations test"""
            name = 'smart list with whitespace search params'
            search_params = '         '
            data = {'name': name, 'search_params': search_params}
            resp = self.call_post_api(data, access_token_first)

            assert resp.status_code == 400

        def test_create_smartlist_without_candidate_ids_and_search_params(self, access_token_first):
            """Test either of search_params or candidate_ids should be present.
            If not it should not create smartlist and should raise 400"""
            name = fake.word()
            data = {'name': name}
            resp = self.call_post_api(data, access_token_first)

            assert resp.status_code == 400

        def test_create_smartlist_with_blank_candidate_ids(self, access_token_first):
            """Test with blank candidate_ids list, it should raise InvalidUsage error"""
            data = {'name': fake.word(), 'candidate_ids': ''}
            resp = self.call_post_api(data, access_token_first)

            assert resp.status_code == 400

        def test_create_smartlist_with_characters_in_candidate_ids(self, access_token_first, talent_pipeline):
            """Test for validation that list of candidate_ids should only contain number"""
            data = {'name': fake.word(), 'candidate_ids': [1, 2, "abcd", 5], 'talent_pipeline_id': talent_pipeline.id}
            resp = self.call_post_api(data, access_token_first)

            assert resp.status_code == 400
            assert resp.json()['error']['message'] == "`candidate_ids` should be list of whole numbers"

        def test_create_smartlist_with_both_search_params_and_candidate_ids(self, access_token_first):
            """Test creating smartlist with both search_params and candidate_ids should not be allowed"""
            data = {'name': fake.word(), 'candidate_ids': [1], 'search_params': {"maximum_years_experience": "5"}}
            resp = self.call_post_api(data, access_token_first)

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

        def test_create_smartlist_with_whitespaces_name(self, access_token_first):
            """Test creating smartlist with whitespaces in name"""
            name = "    "
            data = {'name': name, 'candidate_ids': [1]}
            resp = self.call_post_api(data, access_token_first)

            assert resp.status_code == 400
            assert json.loads(resp.content)['error']['message'] == "Missing input: `name` is required for creating list"

        def test_create_smartlist_presence_of_oauth_decorator(self):
            """Check if no access_token is given it should raise authorization error"""
            data = {'name': fake.word(), 'candidate_ids': [1]}
            resp = self.call_post_api(data, access_token='')

            assert resp.status_code == 401

        def test_create_smartlist_from_candidates_not_in_users_domain(
                self, access_token_first, access_token_second, talent_pipeline, talent_pool_second, user_first, user_second):

            """Test user should not be allowed to create smartlist with candidates not belonging to his own domain"""
            # user_second creates candidates
            add_role_to_test_user(user_second, [DomainRole.Roles.CAN_ADD_CANDIDATES])
            data = FakeCandidatesData.create(talent_pool=talent_pool_second, count=3)
            candidate_ids = create_candidates_from_candidate_api(access_token_second, data)
            data = {'name': fake.word(), 'candidate_ids': candidate_ids, 'talent_pipeline_id': talent_pipeline.id}

            # first user (access_token_first) trying to create smartlist with second user's candidates.
            add_role_to_test_user(user_first, [DomainRole.Roles.CAN_ADD_CANDIDATES])
            resp = self.call_post_api(data, access_token_first)

            assert resp.status_code == 403
            assert json.loads(resp.content)['error']['message'] == "Provided list of candidates does not belong to user's domain"

        def test_create_smartlist_with_existing_name_in_domain(self, access_token_first, user_first, talent_pipeline):
            """Test smartlist creation with same name is now allowed, previously it was not"""
            smartlist_name = fake.word()
            data = {'name': smartlist_name, 'search_params': {'maximum_years_experience': '5'},
                    'talent_pipeline_id': talent_pipeline.id}
            resp = self.call_post_api(data, access_token_first)

            assert resp.status_code == 201  # Successfully created
            assert resp.json()['smartlist']['id']  # assert smartlist id is there

            # add role to test user be able to get candidates
            add_role_to_test_user(user_first, ['CAN_GET_CANDIDATES'])

            # get the smartlist via id
            list_id = resp.json()['smartlist']['id']
            first_smartlist = requests.get(
                url=CandidatePoolApiUrl.SMARTLISTS + '/%s' % list_id,
                headers={'Authorization': 'Bearer %s' % access_token_first}
            )

            # assert it is returned and has the same search params as were input
            assert first_smartlist.status_code == 200
            assert first_smartlist.json()['smartlist']['search_params'] == '{"maximum_years_experience": "5"}'
            assert first_smartlist.json()['smartlist']['name'] == smartlist_name

            # Try creating smartlist with same name
            data2 = {'name': smartlist_name, 'search_params': {"location": "San Jose, CA"},
                     'talent_pipeline_id': talent_pipeline.id}
            resp2 = self.call_post_api(data2, access_token_first)

            assert resp2.status_code == 201  # Successfully created
            assert resp2.json()['smartlist']['id']  # assert smartlist id is there

            # get the smartlist via id
            second_list_id = resp2.json()['smartlist']['id']
            second_smartlist = requests.get(
                url=CandidatePoolApiUrl.SMARTLISTS + '/%s' % second_list_id,
                headers={'Authorization': 'Bearer %s' % access_token_first}
            )

            # assert it is returned and has the same search params as were input
            assert second_smartlist.status_code == 200
            assert second_smartlist.json()['smartlist']['search_params'] == '{"location": "San Jose, CA"}'
            assert second_smartlist.json()['smartlist']['name'] == smartlist_name

    class TestSmartlistResourceGET(object):
        def call_get_api(self, access_token, list_id=None):
            """Calls GET API of SmartlistResource"""
            return requests.get(
                url=CandidatePoolApiUrl.SMARTLISTS + '/%s' % list_id if list_id else CandidatePoolApiUrl.SMARTLISTS,
                headers={'Authorization': 'Bearer %s' % access_token}
            )

        def test_get_api_with_candidate_ids(self, access_token_first, user_first, talent_pool, talent_pipeline):
            """
            Test GET API for smartlist (with candidate ids)
            """
            list_name = fake.name()
            num_of_candidates = 4
            talent_pipeline.search_params = ''
            smartlist_id, candidate_ids = TestSmartlistResource.TestSmartlistResourcePOST.create_and_return_smartlist_with_candidates(
                access_token_first, user_first, talent_pool, talent_pipeline,
                count=num_of_candidates, timeout=60, smartlist_name=list_name)
            resp = self.call_get_api(access_token_first, smartlist_id)
            assert resp.status_code == 200
            response = json.loads(resp.content)
            assert response['smartlist']['name'] == list_name
            assert response['smartlist']['total_found'] == num_of_candidates
            assert response['smartlist']['user_id'] == user_first.id

        def test_get_api_with_search_params(self, access_token_first, user_first, talent_pipeline):
            """
            Test GET API for smartlist (with search_params)
            """
            list_name = fake.name()
            add_role_to_test_user(user_first, [DomainRole.Roles.CAN_GET_CANDIDATES])
            search_params = json.dumps({"location": "San Jose, CA"})
            smartlist = save_smartlist(user_id=user_first.id,
                                       name=list_name,
                                       search_params=search_params, talent_pipeline_id=talent_pipeline.id)
            resp = self.call_get_api(access_token_first, smartlist.id)

            assert resp.status_code == 200

            response = json.loads(resp.content)

            assert response['smartlist']['name'] == list_name
            assert response['smartlist']['user_id'] == user_first.id
            assert response['smartlist']['search_params'] == search_params

        def test_get_smartlist_from_outside_domain(self, user_first, access_token_first,
                                                   access_token_second, talent_pipeline):
            """Test for validate_list_belongs_to_domain"""
            list_name = fake.name()
            add_role_to_test_user(user_first, [DomainRole.Roles.CAN_GET_CANDIDATES])
            search_params = json.dumps({"location": "San Jose, CA"})
            # user 1 of domain 1 saving smartlist
            smartlist = save_smartlist(user_id=user_first.id,
                                       name=list_name,
                                       search_params=search_params, talent_pipeline_id=talent_pipeline.id)
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
                url=CandidatePoolApiUrl.SMARTLISTS + '/%s' % list_id if list_id else CandidatePoolApiUrl.SMARTLISTS,
                headers={'Authorization': 'Bearer %s' % access_token}
            )

        def test_delete_smartlist(self, access_token_first, user_first, talent_pool, talent_pipeline):
            """Test user is able to delete (hide) smartlist.
            Once it is deleted one should not be able to retrieve it from GET API
            """
            list_name = fake.name()
            data = FakeCandidatesData.create(talent_pool, count=1)
            add_role_to_test_user(user_first, [DomainRole.Roles.CAN_ADD_CANDIDATES])
            candidate_ids = create_candidates_from_candidate_api(access_token_first, data)
            smartlist = save_smartlist(user_id=user_first.id, name=list_name, talent_pipeline_id=talent_pipeline.id,
                                       candidate_ids=candidate_ids, access_token=access_token_first)
            db.session.commit()
            smartlist_obj = Smartlist.query.get(smartlist.id)

            assert smartlist_obj.is_hidden is False

            response = self.call_delete_api(access_token_first, smartlist.id)
            assert response.status_code == 200
            resp = response.json()

            assert 'smartlist' in resp
            assert resp['smartlist']['id'] == smartlist.id
            db.session.commit()

            smartlist_after_deletion = Smartlist.query.get(smartlist.id)
            assert smartlist_after_deletion.is_hidden is True  # Verify smartlist is hidden

            # Try calling GET method with deleted (hidden) list id and it should give 404 Not found
            output = requests.get(
                url=CandidatePoolApiUrl.SMARTLISTS + '/%s' % smartlist_after_deletion.id,
                headers={'Authorization': 'Bearer %s' % access_token_first}
            )

            assert output.status_code == 404  # Get method should give 404 for hidden smartlist

        def test_get_all_smartlist_should_not_return_deleted_smartlist(self, user_first,
                                                                       access_token_first, talent_pipeline):
            """Test GET all smartlists in domain should not include the deleted smartlist"""

            smartlist1 = save_smartlist(user_id=user_first.id,
                                        name=fake.name(),
                                        search_params=json.dumps({"query": ""}), talent_pipeline_id=talent_pipeline.id)
            smartlist2 = save_smartlist(user_id=user_first.id, name=fake.name(),
                                        search_params=json.dumps({'maximum_years_experience': '5'}),
                                        talent_pipeline_id=talent_pipeline.id)

            add_role_to_test_user(user_first, [DomainRole.Roles.CAN_GET_CANDIDATES])
            # Call GET all smartlists and it should give both the smartlist ids
            resp1 = requests.get(
                url=CandidatePoolApiUrl.SMARTLISTS,
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
                url=CandidatePoolApiUrl.SMARTLISTS,
                headers={'Authorization': 'Bearer %s' % access_token_first}
            )

            assert resp3.status_code == 200

            smartlist_ids = [smartlist['id'] for smartlist in resp3.json()['smartlists']]
            assert len(smartlist_ids) == 1
            assert smartlist_ids[0] == smartlist2.id

        def test_delete_smartlist_from_other_domain(self, user_first, access_token_first,
                                                    access_token_second, talent_pool, talent_pipeline):
            add_role_to_test_user(user_first, [DomainRole.Roles.CAN_ADD_CANDIDATES])
            list_name = fake.name()
            data = FakeCandidatesData.create(talent_pool, count=1)
            candidate_ids = create_candidates_from_candidate_api(access_token_first, data)
            # User 1 from domain 1 created smartlist
            smartlist = save_smartlist(user_id=user_first.id, name=list_name,
                                       candidate_ids=candidate_ids,
                                       access_token=access_token_first, talent_pipeline_id=talent_pipeline.id)

            # User 2 from domain 2 trying to delete smartlist
            response = self.call_delete_api(access_token_second, smartlist.id)
            assert response.status_code == 403

        def test_delete_smartlist_without_int_id(self, access_token_first):
            response = self.call_delete_api(access_token_first, 'abcd')
            assert response.status_code == 404

        def test_delete_deleted_smartlist(self, user_first, access_token_first, talent_pipeline):
            list_name = fake.name()
            search_params = json.dumps({"location": "San Jose, CA"})
            smartlist = save_smartlist(user_id=user_first.id,
                                       name=list_name,
                                       search_params=search_params, talent_pipeline_id=talent_pipeline.id)
            response = self.call_delete_api(access_token_first, smartlist.id)
            assert response.status_code == 200

            # Now try to delete this deleted smartlist
            response2 = self.call_delete_api(access_token_first, smartlist.id)
            assert response2.status_code == 404


class TestSmartlistCandidatesApi(object):
    def call_smartlist_candidates_get_api(self, smartlist_id, params, access_token):
        return requests.get(
                url=CandidatePoolApiUrl.SMARTLIST_CANDIDATES % smartlist_id,
                params=params,
                headers={'Authorization': 'Bearer %s' % access_token})

    def call_smartlist_candidates_get_api_with_pagination_params(self, smartlist_id, params, access_token, page,
                                                                 per_page):
        """
        Get candidates of smartlist with pagination params and return the response.
        :param smartlist_id: Smartlist id.
        :param params: Specific parameters for search such as candidates_ids_only.
        :param access_token: Token for authentication.
        :param page: Page number.
        :param per_page: Number of records per page.
        :return: HTTP Response
        """
        params.update({'page': page}) if page else None
        params.update({'limit': per_page}) if per_page else None
        return requests.get(url=CandidatePoolApiUrl.SMARTLIST_CANDIDATES % smartlist_id,
                            params=params,
                            headers={'Authorization': 'Bearer %s' % access_token})

    def test_return_candidate_ids_only(self, access_token_first, user_first, talent_pool, talent_pipeline):
        num_of_candidates = random.choice(range(1, 10))
        smartlist_id, candidate_ids = TestSmartlistResource.TestSmartlistResourcePOST.create_and_return_smartlist_with_candidates(
            access_token_first, user_first, talent_pool, talent_pipeline,
            count=num_of_candidates, timeout=50)
        params = {'fields': 'id'}

        resp = self.call_smartlist_candidates_get_api(smartlist_id, params, access_token_first)
        assert resp.status_code == 200

        response = json.loads(resp.content)
        assert response['total_found'] == num_of_candidates

        output_candidate_ids = [candidate['id'] for candidate in response['candidates']]
        assert sorted(map(int, output_candidate_ids)) == sorted(candidate_ids)

    def test_return_count_only(self, access_token_first, user_first, talent_pool, talent_pipeline):
        num_of_candidates = random.choice(range(1, 10))
        smartlist_id, candidate_ids = TestSmartlistResource.TestSmartlistResourcePOST.create_and_return_smartlist_with_candidates(
            access_token_first, user_first, talent_pool, talent_pipeline,
            count=num_of_candidates, timeout=60)
        params = {'fields': 'count_only'}

        resp = self.call_smartlist_candidates_get_api(smartlist_id, params, access_token_first)
        assert resp.status_code == 200

        response = json.loads(resp.content)
        assert response['total_found'] == num_of_candidates

    def test_return_all_fields(self, access_token_first, user_first, talent_pool, talent_pipeline):
        num_of_candidates = random.choice(range(1, 10))
        smartlist_id, candidate_ids = TestSmartlistResource.TestSmartlistResourcePOST.create_and_return_smartlist_with_candidates(
            access_token_first, user_first, talent_pool, talent_pipeline,
            count=num_of_candidates, timeout=60)

        resp = self.call_smartlist_candidates_get_api(smartlist_id, {}, access_token_first)
        assert resp.status_code == 200

        response = json.loads(resp.content)
        assert response['total_found'] == num_of_candidates
        assert 'email' in response['candidates'][0]

    def test_without_list_id(self, access_token_first):
        params = {'fields': 'candidate_ids_only'}
        resp = self.call_smartlist_candidates_get_api('', params, access_token_first)
        assert resp.status_code == 404

    def test_string_in_list_id(self, access_token_first):
        params = {}
        resp = self.call_smartlist_candidates_get_api('123abc', params, access_token_first)
        assert resp.status_code == 404

    def test_incorrect_list_id(self, access_token_first):
        params = {}
        resp = self.call_smartlist_candidates_get_api('123456789', params, access_token_first)
        assert resp.status_code == 404

    def test_presence_of_oauth_decorator(self):
        params = {'id': 1, 'fields': 'all'}
        resp = self.call_smartlist_candidates_get_api(2, params, access_token='')
        assert resp.status_code == 401

    def test_get_candidates_from_search_params(self, access_token_first, user_first, talent_pool, talent_pipeline):
        city = 'San Jose'
        state = 'CA'
        address = [{'address_line_1': fake.street_address(), 'city': city,
                    'state': state, 'zip_code': '95132', 'country': 'US'}]
        no_of_candidates = 2
        first_name = 'special'
        data = FakeCandidatesData.create(talent_pool, count=no_of_candidates, first_name=first_name,
                                         address_list=address)
        add_role_to_test_user(user_first, [DomainRole.Roles.CAN_ADD_CANDIDATES,
                                           DomainRole.Roles.CAN_GET_CANDIDATES])
        candidate_ids = create_candidates_from_candidate_api(access_token_first, data)

        talent_pipeline.search_params = ''
        db.session.commit()

        search_params = json.dumps({"query": "%s" % first_name})
        smartlist = save_smartlist(user_id=user_first.id, name=fake.name(),
                                   talent_pipeline_id=talent_pipeline.id,
                                   search_params=search_params)
        assert poll(assert_smartlist_candidates, [smartlist.id, len(candidate_ids),
                                                  access_token_first], default_result=False), \
            'candidates not found for smartlist'
        resp = self.call_smartlist_candidates_get_api(smartlist.id, {},access_token_first)
        assert resp.status_code == 200

        response = resp.json()
        output_candidate_ids = [long(candidate['id']) for candidate in response['candidates']]
        assert response['total_found'] == no_of_candidates
        assert sorted(candidate_ids) == sorted(output_candidate_ids)

    def test_get_candidates_from_deleted_smartlist(self, user_first, access_token_first, talent_pipeline):
        list_name = fake.name()
        search_params = json.dumps({"location": "San Jose, CA"})
        smartlist = save_smartlist(user_id=user_first.id,
                                   name=list_name,
                                   search_params=search_params, talent_pipeline_id=talent_pipeline.id)

        # Delete (hide) this smartlist
        response = requests.delete(url=CandidatePoolApiUrl.SMARTLISTS + '/%s' % smartlist.id,
                                   headers={'Authorization': 'Bearer %s' % access_token_first})
        assert response.status_code == 200

        # Now try getting candidates from this deleted(hidden) smartlist, it should raise 404(not found)
        response = self.call_smartlist_candidates_get_api(smartlist.id, {'fields': 'all'}, access_token_first)
        assert response.status_code == 404
