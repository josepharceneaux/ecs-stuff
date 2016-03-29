# Candidate Service app instance
from candidate_service.candidate_app import app

# Conftest
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import AddUserRoles
from candidate_service.common.routes import CandidateApiUrl
from candidate_service.common.utils.test_utils import send_request, response_info


class TestGetCandidateLanguages(object):
    def get_data(self, language_id=None, language_code=None, read=None, write=None, speak=None):
        data = {"candidate_languages": [
            {
                'id': language_id,
                'language_code': language_code or 'en',
                'read': read or fake.boolean(),
                'write': write or fake.boolean(),
                'speak': speak or fake.boolean(),
            },
            {
                'id': language_id,
                'language_code': language_code or 'FA',  # all caps should also work
                'read': read or fake.boolean(),
                'write': write or fake.boolean(),
                'speak': speak or fake.boolean(),
            }
        ]}
        return data

    def test_create_and_retrieve_candidates_languages(self, user_first, access_token_first, candidate_first):
        """
        Test:  Make a POST and a GET request to CandidateLanguageResource
        """
        AddUserRoles.add_and_get(user_first)
        create_resp = send_request('post', CandidateApiUrl.LANGUAGES % candidate_first.id, access_token_first,
                                   self.get_data())
        print response_info(create_resp)
        assert create_resp.status_code == 204

        # Retrieve candidate's languages
        get_resp = send_request('get', CandidateApiUrl.LANGUAGES % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 200
        assert len(get_resp.json()['candidate_languages']) == 2

    def test_update_candidate_languages(self, user_first, access_token_first, candidate_first):
        """
        Test:  Update candidate's language
        """
        AddUserRoles.all_roles(user_first)
        create_resp = send_request('post', CandidateApiUrl.LANGUAGES % candidate_first.id, access_token_first,
                                   self.get_data())
        print response_info(create_resp)
        assert create_resp.status_code == 204

        # Retrieve candidate's languages
        get_resp = send_request('get', CandidateApiUrl.LANGUAGES % candidate_first.id, access_token_first)
        print response_info(get_resp)

        # Update one of candidate's language
        language_id = get_resp.json()['candidate_languages'][0]['id']
        update_resp = send_request('patch', CandidateApiUrl.LANGUAGES % candidate_first.id, access_token_first,
                                   self.get_data(language_id=language_id, language_code='ar'))
        print response_info(update_resp)
        assert update_resp.status_code == 204

        # Retrieve candidate's updated language
        get_resp = send_request('get', CandidateApiUrl.LANGUAGE % (candidate_first.id, language_id), access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 200
        assert get_resp.json()['candidate_languages'][0]['language_code'] == 'ar'
        assert get_resp.json()['candidate_languages'][0]['language_name'] == 'Arabic'

    def test_delete_candidate_language(self, user_first, access_token_first, candidate_first):
        """
        Test:  Delete one of candidate's languages
        """
        AddUserRoles.all_roles(user_first)

        # Create candidate languages
        create_resp = send_request('post', CandidateApiUrl.LANGUAGES % candidate_first.id, access_token_first,
                                   self.get_data())
        print response_info(create_resp)
        assert create_resp.status_code == 204

        # Retrieve candidate's languages
        get_resp = send_request('get', CandidateApiUrl.LANGUAGES % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert len(get_resp.json()['candidate_languages']) == 2

        # Delete one of candidate's languages
        language_id = get_resp.json()['candidate_languages'][0]['id']
        del_resp = send_request('delete', CandidateApiUrl.LANGUAGE % (candidate_first.id, language_id),
                                access_token_first)
        print response_info(del_resp)

        # Retrieve candidate's languages
        get_resp = send_request('get', CandidateApiUrl.LANGUAGES % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert len(get_resp.json()['candidate_languages']) == 1, "One of candidate's languages has been deleted"

        del_resp = send_request('delete', CandidateApiUrl.LANGUAGES % candidate_first.id, access_token_first)
        print response_info(del_resp)
        assert del_resp.status_code == 204

        # Retrieve candidate's languages
        get_resp = send_request('get', CandidateApiUrl.LANGUAGES % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert len(get_resp.json()['candidate_languages']) == 0, "All of candidate's languages have been deleted"


