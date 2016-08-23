"""
Test cases pertaining to CandidateEditResource
"""
# Candidate Service app instance
from candidate_service.candidate_app import app

# Conftest
from candidate_service.common.tests.conftest import *

# Helper functions
from candidate_service.common.utils.test_utils import send_request, response_info
from candidate_service.common.routes import CandidateApiUrl
from candidate_service.tests.api.helpers import get_int_version

# Candidate sample data
from candidate_sample_data import generate_single_candidate_data


class TestTrackCandidateEdits(object):
    def test_edit_candidate_primary_info(self, access_token_first, talent_pool):
        """
        Test:   Change Candidate's first, middle, and last names
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        old_candidate_dict = get_resp.json()['candidate']

        # Update Candidate's first and last names
        data = {'candidates': [
            {'id': candidate_id, 'first_name': 'Quentin', 'middle_name': 'Jerome', 'last_name': 'Tarantino'}
        ]}
        send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        new_candidate_dict = get_resp.json()['candidate']

        # Retrieve Candidate Edits
        edit_resp = send_request('get', CandidateApiUrl.CANDIDATE_EDIT % candidate_id, access_token_first)
        print response_info(edit_resp)

        candidate_edits = edit_resp.json()['candidate']['edits']
        assert edit_resp.status_code == 200
        assert candidate_edits[0]['old_value'] in old_candidate_dict['full_name']
        assert candidate_edits[0]['new_value'] in new_candidate_dict['full_name']


class TestTrackCandidateAddressEdits(object):
    def test_edit_candidate_address(self, access_token_first, talent_pool):
        """
        Test:   Edit Candidate's address
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        old_address_dict = get_resp.json()['candidate']['addresses'][0]

        # Update Candidate's address
        data = {'candidates': [
            {'id': candidate_id, 'addresses': [
                {'id': old_address_dict['id'], 'address_line_1': '255 west santa clara'}
            ]}
        ]}
        send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate addresses
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        new_address_dict = get_resp.json()['candidate']['addresses'][0]

        # Retrieve Candidate Edits
        edit_resp = send_request('get', CandidateApiUrl.CANDIDATE_EDIT % candidate_id, access_token_first)
        print response_info(edit_resp)

        candidate_edits = edit_resp.json()['candidate']['edits']
        assert edit_resp.status_code == 200
        assert new_address_dict['address_line_1'] != old_address_dict['address_line_1']
        assert old_address_dict['address_line_1'] in [edit['old_value'] for edit in candidate_edits]
        assert new_address_dict['address_line_1'] in [edit['new_value'] for edit in candidate_edits]


class TestTrackCandidateCustomFieldEdits(object):
    def test_edit_candidate_custom_field(self, access_token_first, talent_pool, domain_custom_fields):
        """
        Test:   Change Candidate's custom fields
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id], custom_fields=domain_custom_fields)
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        old_custom_field_dict = get_resp.json()['candidate']['custom_fields'][0]

        # Update Candidate's custom field
        data = {'candidates': [
            {'id': candidate_id, 'custom_fields': [
                {'id': old_custom_field_dict['id'], 'value': 'foobar'}
            ]}
        ]}
        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(update_resp)

        # Retrieve Candidate custom fields
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        new_custom_field_dict = get_resp.json()['candidate']['custom_fields'][0]

        # Retrieve Candidate Edits
        edit_resp = send_request('get', CandidateApiUrl.CANDIDATE_EDIT % candidate_id, access_token_first)
        print response_info(edit_resp)
        candidate_edits = edit_resp.json()['candidate']['edits']

        assert edit_resp.status_code == requests.codes.OK
        assert old_custom_field_dict['value'] in [edit['old_value'] for edit in candidate_edits]
        assert new_custom_field_dict['value'] in [edit['new_value'] for edit in candidate_edits]


class TestTrackCandidateEducationEdits(object):
    def test_edit_candidate_education(self, access_token_first, talent_pool):
        """
        Test:   Change Candidate's education records
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        old_education_dict = get_resp.json()['candidate']['educations'][0]

        # Update Candidate's education
        data = {'candidates': [
            {'id': candidate_id, 'educations': [
                {'id': old_education_dict['id'], 'school_name': 'UC Davis'}
            ]}
        ]}
        send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate educations
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        new_education_dict = get_resp.json()['candidate']['educations'][0]

        # Retrieve Candidate Edits
        edit_resp = send_request('get', CandidateApiUrl.CANDIDATE_EDIT % candidate_id, access_token_first)
        print response_info(edit_resp)
        candidate_edits = edit_resp.json()['candidate']['edits']
        assert edit_resp.status_code == 200
        assert new_education_dict['school_name'] != old_education_dict['school_name']
        old_values = [edit['old_value'] for edit in candidate_edits]
        new_values = [edit['new_value'] for edit in candidate_edits]
        assert old_education_dict['school_name'] in old_values
        assert new_education_dict['school_name'] in new_values

    def test_edit_candidate_education_degree_goo(self, access_token_first, talent_pool):
        """
        Test:   Change Candidate's education degree records
        Expect: 200
        """

        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        old_education_dict = get_resp.json()['candidate']['educations'][0]

        # Change degree type to something different
        current_degree = get_resp.json()['candidate']['educations'][0]['degrees'][0]['type']
        degree_type = ['BS', 'MS', 'BA', 'PhD']
        if current_degree in degree_type:
            degree_type.remove(current_degree)

        # Update Candidate's education degree
        data = {'candidates': [
            {'id': candidate_id, 'educations': [
                {'id': old_education_dict['id'], 'degrees': [
                    {'id': old_education_dict['degrees'][0]['id'],
                     'type': random.choice(degree_type), 'title': 'Biomedical Engineering'}
                ]}
            ]}
        ]}
        send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate education
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        new_education_dict = get_resp.json()['candidate']['educations'][0]

        # Retrieve Candidate Edits
        edit_resp = send_request('get', CandidateApiUrl.CANDIDATE_EDIT % candidate_id, access_token_first)
        print response_info(edit_resp)

        candidate_edits = edit_resp.json()['candidate']['edits']
        assert edit_resp.status_code == requests.codes.OK
        assert new_education_dict['degrees'][0]['type'] != old_education_dict['degrees'][0]['type']
        assert new_education_dict['degrees'][0]['title'] != old_education_dict['degrees'][0]['title']

        old_values = [edit['old_value'] for edit in candidate_edits]
        new_values = [edit['new_value'] for edit in candidate_edits]

        assert old_education_dict['degrees'][0]['type'] in old_values
        assert old_education_dict['degrees'][0]['title'] in old_values
        assert new_education_dict['degrees'][0]['type'] in new_values
        assert new_education_dict['degrees'][0]['title'] in new_values

    def test_edit_candidate_education_degree_bullet(self, access_token_first, talent_pool):
        """
        Test:   Change Candidate's education degree bullet records
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        old_education_dict = get_resp.json()['candidate']['educations'][0]
        old_degree_bullet_dict = old_education_dict['degrees'][0]['bullets'][0]

        # Update Candidate's education degree bullet
        data = {'candidates': [
            {'id': candidate_id, 'educations': [
                {'id': old_education_dict['id'], 'degrees': [
                    {'id': old_education_dict['degrees'][0]['id'], 'bullets': [
                        {'id': old_degree_bullet_dict['id'], 'major': 'nursing'}
                    ]}
                ]}
            ]}
        ]}
        send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate education
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        new_education_dict = get_resp.json()['candidate']['educations'][0]
        new_degree_bullet_dict = new_education_dict['degrees'][0]['bullets'][0]

        # Retrieve Candidate Edits
        edit_resp = send_request('get', CandidateApiUrl.CANDIDATE_EDIT % candidate_id, access_token_first)
        print response_info(edit_resp)

        candidate_edits = edit_resp.json()['candidate']['edits']
        assert edit_resp.status_code == 200
        assert new_degree_bullet_dict['major'] != old_degree_bullet_dict['major']
        assert old_degree_bullet_dict['major'] in [edit['old_value'] for edit in candidate_edits]
        assert new_degree_bullet_dict['major'] in [edit['new_value'] for edit in candidate_edits]


class TestTrackCandidateExperienceEdits(object):
    def test_edit_candidate_experience(self, access_token_first, user_first, talent_pool):
        """
        Test:   Change Candidate's experience records
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        old_experience_dict = get_resp.json()['candidate']['work_experiences'][0]

        # Update Candidate's experience
        data = {'candidates': [
            {'id': candidate_id, 'work_experiences': [
                {'id': old_experience_dict['id'], 'organization': 'Dice', 'position': 'Software Engineer'}
            ]}
        ]}
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)

        # Retrieve Candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        new_experience_dict = get_resp.json()['candidate']['work_experiences'][0]

        # Retrieve Candidate Edits
        edit_resp = send_request('get', CandidateApiUrl.CANDIDATE_EDIT % candidate_id, access_token_first)
        print response_info(edit_resp)

        candidate_edits = edit_resp.json()['candidate']['edits']
        assert edit_resp.status_code == 200
        assert new_experience_dict['organization'] != old_experience_dict['organization']
        assert new_experience_dict['position'] != old_experience_dict['position']
        assert candidate_edits[-2]['old_value'] == old_experience_dict['position']
        assert candidate_edits[-2]['new_value'] == new_experience_dict['position']
        assert candidate_edits[-1]['old_value'] == old_experience_dict['organization']
        assert candidate_edits[-1]['new_value'] == new_experience_dict['organization']

    def test_edit_candidate_experience_bullet(self, access_token_first, user_first, talent_pool):
        """
        Test:   Change Candidate's experience bullet records
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        old_experience_dict = get_resp.json()['candidate']['work_experiences'][0]
        old_experience_bullet_dict = old_experience_dict['bullets'][0]

        # Update Candidate's experience bullet
        data = {'candidates': [
            {'id': candidate_id, 'work_experiences': [
                {'id': old_experience_dict['id'], 'bullets': [
                    {'id': old_experience_bullet_dict['id'], 'description': 'job sucked'}
                ]}
            ]}
        ]}
        send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        new_experience_dict = get_resp.json()['candidate']['work_experiences'][0]
        new_experience_bullet_dict = new_experience_dict['bullets'][0]

        # Retrieve Candidate Edits
        edit_resp = send_request('get', CandidateApiUrl.CANDIDATE_EDIT % candidate_id, access_token_first)
        print response_info(edit_resp)

        candidate_edits = edit_resp.json()['candidate']['edits']
        assert edit_resp.status_code == 200
        assert candidate_edits[-1]['old_value'] == old_experience_bullet_dict['description']
        assert candidate_edits[-1]['new_value'] == new_experience_bullet_dict['description']


class TestTrackCandidateWorkPreferenceEdits(object):
    def test_edit_candidate_work_preference(self, access_token_first, user_first, talent_pool):
        """
        Test:   Change Candidate's work preference records
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        old_work_pref_dict = get_resp.json()['candidate']['work_preference']

        # Update Candidate's work preference
        data = {'candidates': [
            {'id': candidate_id, 'work_preference': {
                'id': old_work_pref_dict['id'], 'salary': '150000', 'hourly_rate': '75'
            }}
        ]}
        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(update_resp)

        # Retrieve Candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        new_work_pref_dict = get_resp.json()['candidate']['work_preference']

        # Retrieve Candidate Edits
        edit_resp = send_request('get', CandidateApiUrl.CANDIDATE_EDIT % candidate_id, access_token_first)
        print response_info(edit_resp)

        candidate_edits = edit_resp.json()['candidate']['edits']
        assert edit_resp.status_code == 200
        old_values = map(get_int_version, [edit['old_value'] for edit in candidate_edits])
        new_values = map(get_int_version, [edit['new_value'] for edit in candidate_edits])
        assert get_int_version(old_work_pref_dict['salary']) in old_values
        assert get_int_version(old_work_pref_dict['hourly_rate']) in old_values
        assert get_int_version(new_work_pref_dict['salary']) in new_values
        assert get_int_version(new_work_pref_dict['hourly_rate']) in new_values


class TestTrackCandidatePhoneEdits(object):
    def test_edit_candidate_phone(self, access_token_first, user_first, talent_pool):
        """
        Test:   Change Candidate's phone record
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        old_phone_dict = get_resp.json()['candidate']['phones'][0]

        # Update Candidate's phone
        data = {'candidates': [
            {'id': candidate_id, 'phones': [{'id': old_phone_dict['id'], 'value': '4084054085'}]}
        ]}
        send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        new_phone_dict = get_resp.json()['candidate']['phones'][0]

        # Retrieve Candidate Edits
        edit_resp = send_request('get', CandidateApiUrl.CANDIDATE_EDIT % candidate_id, access_token_first)
        print response_info(edit_resp)

        candidate_edits = edit_resp.json()['candidate']['edits']
        assert edit_resp.status_code == 200
        assert old_phone_dict['value'] in [edit['old_value'] for edit in candidate_edits]
        assert new_phone_dict['value'] in [edit['new_value'] for edit in candidate_edits]


class TestTrackCandidateMilitaryServiceEdits(object):
    def test_edit_candidate_military_service(self, access_token_first, user_first, talent_pool):
        """
        Test:   Change Candidate's military service record
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        old_military_service_dict = get_resp.json()['candidate']['military_services'][0]

        # Update Candidate's military service
        data = {'candidates': [
            {'id': candidate_id, 'military_services': [{'id': old_military_service_dict['id'], 'branch': 'gettalent'}]}
        ]}
        send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate military services
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        new_military_service_dict = get_resp.json()['candidate']['military_services'][0]

        # Retrieve Candidate Edits
        edit_resp = send_request('get', CandidateApiUrl.CANDIDATE_EDIT % candidate_id, access_token_first)
        print response_info(edit_resp)
        candidate_edits = edit_resp.json()['candidate']['edits']
        assert edit_resp.status_code == 200
        assert old_military_service_dict['branch'] in [edit['old_value'] for edit in candidate_edits]
        assert new_military_service_dict['branch'] in [edit['new_value'] for edit in candidate_edits]


class TestTrackCandidatePreferredLocationEdits(object):
    def test_edit_candidate_preferred_location_edits(self, access_token_first, user_first, talent_pool):
        """
        Test:   Change Candidate's preferred location record
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        old_preferred_location_dict = get_resp.json()['candidate']['preferred_locations'][0]

        # Update Candidate's preferred location
        data = {'candidates': [
            {'id': candidate_id, 'preferred_locations': [
                {'id': old_preferred_location_dict['id'], 'city': 'man jose'}
            ]}
        ]}
        send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate preferred locations
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        new_preferred_location_dict = get_resp.json()['candidate']['preferred_locations'][0]

        # Retrieve Candidate Edits
        edit_resp = send_request('get', CandidateApiUrl.CANDIDATE_EDIT % candidate_id, access_token_first)
        print response_info(edit_resp)

        candidate_edits = edit_resp.json()['candidate']['edits']
        assert edit_resp.status_code == 200
        old_values = [edit['old_value'] for edit in candidate_edits]
        new_values = [edit['new_value'] for edit in candidate_edits]
        assert old_preferred_location_dict['city'] in old_values
        assert new_preferred_location_dict['city'] in new_values


class TestTrackCandidateSkillEdits(object):
    def test_edit_candidate_skill_edits(self, access_token_first, user_first, talent_pool):
        """
        Test:   Change Candidate's skill record
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        old_skill_dict = get_resp.json()['candidate']['skills'][0]

        # Update Candidate's skill
        data = {'candidates': [
            {'id': candidate_id, 'skills': [
                {'id': old_skill_dict['id'], 'name': 'useless skill'}
            ]}
        ]}
        send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate skills
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        new_skill_dict = get_resp.json()['candidate']['skills'][0]

        # Retrieve Candidate Edits
        edit_resp = send_request('get', CandidateApiUrl.CANDIDATE_EDIT % candidate_id, access_token_first)
        print response_info(edit_resp)

        candidate_edits = edit_resp.json()['candidate']['edits']
        assert edit_resp.status_code == 200
        assert old_skill_dict['name'] in [edit['old_value'] for edit in candidate_edits]
        assert new_skill_dict['name'] in [edit['new_value'] for edit in candidate_edits]


class TestTrackCandidateSocialNetworkEdits(object):
    def test_edit_candidate_social_network_edits(self, access_token_first, user_first, talent_pool):
        """
        Test:   Change Candidate's social network record
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        old_sn_dict = get_resp.json()['candidate']['social_networks'][0]

        # Update Candidate's social network
        data = {'candidates': [
            {'id': candidate_id, 'social_networks': [
                {'id': old_sn_dict['id'], 'name': 'Facebook', 'profile_url': fake.url()}
            ]}
        ]}
        send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate social networks
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        new_sn_dict = get_resp.json()['candidate']['social_networks'][0]

        # Retrieve Candidate Edits
        edit_resp = send_request('get', CandidateApiUrl.CANDIDATE_EDIT % candidate_id, access_token_first)
        print response_info(edit_resp)

        candidate_edits = edit_resp.json()['candidate']['edits']
        assert edit_resp.status_code == 200
        assert old_sn_dict['profile_url'] in [edit['old_value'] for edit in candidate_edits]
        assert new_sn_dict['profile_url'] in [edit['new_value'] for edit in candidate_edits]
