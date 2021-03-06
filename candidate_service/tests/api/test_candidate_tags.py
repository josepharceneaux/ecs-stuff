"""
Test cases for CandidateTagResource endpoints & their modules
"""
from candidate_service.common.tests.conftest import *
from candidate_service.common.utils.test_utils import send_request, response_info
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_errors


class TestCreateCandidateTags(object):
    def test_add_tags(self, access_token_first, candidate_first):
        """
        Test:  Add tags to candidate
        Expect: 201
        """

        # Create candidate Tags
        data = {"tags": [{"name": str(uuid.uuid4())[:5]}, {"name": str(uuid.uuid4())[:5]}]}
        create_resp = send_request('post', CandidateApiUrl.TAGS % candidate_first.id, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED
        assert len(create_resp.json()['tags']) == len(data['tags'])

    def test_add_duplicate_tags(self, access_token_first, candidate_first):
        """
        Test:  Add duplicate tags
        Expect: 201, but no duplicate tags should be in db
        """

        # Create candidate tags
        name = str(uuid.uuid4())[:5]
        data = {"tags": [{"name": name}]}
        create_resp = send_request('post', CandidateApiUrl.TAGS % candidate_first.id, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED
        assert len(create_resp.json()['tags']) == len(data['tags'])

        create_resp = send_request('post', CandidateApiUrl.TAGS % candidate_first.id, access_token_first, data)
        print response_info(create_resp)


class TestGetCandidateTags(object):
    def test_get_all_tags(self, access_token_first, candidate_first):
        """
        Test:  Add & retrieve candidate tags
        Expect: 200
        """

        # Create candidate Tags
        data = {"tags": [{"name": str(uuid.uuid4())[:5]}, {"name": str(uuid.uuid4())[:5]}]}
        send_request('post', CandidateApiUrl.TAGS % candidate_first.id, access_token_first, data)

        # Retrieve all of candidate's tags
        get_resp = send_request('get', CandidateApiUrl.TAGS % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.OK
        assert len(get_resp.json()['tags']) == len(data['tags'])
        assert 'id' in get_resp.json()['tags'][0]

    def test_get_candidate_tag(self, access_token_first, candidate_first):
        """
        Test:  Retrieve a single tag
        Expect: 200
        """

        # Create candidate Tags
        data = {"tags": [{"name": str(uuid.uuid4())[:5]}, {"name": str(uuid.uuid4())[:5]}]}
        create_resp = send_request('post', CandidateApiUrl.TAGS % candidate_first.id, access_token_first, data)

        # Retrieve all of candidate's tags
        tag_id = create_resp.json()['tags'][0]['id']
        url = CandidateApiUrl.TAG % (candidate_first.id, tag_id)
        get_resp = send_request('get', url, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.OK
        assert get_resp.json()['name'] == data['tags'][0]['name']


class TestUpdateCandidateTags(object):
    def test_update_tag(self, access_token_first, candidate_first):
        """
        Test:  Update a single candidate's tag
        Expect: 200
        """

        # Create some tags for candidate_first
        url = CandidateApiUrl.TAGS % candidate_first.id
        data = {"tags": [{"name": str(uuid.uuid4())[:5]}, {"name": str(uuid.uuid4())[:5]}]}
        create_resp = send_request('post', url, access_token_first, data)
        print response_info(create_resp)

        # Retrieve all of candidate's tags
        get_resp = send_request('get', url, access_token_first)
        print response_info(get_resp)

        # Update one of candidate's tag
        update_url = CandidateApiUrl.TAG % (candidate_first.id, create_resp.json()['tags'][0]['id'])
        update_data = {'tags': [{'name': 'lazy'}]}
        update_resp = send_request('patch', update_url, access_token_first, update_data)
        print response_info(update_resp)

    def test_update_multiple_tags(self, access_token_first, candidate_first):
        """
        Test:  Update multiple candidate tags
        """

        # Create two tags for candidate
        url = CandidateApiUrl.TAGS % candidate_first.id
        data = {"tags": [{"name": str(uuid.uuid4())[:5]}, {"name": str(uuid.uuid4())[:5]}]}
        create_resp = send_request('post', url, access_token_first, data)
        print response_info(create_resp)

        # Get tag IDs
        tag_1_id, tag_2_id = create_resp.json()['tags'][0]['id'], create_resp.json()['tags'][1]['id']

        # Update one of candidate's tag
        update_data = {'tags': [
            {'id': tag_1_id, 'name': str(uuid.uuid4())[:5]}, {'id': tag_2_id, 'name': str(uuid.uuid4())[:5]}
        ]}
        update_resp = send_request('patch', url, access_token_first, update_data)
        print response_info(update_resp)
        assert update_resp.status_code == requests.codes.OK
        assert len(update_resp.json()['updated_tags']) == len(update_data['tags'])
        assert update_resp.json()['updated_tags'][0]['id'] != (tag_1_id or tag_2_id)


class TestDeleteCandidateTags(object):
    def test_delete_one(self, access_token_first, candidate_first):
        """
        Test:  Delete one of candidate's tags
        Expect: 403, tag is not permitted for candidate (since it was not created or it was deleted)
        """

        # Create some tags for candidate_first
        data = {"tags": [{"name": str(uuid.uuid4())[:8]}, {"name": str(uuid.uuid4())[:8]}]}
        create_resp = send_request('post', CandidateApiUrl.TAGS % candidate_first.id, access_token_first, data)
        print response_info(create_resp)

        # Delete one tag
        url = CandidateApiUrl.TAG % (candidate_first.id, create_resp.json()['tags'][0]['id'])
        del_resp = send_request('delete', url, access_token_first)
        print response_info(del_resp)

        # Retrieve candidate's tag that was just deleted
        get_resp = send_request('get', url, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.FORBIDDEN
        assert get_resp.json()['error']['code'] == custom_errors.TAG_FORBIDDEN

        # TODO: Fix flaky test and uncomment - Amir
        # Cloud search must also be updated
        # deleted_tag_id = del_resp.json()['deleted_tag']['id']
        # search_resp = get_response(access_token_first, '?tag_ids={}'.format(deleted_tag_id),
        #                            expected_count=0, attempts=30, pause=5, comp_operator='==')
        # print response_info(search_resp)
        # assert search_resp.json()['total_found'] == 0

    def test_delete_all(self, access_token_first, candidate_first):
        """
        Test:  Delete all of candidate's tags
        Expect: 404, candidate does not have any tags
        """

        # Create some tags for candidate_first
        data = {"tags": [{"name": str(uuid.uuid4())[:8]}, {"name": str(uuid.uuid4())[:8]}]}
        create_resp = send_request('post', CandidateApiUrl.TAGS % candidate_first.id, access_token_first, data)
        print response_info(create_resp)

        # Delete all of candidate's tags
        del_resp = send_request('delete', CandidateApiUrl.TAGS % candidate_first.id, access_token_first)
        print response_info(del_resp)

        # Retrieve candidate's tags
        get_resp = send_request('get', CandidateApiUrl.TAGS % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.NOT_FOUND
        assert get_resp.json()['error']['code'] == custom_errors.TAG_NOT_FOUND

        # TODO: Fix flaky test and uncomment - Amir
        # Cloud search must also be updated
        # deleted_tag_ids = [tag['id'] for tag in del_resp.json()['deleted_tags']]
        # search_resp = get_response(access_token_first, '?tag_ids={}'.format(','.join(map(str, deleted_tag_ids))),
        #                            expected_count=0, attempts=30, pause=5, comp_operator='==')
        # print response_info(search_resp)
        # assert search_resp.json()['total_found'] == 0
