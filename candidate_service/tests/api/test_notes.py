# Candidate Service app instance
from candidate_service.candidate_app import app

# Conftest
from candidate_service.common.tests.conftest import *

# Helpers
from candidate_service.common.utils.test_utils import send_request, response_info
from candidate_service.common.routes import CandidateApiUrl

URL = CandidateApiUrl.NOTES


class TestAddNotes(object):

    def test_add_candidate_notes(self, access_token_first, candidate_first):
        """
        Test:  Add notes to candidate
        """

        # Create notes for candidate
        notes_data = {'notes': [
            {'title': 'interests', 'comment': 'Interested in internet security'},
            {'title': 'Open Source Contributor', 'comment': 'Contributed to Linux OSS'}
        ]}
        create_resp = send_request('post', CandidateApiUrl.NOTES % candidate_first.id, access_token_first, notes_data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED
        assert len(create_resp.json()['candidate_notes']) == len(notes_data['notes'])

    def test_add_note_without_title(self, access_token_first, candidate_first):
        """
        Test: Add note for candidate without providing a note title
        """

        notes_data = {'notes': [{'comment': fake.bs()}, {'comment': fake.bs()}]}
        create_resp = send_request('post', CandidateApiUrl.NOTES % candidate_first.id, access_token_first, notes_data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED
        assert len(create_resp.json()['candidate_notes']) == len(notes_data['notes'])


class TestGetNotes(object):

    def test_get_candidate_notes(self, notes_first, access_token_first):
        """
        Test: Retrieve all of candidate's notes
        """

        get_resp = send_request('get', CandidateApiUrl.NOTES % notes_first['candidate'].id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.OK
        assert len(get_resp.json()['candidate_notes']) == len(notes_first['notes']['candidate_notes'])

    def test_get_candidate_note(self, notes_first, access_token_first):
        """
        Test: Retrieve one of candidate's notes
        """
        candidate_id = notes_first['candidate'].id
        note_id = notes_first['notes']['candidate_notes'][0]['id']

        get_resp = send_request('get', CandidateApiUrl.NOTE % (candidate_id, note_id), access_token_first)
        print response_info(get_resp)

        note_data = notes_first['data']['notes'][0]
        assert get_resp.status_code == requests.codes.OK
        assert get_resp.json()['candidate_note']['comment'] == note_data['comment'].lower()
        assert get_resp.json()['candidate_note']['title'] == note_data['title'].lower()
        assert get_resp.json()['candidate_note']['candidate_id'] == notes_first['candidate'].id
        assert get_resp.json()['candidate_note']['id'] == note_id
        assert get_resp.json()['candidate_note']['owner_id'] == notes_first['user'].id


class TestDeleteNotes(object):

    def test_delete_candidate_notes(self, notes_first, access_token_first):
        """
        Test: Delete all of candidate's notes
        """

        del_resp = send_request('delete', CandidateApiUrl.NOTES % notes_first['candidate'].id, access_token_first)
        print response_info(del_resp)
        assert del_resp.status_code == requests.codes.OK

        # Candidate should not have any notes left
        get_resp = send_request('get', CandidateApiUrl.NOTES % notes_first['candidate'].id, access_token_first)
        assert get_resp.status_code == requests.codes.OK
        assert get_resp.json()['candidate_notes'] == []

    def test_delete_candidate_note(self, notes_first, access_token_first):
        """
        Test: Delete one of candidate's notes
        """

        candidate_id = notes_first['candidate'].id
        note_id = notes_first['notes']['candidate_notes'][0]['id']

        # Delete candidate's note
        del_resp = send_request('delete', CandidateApiUrl.NOTE % (candidate_id, note_id), access_token_first)
        print response_info(del_resp)

        assert del_resp.status_code == requests.codes.OK
        assert del_resp.json()['candidate_note']['id'] == note_id

        # Retrieve candidate notes
        get_resp = send_request('get', CandidateApiUrl.NOTE % (candidate_id, note_id), access_token_first)
        print response_info(get_resp)

        assert get_resp.status_code == requests.codes.NOT_FOUND
