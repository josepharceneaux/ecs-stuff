"""
Test cases for CandidateResource/delete()
"""
# Candidate Service app instance
from candidate_service.candidate_app import app

# Conftest
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import AddUserRoles
from candidate_service.common.routes import CandidateApiUrl
from candidate_service.common.utils.test_utils import send_request, response_info

# Sample data
from candidate_sample_data import generate_single_candidate_data

# Custom errors
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error


class TestDeleteWorkExperience(object):
    def test_delete_experience_and_check_total_months_experience(self, access_token_first, user_first, talent_pool):
        """
        Test:  Delete one of candidate's work experiences
        Expect:  Candidate.total_months_experience to be updated accordingly
        """
        AddUserRoles.all_roles(user_first)
        data = {'candidates': [
            {
                'talent_pool_ids': {'add': [talent_pool.id]},
                'work_experiences': [
                    {'start_year': 2005, 'end_year': 2007},  # 12*2 = 24 months of experience
                    {'start_year': 2011, 'end_year': None}   # 12*5 = 60 months of experience
                ]
            }
        ]}
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Check candidate's total_months_experience from db
        candidate_id = create_resp.json()['candidates'][0]['id']
        db.session.commit()
        candidate = Candidate.get_by_id(candidate_id)
        assert candidate.total_months_experience == 84  # 24 + 60

        # Retrieve candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)

        # Delete one of the experiences
        experience_id = get_resp.json()['candidate']['work_experiences'][0]['id']
        del_resp = send_request('delete', CandidateApiUrl.EXPERIENCE % (candidate_id, experience_id), access_token_first)
        print response_info(del_resp)
        db.session.commit()
        assert candidate.total_months_experience == 24  # (84 - 60)

    def test_non_logged_in_user_delete_can_experience(self):
        """
        Test:   Delete candidate's experiences without logging in
        Expect: 401
        """
        # Delete Candidate's experiences
        resp = send_request('delete', CandidateApiUrl.EXPERIENCES % 5, None)
        print response_info(resp)
        assert resp.status_code == 401

    def test_delete_candidate_experience_with_bad_input(self):
        """
        Test:   Attempt to delete candidate experience with non integer values for candidate_id & experience_id
        Expect: 404
        """
        # Delete Candidate's experiences
        resp = send_request('delete', CandidateApiUrl.EXPERIENCES % 'x', access_token_first)
        print response_info(resp)
        assert resp.status_code == 404

        # Delete Candidate's experience
        resp = send_request('delete', CandidateApiUrl.EXPERIENCE % (5, 'x'), access_token_first)
        print response_info(resp)
        assert resp.status_code == 404

    def test_delete_experience_of_a_candidate_belonging_to_a_diff_user(self, user_first, access_token_first,
                                                                       talent_pool, user_second,
                                                                       access_token_second):
        """
        Test:   Attempt to delete the experience of a Candidate that belongs
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

        # Delete candidate_1's experience with sample_user_2 logged in
        updated_resp = send_request('delete', CandidateApiUrl.EXPERIENCES % candidate_1_id, access_token_second, data)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403

    def test_delete_experience_of_a_different_candidate(self, user_first, access_token_first, talent_pool):
        """
        Test:   Attempt to delete the experience of a different Candidate
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

        # Retrieve candidate_2's experiences
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_2_id, access_token_first)
        can_2_experiences = get_resp.json()['candidate']['work_experiences']

        # Delete candidate_2's experience using candidate_1_id
        exp_id = can_2_experiences[0]['id']
        updated_resp = send_request('delete', CandidateApiUrl.EXPERIENCE % (candidate_1_id, exp_id), access_token_first)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403
        assert updated_resp.json()['error']['code'] == custom_error.EXPERIENCE_FORBIDDEN

    def test_delete_candidate_experiences(self, user_first, access_token_first, talent_pool):
        """
        Test:   Remove all of candidate's experiences from db
        Expect: 204; Candidate should not have any experience left
        """
        # Create Candidate
        AddUserRoles.all_roles(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        candidate_id = create_resp.json()['candidates'][0]['id']

        # Remove all of Candidate's experiences
        updated_resp = send_request('delete', CandidateApiUrl.EXPERIENCES % candidate_id, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']
        assert updated_resp.status_code == 204
        assert len(can_dict_after_update['work_experiences']) == 0

    def test_delete_candidate_experience(self, user_first, access_token_first, talent_pool):
        """
        Test:   Remove Candidate's experience from db
        Expect: 204, Candidate's experience must be less 1.
        """
        # Create Candidate
        AddUserRoles.all_roles(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']
        candidate_experiences = candidate_dict['work_experiences']

        # Current number of Candidate's experiences
        experiences_count_before_delete = len(candidate_experiences)

        # Remove one of Candidate's education
        exp_id = candidate_experiences[0]['id']
        updated_resp = send_request('delete', CandidateApiUrl.EXPERIENCE % (candidate_id, exp_id), access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']
        assert updated_resp.status_code == 204
        assert len(can_dict_after_update['work_experiences']) == experiences_count_before_delete - 1

    def test_non_logged_in_user_delete_can_experience_bullets(self):
        """
        Test:   Delete candidate's experience-bullets without logging in
        Expect: 401
        """
        # Delete Candidate's experience-bullets
        resp = send_request('delete', CandidateApiUrl.EXPERIENCE_BULLETS % (5, 5), access_token_first)
        print response_info(resp)
        assert resp.status_code == 401

    def test_delete_candidate_experience_bullet_with_bad_input(self):
        """
        Test:   Attempt to delete candidate experience-bullet with non integer values
                for candidate_id & experience_id
        Expect: 404
        """
        # Delete Candidate's experience-bullets
        url = CandidateApiUrl.EXPERIENCE_BULLETS % ('x', 5)
        resp = send_request('delete', url, access_token_first)
        print response_info(resp)
        assert resp.status_code == 404

        # Delete Candidate's experience-bullet
        url = CandidateApiUrl.EXPERIENCE_BULLET % (5, 5, 'x')
        resp = send_request('delete', url, None)
        print response_info(resp)
        assert resp.status_code == 404

    def test_delete_exp_bullets_of_a_candidate_belonging_to_a_diff_user(self, user_first, access_token_first,
                                                                        talent_pool, user_second,
                                                                        access_token_second):
        """
        Test:   Attempt to delete exp-bullets of a Candidate that belongs
                to a different user from a different domain
        Expect: 403
        """
        # Get access token_1 & access_token_second for sample_user & sample_user_2, respectively
        AddUserRoles.add_and_get(user_first)
        AddUserRoles.delete(user_second)

        # Create candidate_1 & candidate_2 with sample_user & sample_user_2
        data = generate_single_candidate_data([talent_pool.id])
        create_resp_1 = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve candidate_1's experiences
        candidate_1_id = create_resp_1.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_1_id, access_token_first)
        experience = get_resp.json()['candidate']['work_experiences'][0]

        # Delete candidate_1's exp-bullets with sample_user_2 logged in
        url = CandidateApiUrl.EXPERIENCE_BULLETS % (candidate_1_id, experience['id'])
        updated_resp = send_request('delete', url, access_token_second)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403

    def test_delete_exp_bullets_of_a_different_candidate(self, user_first, access_token_first, talent_pool):
        """
        Test:   Attempt to delete the exp-bullets of a different Candidate
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

        # Retrieve candidate_2's experiences
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_2_id, access_token_first)
        can_2_experiences = get_resp.json()['candidate']['work_experiences']

        # Delete candidate_2's experience bullet using candidate_1_id
        url = CandidateApiUrl.EXPERIENCE_BULLETS % (candidate_1_id, can_2_experiences[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403
        assert updated_resp.json()['error']['code'] == custom_error.EXPERIENCE_FORBIDDEN

    def test_delete_candidate_experience_bullets(self, user_first, access_token_first, talent_pool):
        """
        Test:   Remove all of Candidate's experience-bullets from db
        Expect: 204; Candidate should not have any experience bullets left.
                No experiences should be removed
        """
        # Create Candidate
        AddUserRoles.all_roles(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate Experiences
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_experiences = get_resp.json()['candidate']['work_experiences']

        # Current Number of can_experiences
        experience_count_before_deleting_bullets = len(can_experiences)

        # Remove all of Candidate's experiences
        url = CandidateApiUrl.EXPERIENCE_BULLETS % (candidate_id, can_experiences[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']
        assert updated_resp.status_code == 204
        assert len(can_dict_after_update['work_experiences'][0]['bullets']) == 0
        assert len(can_dict_after_update['work_experiences']) == experience_count_before_deleting_bullets

    def test_delete_candidates_experience_bullet(self, user_first, access_token_first, talent_pool):
        """
        Test:   Remove Candidate's experience-bullet from db
        Expect: 204, Candidate's experience-bullet must be less 1; no experiences must be removed
        """
        # Create Candidate
        AddUserRoles.all_roles(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate Experiences
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_experiences = get_resp.json()['candidate']['work_experiences']

        # Current Number of can_experiences, and can_experiences' first bullets
        experience_count_before_deleting_bullets = len(can_experiences)
        experience_bullet_count_before_deleting = len(can_experiences[0]['bullets'])

        # Remove all of Candidate's experiences
        url = CandidateApiUrl.EXPERIENCE_BULLET % (candidate_id, can_experiences[0]['id'],
                                                   can_experiences[0]['bullets'][0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']
        assert updated_resp.status_code == 204
        assert len(can_dict_after_update['work_experiences'][0]['bullets']) == experience_bullet_count_before_deleting - 1
        assert len(can_dict_after_update['work_experiences']) == experience_count_before_deleting_bullets


class TestDeleteCandidateEmail(object):
    def test_non_logged_in_user_delete_can_emails(self):
        """
        Test:   Delete candidate's emails without logging in
        Expect: 401
        """
        # Delete Candidate's emails
        resp = send_request('delete', CandidateApiUrl.EMAILS % 5, None)
        print response_info(resp)
        assert resp.status_code == 401

    def test_delete_candidate_email_with_bad_input(self):
        """
        Test:   Attempt to delete candidate email with non integer values for candidate_id & email_id
        Expect: 404
        """
        # Delete Candidate's emails
        resp = send_request('delete', CandidateApiUrl.EMAILS % 'x', access_token_first)
        print response_info(resp)
        assert resp.status_code == 404

        # Delete Candidate's email
        resp = send_request('delete', CandidateApiUrl.EMAIL % (5, 'x'), access_token_first)
        print response_info(resp)
        assert resp.status_code == 404

    def test_delete_email_of_a_candidate_belonging_to_a_diff_user(self, user_first, access_token_first, talent_pool,
                                                                  user_second, access_token_second):
        """
        Test:   Attempt to delete the email of a Candidate that belongs
                to a different user from a different domain
        Expect: 403
        """
        # Create candidate_1 & candidate_2 with sample_user & sample_user_2
        AddUserRoles.add(user_first)
        AddUserRoles.delete(user_second)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp_1 = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        candidate_1_id = create_resp_1.json()['candidates'][0]['id']

        # Delete candidate_1's email with sample_user_2 logged in
        updated_resp = send_request('delete', CandidateApiUrl.EMAILS % candidate_1_id, access_token_second)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403
        assert updated_resp.json()['error']['code'] == custom_error.CANDIDATE_FORBIDDEN

    def test_delete_email_of_a_different_candidate(self, user_first, access_token_first, talent_pool):
        """
        Test:   Attempt to delete the email of a different Candidate
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

        # Retrieve candidate_2's emails
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_2_id, access_token_first)
        can_2_emails = get_resp.json()['candidate']['emails']

        # Delete candidate_2's id using candidate_1_id
        url = CandidateApiUrl.EMAIL % (candidate_1_id, can_2_emails[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403
        assert updated_resp.json()['error']['code'] == custom_error.EMAIL_FORBIDDEN

    def test_delete_candidate_emails(self, user_first, access_token_first, talent_pool):
        """
        Test:   Remove Candidate's emails from db
        Expect: 204, Candidate must not have any emails left
        """
        # Create Candidate
        AddUserRoles.all_roles(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Delete Candidate's emails
        candidate_id = create_resp.json()['candidates'][0]['id']
        updated_resp = send_request('delete', CandidateApiUrl.EMAILS % candidate_id, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']
        assert updated_resp.status_code == 204
        assert len(can_dict_after_update['emails']) == 0

    def test_delete_candidate_email(self, user_first, access_token_first, talent_pool):
        """
        Test:   Remove Candidate's email from db
        Expect: 204, Candidate's emails must be less 1
        """
        # Create Candidate
        AddUserRoles.all_roles(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate's emails
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_emails = get_resp.json()['candidate']['emails']

        # Current number of candidate's emails
        emails_count_before_delete = len(can_emails)

        # Delete Candidate's email
        url = CandidateApiUrl.EMAIL % (candidate_id, can_emails[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate's emails after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_emails_after_delete = get_resp.json()['candidate']['emails']
        assert updated_resp.status_code == 204
        assert len(can_emails_after_delete) == emails_count_before_delete - 1


class TestDeleteCandidateMilitaryService(object):
    def test_non_logged_in_user_delete_can_military_service(self):
        """
        Test:   Delete candidate's military_services without logging in
        Expect: 401
        """
        # Delete Candidate's military_services
        resp = send_request('delete', CandidateApiUrl.MILITARY_SERVICES % 5, None)
        print response_info(resp)
        assert resp.status_code == 401

    def test_delete_candidate_military_service_with_bad_input(self):
        """
        Test:   Attempt to delete candidate military_services with non integer values
                for candidate_id & military_service_id
        Expect: 404
        """
        # Delete Candidate's military_services
        resp = resp = send_request('delete', CandidateApiUrl.MILITARY_SERVICES % 'x', None)
        print response_info(resp)
        assert resp.status_code == 404

        # Delete Candidate's military_service
        resp = send_request('delete', CandidateApiUrl.MILITARY_SERVICE % (5, 'x'), None)
        print response_info(resp)
        assert resp.status_code == 404

    def test_delete_military_service_of_a_candidate_belonging_to_a_diff_user(self, user_first, access_token_first,
                                                                             talent_pool, user_second,
                                                                             access_token_second):
        """
        Test:   Attempt to delete the military_services of a Candidate that belongs
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

        # Delete candidate_1's military_services with sample_user_2 logged in
        updated_resp = send_request('delete', CandidateApiUrl.MILITARY_SERVICES % candidate_1_id, access_token_second)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403
        assert updated_resp.json()['error']['code'] == custom_error.CANDIDATE_FORBIDDEN

    def test_delete_military_service_of_a_different_candidate(self, user_first, access_token_first, talent_pool):
        """
        Test:   Attempt to delete the military_service of a different Candidate
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

        # Retrieve candidate_2's military_services
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_2_id, access_token_first)
        can_2_military_services = get_resp.json()['candidate']['military_services']

        # Delete candidate_2's military service using candidate_1_id
        url = CandidateApiUrl.MILITARY_SERVICE % (candidate_1_id, can_2_military_services[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403
        assert updated_resp.json()['error']['code'] == custom_error.MILITARY_FORBIDDEN

    def test_delete_candidate_military_services(self, user_first, access_token_first, talent_pool):
        """
        Test:   Remove Candidate's military services from db
        Expect: 204, Candidate must not have any military services left
        """
        # Create Candidate
        AddUserRoles.all_roles(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Delete Candidate's military services
        candidate_id = create_resp.json()['candidates'][0]['id']
        updated_resp = send_request('delete', CandidateApiUrl.MILITARY_SERVICES % candidate_id, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']
        assert updated_resp.status_code == 204
        assert len(can_dict_after_update['military_services']) == 0

    def test_delete_can_military_service(self, user_first, access_token_first, talent_pool):
        """
        Test:   Remove Candidate's military service from db
        Expect: 204, Candidate's military services must be less 1
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        AddUserRoles.all_roles(user_first)
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate's military services
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_military_services = get_resp.json()['candidate']['military_services']

        # Current number of candidate's military services
        military_services_count_before_delete = len(can_military_services)

        # Delete Candidate's military service
        url = CandidateApiUrl.MILITARY_SERVICE % (candidate_id, can_military_services[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate's military services after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_military_services_after_delete = get_resp.json()['candidate']['military_services']
        assert updated_resp.status_code == 204
        assert len(can_military_services_after_delete) == military_services_count_before_delete - 1


class TestDeleteCandidatePhone(object):
    def test_non_logged_in_user_delete_can_phone(self):
        """
        Test:   Delete candidate's phone without logging in
        Expect: 401
        """
        # Delete Candidate's phones
        resp = send_request('delete', CandidateApiUrl.PHONES % 5, None)
        print response_info(resp)
        assert resp.status_code == 401

    def test_delete_candidate_phone_with_bad_input(self):
        """
        Test:   Attempt to delete candidate phone with non integer values for candidate_id & phone_id
        Expect: 404
        """
        # Delete Candidate's phones
        resp = send_request('delete', CandidateApiUrl.PHONES % 'x', None)
        print response_info(resp)
        assert resp.status_code == 404

        # Delete Candidate's phone
        resp = send_request('delete', CandidateApiUrl.PHONE % (5, 'x'), None)
        print response_info(resp)
        assert resp.status_code == 404

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
        assert updated_resp.status_code == 403
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
        assert updated_resp.status_code == 403
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
        assert updated_resp.status_code == 204
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
        assert updated_resp.status_code == 204
        assert len(can_phones_after_delete) == phones_count_before_delete - 1


class TestDeleteCandidatePreferredLocation(object):
    def test_non_logged_in_user_delete_can_preferred_location(self):
        """
        Test:   Delete candidate's preferred location without logging in
        Expect: 401
        """
        # Delete Candidate's preferred locations
        resp = send_request('delete', CandidateApiUrl.PREFERRED_LOCATIONS % 5, None)
        print response_info(resp)
        assert resp.status_code == 401

    def test_delete_candidate_preferred_location_with_bad_input(self):
        """
        Test:   Attempt to delete candidate preferred location with non integer values
                for candidate_id & preferred_location_id
        Expect: 404
        """
        # Delete Candidate's preferred locations
        resp = send_request('delete', CandidateApiUrl.PREFERRED_LOCATIONS % 'x', None)
        print response_info(resp)
        assert resp.status_code == 404

        # Delete Candidate's preferred location
        resp = send_request('delete', CandidateApiUrl.PREFERRED_LOCATION % (5, 'x'), None)
        print response_info(resp)
        assert resp.status_code == 404

    def test_delete_preferred_location_of_a_candidate_belonging_to_a_diff_user(self, user_first, access_token_first,
                                                                               talent_pool, user_second,
                                                                               access_token_second):
        """
        Test:   Attempt to delete preferred locations of a Candidate that belongs
                to a user from a different domain
        Expect: 403
        """
        # Create candidate_1 & candidate_2 with sample_user & sample_user_2
        AddUserRoles.add(user_first)
        AddUserRoles.delete(user_second)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp_1 = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve candidate_1
        candidate_1_id = create_resp_1.json()['candidates'][0]['id']

        # Delete candidate_1's preferred locations with sample_user_2 logged in
        url = CandidateApiUrl.PREFERRED_LOCATIONS % candidate_1_id
        updated_resp = send_request('delete', url, access_token_second)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403

    def test_delete_preferred_location_of_a_different_candidate(self, user_first, access_token_first, talent_pool):
        """
        Test:   Attempt to delete the preferred location of a different Candidate
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

        # Retrieve candidate_2's preferred locations
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_2_id, access_token_first)
        can_2_preferred_locationes = get_resp.json()['candidate']['preferred_locations']

        # Delete candidate_2's id using candidate_1_id
        url = CandidateApiUrl.PREFERRED_LOCATION % (candidate_1_id, can_2_preferred_locationes[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403

    def test_delete_candidate_preferred_locations(self, user_first, access_token_first, talent_pool):
        """
        Test:   Remove Candidate's preferred locations from db
        Expect: 204, Candidate must not have any preferred locations left
        """
        # Create Candidate
        AddUserRoles.all_roles(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Delete Candidate's preferred locations
        candidate_id = create_resp.json()['candidates'][0]['id']
        updated_resp = send_request('delete', CandidateApiUrl.PREFERRED_LOCATIONS % candidate_id, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']
        assert updated_resp.status_code == 204
        assert len(can_dict_after_update['preferred_locations']) == 0

    def test_delete_candidate_preferred_location(self, user_first, access_token_first, talent_pool):
        """
        Test:   Remove Candidate's preferred location from db
        Expect: 204, Candidate's preferred locations must be less 1
        """
        # Create Candidate
        AddUserRoles.all_roles(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate's preferred locations
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_preferred_locations = get_resp.json()['candidate']['preferred_locations']

        # Current number of candidate's preferred locations
        preferred_locations_count_before_delete = len(can_preferred_locations)

        # Delete Candidate's preferred location
        url = CandidateApiUrl.PREFERRED_LOCATION % (candidate_id, can_preferred_locations[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate's preferred locations after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_preferred_locations_after_delete = get_resp.json()['candidate']['preferred_locations']
        assert updated_resp.status_code == 204
        assert len(can_preferred_locations_after_delete) == preferred_locations_count_before_delete - 1


class TestDeleteCandidateSkill(object):
    def test_non_logged_in_user_delete_can_skill(self):
        """
        Test:   Delete candidate's skills without logging in
        Expect: 401
        """
        # Delete Candidate's skills
        resp = send_request('delete', CandidateApiUrl.SKILLS % 5, None)
        print response_info(resp)
        assert resp.status_code == 401

    def test_delete_candidate_skill_with_bad_input(self):
        """
        Test:   Attempt to delete candidate skill with non integer values for candidate_id & skill_id
        Expect: 404
        """
        # Delete Candidate's skills
        resp = send_request('delete', CandidateApiUrl.SKILLS % 'x', None)
        print response_info(resp)
        assert resp.status_code == 404

        # Delete Candidate's skill
        resp = send_request('delete', CandidateApiUrl.SKILL % (5, 'x'), None)
        print response_info(resp)
        assert resp.status_code == 404

    def test_delete_skill_of_a_candidate_belonging_to_a_diff_user(self, user_first, access_token_first,
                                                                  talent_pool, user_second,
                                                                  access_token_second):
        """
        Test:   Attempt to delete the skill of a Candidate that belongs
                to a different user from a different domain
        Expect: 403
        """
        # Create candidate_1 & candidate_2
        AddUserRoles.add(user_first)
        AddUserRoles.delete(user_second)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp_1 = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp_1)

        # Retrieve candidate_1
        candidate_1_id = create_resp_1.json()['candidates'][0]['id']

        # Delete candidate_1's skills with user_second logged in
        updated_resp = send_request('delete', CandidateApiUrl.SKILLS % candidate_1_id, access_token_second)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403
        assert updated_resp.json()['error']['code'] == custom_error.CANDIDATE_FORBIDDEN

    def test_delete_skill_of_a_different_candidate(self, user_first, access_token_first, talent_pool):
        """
        Test:   Attempt to delete skill of a different Candidate
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

        # Retrieve candidate_2's skills
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_2_id, access_token_first)
        can_2_skills = get_resp.json()['candidate']['skills']

        # Delete candidate_2's id using candidate_1_id
        url = CandidateApiUrl.SKILL % (candidate_1_id, can_2_skills[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403
        assert updated_resp.json()['error']['code'] == custom_error.SKILL_FORBIDDEN

    def test_delete_candidate_skills(self, user_first, access_token_first, talent_pool):
        """
        Test:   Remove Candidate's skills from db
        Expect: 204, Candidate must not have any skills left
        """
        # Create Candidate
        AddUserRoles.all_roles(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Delete Candidate's skills
        candidate_id = create_resp.json()['candidates'][0]['id']
        updated_resp = send_request('delete', CandidateApiUrl.SKILLS % candidate_id, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']
        assert updated_resp.status_code == 204
        assert len(can_dict_after_update['skills']) == 0

    def test_delete_candidate_skill(self, user_first, access_token_first, talent_pool):
        """
        Test:   Remove Candidate's skill from db
        Expect: 204, Candidate's skills must be less 1
        """
        # Create Candidate
        AddUserRoles.all_roles(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate's skills
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_skills = get_resp.json()['candidate']['skills']

        # Current number of candidate's phones
        skills_count_before_delete = len(can_skills)

        # Delete Candidate's skill
        url = CandidateApiUrl.SKILL % (candidate_id, can_skills[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate's skills after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_skills_after_delete = get_resp.json()['candidate']['skills']
        assert updated_resp.status_code == 204
        assert len(can_skills_after_delete) == skills_count_before_delete - 1


class TestDeleteCandidateSocialNetwork(object):
    def test_non_logged_in_user_delete_can_social_network(self):
        """
        Test:   Delete candidate's social network without logging in
        Expect: 401
        """
        # Delete Candidate's social networks
        resp = send_request('delete', CandidateApiUrl.SOCIAL_NETWORKS % 5, None)
        print response_info(resp)
        assert resp.status_code == 401

    def test_delete_candidate_social_network_with_bad_input(self):
        """
        Test:   Attempt to delete candidate social network with non integer values
                for candidate_id & social_network_id
        Expect: 404
        """
        # Delete Candidate's social networks
        resp = send_request('delete', CandidateApiUrl.SOCIAL_NETWORKS % 'x', None)
        print response_info(resp)
        assert resp.status_code == 404

        # Delete Candidate's social network
        resp = send_request('delete', CandidateApiUrl.SOCIAL_NETWORK % (5, 'x'), None)
        print response_info(resp)
        assert resp.status_code == 404

    def test_delete_social_network_of_a_candidate_belonging_to_a_diff_user(self, user_first, access_token_first,
                                                                           talent_pool, user_second,
                                                                           access_token_second):
        """
        Test:   Attempt to delete the social networks of a Candidate that belongs
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

        # Delete candidate_1's social networks with sample_user_2 logged in
        updated_resp = send_request('delete', CandidateApiUrl.SOCIAL_NETWORKS % candidate_1_id, access_token_second)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403
        assert updated_resp.json()['error']['code'] == custom_error.CANDIDATE_FORBIDDEN

    def test_delete_social_network_of_a_different_candidate(self, user_first, access_token_first, talent_pool):
        """
        Test:   Attempt to delete the social network of a different Candidate
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


        # Retrieve candidate_2's social networks
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_2_id, access_token_first)
        can_2_social_networkes = get_resp.json()['candidate']['social_networks']

        # Delete candidate_2's id using candidate_1_id
        url = CandidateApiUrl.SOCIAL_NETWORK % (candidate_1_id, can_2_social_networkes[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403
        assert updated_resp.json()['error']['code'] == custom_error.SOCIAL_NETWORK_FORBIDDEN

    def test_delete_candidate_social_networks(self, user_first, access_token_first, talent_pool):
        """
        Test:   Remove Candidate's social networks from db
        Expect: 204, Candidate must not have any social networks left
        """
        # Create Candidate
        AddUserRoles.all_roles(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Delete Candidate's social networks
        candidate_id = create_resp.json()['candidates'][0]['id']
        updated_resp = send_request('delete', CandidateApiUrl.SOCIAL_NETWORKS % candidate_id, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']
        assert updated_resp.status_code == 204
        assert len(can_dict_after_update['social_networks']) == 0

    def test_delete_can_social_network(self, user_first, access_token_first, talent_pool):
        """
        Test:   Remove Candidate's social network from db
        Expect: 204, Candidate's social networks must be less 1
        """
        # Create Candidate
        AddUserRoles.all_roles(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate's social networks
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_sn = get_resp.json()['candidate']['social_networks']

        # Current number of candidate's social networks
        sn_count_before_delete = len(can_sn)

        # Delete Candidate's skill
        url = CandidateApiUrl.SOCIAL_NETWORK % (candidate_id, can_sn[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate's social networks after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_sn_after_delete = get_resp.json()['candidate']['social_networks']
        assert updated_resp.status_code == 204
        assert len(can_sn_after_delete) == sn_count_before_delete - 1


class TestDeleteWorkPreference(object):
    def test_non_logged_in_user_delete_can_work_preference(self):
        """
        Test:   Delete candidate's work preference without logging in
        Expect: 401
        """
        # Delete Candidate's work preference
        resp = send_request('delete', CandidateApiUrl.WORK_PREFERENCE % 5, None)
        print response_info(resp)
        assert resp.status_code == 401

    def test_delete_candidate_work_preference_with_bad_input(self):
        """
        Test:   Attempt to delete candidate work preference with non integer values
                for candidate_id & work_preference_id
        Expect: 404
        """
        # Delete Candidate's work preference
        resp = send_request('delete', CandidateApiUrl.WORK_PREFERENCE % 'x', None)
        print response_info(resp)
        assert resp.status_code == 404

    def test_delete_work_preference_of_a_candidate_belonging_to_a_diff_user(self, user_first, access_token_first,
                                                                            talent_pool, user_second,
                                                                            access_token_second):
        """
        Test:   Attempt to delete the work preference of a Candidate that belongs
                to a user from a different domain
        Expect: 403
        """
        # Get access token_1 & access_token_second for sample_user & sample_user_2, respectively
        AddUserRoles.add_and_get(user_first)
        AddUserRoles.delete(user_second)

        # Create candidate_1 & candidate_2 with sample_user & sample_user_2
        data = generate_single_candidate_data([talent_pool.id])
        create_resp_1 = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        candidate_1_id = create_resp_1.json()['candidates'][0]['id']

        # Delete candidate_1's work preference with sample_user_2 logged in
        updated_resp = send_request('delete', CandidateApiUrl.WORK_PREFERENCE % candidate_1_id, access_token_second)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403
        assert updated_resp.json()['error']['code'] == custom_error.CANDIDATE_FORBIDDEN

    def test_delete_candidate_work_preference(self, user_first, access_token_first, talent_pool):
        """
        Test:   Remove Candidate's work-preference from db
        Expect: 204, Candidate must not have any work-preference left
        """
        # Create Candidate
        AddUserRoles.all_roles(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate's work preference
        candidate_id = create_resp.json()['candidates'][0]['id']

        # Delete Candidate's work preference
        updated_resp = send_request('delete', CandidateApiUrl.WORK_PREFERENCE % candidate_id, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']
        assert updated_resp.status_code == 204
        assert len(can_dict_after_update['work_preference']) == 0
