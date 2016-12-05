# Candidate Service app instance

# Conftest
import pycountry

from candidate_sample_data import GenerateCandidateData, generate_single_candidate_data
from candidate_service.common.routes import CandidateApiUrl
from candidate_service.common.tests.conftest import *
from candidate_service.common.utils.custom_error_codes import CandidateCustomErrors as custom_error
from candidate_service.common.utils.test_utils import send_request, response_info
from helpers import get_country_code_from_name


class TestCreateCandidateEducation(object):
    def test_create_successfully(self, access_token_first, user_first, talent_pool):
        """
        Test: Create candidate + education
        Expect: 201
        """
        # Create candidate + education
        data = GenerateCandidateData.educations([talent_pool.id])
        country_code = data['candidates'][0]['educations'][0]['country_code']
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 200
        assert get_country_code_from_name(get_resp.json()['candidate']['educations'][0]['country']) == country_code

    def test_create_education_with_empty_values(self, access_token_first, user_first, talent_pool):
        """
        Test:  Create candidate education with some or all empty values and some with whitespaces
        Expect:  201; all-empty data should not be inserted into db & whitespaces must be stripped
        """
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'educations': [
                {'school_name': ' ', 'school_type': ' ', 'city': None, 'subdivision_code': ''}
            ]}
        ]}
        # Create candidate education with empty values
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        assert create_resp.status_code == requests.codes.CREATED

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_educations = get_resp.json()['candidate']['educations']
        assert not candidate_educations, "Candidate education record not added to db because data was empty"

        # Create candidate education with some whitespaces and some empty values
        data['candidates'][0]['educations'][0]['school_name'] = ' UC Davis      '
        data['candidates'][0]['educations'][0]['school_type'] = 'University  '

        # Create candidate education with updated data
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        assert create_resp.status_code == requests.codes.CREATED

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_educations = get_resp.json()['candidate']['educations']
        assert len(candidate_educations) == 1
        assert candidate_educations[0]['school_name'] == data['candidates'][0]['educations'][0]['school_name'].strip()
        assert candidate_educations[0]['school_type'] == data['candidates'][0]['educations'][0]['school_type'].strip()

    def test_add_education_with_faulty_start_date(self, access_token_first, user_first, talent_pool):
        """
        Test:  Start date must be a valid date and must not be later than end date of education
        """

        end_year = 1990
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'educations': [
                {'school_name': 'west valley', 'city': fake.city(),
                 'subdivision_code': 'US-CA', 'state': fake.state(),
                 'country_code': fake.country_code(), 'is_current': fake.boolean(),
                 'degrees': [{'start_year': end_year + 1, 'end_year': end_year}]
                 }
            ]}
        ]}

        # Add education
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.BAD
        assert create_resp.json()['error']['code'] == custom_error.INVALID_USAGE

    def test_create_candidate_educations_with_no_degrees(self, access_token_first, user_first, talent_pool):
        """
        Test:   Create CandidateEducation for Candidate
        Expect: 201
        """
        # Create Candidate without degrees
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        can_educations = candidate_dict['educations']
        data_educations = data['candidates'][0]['educations'][0]
        assert isinstance(can_educations, list)
        assert can_educations[0]['city'] == data_educations['city']
        assert can_educations[0]['school_name'] == data_educations['school_name']

        can_edu_degrees = can_educations[0]['degrees']
        assert isinstance(can_edu_degrees, list)


class TestUpdateCandidateEducation(object):
    def test_add_new_education(self, access_token_first, user_first, talent_pool):
        """
        Test:   Add a new CandidateEducation. Candidate's CandidateEducation count should
                increase by 1.
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        can_educations_count = len(candidate_dict['educations'])

        # Add new CandidateEducation
        data = GenerateCandidateData.educations(candidate_id=candidate_id)
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        updated_can_dict = get_resp.json()['candidate']
        updated_educations = updated_can_dict['educations']

        can_ed_from_data = data['candidates'][0]['educations'][0]
        can_ed_degrees = can_ed_from_data['degrees'][0]
        can_ed_degree_bullets = can_ed_degrees['bullets'][0]

        assert candidate_id == updated_can_dict['id']
        assert isinstance(updated_educations, list)
        assert updated_educations[-1]['city'] == can_ed_from_data['city']
        assert updated_educations[-1]['school_name'] == can_ed_from_data['school_name']
        assert updated_educations[-1]['degrees'][-1]['type'] == can_ed_degrees['type']
        assert updated_educations[-1]['degrees'][-1]['title'] == can_ed_degrees['title']
        assert updated_educations[-1]['degrees'][-1]['bullets'][-1]['major'] == can_ed_degree_bullets['major']
        assert updated_educations[-1]['country'] == pycountry.countries.get(
            alpha2=can_ed_from_data['country_code']).name
        assert len(updated_educations) == can_educations_count + 1

    def test_update_education_of_a_diff_candidate(self, access_token_first, user_first, talent_pool):
        """
        Test:   Update education information of a different Candidate
        Expect: 403
        """

        # Create Candidate
        data_1 = generate_single_candidate_data([talent_pool.id])
        data_2 = generate_single_candidate_data([talent_pool.id])
        resp_1 = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data_1)
        resp_2 = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data_2)
        candidate_1_id = resp_1.json()['candidates'][0]['id']
        candidate_2_id = resp_2.json()['candidates'][0]['id']

        # Retrieve Candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_1_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        # Update existing CandidateEducation of a different Candidate
        data = GenerateCandidateData.educations(candidate_id=candidate_2_id,
                                                education_id=candidate_dict['educations'][0]['id'])
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403
        assert updated_resp.json()['error']['code'] == custom_error.EDUCATION_FORBIDDEN

    def test_update_education_primary_info(self, access_token_first, user_first, talent_pool):
        """
        Test:   Updates candidate's education's city, school_name, and state
                Since this is an update only, total number of candidate's education
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

        candidate_education_count = len(candidate_dict['educations'])

        # Update existing CandidateEducation
        data = GenerateCandidateData.educations(candidate_id=candidate_id,
                                                education_id=candidate_dict['educations'][0]['id'])
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        updated_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        education_dict = updated_resp.json()['candidate']['educations'][0]

        can_ed_from_data = data['candidates'][0]['educations'][0]
        assert education_dict['city'] == can_ed_from_data['city']
        assert education_dict['subdivision'] == pycountry.subdivisions.get(
            code=can_ed_from_data['subdivision_code']).name
        assert education_dict['school_name'] == can_ed_from_data['school_name']
        assert education_dict['country'] == pycountry.countries.get(alpha2=can_ed_from_data['country_code']).name
        assert len(updated_resp.json()['candidate']['educations']) == candidate_education_count

    def test_add_education_degree(self, access_token_first, user_first, talent_pool):
        """
        Test:   Add CandidateEducationDegree to an existing candidate's education.
                The number of CandidateEducationDegree must increase by 1 for this candidate.
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        candidate_education_count = len(candidate_dict['educations'][0]['degrees'])

        # Update existing CandidateEducation
        data = {'candidates': [{'id': candidate_id, 'educations': [
            {'id': candidate_dict['educations'][0]['id'], 'degrees': [
                {'type': 'AA', 'title': 'associate', 'bullets': [
                    {'major': 'mathematics', 'comments': 'obtained a high GPA whilst working full time'}
                ]}
            ]}
        ]}]}
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        updated_can_dict = get_resp.json()['candidate']
        education_dict = updated_can_dict['educations'][0]

        assert candidate_id == updated_can_dict['id']
        assert len(education_dict['degrees']) == candidate_education_count + 1
        assert education_dict['degrees'][-1]['type'] == 'AA'
        assert education_dict['degrees'][-1]['title'] == 'associate'
        assert education_dict['degrees'][-1]['bullets'][-1]['major'] == 'mathematics'

    def test_update_start_year_with_incorrect_value(self, user_first, access_token_first, talent_pool):
        """
        Test: Update candidate's education start year to a year that is greater than its end year
        """

        # Create candidate + education
        data = GenerateCandidateData.educations([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)

        # Format inputs
        education_id = get_resp.json()['candidate']['educations'][0]['id']
        degree_id = get_resp.json()['candidate']['educations'][0]['degrees'][0]['id']
        education_end_year = get_resp.json()['candidate']['educations'][0]['degrees'][0]['end_year']

        # Update candidate-education's end year
        update_data = {'candidates': [
            {'educations': [
                {'id': education_id, 'degrees': [{'id': degree_id, 'start_year': int(education_end_year) + 1}]}
            ]}
        ]}
        update_resp = send_request('patch', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first, update_data)
        print response_info(update_resp)
        assert update_resp.status_code == requests.codes.BAD

    def test_update_end_year_with_incorrect_value(self, user_first, access_token_first, talent_pool):
        """
        Test: Update candidate's education end year to a year that is less than its start year
        """

        # Create candidate + education
        data = GenerateCandidateData.educations([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)

        # Format inputs
        education_id = get_resp.json()['candidate']['educations'][0]['id']
        degree_id = get_resp.json()['candidate']['educations'][0]['degrees'][0]['id']
        education_start_year = get_resp.json()['candidate']['educations'][0]['degrees'][0]['start_year']

        # Update candidate-education's end year
        update_data = {'candidates': [
            {'educations': [
                {'id': education_id, 'degrees': [{'id': degree_id, 'end_year': int(education_start_year) - 1}]}
            ]}
        ]}
        update_resp = send_request('patch', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first, update_data)
        print response_info(update_resp)
        assert update_resp.status_code == requests.codes.BAD


class TestCreateCandidateEducationDegree(object):
    def test_with_empty_values(self, access_token_first, user_first, talent_pool):
        """
        Test:  Create candidate education degree with some whitespaces and empty values
        Expect: 201
        """
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'educations': [
                {'school_name': ' ', 'school_type': ' ', 'city': None, 'subdivision_code': ''}
            ]}
        ]}
        # Create candidate education with empty values
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        print "\ncandidate_id: {}".format(candidate_id)
        print "\ndomain_id: {}".format(user_first.domain_id)
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        candidate_educations = get_resp.json()['candidate']['educations']
        assert not candidate_educations, "Candidate education record not added to db because data was empty"

    def test_candidate_education_degree_with_no_degree_title_or_degree_type(self, access_token_first,
                                                                            user_first, talent_pool):
        """
        Test:  Degree title or degree type must be provided for other fields to count. e.g.
          If gpa & start year of education degree are provided but not the degree title or degree type
          then nothing gets added to db.
        Expect: 201, but education degree should not be added to db
        """
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'educations': [
                {'school_name': 'uc berkeley', 'city': 'berkeley', 'degrees': [
                    {'title': ' ', 'gpa': 3.50, 'start_year': 2012, 'end_year': 2016}]}
            ]}
        ]}
        # Create candidate education with empty values
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_educations = get_resp.json()['candidate']['educations']
        assert get_resp.status_code == 200
        assert len(candidate_educations[0]['degrees']) == 0


class TestDeleteCandidateEducation(object):
    def test_non_logged_in_user_delete_can_education(self):
        """
        Test:   Delete candidate's education without logging in
        Expect: 401
        """
        # Delete Candidate's educations
        resp = send_request('delete', CandidateApiUrl.EDUCATIONS % '5', None)
        print response_info(resp)
        assert resp.status_code == 401

    def test_delete_candidate_education_with_bad_input(self):
        """
        Test:   Attempt to delete candidate education with non integer values for candidate_id & education_id
        Expect: 404
        """
        # Delete Candidate's educations
        resp = send_request('delete', CandidateApiUrl.EDUCATIONS % 'x', None)
        print response_info(resp)
        assert resp.status_code == 404

        # Delete Candidate's education
        resp = send_request('delete', CandidateApiUrl.EDUCATION % (5, 'x'), None)
        print response_info(resp)
        assert resp.status_code == 404

    def test_delete_education_of_a_candidate_in_same_domain(self, access_token_first, user_first, talent_pool,
                                                            user_second, access_token_second):
        """
        Test:   Attempt to delete the education of a Candidate that belongs to a user in a different domain
        Expect: 204, deletion must be prevented
        """

        # Create candidate_1 & candidate_2 with user_first & user_first_2
        data = generate_single_candidate_data([talent_pool.id])
        create_resp_1 = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve candidate_1
        candidate_1_id = create_resp_1.json()['candidates'][0]['id']

        # Delete candidate_1's education with user_first_2 logged in
        updated_resp = send_request('delete', CandidateApiUrl.EDUCATIONS % candidate_1_id, access_token_second)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403
        assert updated_resp.json()['error']['code'] == custom_error.CANDIDATE_FORBIDDEN

    def test_delete_education_of_a_different_candidate(self, access_token_first, user_first, talent_pool):
        """
        Test:   Attempt to delete the education of a different Candidate in the same domain
        Expect: 403
        """
        # Create candidate_1 and candidate_2
        data_1 = generate_single_candidate_data([talent_pool.id])
        data_2 = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data_1)
        candidate_1_id = create_resp.json()['candidates'][0]['id']
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data_2)
        candidate_2_id = create_resp.json()['candidates'][0]['id']

        # Retrieve candidate_2's educations
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_2_id, access_token_first)
        can_2_educations = get_resp.json()['candidate']['educations']

        # Delete candidate_2's id using candidate_1_id
        url = CandidateApiUrl.EDUCATION % (candidate_1_id, can_2_educations[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403
        assert updated_resp.json()['error']['code'] == custom_error.EDUCATION_FORBIDDEN

    def test_delete_candidate_educations(self, access_token_first, user_first, talent_pool):
        """
        Test:   Remove all of candidate's educations from db
        Expect: 204, Candidate should not have any educations left
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Remove all of Candidate's educations
        candidate_id = create_resp.json()['candidates'][0]['id']
        updated_resp = send_request('delete', CandidateApiUrl.EDUCATIONS % candidate_id, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']
        assert updated_resp.status_code == 204
        assert len(can_dict_after_update['educations']) == 0

    def test_delete_candidates_education(self, access_token_first, user_first, talent_pool):
        """
        Test:   Remove Candidate's education from db
        Expect: 204, Candidate's education must be less 1
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']
        candidate_educations = candidate_dict['educations']

        # Current number of Candidate's educations
        candidate_educations_count = len(candidate_educations)

        # Remove one of Candidate's education
        url = CandidateApiUrl.EDUCATION % (candidate_id, candidate_educations[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']
        assert updated_resp.status_code == 204
        assert len(can_dict_after_update['educations']) == candidate_educations_count - 1


class TestDeleteCandidateEducationDegree(object):
    def test_non_logged_in_user_delete_can_edu_degree(self):
        """
        Test:   Delete Candidate's education degree without logging in
        Expect: 401
        """
        # Delete Candidate's education degrees
        resp = send_request('delete', CandidateApiUrl.DEGREES % (5, 5), None)
        print response_info(resp)
        assert resp.status_code == 401

    def test_delete_candidate_education_degrees_with_bad_input(self):
        """
        Test:   Attempt to delete Candidate's education-degree with non integer values
                for candidate_id & degree_id
        Expect: 404
        """
        # Delete Candidate's education degrees
        resp = send_request('delete', CandidateApiUrl.DEGREES % ('x', 5), None)
        print response_info(resp)
        assert resp.status_code == 404

        # Delete Candidate's education degree
        resp = send_request('delete', CandidateApiUrl.DEGREE % (5, 5, 'x'), None)
        print response_info(resp)
        assert resp.status_code == 404

    def test_delete_edu_degree_of_a_candidate_belonging_to_a_diff_user(self, access_token_first, user_first,
                                                                       talent_pool, user_second,
                                                                       access_token_second):
        """
        Test:   Attempt to delete the education-degrees of a Candidate that belongs to user from a diff domain
        Expect: 403, deletion must be prevented
        """

        # Create candidate_1 & candidate_2 with user_first & user_first_2
        data = generate_single_candidate_data([talent_pool.id])
        create_resp_1 = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve candidate_1
        candidate_1_id = create_resp_1.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_1_id, access_token_first)
        can_1_edu_id = get_resp.json()['candidate']['educations'][0]['id']

        # Delete candidate_1's education degree with user_first_2 logged in
        url = CandidateApiUrl.DEGREES % (candidate_1_id, can_1_edu_id)
        updated_resp = send_request('delete', url, access_token_second)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403
        assert updated_resp.json()['error']['code'] == custom_error.CANDIDATE_FORBIDDEN

    def test_delete_education_degree_of_a_different_candidate(self, access_token_first, user_first, talent_pool):
        """
        Test:   Attempt to delete the education-degrees of a different Candidate
        Expect: 403
        """
        # Create candidate_1 and candidate_2
        data_1 = generate_single_candidate_data([talent_pool.id])
        data_2 = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data_1)
        candidate_1_id = create_resp.json()['candidates'][0]['id']
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data_2)
        candidate_2_id = create_resp.json()['candidates'][0]['id']

        # Retrieve candidate_2's education degrees
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_2_id, access_token_first)
        can_2_educations = get_resp.json()['candidate']['educations']

        # Delete candidate_2's id using candidate_1_id
        url = CandidateApiUrl.DEGREES % (candidate_1_id, can_2_educations[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403
        assert updated_resp.json()['error']['code'] == custom_error.EDUCATION_FORBIDDEN

    def test_delete_candidate_education_degrees(self, access_token_first, user_first, talent_pool):
        """
        Test:   Remove all of candidate's degrees from db
        Expect: 204; Candidate should not have any degrees left; Candidate's Education should not be removed
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_educations = get_resp.json()['candidate']['educations']

        # Current number of candidate educations
        count_of_edu_degrees_before_deleting = len(can_educations[0])

        # Remove all of Candidate's degrees
        url = CandidateApiUrl.DEGREES % (candidate_id, can_educations[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']
        assert updated_resp.status_code == 204
        assert len(can_dict_after_update['educations'][0]['degrees']) == 0
        assert len(can_dict_after_update['educations'][0]) == count_of_edu_degrees_before_deleting

    def test_delete_candidates_education_degree(self, access_token_first, user_first, talent_pool):
        """
        Test:   Remove Candidate's education from db
        Expect: 204, Candidate's education must be less 1
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']
        candidate_educations = candidate_dict['educations']

        # Current number of Candidate's educations
        candidate_educations_count = len(candidate_educations)

        # Remove one of Candidate's education degree
        url = CandidateApiUrl.DEGREE % (
            candidate_id, candidate_educations[0]['id'], candidate_educations[0]['degrees'][0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']
        assert updated_resp.status_code == 204
        assert len(can_dict_after_update['educations']) == candidate_educations_count - 1


class TestDeleteCandidateEducationDegreeBullet(object):
    def test_non_logged_in_user_delete_can_edu_degree_bullets(self):
        """
        Test:   Delete candidate's degree-bullets without logging in
        Expect: 401
        """
        # Delete Candidate's degree-bullets
        resp = send_request('delete', CandidateApiUrl.DEGREE_BULLETS % (5, 5, 5), None)
        print response_info(resp)
        assert resp.status_code == 401
        assert resp.json()['error']['code'] == 11

    def test_delete_candidate_edu_degree_bullets_with_bad_input(self):
        """
        Test:   Attempt to delete candidate degree-bullets with non integer values for candidate_id & education_id
        Expect: 404
        """
        # Delete Candidate's degree-bullets
        resp = send_request('delete', CandidateApiUrl.DEGREE_BULLETS % ('x', 5, 5), None)
        print response_info(resp)
        assert resp.status_code == 404

        # Delete Candidate's degree-bullets
        resp = send_request('delete', CandidateApiUrl.DEGREE_BULLETS % (5, 'x', 5), None)
        print response_info(resp)
        assert resp.status_code == 404

    def test_delete_degree_bullets_of_a_candidate_belonging_to_a_diff_user(self, access_token_first, user_first,
                                                                           talent_pool, user_second,
                                                                           access_token_second):
        """
        Test:   Attempt to delete degree-bullets of a Candidate that belongs to a user from a diff domain
        Expect: 204
        """

        # Create candidate_1 & candidate_2 with user_first & user_first_2
        data = generate_single_candidate_data([talent_pool.id])
        create_resp_1 = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve candidate_1
        candidate_1_id = create_resp_1.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_1_id, access_token_first)
        can_1_educations = get_resp.json()['candidate']['educations']

        # Delete candidate_1's degree-bullets with user_first_2 logged in
        url = CandidateApiUrl.DEGREE_BULLETS % (candidate_1_id, can_1_educations[0]['id'],
                                                can_1_educations[0]['degrees'][0]['id'])
        updated_resp = send_request('delete', url, access_token_second)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403
        assert updated_resp.json()['error']['code'] == custom_error.CANDIDATE_FORBIDDEN

    def test_delete_can_edu_degree_bullets_of_a_different_candidate(self, access_token_first, user_first, talent_pool):
        """
        Test:   Attempt to delete degree-bullets of a different Candidate
        Expect: 403
        """
        # Create candidate_1 and candidate_2
        data_1 = generate_single_candidate_data([talent_pool.id])
        data_2 = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data_1)
        candidate_1_id = create_resp.json()['candidates'][0]['id']
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data_2)
        candidate_2_id = create_resp.json()['candidates'][0]['id']

        # Retrieve candidate_2's degree-bullets
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_2_id, access_token_first)
        can_2_edu = get_resp.json()['candidate']['educations'][0]
        can_2_edu_degree = can_2_edu['degrees'][0]
        can_2_edu_degree_bullet = can_2_edu['degrees'][0]['bullets'][0]

        # Delete candidate_2's degree bullet using candidate_1_id
        url = CandidateApiUrl.DEGREE_BULLET % (candidate_1_id, can_2_edu['id'], can_2_edu_degree['id'],
                                               can_2_edu_degree_bullet['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)
        assert updated_resp.status_code == 404
        assert updated_resp.json()['error']['code'] == custom_error.DEGREE_NOT_FOUND

    def test_delete_candidate_education_degree_bullets(self, access_token_first, user_first, talent_pool):
        """
        Test:   Remove all of candidate's degree_bullets from db
        Expect: 204; Candidate should not have any degrees left; Candidate's
        Education and degrees should not be removed
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_educations = get_resp.json()['candidate']['educations']

        # Current number of candidate educations & degrees
        count_of_educations_before_deleting = len(can_educations[0])
        count_of_edu_degrees_before_deleting = len(can_educations[0]['degrees'])

        # Remove all of Candidate's degree_bullets
        url = CandidateApiUrl.DEGREE_BULLETS % (candidate_id, can_educations[0]['id'],
                                                can_educations[0]['degrees'][0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']
        assert updated_resp.status_code == 204
        assert len(can_dict_after_update['educations'][0]['degrees'][0]['bullets']) == 0
        assert len(can_dict_after_update['educations'][0]) == count_of_educations_before_deleting
        assert len(can_dict_after_update['educations'][0]['degrees']) == count_of_edu_degrees_before_deleting

    def test_delete_candidates_education_degree_bullet(self, access_token_first, user_first, talent_pool):
        """
        Test:   Remove Candidate's degree_bullet from db
        Expect: 204, Candidate's degree_bullet must be less 1. Candidate's education and degrees
                should not be removed
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']
        candidate_educations = candidate_dict['educations']

        # Current number of Candidate's educations, degrees, and bullets
        educations_count_before_delete = len(candidate_educations)
        degrees_count_before_delete = len(candidate_educations[0]['degrees'])
        degree_bullets_count_before_delete = len(candidate_educations[0]['degrees'][0]['bullets'])

        # Remove one of Candidate's education degree bullet
        url = CandidateApiUrl.DEGREE_BULLET % (candidate_id, candidate_educations[0]['id'],
                                               candidate_educations[0]['degrees'][0]['id'],
                                               candidate_educations[0]['degrees'][0]['bullets'][0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']
        assert updated_resp.status_code == 204
        assert len(can_dict_after_update['educations']) == educations_count_before_delete
        assert len(can_dict_after_update['educations'][0]['degrees']) == degrees_count_before_delete
        assert len(
            can_dict_after_update['educations'][0]['degrees'][0]['bullets']) == degree_bullets_count_before_delete - 1
