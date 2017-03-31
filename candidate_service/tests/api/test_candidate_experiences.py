"""
Test cases for adding, retrieving, updating, and deleting candidate work experiences
"""
import pycountry

from candidate_service.common.tests.conftest import *
from candidate_service.common.utils.test_utils import send_request, response_info
from candidate_service.tests.api.candidate_sample_data import GenerateCandidateData, generate_single_candidate_data


class TestUpdateCandidateExperienceSuccessfully(object):
    """
    Class contains functional tests that will update facets of candidate's work experiences
    """

    def test_update_start_and_end_dates(self, test_candidate_1, access_token_first):
        """
        Test: will update the start date & end date of one of candidate's work experience
        """
        candidate_id = test_candidate_1['candidate']['id']
        work_experience = test_candidate_1['candidate']['work_experiences'][0]
        updated_start_year = int(work_experience['start_date'][:4]) - 5
        updated_end_year = int(work_experience['end_date'][:4]) - 3

        update_data = {
            "candidates": [
                {
                    'work_experiences': [
                        {
                            'id': work_experience['id'],
                            'start_year': updated_start_year,
                            'end_year': updated_end_year
                        }
                    ]
                }
            ]
        }

        # Update candidate
        update_resp = send_request('patch', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first, update_data)
        print response_info(update_resp)
        assert update_resp.status_code == requests.codes.OK

        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        assert update_resp.status_code == requests.codes.OK
        candidate_experiences = get_resp.json()['candidate']['work_experiences']
        updated_experience = [exp for exp in candidate_experiences if exp['id'] == work_experience['id']][0]
        assert updated_experience['start_date'][:4] == str(updated_start_year)
        assert updated_experience['end_date'][:4] == str(updated_end_year)


class TestUpdateWorkExperience(object):
    def test_add_experiences(self, access_token_first, talent_pool):
        """
        Test:  Add candidate work experience and check for total months of experiences accumulated
        Expect: Candidate.total_months_experience to be updated accordingly
        """
        data = {'candidates': [
            {
                'talent_pool_ids': {'add': [talent_pool.id]},
                'work_experiences': [
                    {'start_year': 2005, 'end_year': 2007},  # 12*2 = 24 months of experience
                    {'start_year': 2011, 'end_year': None}  # 12*5 = 60 months of experience
                ]
            }
        ]}
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED

        # Check candidate's total_months_experience from db
        candidate_id = create_resp.json()['candidates'][0]['id']
        db.session.commit()
        candidate = Candidate.get_by_id(candidate_id)

        start_year_1 = data['candidates'][0]['work_experiences'][0]['start_year']
        end_year_1 = data['candidates'][0]['work_experiences'][0]['end_year']
        start_year_2 = data['candidates'][0]['work_experiences'][1]['start_year']
        end_year_2 = datetime.utcnow().year  # current year because end_year is null for most recent job
        total_months_worked = (end_year_1 - start_year_1) * 12 + (end_year_2 - start_year_2) * 12
        assert candidate.total_months_experience == total_months_worked

        # Retrieve candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)

        # Add more experiences
        experience_id = get_resp.json()['candidate']['work_experiences'][0]['id']
        update_data = {'candidates': [
            {'id': candidate_id, 'work_experiences': [
                {'id': experience_id, 'start_year': 2003, 'end_year': 2011}]  # 12 * 8 = 96 months of experience
             }
        ]}
        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, update_data)
        print response_info(update_resp)
        db.session.commit()
        assert candidate.total_months_experience == 120  # (84 - 60) + 96

    def test_add_candidate_experience(self, access_token_first, talent_pool):
        """
        Test:   Add a CandidateExperience to an existing Candidate. Number of Candidate's
                CandidateExperience must increase by 1.
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']
        candidate_experience_count = len(candidate_dict['work_experiences'])

        # Add CandidateExperience
        data = GenerateCandidateData.work_experiences(candidate_id=candidate_id)
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        updated_can_dict = get_resp.json()['candidate']
        can_experiences = updated_can_dict['work_experiences']
        can_experiences_from_data = data['candidates'][0]['work_experiences']
        assert candidate_id == updated_can_dict['id']
        assert isinstance(can_experiences, list)
        assert can_experiences[0]['organization'] == can_experiences_from_data[0]['organization']
        assert can_experiences[0]['position'] == can_experiences_from_data[0]['position']
        assert can_experiences[0]['city'] == can_experiences_from_data[0]['city']
        assert can_experiences[0]['subdivision'] == pycountry.subdivisions.get(
            code=can_experiences_from_data[0]['subdivision_code']).name
        assert len(can_experiences) == candidate_experience_count + 1

    def test_multiple_is_current_experiences(self, access_token_first, talent_pool):
        """
        Test:   Add more than one CandidateExperience with is_current set to True
        Expect: 200, but only one CandidateExperience must have is_current True, the rest must be False
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Add a new work experience to the existing Candidate with is_current set to True
        candidate_id = create_resp.json()['candidates'][0]['id']
        send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        updated_candidate_dict = get_resp.json()['candidate']
        updated_can_experiences = updated_candidate_dict['work_experiences']

        # Only one of the experiences must be current!
        assert sum([1 for experience in updated_can_experiences if experience['is_current']]) == 1

    def test_add_experience_bullet(self, access_token_first, talent_pool):
        """
        Test:   Adds a CandidateExperienceBullet to an existing CandidateExperience
                Total number of candidate's experience_bullet must increase by 1, and
                number of candidate's CandidateExperience must remain unchanged.
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        bullet_count = len(candidate_dict['work_experiences'][0]['bullets'])

        # Add CandidateExperienceBullet to existing CandidateExperience
        data = GenerateCandidateData.work_experiences(
            candidate_id=candidate_id, experience_id=candidate_dict['work_experiences'][0]['id'])
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        updated_can_dict = get_resp.json()['candidate']
        updated_experiences = updated_can_dict['work_experiences']

        bullets_from_data = data['candidates'][0]['work_experiences'][0]['bullets'][0]
        assert isinstance(updated_experiences, list)
        assert candidate_id == updated_can_dict['id']
        assert updated_experiences[0]['bullets'][-1]['description'] == bullets_from_data['description']
        assert len(updated_experiences[0]['bullets']) == bullet_count + 1
        assert len(updated_experiences) == len(updated_can_dict['work_experiences'])

    def test_update_experience_bullet(self, access_token_first, talent_pool):
        """
        Test:   Update an existing CandidateExperienceBullet
                Since this is an update only, the number of candidate's experience_bullets
                must remain unchanged.
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        experience_dict = candidate_dict['work_experiences'][0]
        candidate_experience_bullet_count = len(experience_dict['bullets'])

        # Update CandidateExperienceBullet
        data = GenerateCandidateData.work_experiences(candidate_id=candidate_id,
                                                      experience_id=experience_dict['id'],
                                                      bullet_id=experience_dict['bullets'][0]['id'])

        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        updated_can_dict = get_resp.json()['candidate']
        updated_exp_bullet_dict = updated_can_dict['work_experiences'][0]['bullets']

        exp_bullet_dict_from_data = data['candidates'][0]['work_experiences'][0]['bullets'][0]

        assert candidate_experience_bullet_count == len(updated_exp_bullet_dict)
        assert updated_exp_bullet_dict[0]['description'] == exp_bullet_dict_from_data['description']


class TestCandidateTitle(object):
    def test_create_candidate_with_no_title(self, access_token_first, talent_pool):
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'first_name': fake.first_name(),
             'work_experiences': [
                 {'position': 'engineerIII', 'start_year': 2015, 'end_year': 2016},
                 {'position': 'engineerII'}
             ]}
        ]}
        r = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(r)

        candidate_id = r.json()['candidates'][0]['id']

        # Candidate's title should be set to its most recent work experience since title is not provided
        r = send_request('get', CandidateApiUrl.CANDIDATE % str(candidate_id), access_token_first)
        print response_info(r)
        assert r.json()['candidate']['title'] == data['candidates'][0]['work_experiences'][0]['position']

        # Update candidate's title
        update_data = {'candidates': [
            {'id': candidate_id, 'work_experiences': [{'position': 'lawyer', 'is_current': True}]}
        ]}
        send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, update_data)

        r = send_request('get', CandidateApiUrl.CANDIDATE % str(candidate_id), access_token_first)
        print response_info(r)
        assert r.json()['candidate']['title'] == update_data['candidates'][0]['work_experiences'][0]['position']

    def test_set_candidate_title(self, access_token_first, talent_pool):
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'first_name': fake.first_name(), 'title': 'engineerI'}
        ]}
        r = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(r)

        candidate_id = r.json()['candidates'][0]['id']
        r = send_request('get', CandidateApiUrl.CANDIDATE % str(candidate_id), access_token_first)
        print response_info(r)
        assert r.json()['candidate']['title'] == data['candidates'][0]['title']

    def test_set_title_from_experiences(self, access_token_first, talent_pool):
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'first_name': fake.first_name(), 'work_experiences': [
                {'position': 'engineerI', 'is_current': True},
                {'position': 'engineerII', 'start_year': 2015, 'end_year': 2016}
            ]}
        ]}
        r = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(r)

        candidate_id = r.json()['candidates'][0]['id']
        r = send_request('get', CandidateApiUrl.CANDIDATE % str(candidate_id), access_token_first)
        print response_info(r)
        assert r.json()['candidate']['title'] == data['candidates'][0]['work_experiences'][0]['position']

    def test_set_title_from_experiences_and_title(self, access_token_first, talent_pool):
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'first_name': fake.first_name(), 'title': 'engineerI',
             'work_experiences': [
                 {'position': 'engineerII', 'is_current': True},
                 {'position': 'engineerIII', 'start_year': 2015, 'end_year': 2016}
             ]}
        ]}
        r = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(r)

        candidate_id = r.json()['candidates'][0]['id']
        r = send_request('get', CandidateApiUrl.CANDIDATE % str(candidate_id), access_token_first)
        print response_info(r)
        assert r.json()['candidate']['title'] == data['candidates'][0]['title']

    def test_update_title_from_title(self, access_token_first, talent_pool):
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'first_name': fake.first_name(), 'title': 'engineerI',
             'work_experiences': [
                 {'position': 'engineerII', 'is_current': True},
                 {'position': 'engineerIII', 'start_year': 2015, 'end_year': 2016}
             ]}
        ]}
        r = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        candidate_id = r.json()['candidates'][0]['id']
        r = send_request('get', CandidateApiUrl.CANDIDATE % str(candidate_id), access_token_first)
        print response_info(r)
        assert r.json()['candidate']['title'] == data['candidates'][0]['title']

        # Update candidate's title
        update_data = {'candidates': [
            {'id': candidate_id, 'title': 'farmerI'}
        ]}
        send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, update_data)

        r = send_request('get', CandidateApiUrl.CANDIDATE % str(candidate_id), access_token_first)
        print response_info(r)
        assert r.json()['candidate']['title'] == update_data['candidates'][0]['title']

    def test_update_title_from_experiences(self, access_token_first, talent_pool):
        data = {'candidates': [
            {
                'talent_pool_ids': {'add': [talent_pool.id]}, 'first_name': fake.first_name(), 'title': 'engineerI',
                'work_experiences': [
                    {'position': 'engineerII', 'start_year': 2012, 'end_year': 2014},
                    {'position': 'engineerIII', 'start_year': 2015, 'end_year': 2016}
                ]
            }
        ]}
        r = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        candidate_id = r.json()['candidates'][0]['id']
        r = send_request('get', CandidateApiUrl.CANDIDATE % str(candidate_id), access_token_first)
        print response_info(r)
        assert r.json()['candidate']['title'] == data['candidates'][0]['title']

        # Candidate's title should remain the same since its title had been explicitly defined
        update_data = {'candidates': [
            {'id': candidate_id, 'work_experiences': [{'position': 'engineerIV'}]}
        ]}
        send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, update_data)

        r = send_request('get', CandidateApiUrl.CANDIDATE % str(candidate_id), access_token_first)
        print response_info(r)
        assert r.json()['candidate']['title'] == data['candidates'][0]['title']

        # Update candidate's title should change since title is explicitly defined below
        update_data = {'candidates': [
            {'id': candidate_id, 'title': 'pediatrician'}
        ]}
        send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, update_data)

        r = send_request('get', CandidateApiUrl.CANDIDATE % str(candidate_id), access_token_first)
        print response_info(r)
        assert r.json()['candidate']['title'] == update_data['candidates'][0]['title']
