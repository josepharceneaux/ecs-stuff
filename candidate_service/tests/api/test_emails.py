"""
Test cases for adding, retrieving, updating, and deleting candidate emails
"""
# Candidate Service app instance
from candidate_service.candidate_app import app

# Conftest
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import AddUserRoles
from candidate_service.common.utils.test_utils import send_request, response_info
from candidate_service.common.routes import CandidateApiUrl

# Candidate sample data
from candidate_sample_data import (fake, generate_single_candidate_data, GenerateCandidateData)

# Custom errors
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error


class TestUpdateCandidateEmails(object):
    def test_add_emails(self, access_token_first, user_first, talent_pool):
        """
        Test:   Add an email to an existing Candidate. Number of candidate's emails must increase by 1.
        Expect: 200
        """
        # Create Candidate
        AddUserRoles.add_get_edit(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        emails = get_resp.json()['candidate']['emails']
        emails_count = len(emails)

        # Add new email
        data = GenerateCandidateData.emails(candidate_id=candidate_id)
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        emails = candidate_dict['emails']
        email_from_data = data['candidates'][0]['emails'][0]

        assert candidate_id == candidate_dict['id']
        assert emails[-1]['label'] == email_from_data['label'].capitalize()
        assert emails[-1]['address'] == email_from_data['address']
        assert len(emails) == emails_count + 1

    def test_multiple_is_default_emails(self, access_token_first, user_first, talent_pool):
        """
        Test:   Add more than one CandidateEmail with is_default set to True
        Expect: 200, but only one CandidateEmail must have is_current True, the rest must be False
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
        updated_can_emails = updated_candidate_dict['emails']

        # Only one of the emails must be default!
        assert sum([1 for email in updated_can_emails if email['is_default']]) == 1

    def test_update_existing_email(self, access_token_first, user_first, talent_pool):
        """
        Test:   Update an existing CandidateEmail. Number of candidate's emails must remain unchanged
        Expect: 200
        """
        # Create Candidate
        AddUserRoles.add_get_edit(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        emails_before_update = get_resp.json()['candidate']['emails']
        emails_count_before_update = len(emails_before_update)

        # Update first email
        data = GenerateCandidateData.emails(candidate_id=candidate_id, email_id=emails_before_update[0]['id'])
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        emails_after_update = candidate_dict['emails']

        assert candidate_id == candidate_dict['id']
        assert emails_before_update[0]['id'] == emails_after_update[0]['id']
        assert emails_before_update[0]['address'] != emails_after_update[0]['address']
        assert emails_after_update[0]['address'] == data['candidates'][0]['emails'][0]['address']
        assert emails_count_before_update == len(emails_after_update)

    def test_update_existing_email_with_bad_email_address(self, access_token_first, user_first, talent_pool):
        """
        Test:   Use a bad email address to update and existing CandidateEmail
        Expect: 400
        """
        # Create Candidate
        AddUserRoles.add_get_edit(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        emails_before_update = get_resp.json()['candidate']['emails']
        emails_count_before_update = len(emails_before_update)

        # Update first email with an invalid email address
        data = {'candidates': [{'id': candidate_id, 'emails': [
            {'id': emails_before_update[0]['id'], 'label': 'primary', 'address': 'bad_email.com'}
        ]}]}
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        emails_after_update = candidate_dict['emails']
        assert updated_resp.status_code == 400
        assert candidate_id == candidate_dict['id']
        assert emails_count_before_update == len(emails_after_update)
        assert emails_before_update[0]['address'] == emails_after_update[0]['address']

    def test_add_forbidden_email_to_candidate(self, access_token_first, user_first, talent_pool):
        """
        Test: Add two candidates. Then add another email to candidate 2 using candidate's 1 email
        """
        AddUserRoles.add_get_edit(user_first)

        # Define email address
        first_candidates_email = fake.safe_email()

        # Create both candidates
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'emails': [{'address': first_candidates_email}]},
            {'talent_pool_ids': {'add': [talent_pool.id]}}
        ]}
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED

        # Add a second email to the second candidate using first-candidate's email address
        candidate_2_id = create_resp.json()['candidates'][1]['id']
        update_data = {'candidates': [{'id': candidate_2_id, 'emails': [{'address': first_candidates_email}]}]}
        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, update_data)
        print response_info(update_resp)
        assert update_resp.status_code == requests.codes.FORBIDDEN
        assert update_resp.json()['error']['code'] == custom_error.EMAIL_FORBIDDEN
