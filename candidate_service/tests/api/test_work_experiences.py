"""
Test cases for CandidateWorkExperienceResource
"""
# Candidate Service app instance
from candidate_service.candidate_app import app

# Conftest
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import AddUserRoles, get_country_code_from_name
from candidate_service.common.routes import CandidateApiUrl
from candidate_service.common.utils.test_utils import send_request, response_info

# Sample data
from candidate_sample_data import (GenerateCandidateData, generate_single_candidate_data)

# Custom errors
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error


class TestDeleteWorkExperience(object):
    OK = 200
    CREATED = 201
    DELETED = 204
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CANDIDATE_URL = CandidateApiUrl.CANDIDATE
    CANDIDATES_URL = CandidateApiUrl.CANDIDATES
    EXPERIENCE_URL = CandidateApiUrl.EXPERIENCE
    EXPERIENCES_URL = CandidateApiUrl.EXPERIENCES

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
                    {'start_year': 2011, 'end_year': None}  # 12*5 = 60 months of experience
                ]
            }
        ]}
        create_resp = send_request('post', self.CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == self.CREATED

        # Check candidate's total_months_experience from db
        candidate_id = create_resp.json()['candidates'][0]['id']
        db.session.commit()
        candidate = Candidate.get_by_id(candidate_id)
        assert candidate.total_months_experience == 84  # 24 + 60

        # Retrieve candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)

        # Delete one of the experiences
        experience_id = get_resp.json()['candidate']['work_experiences'][0]['id']
        del_resp = send_request('delete', self.EXPERIENCE_URL % (candidate_id, experience_id), access_token_first)
        print response_info(del_resp)
        db.session.commit()
        assert candidate.total_months_experience == 24  # (84 - 60)

    def test_non_logged_in_user_delete_can_experience(self):
        """
        Test:   Delete candidate's experiences without logging in
        Expect: 401
        """
        # Delete Candidate's experiences
        resp = send_request('delete', self.EXPERIENCES_URL % 5, None)
        print response_info(resp)
        assert resp.status_code == self.UNAUTHORIZED

    def test_delete_candidate_experience_with_bad_input(self, access_token_first):
        """
        Test:   Attempt to delete candidate experience with non integer values for candidate_id & experience_id
        Expect: 404
        """
        # Delete Candidate's experiences
        resp = send_request('delete', self.EXPERIENCES_URL % 'x', access_token_first)
        print response_info(resp)
        assert resp.status_code == self.NOT_FOUND

        # Delete Candidate's experience
        resp = send_request('delete', self.EXPERIENCE_URL % (5, 'x'), access_token_first)
        print response_info(resp)
        assert resp.status_code == self.NOT_FOUND

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
        create_resp_1 = send_request('post', self.CANDIDATES_URL, access_token_first, data)

        # Retrieve candidate_1
        candidate_1_id = create_resp_1.json()['candidates'][0]['id']

        # Delete candidate_1's experience with sample_user_2 logged in
        updated_resp = send_request('delete', self.EXPERIENCES_URL % candidate_1_id, access_token_second, data)
        print response_info(updated_resp)
        assert updated_resp.status_code == self.FORBIDDEN

    def test_delete_experience_of_a_different_candidate(self, user_first, access_token_first, talent_pool):
        """
        Test:   Attempt to delete the experience of a different Candidate
        Expect: 403
        """
        # Create candidate_1 and candidate_2
        AddUserRoles.all_roles(user_first)
        data_1 = generate_single_candidate_data([talent_pool.id])
        data_2 = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', self.CANDIDATES_URL, access_token_first, data_1)
        candidate_1_id = create_resp.json()['candidates'][0]['id']
        create_resp = send_request('post', self.CANDIDATES_URL, access_token_first, data_2)
        candidate_2_id = create_resp.json()['candidates'][0]['id']

        # Retrieve candidate_2's experiences
        get_resp = send_request('get', self.CANDIDATE_URL % candidate_2_id, access_token_first)
        can_2_experiences = get_resp.json()['candidate']['work_experiences']

        # Delete candidate_2's experience using candidate_1_id
        exp_id = can_2_experiences[0]['id']
        updated_resp = send_request('delete', self.EXPERIENCE_URL % (candidate_1_id, exp_id), access_token_first)
        print response_info(updated_resp)
        assert updated_resp.status_code == self.FORBIDDEN
        assert updated_resp.json()['error']['code'] == custom_error.EXPERIENCE_FORBIDDEN

    def test_delete_candidate_experiences(self, user_first, access_token_first, talent_pool):
        """
        Test:   Remove all of candidate's experiences from db
        Expect: 204; Candidate should not have any experience left
        """
        # Create Candidate
        AddUserRoles.all_roles(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', self.CANDIDATES_URL, access_token_first, data)
        candidate_id = create_resp.json()['candidates'][0]['id']

        # Remove all of Candidate's experiences
        updated_resp = send_request('delete', self.EXPERIENCES_URL % candidate_id, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', self.CANDIDATE_URL % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']
        assert updated_resp.status_code == self.DELETED
        assert len(can_dict_after_update['work_experiences']) == 0

    def test_delete_candidate_experience(self, user_first, access_token_first, talent_pool):
        """
        Test:   Remove Candidate's experience from db
        Expect: 204, Candidate's experience must be less 1.
        """
        # Create Candidate
        AddUserRoles.all_roles(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', self.CANDIDATES_URL, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', self.CANDIDATE_URL % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']
        candidate_experiences = candidate_dict['work_experiences']

        # Current number of Candidate's experiences
        experiences_count_before_delete = len(candidate_experiences)

        # Remove one of Candidate's education
        exp_id = candidate_experiences[0]['id']
        updated_resp = send_request('delete', self.EXPERIENCE_URL % (candidate_id, exp_id), access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', self.CANDIDATE_URL % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']
        assert updated_resp.status_code == self.DELETED
        assert len(can_dict_after_update['work_experiences']) == experiences_count_before_delete - 1


class TestDeleteWorkExperienceBullet(object):
    UNAUTHORIZED = 401
    NOT_FOUND = 404
    FORBIDDEN = 403
    DELETED = 204
    CANDIDATE_URL = CandidateApiUrl.CANDIDATE
    CANDIDATES_URL = CandidateApiUrl.CANDIDATES
    BULLET_URL = CandidateApiUrl.EXPERIENCE_BULLET
    BULLETS_URL = CandidateApiUrl.EXPERIENCE_BULLETS

    def test_non_logged_in_user_delete_can_experience_bullets(self, access_token_first):
        """
        Test:   Delete candidate's experience-bullets without logging in
        Expect: 401
        """
        # Delete Candidate's experience-bullets
        resp = send_request('delete', self.BULLETS_URL % (5, 5), access_token_first)
        print response_info(resp)
        assert resp.status_code == self.UNAUTHORIZED

    def test_delete_candidate_experience_bullet_with_bad_input(self, access_token_first):
        """
        Test:   Attempt to delete candidate experience-bullet with non integer values
                for candidate_id & experience_id
        Expect: 404
        """
        # Delete Candidate's experience-bullets
        url = self.BULLETS_URL % ('x', 5)
        resp = send_request('delete', url, access_token_first)
        print response_info(resp)
        assert resp.status_code == self.NOT_FOUND

        # Delete Candidate's experience-bullet
        url = self.BULLET_URL % (5, 5, 'x')
        resp = send_request('delete', url, None)
        print response_info(resp)
        assert resp.status_code == self.NOT_FOUND

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
        url = self.BULLETS_URL % (candidate_1_id, experience['id'])
        updated_resp = send_request('delete', url, access_token_second)
        print response_info(updated_resp)
        assert updated_resp.status_code == self.FORBIDDEN

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
        url = self.BULLETS_URL % (candidate_1_id, can_2_experiences[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)
        assert updated_resp.status_code == self.FORBIDDEN
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
        url = self.BULLETS_URL % (candidate_id, can_experiences[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']
        assert updated_resp.status_code == self.DELETED
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
        url = self.BULLET_URL % (candidate_id, can_experiences[0]['id'],
                                                   can_experiences[0]['bullets'][0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']
        assert updated_resp.status_code == self.DELETED
        assert len(
            can_dict_after_update['work_experiences'][0]['bullets']) == experience_bullet_count_before_deleting - 1
        assert len(can_dict_after_update['work_experiences']) == experience_count_before_deleting_bullets


class TestCreateWorkExperience(object):
    OK = 200
    CREATED = 201
    CANDIDATES_URL = CandidateApiUrl.CANDIDATES
    CANDIDATE_URL = CandidateApiUrl.CANDIDATE

    def test_create_work_experience_successfully(self, access_token_first, user_first, talent_pool):
        """
        Test:  Create candidate + work experience
        Expect: 201
        """
        # Create candidate +  work experience
        AddUserRoles.add_and_get(user_first)
        data = GenerateCandidateData.work_experiences([talent_pool.id])
        country_code = data['candidates'][0]['work_experiences'][0]['country_code']
        create_resp = send_request('post', self.CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == self.CREATED

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', self.CANDIDATE_URL % candidate_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == self.OK
        assert get_country_code_from_name(
            get_resp.json()['candidate']['work_experiences'][0]['country']) == country_code

    def test_create_experiences(self, access_token_first, user_first, talent_pool):
        """
        Test:  Add candidate work experience and check for total months of experiences accumulated
        """
        AddUserRoles.add_and_get(user_first)
        data = {'candidates': [
            {
                'talent_pool_ids': {'add': [talent_pool.id]},
                'work_experiences': [
                    {'start_year': 2005, 'end_year': 2007},  # 12*2 = 24 months of experience
                    {'start_year': 2008, 'end_year': None},  # 12*1 = 12 months of experience
                    {'start_year': 2011, 'end_year': 2016}  # 12*5 = 60 months of experience
                ]
            }
        ]}
        create_resp = send_request('post', self.CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == self.CREATED

        # Check candidate's total_months_experience from db
        candidate_id = create_resp.json()['candidates'][0]['id']
        db.session.commit()
        assert Candidate.get_by_id(candidate_id).total_months_experience == 96  # 24 + 12 + 60

    def test_create_candidate_experience(self, access_token_first, user_first, talent_pool):
        """
        Test:   Create CandidateExperience for Candidate
        Expect: 201
        """
        AddUserRoles.add_and_get(user=user_first)

        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', self.CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == self.CREATED

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', self.CANDIDATE_URL % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        # Assert data sent in = data retrieved
        can_experiences = candidate_dict['work_experiences']
        can_exp_data = data['candidates'][0]['work_experiences'][0]
        assert isinstance(can_experiences, list)

        assert can_experiences[0]['organization'] == can_exp_data['organization']
        assert can_experiences[0]['position'] == can_exp_data['position']
        assert can_experiences[0]['city'] == can_exp_data['city']
        assert can_experiences[0]['is_current'] == can_exp_data['is_current']

        can_exp_bullets = can_experiences[0]['bullets']
        assert isinstance(can_exp_bullets, list)
        assert can_exp_bullets[0]['description'] == can_exp_data['bullets'][0]['description']

    def test_create_candidate_experiences_with_no_bullets(self, access_token_first, user_first, talent_pool):
        """
        Test:   Create CandidateEducation for Candidate
        Expect: 201
        """
        # Create Candidate without degrees
        AddUserRoles.add_and_get(user_first)
        data = {'candidates': [
            {'work_experiences': [
                {'organization': 'Apple', 'city': 'Cupertino', 'state': None, 'country': None,
                 'start_month': None, 'start_year': None, 'end_month': None, 'end_year': None,
                 'position': None, 'is_current': None, 'bullets': None}],
                'talent_pool_ids': {'add': [talent_pool.id]}
            }
        ]}
        create_resp = send_request('post', self.CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == self.CREATED

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', self.CANDIDATE_URL % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        can_experiences = candidate_dict['work_experiences']
        assert isinstance(can_experiences, list)
        assert can_experiences[0]['organization'] == 'Apple'
        assert can_experiences[0]['city'] == 'Cupertino'
        can_experience_bullets = can_experiences[0]['bullets']
        assert isinstance(can_experience_bullets, list)
