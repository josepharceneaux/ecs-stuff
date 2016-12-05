# Candidate Service app instance

# Conftest
from candidate_service.common.routes import CandidateApiUrl
from candidate_service.common.tests.conftest import *
from candidate_service.common.utils.custom_error_codes import CandidateCustomErrors as custom_errors
from candidate_service.common.utils.test_utils import send_request, response_info

data = {'candidate_references': [
    {
        'name': fake.name(), 'position_title': fake.job(), 'comments': 'Do not hire this guy!',
        'reference_email': {'is_default': None, 'address': fake.safe_email(), 'label': None},
        'reference_phone': {'is_default': True, 'value': '14055689944'},
        'reference_web_address': {'url': fake.url(), 'description': fake.bs()}
    },
    {
        'name': fake.name(), 'position_title': fake.job(), 'comments': 'Do not hire this guy!',
        'reference_email': {'is_default': False, 'address': fake.safe_email(), 'label': None},
        'reference_web_address': {'url': fake.url(), 'description': fake.bs()}
    },
    {'name': fake.name(), 'position_title': fake.job(), 'comments': 'Do not hire this guy!'}
]}


class TestCreateCandidateReference(object):
    URL = CandidateApiUrl.REFERENCES

    def test_add_references(self, access_token_first, candidate_first):
        """
        Test: Create references for candidate & retrieve them
        Expect: 201
        """
        # Create references for candidate
        create_resp = send_request('post', self.URL % candidate_first.id, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201
        assert len(create_resp.json()['candidate_references']) == len(data['candidate_references'])

        # Retrieve candidate's references
        get_resp = send_request('get', self.URL % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 200
        assert len(get_resp.json()['candidate_references']) == len(data['candidate_references'])
        assert get_resp.json()['candidate_references'][0]['comments'] == data['candidate_references'][0]['comments']

    def test_add_references_with_empty_reference_contact_info_values(self, access_token_first, candidate_first):
        """
        Test: Create a reference for candidate with no values for the reference Email, Phone, and Web Address dicts
        Expect: 201, but ReferenceEmail, ReferencePhone, and ReferenceWebAddress should not be added to db
        """
        # Create references for candidate
        data = {'candidate_references': [
            {
                'name': fake.name(), 'position_title': fake.job(), 'comments': 'red chili pepper!',
                'reference_email': {'is_default': None, 'address': '', 'label': '  '},
                'reference_phone': {'is_default': True, 'value': ' '},
                'reference_web_address': {'url': None}}
        ]}

        create_resp = send_request('post', self.URL % candidate_first.id, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201
        assert len(create_resp.json()['candidate_references']) == len(data['candidate_references'])

        # Retrieve candidate's references
        get_resp = send_request('get', self.URL % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 200
        assert len(get_resp.json()['candidate_references']) == len(data['candidate_references'])
        assert get_resp.json()['candidate_references'][0]['comments'] == data['candidate_references'][0]['comments']
        assert 'reference_email' not in get_resp.json()['candidate_references'][0]
        assert 'reference_phone' not in get_resp.json()['candidate_references'][0]
        assert 'reference_web_address' not in get_resp.json()['candidate_references'][0]


class TestUpdateCandidateReference(object):
    URL = CandidateApiUrl.REFERENCES

    def test_update_reference(self, access_token_first, candidate_first):
        """
        """
        # Create references for candidate
        create_resp = send_request('post', self.URL % candidate_first.id, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Update reference's info
        update_data = {'candidate_references': [{
            'id': create_resp.json()['candidate_references'][0]['id'],
            'comments': "in second thought, he ain't too bad"
        }]}
        update_resp = send_request('patch', self.URL % candidate_first.id, access_token_first, update_data)
        print response_info(update_resp)
        assert update_resp.status_code == 200

        # Retrieve candidate's references
        get_resp = send_request('get', self.URL % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 200
        assert len(get_resp.json()['candidate_references']) == len(data['candidate_references'])
        assert get_resp.json()['candidate_references'][0]['comments'] == update_data['candidate_references'][0]['comments']


class TestDeleteCandidateReference(object):
    URL = CandidateApiUrl.REFERENCES

    def test_delete_reference(self, access_token_first, candidate_first):
        """
        Test:  Create references, delete one, assert on the result, then delete all of candidate's references
        Expect: 200
        """
        # Create references for candidate
        create_resp = send_request('post', self.URL % candidate_first.id, access_token_first, data)
        assert len(create_resp.json()['candidate_references']) == len(data['candidate_references'])

        # Retrieve candidate's references
        get_resp = send_request('get', self.URL % candidate_first.id, access_token_first)
        assert len(get_resp.json()['candidate_references']) == len(data['candidate_references'])

        # Delete one of candidate's references
        reference_id = get_resp.json()['candidate_references'][0]['id']
        url = CandidateApiUrl.REFERENCE % (candidate_first.id, reference_id)
        del_resp = send_request('delete', url, access_token_first)
        print response_info(del_resp)
        assert del_resp.status_code == 200
        assert del_resp.json()['candidate_reference']['id'] == reference_id

        # # Retrieve candidate's references
        get_resp = send_request('get', self.URL % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert len(get_resp.json()['candidate_references']) == len(data['candidate_references']) - 1

        # # Delete all of candidate's references
        del_resp = send_request('delete', self.URL % candidate_first.id, access_token_first)
        print response_info(del_resp)
        assert del_resp.status_code == 200

        # Retrieve candidate's references
        get_resp = send_request('get', self.URL % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert len(get_resp.json()['candidate_references']) == 0

    def test_delete_another_candidates_reference(self, access_token_first, candidate_first, candidate_first_2):
        """
        Test:  Attempt to delete reference of a different candidate
        Expect: 403, no records should be deleted
        """
        # Create references for candidate
        send_request('post', self.URL % candidate_first.id, access_token_first, data)

        # Retrieve candidate's references
        get_resp = send_request('get', self.URL % candidate_first.id, access_token_first)

        # Delete one of candidate's references
        url = CandidateApiUrl.REFERENCE % (candidate_first_2.id, get_resp.json()['candidate_references'][0]['id'])
        del_resp = send_request('delete', url, access_token_first)
        print response_info(del_resp)
        assert del_resp.status_code == 403
        assert del_resp.json()['error']['code'] == custom_errors.REFERENCE_FORBIDDEN


class TestGetCandidateReference(object):
    URL = CandidateApiUrl.REFERENCES
    REFERENCE_URL = CandidateApiUrl.REFERENCE

    def test_get_candidate_reference(self, access_token_first, candidate_first):
        """
        Test: Retrieve a single candidate reference by providing its ID
        """
        # Create references for candidate
        create_resp = send_request('post', self.URL % candidate_first.id, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        reference_id = create_resp.json()['candidate_references'][0]['id']

        # Retrieve candidate's references
        get_resp = send_request('get', self.REFERENCE_URL % (candidate_first.id, reference_id), access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 200
        assert get_resp.json()['candidate_reference']['comments'] == data['candidate_references'][0]['comments']
        assert get_resp.json()['candidate_reference']['name'] == data['candidate_references'][0]['name']
