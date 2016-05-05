"""
Test cases for CandidateTagResource endpoints & their modules
"""
# Candidate Service app instance
from candidate_service.candidate_app import app

# Conftest
from candidate_service.common.tests.conftest import *

import uuid

# Custom Errors
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_errors

# Helper functions
from candidate_service.tests.api.candidate_sample_data import generate_single_candidate_data
from helpers import AddUserRoles
from candidate_service.common.routes import CandidateApiUrl
from candidate_service.common.utils.test_utils import send_request, response_info

data = {"tags": [{"name": str(uuid.uuid4())[:5]}, {"name": str(uuid.uuid4())[:5]}]}


class TestCreateCandidateTags(object):
    def test_add_without_necessary_permissions(self, access_token_first, candidate_first):
        """
        Test:  Add tags to candidate without giving user permissions such as authentication & role
        Expect: 401
        """
        # Unauthorized user
        create_resp = send_request('post', CandidateApiUrl.TAGS % candidate_first.id, None, data)
        print response_info(create_resp)
        assert create_resp.status_code == 401

        # Authorized but not permitted user
        create_resp = send_request('post', CandidateApiUrl.TAGS % candidate_first.id, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 401

    def test_add_tags(self, access_token_first, user_first, candidate_first):
        """
        Test:  Add tags to candidate
        Expect: 201
        """
        AddUserRoles.add(user_first)
        # Create candidate Tags
        create_resp = send_request('post', CandidateApiUrl.TAGS % candidate_first.id, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201
        assert len(create_resp.json()['tags']) == len(data['tags'])

    def test_add_duplicate_tags(self, access_token_first, user_first, candidate_first):
        """
        Test:  Add duplicate tags
        Expect: 201, but no duplicate tags should be in db
        """
        AddUserRoles.add_and_get(user_first)

        # Create candidate tags
        name = str(uuid.uuid4())[:5]
        data = {"tags": [{"name": name}]}
        create_resp = send_request('post', CandidateApiUrl.TAGS % candidate_first.id, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201
        assert len(create_resp.json()['tags']) == len(data['tags'])

        create_resp = send_request('post', CandidateApiUrl.TAGS % candidate_first.id, access_token_first, data)
        print response_info(create_resp)


class TestGetCandidateTags(object):
    def test_get_all_tags(self, access_token_first, user_first, candidate_first):
        """
        Test:  Add & retrieve candidate tags
        Expect: 200
        """
        AddUserRoles.add_and_get(user_first)

        # Create candidate Tags
        send_request('post', CandidateApiUrl.TAGS % candidate_first.id, access_token_first, data)

        # Retrieve all of candidate's tags
        get_resp = send_request('get', CandidateApiUrl.TAGS % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 200
        assert len(get_resp.json()['tags']) == len(data['tags'])

    def test_get_candidate_tag(self, access_token_first, user_first, candidate_first):
        """
        Test:  Retrieve a single tag
        Expect: 200
        """
        AddUserRoles.add_and_get(user_first)

        # Create candidate Tags
        create_resp = send_request('post', CandidateApiUrl.TAGS % candidate_first.id, access_token_first, data)

        # Retrieve all of candidate's tags
        tag_id = create_resp.json()['tags'][0]['id']
        url = CandidateApiUrl.TAG % (candidate_first.id, tag_id)
        get_resp = send_request('get', url, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 200
        assert get_resp.json()['name'] == data['tags'][0]['name']


class TestUpdateCandidateTags(object):
    def test_update_tag(self, user_first, access_token_first, candidate_first):
        """
        Test:  Update a single candidate's tag
        Expect: 200
        """
        AddUserRoles.all_roles(user_first)

        # Create some tags for candidate_first
        url = CandidateApiUrl.TAGS % candidate_first.id
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


class TestDeleteCandidateTags(object):
    def test_delete_one(self, user_first, access_token_first, candidate_first):
        """
        Test:  Delete one of candidate's tags
        Expect: 403, tag is not permitted for candidate (since it was not created or it was deleted)
        """
        AddUserRoles.all_roles(user_first)

        # Create some tags for candidate_first
        create_resp = send_request('post', CandidateApiUrl.TAGS % candidate_first.id, access_token_first, data)
        print response_info(create_resp)

        # Delete one tag
        url = CandidateApiUrl.TAG % (candidate_first.id, create_resp.json()['tags'][0]['id'])
        del_resp = send_request('delete', url, access_token_first)
        print response_info(del_resp)

        # Retrieve candidate's tag that was just deleted
        get_resp = send_request('get', url, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 403
        assert get_resp.json()['error']['code'] == 3172

    def test_delete_all(self, user_first, access_token_first, candidate_first):
        """
        Test:  Delete all of candidate's tags
        Expect: 404, candidate does not have any tags
        """
        AddUserRoles.all_roles(user_first)

        # Create some tags for candidate_first
        create_resp = send_request('post', CandidateApiUrl.TAGS % candidate_first.id, access_token_first, data)
        print response_info(create_resp)

        # Delete one tag
        del_resp = send_request('delete', CandidateApiUrl.TAGS % candidate_first.id, access_token_first)
        print response_info(del_resp)

        # Retrieve candidate's tag that was just deleted
        get_resp = send_request('get', CandidateApiUrl.TAGS % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 404
        assert get_resp.json()['error']['code'] == 3170
