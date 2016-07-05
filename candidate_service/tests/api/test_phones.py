"""
Test cases for adding, retrieving, updating, and deleting candidate phones
"""
# Candidate Service app instance
from candidate_service.candidate_app import app

# Conftest
from candidate_service.common.tests.conftest import *

from candidate_service.common.models.candidate import PhoneLabel

# Helper functions
from helpers import AddUserRoles
from candidate_service.common.utils.test_utils import send_request, response_info
from candidate_service.common.routes import CandidateApiUrl
from candidate_service.common.utils.validators import get_phone_number_extension_if_exists

# Candidate sample data
from candidate_sample_data import fake, GenerateCandidateData, candidate_phones, generate_single_candidate_data

# Custom errors
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error


class TestAddCandidatePhones(object):
    def test_create_candidate_phones(self, access_token_first, user_first, talent_pool):
        """
        Test:   Create CandidatePhones for Candidate
        Expect: 201
        """
        # Create Candidate
        AddUserRoles.add_and_get(user_first)
        data = candidate_phones(talent_pool)
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        # Assert data sent in = data retrieved
        can_phones = candidate_dict['phones']
        can_phones_data = data['candidates'][0]['phones']
        assert isinstance(can_phones, list)
        assert can_phones_data[0]['value'] == data['candidates'][0]['phones'][0]['value']
        assert can_phones_data[0]['label'] == data['candidates'][0]['phones'][0]['label']

    def test_create_international_phone_number(self, access_token_first, user_first, talent_pool):
        """
        Test:  Create CandidatePhone using international phone number
        Expect: 201, phone number must be formatted before inserting into db
        """
        # Create candidate
        AddUserRoles.add_and_get(user_first)
        data = GenerateCandidateData.phones([talent_pool.id], internationalize=True)
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        candidate_phones = get_resp.json()['candidate']['phones']
        phone_number_from_data = data['candidates'][0]['phones'][0]['value']
        # assert candidate_phones[0]['value'] in data['candidates'][0]['phones'][0]['value']
        assert get_phone_number_extension_if_exists(phone_number_from_data)[-1] == candidate_phones[0]['extension']

    def test_create_candidate_without_phone_label(self, access_token_first, user_first, talent_pool):
        """
        Test:   Create a Candidate without providing phone's label
        Expect: 201; phone's label must be 'Home'
        """
        # Create Candidate without label
        AddUserRoles.add_and_get(user_first)
        data = {'candidates': [{'phones':
            [
                {'label': None, 'is_default': None, 'value': '6504084069'},
                {'label': None, 'is_default': None, 'value': '6505084069'}
            ], 'talent_pool_ids': {'add': [talent_pool.id]}}
        ]}
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']
        assert create_resp.status_code == requests.codes.CREATED
        assert candidate_dict['phones'][0]['label'] == PhoneLabel.DEFAULT_LABEL
        assert candidate_dict['phones'][-1]['label'] == PhoneLabel.OTHER_LABEL

    def test_create_candidate_with_bad_phone_label(self, access_token_first, user_first, talent_pool):
        """
        Test:   e.g. Phone label = 'vork'
        Expect: 201, phone label must be 'Other'
        """
        # Create Candidate without label
        AddUserRoles.add_and_get(user_first)
        data = {'candidates': [{'phones':
            [
                {'label': 'vork', 'is_default': None, 'value': '6504084069'},
                {'label': '2564', 'is_default': None, 'value': '6505084069'}
            ], 'talent_pool_ids': {'add': [talent_pool.id]}}
        ]}
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']
        assert create_resp.status_code == requests.codes.CREATED
        assert candidate_dict['phones'][0]['label'] == PhoneLabel.OTHER_LABEL
        assert candidate_dict['phones'][-1]['label'] == PhoneLabel.OTHER_LABEL

    def test_add_phone_without_value(self, access_token_first, user_first, talent_pool):
        """
        Test:  Add candidate phone without providing value
        Expect:  400; phone value is a required property
        """
        AddUserRoles.add(user_first)
        data = {'candidates': [{'talent_pool_ids': {'add': [talent_pool.id]}, 'phones': [
            {'label': 'Work', 'is_default': False, 'value': None}]}]}

        # Create candidate phone without value
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.BAD
        assert create_resp.json()['error']['code'] == custom_error.INVALID_INPUT

    def test_add_candidate_with_duplicate_phone_number(self, access_token_first, user_first, talent_pool):
        """
        Test: Add candidate using identical phone numbers
        """
        AddUserRoles.add(user_first)

        # Create candidate with identical phone numbers
        phone_number = fake.phone_number()
        data = {'candidates': [{'talent_pool_ids': {'add': [talent_pool.id]}, 'phones': [
            {'value': phone_number}, {'value': phone_number}
        ]}]}
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.BAD
        assert create_resp.json()['error']['code'] == custom_error.INVALID_USAGE

    def test_add_candidate_using_an_existing_number(self, access_token_first, user_first, talent_pool):
        """
        Test: Add a candidate using a phone number that already exists in candidate's domain
        """
        AddUserRoles.add(user_first)

        # Create candidate with phone number
        phone_number = fake.phone_number()
        data = {'candidates': [{'talent_pool_ids': {'add': [talent_pool.id]}, 'phones': [{'value': phone_number}]}]}
        send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Create another candidate using the same phone number as above
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.FORBIDDEN
        assert create_resp.json()['error']['code'] == custom_error.PHONE_FORBIDDEN


class TestUpdateCandidatePhones(object):
    def test_add_invlid_phone_number(self, access_token_first, user_first, candidate_first):
        """
        Test:  Add invalid phone numbers to candidate's profile
        Expect: 400; phone numbers should not be added to candidate's profile
        """
        AddUserRoles.edit(user_first)

        data_1 = {'candidates': [{'phones': [{'value': '+19-984abcde'}]}]}  # value contains letters + only 5 letters
        data_2 = {'candidates': [{'phones': [{'value': 'lettersonly'}]}]}  # value contains letters only
        data_3 = {'candidates': [{'phones': [{'value': '408556'}]}]}  # value too short

        resp = send_request('patch', CandidateApiUrl.CANDIDATE % candidate_first.id, access_token_first, data_1)
        print response_info(resp)
        assert resp.status_code == requests.codes.BAD

        resp = send_request('patch', CandidateApiUrl.CANDIDATE % candidate_first.id, access_token_first, data_2)
        print response_info(resp)
        assert resp.status_code == requests.codes.BAD

        resp = send_request('patch', CandidateApiUrl.CANDIDATE % candidate_first.id, access_token_first, data_3)
        print response_info(resp)
        assert resp.status_code == requests.codes.BAD


    def test_add_candidate_phones(self, access_token_first, user_first, talent_pool):
        """
        Test:   Add CandidatePhone to an existing Candidate. Number of candidate's phones must increase by 1.
        Expect: 200
        """
        # Create Candidate
        AddUserRoles.add_get_edit(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        phones_before_update = get_resp.json()['candidate']['phones']
        phones_count_before_update = len(phones_before_update)

        # Add new phone
        data = GenerateCandidateData.phones([talent_pool.id], candidate_id, internationalize=True)
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        phones_after_update = candidate_dict['phones']
        phones_from_data = data['candidates'][0]['phones']

        assert candidate_id == candidate_dict['id']
        assert phones_after_update[-1]['label'] == phones_from_data[0]['label'].capitalize()
        assert len(phones_after_update) == phones_count_before_update + 1

    def test_multiple_is_default_phones(self, access_token_first, user_first, talent_pool):
        """
        Test:   Add more than one CandidatePhone with is_default set to True
        Expect: 200, but only one CandidatePhone must have is_current True, the rest must be False
        """
        # Create Candidate
        AddUserRoles.add_get_edit(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Add a new email to the existing Candidate with is_current set to True
        candidate_id = create_resp.json()['candidates'][0]['id']
        send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        updated_candidate_dict = get_resp.json()['candidate']
        updated_can_phones = updated_candidate_dict['phones']

        # Only one of the phones must be default!
        assert sum([1 for phone in updated_can_phones if phone['is_default']]) == 1

    def test_update_existing_phone(self, access_token_first, user_first, talent_pool):
        """
        Test:   Update an existing CandidatePhone. Number of candidate's phones must remain unchanged.
        Expect: 200
        """
        # Create Candidate
        AddUserRoles.add_get_edit(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        phones_before_update = get_resp.json()['candidate']['phones']
        phones_count_before_update = len(phones_before_update)

        # Update first phone
        data = GenerateCandidateData.phones([talent_pool.id], candidate_id, phones_before_update[0]['id'])
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        phones_after_update = candidate_dict['phones']
        assert candidate_id == candidate_dict['id']
        assert phones_before_update[0]['id'] == phones_after_update[0]['id']
        assert phones_before_update[0]['value'] != phones_after_update[0]['value']
        assert phones_count_before_update == len(phones_after_update)


class TestDeleteCandidatePhone(object):
    def test_non_logged_in_user_delete_can_phone(self):
        """
        Test:   Delete candidate's phone without logging in
        Expect: 401
        """
        # Delete Candidate's phones
        resp = send_request('delete', CandidateApiUrl.PHONES % '5', None)
        print response_info(resp)
        assert resp.status_code == requests.codes.UNAUTHORIZED

    def test_delete_candidate_phone_with_bad_input(self):
        """
        Test:   Attempt to delete candidate phone with non integer values for candidate_id & phone_id
        Expect: 404
        """
        # Delete Candidate's phones
        resp = send_request('delete', CandidateApiUrl.PHONES % 'x', None)
        print response_info(resp)
        assert resp.status_code == requests.codes.NOT_FOUND

        # Delete Candidate's phone
        resp = send_request('delete', CandidateApiUrl.PHONE % (5, 'x'), None)
        print response_info(resp)
        assert resp.status_code == requests.codes.NOT_FOUND

    def test_delete_phone_of_a_candidate_belonging_to_a_diff_user(self, user_first, access_token_first,
                                                                  talent_pool, user_second,
                                                                  access_token_second):
        """
        Test:   Attempt to delete the phone of a Candidate that belongs
                to a different user from a different domain
        Expect: 403
        """
        # Create candidate_1 & candidate_2 with sample_user & sample_user_2
        AddUserRoles.add(user_first)
        AddUserRoles.delete(user_second)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp_1 = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve candidate_1
        candidate_1_id = create_resp_1.json()['candidates'][0]['id']

        # Delete candidate_1's phone with sample_user_2 logged in
        updated_resp = send_request('delete', CandidateApiUrl.PHONES % candidate_1_id, access_token_second)
        print response_info(updated_resp)
        assert updated_resp.status_code == requests.codes.FORBIDDEN
        assert updated_resp.json()['error']['code'] == custom_error.CANDIDATE_FORBIDDEN

    def test_delete_phone_of_a_different_candidate(self, user_first, access_token_first, talent_pool):
        """
        Test:   Attempt to delete the phone of a different Candidate
        Expect: 403
        """
        # Create candidate_1 and candidate_2
        AddUserRoles.all_roles(user_first)
        data_1 = generate_single_candidate_data([talent_pool.id])
        data_2 = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data_1)
        candidate_1_id = create_resp.json()['candidates'][0]['id']
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data_2)
        candidate_2_id = create_resp.json()['candidates'][0]['id']

        # Retrieve candidate_2's phones
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_2_id, access_token_first)
        can_2_phones = get_resp.json()['candidate']['phones']

        # Delete candidate_2's id using candidate_1_id
        url = CandidateApiUrl.PHONE % (candidate_1_id, can_2_phones[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)
        assert updated_resp.status_code == requests.codes.FORBIDDEN
        assert updated_resp.json()['error']['code'] == custom_error.PHONE_FORBIDDEN

    def test_delete_candidate_phones(self, user_first, access_token_first, talent_pool):
        """
        Test:   Remove Candidate's phones from db
        Expect: 204, Candidate must not have any phones left
        """
        # Create Candidate
        AddUserRoles.all_roles(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Delete Candidate's phones
        candidate_id = create_resp.json()['candidates'][0]['id']
        updated_resp = send_request('delete', CandidateApiUrl.PHONES % candidate_id, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']
        assert updated_resp.status_code == requests.codes.NO_CONTENT
        assert len(can_dict_after_update['phones']) == 0

    def test_delete_candidate_phone(self, user_first, access_token_first, talent_pool):
        """
        Test:   Remove Candidate's phone from db
        Expect: 204, Candidate's phones must be less 1
        """
        # Create Candidate
        AddUserRoles.all_roles(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate's phones
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_phones = get_resp.json()['candidate']['phones']

        # Current number of candidate's phones
        phones_count_before_delete = len(can_phones)

        # Delete Candidate's phone
        url = CandidateApiUrl.PHONE % (candidate_id, can_phones[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate's phones after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_phones_after_delete = get_resp.json()['candidate']['phones']
        assert updated_resp.status_code == requests.codes.NO_CONTENT
        assert len(can_phones_after_delete) == phones_count_before_delete - 1
