from . import *


class TestGetNotes(object):
    def test_get_candidate_notes(self, user_first, access_token_first, talent_pool):
        """
        Test:  Create candidate + add some notes for the candidate
        Expect: 204 for creation and 200 after retrieving
        """
        # Create Candidate
        AddUserRoles.add_and_get(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = request_to_candidates_resource(access_token_first, 'post', data)
        print response_info(create_resp)

        # Create notes for candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        notes_data = {'notes': [
            {'comment': 'Interested in internet security'},
            {'comment': 'Contributed to Linux OSS'}
        ]}
        resp = req_to_notes_resource(access_token_first, 'post', candidate_id, notes_data)
        print response_info(resp)
        assert resp.status_code == 204

        # Retrieve candidate's notes
        get_resp = req_to_notes_resource(access_token_first, 'get', candidate_id)
        print response_info(get_resp)
        assert get_resp.status_code == 200
        assert len(get_resp.json()['candidate_notes']) == len(notes_data['notes'])