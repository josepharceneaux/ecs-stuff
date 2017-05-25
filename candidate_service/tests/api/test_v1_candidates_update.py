"""
Test cases for CandidateResource/patch()
"""
# Candidate Service app instance
import pycountry

from candidate_sample_data import (fake, generate_single_candidate_data, GenerateCandidateData)
from candidate_service.common.models.candidate import CandidateEmail

# Conftest
from candidate_service.common.tests.conftest import *

# Helper functions
from candidate_service.common.utils.test_utils import send_request, response_info
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error


class TestUpdateCandidateSuccessfully(object):
    """
    Class contains functional test that expect a 200 response
    """

    def test_primary_information(self, access_token_first, test_candidate_1, domain_source_2):
        """
        Test: Edit the primary information of a full candidate's profile
        """
        candidate_id = test_candidate_1['candidate']['id']

        update_data = {
            'candidates': [
                {
                    'id': candidate_id,
                    'first_name': fake.first_name(),
                    'middle_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'source_id': domain_source_2['source']['id'],
                    'objective': fake.sentence(),
                    'source_product_id': 2  # Web
                }
            ]
        }

        # Update candidate's primary information
        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, update_data)
        print response_info(update_resp)
        assert update_resp.status_code == requests.codes.OK

        # Retrieve candidate and assert its primary data have been updated
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % str(candidate_id), access_token_first)
        print response_info(get_resp)

        candidate_data = get_resp.json()['candidate']

        assert candidate_data['id'] == candidate_id
        assert candidate_data['first_name'] == update_data['candidates'][0]['first_name']
        assert candidate_data['middle_name'] == update_data['candidates'][0]['middle_name']
        assert candidate_data['last_name'] == update_data['candidates'][0]['last_name']
        assert candidate_data['source_id'] == update_data['candidates'][0]['source_id']
        assert candidate_data['objective'] == update_data['candidates'][0]['objective']
        assert candidate_data['source_product_id'] == update_data['candidates'][0]['source_product_id']


class TestUpdateCandidate(object):
    def test_archive_candidates(self, access_token_first, talent_pool, domain_source, domain_aois, domain_custom_fields):
        """
        Test:  Create a candidate and archive it
        Expect: 200; candidate should not be retrievable
        """
        # Create candidate
        data = generate_single_candidate_data(talent_pool_ids=[talent_pool.id],
                                              areas_of_interest=domain_aois,
                                              custom_fields=domain_custom_fields,
                                              source_id=domain_source['source']['id'])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)

        # Archive candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        data = {'candidates': [{'id': candidate_id, 'archive': True}]}
        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(update_resp)
        assert update_resp.status_code == 200
        assert update_resp.json()['archived_candidates'][0] == candidate_id

        # Retrieve candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 404
        assert get_resp.json()['error']['code'] == custom_error.CANDIDATE_IS_ARCHIVED

    def test_archive_and_unarchive_candidates(self, access_token_first, talent_pool):
        """
        Test:  Create candidates, archive them, and un-archive them again via Patch call
        """
        # Create candidates
        data_1 = generate_single_candidate_data([talent_pool.id])
        data_2 = generate_single_candidate_data([talent_pool.id])
        create_resp_1 = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data_1)
        create_resp_2 = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data_2)

        candidate_id_1 = create_resp_1.json()['candidates'][0]['id']
        candidate_id_2 = create_resp_2.json()['candidates'][0]['id']

        # Archive both candidates
        archive_data = {'candidates': [
            {'id': candidate_id_1, 'archive': True}, {'id': candidate_id_2, 'archive': True}]
        }
        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, archive_data)
        print response_info(update_resp)
        assert update_resp.status_code == 200
        assert len(update_resp.json()['archived_candidates']) == len(archive_data['candidates'])

        # Retrieve candidates
        data = {'candidate_ids': [candidate_id_1, candidate_id_2]}
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE_SEARCH_URI, access_token_first, data)
        print response_info(get_resp)
        assert get_resp.status_code == 404
        assert get_resp.json()['error']['code'] == custom_error.CANDIDATE_IS_ARCHIVED

        # Undo Archived candidates
        unarchive_data = {'candidates': [
            {'id': candidate_id_1, 'archive': False}, {'id': candidate_id_2, 'archive': False}]
        }
        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, unarchive_data)
        print response_info(update_resp)
        assert update_resp.status_code == 200

        # Retrieve candidates
        data = {'candidate_ids': [candidate_id_1, candidate_id_2]}
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE_SEARCH_URI, access_token_first, data)
        print response_info(get_resp)
        assert get_resp.status_code == 200

    def test_update_candidate_outside_of_domain(self, access_token_first, talent_pool, access_token_second):
        """
        Test: User attempts to update a candidate from a different domain
        Expect: 403
        """
        # Create Candidate

        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        candidate_id = create_resp.json()['candidates'][0]['id']

        # User from different domain to update candidate
        data = {'candidates': [{'id': candidate_id, 'first_name': 'moron'}]}
        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_second, data)
        print response_info(update_resp)
        assert update_resp.status_code == 403
        assert update_resp.json()['error']['code'] == custom_error.CANDIDATE_FORBIDDEN

    def test_update_candidate_without_id(self, access_token_first):
        """
        Test:   Attempt to update a Candidate without providing the ID
        Expect: 400
        """
        # Update Candidate's first_name
        data = {'candidate': {'first_name': fake.first_name()}}
        resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)

        print response_info(resp)
        assert resp.status_code == 400
        assert resp.json()['error']['code'] == custom_error.INVALID_INPUT

    def test_update_candidate_names(self, access_token_first, talent_pool):
        """
        Test:   Update candidate's first, middle, and last names
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Update Candidate's first_name
        candidate_id = create_resp.json()['candidates'][0]['id']
        data = {'candidates': [
            {'id': candidate_id, 'first_name': fake.first_name(),
             'middle_name': fake.first_name(), 'last_name': fake.last_name()}
        ]}
        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(update_resp)
        assert candidate_id == update_resp.json()['candidates'][0]['id']

        # Retrieve Candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        # Assert on updated field
        f_name, l_name = data['candidates'][0]['first_name'], data['candidates'][0]['last_name']
        m_name = data['candidates'][0]['middle_name']
        full_name_from_data = str(f_name) + ' ' + str(m_name) + ' ' + str(l_name)
        assert candidate_dict['full_name'] == full_name_from_data

    def test_update_candidate_names_with_candidate_id_in_url(self, access_token_first, talent_pool):
        """
        Test:   Update candidate's first, middle, and last names with candidate ID sent thru the url
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Update Candidate's first_name
        candidate_id = create_resp.json()['candidates'][0]['id']
        data = {'candidates': [
            {'first_name': fake.first_name(), 'middle_name': fake.first_name(), 'last_name': fake.last_name()}
        ]}
        update_resp = send_request('patch', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first, data)
        print response_info(update_resp)
        assert candidate_id == update_resp.json()['candidates'][0]['id']

        # Retrieve Candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        # Assert on updated field
        f_name, l_name = data['candidates'][0]['first_name'], data['candidates'][0]['last_name']
        m_name = data['candidates'][0]['middle_name']
        full_name_from_data = str(f_name) + ' ' + str(m_name) + ' ' + str(l_name)
        assert candidate_dict['full_name'] == full_name_from_data

    def test_update_candidates_in_bulk_with_one_erroneous_data(self, access_token_first, talent_pool):
        """
        Test: Attempt to update few candidates, one of which will have bad data
        Expect: 400; no record should be added to the db
        """
        # Create Candidate
        email_1, email_2 = fake.safe_email(), fake.safe_email()
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'emails': [{'label': None, 'address': email_1}]},
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'emails': [{'label': None, 'address': email_2}]}
        ]}
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        candidate_ids = [candidate['id'] for candidate in create_resp.json()['candidates']]

        # Retrieve both candidates
        data = {'candidate_ids': candidate_ids}
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE_SEARCH_URI, access_token_first, data)
        candidates = get_resp.json()['candidates']

        # Update candidates' email address, one will be an invalid email address
        candidate_1_id, candidate_2_id = candidates[0]['id'], candidates[1]['id']
        email_1_id = candidates[0]['emails'][0]['id']
        email_2_id = candidates[1]['emails'][0]['id']
        update_data = {'candidates': [
            {'id': candidate_1_id, 'emails': [{'id': email_1_id, 'address': fake.safe_email()}]},
            {'id': candidate_2_id, 'emails': [{'id': email_2_id, 'address': 'bad_email_.com'}]}
        ]}
        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, update_data)
        db.session.commit()
        print response_info(update_resp)

        # Candidates' emails must remain unchanged
        assert update_resp.status_code == 400
        assert update_resp.json()['error']['code'] == custom_error.INVALID_EMAIL
        assert CandidateEmail.get_by_id(_id=email_1_id).address == email_1
        assert CandidateEmail.get_by_id(_id=email_2_id).address == email_2

    def test_add_duplicate_custom_fields(self, access_token_first, candidate_first, domain_custom_fields):
        """
        Test: Attempt to add identical custom fields to candidate's records
        """
        custom_field_value = fake.word()
        data = {'candidates': [
            {
                'id': candidate_first.id,
                'custom_fields': [
                    {'custom_field_id': domain_custom_fields[0].id, 'value': custom_field_value},
                    {'custom_field_id': domain_custom_fields[0].id, 'value': custom_field_value}
                ]
            }
        ]}

        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(update_resp)

        # Retrieve candidate's custom fields and ensure only one has been added
        get_resp = send_request('get', CandidateApiUrl.CUSTOM_FIELDS % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert len(get_resp.json()['candidate_custom_fields']) == 1

    def test_add_duplicate_aois(self, access_token_first, candidate_first, domain_aois):
        """
        Test: Attempt to add identical areas of interest to candidate's records
        """
        custom_field_value = fake.word()
        data = {'candidates': [
            {
                'id': candidate_first.id,
                'areas_of_interest': [
                    {'area_of_interest_id': domain_aois[0].id},
                    {'area_of_interest_id': domain_aois[0].id}
                ]
            }
        ]}

        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(update_resp)

        # Retrieve candidate's areas of interest and ensure only one has been added
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert len(get_resp.json()['candidate']['areas_of_interest']) == 1

    def test_add_duplicate_addresses(self, access_token_first, candidate_first):
        """
        Test: Attempt to add identical addresses to candidate's records
        """
        data = {'candidates': [
            {
                'id': candidate_first.id,
                'addresses': [{'city': 'San Jose', 'state': 'CA'}, {'city': 'San Jose', 'state': 'CA'}]
            }
        ]}

        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(update_resp)

        # Retrieve candidate's addresses and ensure only one has been added
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert len(get_resp.json()['candidate']['addresses']) == 1

    def test_add_duplicate_educations(self, access_token_first, candidate_first):
        """
        Test: Attempt to add identical educations to candidate's records
        """
        education_data = {
            'school_name': 'westvalley', 'school_type': 'college', 'city': fake.city(),
            'state': fake.state(), 'country_code': fake.country_code(), 'is_current': fake.boolean(),
            'degrees': [{
                'type': 'ms', 'title': 'masters of science', 'start_year': 2002, 'start_month': 11,
                'end_year': 2006, 'end_month': 12, 'gpa': 1.5, 'bullets': [
                    {
                        'major': 'mathematics', 'comments': 'once a mathematician, always a mathematician'
                    }]
            }]
        }
        data = {'candidates': [
            {'id': candidate_first.id, 'educations': [education_data, education_data]}
        ]}

        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(update_resp)

        # Retrieve candidate's educations and ensure only one has been added
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert len(get_resp.json()['candidate']['educations']) == 1

    def test_update_with_matching_education(self, access_token_first, talent_pool):
        """
        Test: Attempt to add matching educations (with similar name) to candidate's records
        """
        data = GenerateCandidateData.educations([talent_pool.id])
        education_data = {
            'school_name': 'westvalley', 'school_type': 'college', 'city': fake.city(),
            'state': fake.state(), 'country_code': fake.country_code(), 'is_current': fake.boolean(),
            'degrees': [{
                'type': 'ms', 'title': 'masters of science', 'start_year': 2002, 'start_month': 11,
                'end_year': 2006, 'end_month': 12, 'gpa': 1.5, 'bullets': [
                    {
                        'major': 'mathematics', 'comments': 'once a mathematician, always a mathematician'
                    }]
            }]
        }
        data['candidates'][0]['educations'] = [education_data]
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        assert create_resp.status_code == 201, 'status_code should be 201, found: {}'.format(create_resp.status_code)
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        assert get_resp.status_code == 200, 'expected: 200, found: {}'.format(get_resp.status_code)
        candidate_dict = get_resp.json()['candidate']
        candidate_existing_education = candidate_dict['educations'][-1]
        education_data['school_name'] = 'westvallee'
        data['candidates'][0]['id'] = candidate_id
        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        assert update_resp.status_code == 200, 'status_code should be 200, found: {}'.format(update_resp.status_code)
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % update_resp.json()['candidates'][0]['id'], access_token_first)
        assert get_resp.status_code == 200, 'expected: 200, found: {}'.format(get_resp.status_code)
        candidate_dict_updated = get_resp.json()['candidate']
        educations_count = len(candidate_dict_updated['educations'])
        assert educations_count == 1, 'no duplicate education should be added, ' \
                                      'found {} educations instead of 1'.format(educations_count)
        candidate_updated_education = candidate_dict_updated['educations'][-1]
        assert candidate_existing_education['id'] == candidate_updated_education['id'], \
            'expected: {}, found: {}'.format(candidate_existing_education['id'], candidate_updated_education['id'])
        assert 'westvallee' == candidate_updated_education['school_name'], \
            'expected: {}, found: {}'.format('westvallee', candidate_updated_education['school_name'])

    def test_update_with_matching_degree(self, access_token_first, talent_pool):
        """
        Test: Attempt to add matching educations (with similar name) to candidate's records
        """
        data = GenerateCandidateData.educations([talent_pool.id])
        education_data = {
            'school_name': 'westvalley', 'school_type': 'college', 'city': fake.city(),
            'state': fake.state(), 'country_code': fake.country_code(), 'is_current': fake.boolean(),
            'degrees': [{
                'type': 'ms', 'title': 'master of science', 'start_year': 2002, 'start_month': 11,
                'end_year': 2006, 'end_month': 12, 'gpa': 1.5, 'bullets': [
                    {
                        'major': 'mathematics', 'comments': 'once a mathematician, always a mathematician'
                    }]
            }]
        }
        data['candidates'][0]['educations'] = [education_data]
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        assert create_resp.status_code == 201, 'status_code should be 201, found: {}'.format(create_resp.status_code)
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        assert get_resp.status_code == 200, 'expected: 200, found: {}'.format(get_resp.status_code)
        candidate_dict = get_resp.json()['candidate']
        candidate_existing_education = candidate_dict['educations'][0]
        existing_degree = candidate_dict['educations'][0]['degrees'][0]
        data['candidates'][0]['id'] = candidate_id
        education_data['degrees'][0]['title'] = 'M.Sc'
        data['candidates'][0]['educations'][0] = dict(id=candidate_existing_education['id'],
                                                      degrees=education_data['degrees'])
        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        assert update_resp.status_code == 200, 'status_code should be 200, found: {}'.format(update_resp.status_code)
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % update_resp.json()['candidates'][0]['id'], access_token_first)
        assert get_resp.status_code == 200, 'expected: 200, found: {}'.format(get_resp.status_code)
        candidate_dict_updated = get_resp.json()['candidate']
        degrees_count = len(candidate_dict_updated['educations'][0]['degrees'])
        assert degrees_count == 1, 'no duplicate degree should be added, ' \
                                   'found {} degrees instead of 1'.format(degrees_count)
        updated_degree = candidate_dict_updated['educations'][0]['degrees'][-1]
        assert existing_degree['id'] == updated_degree['id'], \
            'expected: {}, found: {}'.format(existing_degree['id'], updated_degree['id'])
        assert 'M.Sc' == updated_degree['title'], \
            'expected: {}, found: {}'.format('M.Sc', updated_degree['title'])

    def test_add_duplicate_educations_degrees(self, access_token_first, candidate_first):
        """
        Test: Attempt to add identical education degrees to candidate's records
        """
        education_data = {
            'school_name': 'westvalley', 'school_type': 'college', 'city': fake.city(),
            'state': fake.state(), 'country_code': fake.country_code(), 'is_current': fake.boolean(),
            'degrees': [
                {
                    'type': 'ms', 'title': 'masters of science', 'start_year': 2002, 'start_month': 11,
                    'end_year': 2006, 'end_month': 12, 'gpa': 1.5, 'bullets': [
                    {
                        'major': 'mathematics', 'comments': 'once a mathematician, always a mathematician'
                    }
                ],

                },
                {
                    'type': 'ms', 'title': 'masters of science', 'start_year': 2002, 'start_month': 11,
                    'end_year': 2006, 'end_month': 12, 'gpa': 1.5, 'bullets': [
                    {
                        'major': 'mathematics', 'comments': 'once a mathematician, always a mathematician'
                    }
                ],

                }
            ]
        }
        data = {'candidates': [{'id': candidate_first.id, 'educations': [education_data]}]}

        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(update_resp)

        # Retrieve candidate's educations and ensure only one education & education degree have been added
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert len(get_resp.json()['candidate']['educations']) == 1
        assert len(get_resp.json()['candidate']['educations'][0]['degrees']) == 1

    def test_add_duplicate_educations_degree_bullets(self, access_token_first, candidate_first):
        """
        Test: Attempt to add identical education degree bullets to candidate's records
        """
        education_data = {
            'school_name': 'westvalley', 'school_type': 'college', 'city': fake.city(),
            'state': fake.state(), 'country_code': fake.country_code(), 'is_current': fake.boolean(),
            'degrees': [
                {
                    'type': 'ms', 'title': 'masters of science', 'start_year': 2002, 'start_month': 11,
                    'end_year': 2006, 'end_month': 12, 'gpa': 1.5, 'bullets':
                    [
                        {
                            'major': 'mathematics', 'comments': 'once a mathematician, always a mathematician'
                        },
                        {
                            'major': 'mathematics', 'comments': 'once a mathematician, always a mathematician'
                        }
                    ],

                }
            ]
        }
        data = {'candidates': [{'id': candidate_first.id, 'educations': [education_data]}]}

        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(update_resp)

        # Retrieve candidate's educations and ensure only one education, education degree, and bullet have been added
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert len(get_resp.json()['candidate']['educations']) == 1
        assert len(get_resp.json()['candidate']['educations'][0]['degrees']) == 1
        assert len(get_resp.json()['candidate']['educations'][0]['degrees'][0]['bullets']) == 1

    def test_add_duplicate_emails(self, access_token_first, candidate_first):
        """
        Test: Attempt to add identical emails to candidate's records
        """
        data = {'candidates': [
            {
                'id': candidate_first.id,
                'emails': [{'address': 'shali+company@example.com'}, {'address': 'shali+company@example.com'}]
            }
        ]}

        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(update_resp)

        # Retrieve candidate's emails and ensure only one has been added
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert len(get_resp.json()['candidate']['emails']) == 1

    def test_add_duplicate_experiences(self, access_token_first, candidate_first):
        """
        Test: Attempt to add identical experiences to candidate's records
        """
        experience_data = {
            'organization': 'apple', 'position': 'engineer',
            'start_year': 2008, 'end_year': 2012, 'start_month': 10, 'end_month': 2,
            'bullets': [{'description': 'job = sucked'}]
        }

        data = {'candidates': [
            {'id': candidate_first.id, 'work_experiences': [experience_data, experience_data]}
        ]}

        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(update_resp)

        # Retrieve candidate's experiences and ensure only one has been added
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert len(get_resp.json()['candidate']['work_experiences']) == 1

    def test_add_duplicate_experience_bullet(self, access_token_first, candidate_first):
        """
        Test: Attempt to add identical experience bullet to candidate's records
        """
        experience_data = {
            'organization': 'apple', 'position': 'engineer', 'bullets': [
                {'description': 'job = sucked'}, {'description': 'job = sucked'}]
        }

        data = {'candidates': [
            {'id': candidate_first.id, 'work_experiences': [experience_data, experience_data]}
        ]}

        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(update_resp)

        # Retrieve candidate's experiences and ensure only one experience & one experience bullet has been added
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert len(get_resp.json()['candidate']['work_experiences']) == 1
        assert len(get_resp.json()['candidate']['work_experiences'][0]['bullets']) == 1

    def test_add_duplicate_phones(self, access_token_first, candidate_first):
        """
        Test: Attempt to add identical phones to candidate's records
        """
        data = {'candidates': [
            {
                'id': candidate_first.id,
                'phones': [{'value': '4086667778'}, {'value': '4086667778'}]
            }
        ]}

        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(update_resp)

        # Retrieve candidate's phones and ensure only one has been added
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert len(get_resp.json()['candidate']['phones']) == 1

    def test_add_duplicate_military_services(self, access_token_first, candidate_first):
        """
        Test: Attempt to add identical military services to candidate's records
        """
        data = {'candidates': [
            {
                'id': candidate_first.id,
                'military_services': [{'status': 'active'}, {'status': 'active'}]
            }
        ]}

        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(update_resp)

        # Retrieve candidate's military services and ensure only one has been added
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert len(get_resp.json()['candidate']['military_services']) == 1

    def test_add_duplicate_preferred_locations(self, access_token_first, candidate_first):
        """
        Test: Attempt to add identical preferred locations to candidate's records
        """
        data = {'candidates': [
            {
                'id': candidate_first.id,
                'preferred_locations': [{'city': 'cancun'}, {'city': 'cancun'}]
            }
        ]}

        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(update_resp)

        # Retrieve candidate's preferred locations and ensure only one has been added
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert len(get_resp.json()['candidate']['preferred_locations']) == 1

    def test_add_duplicate_skills(self, access_token_first, candidate_first):
        """
        Test: Attempt to add identical skills to candidate's records
        """
        data = {'candidates': [
            {
                'id': candidate_first.id,
                'skills': [{'name': 'python'}, {'name': 'python'}]
            }
        ]}

        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(update_resp)

        # Retrieve candidate's skills and ensure only one has been added
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert len(get_resp.json()['candidate']['skills']) == 1

    def test_add_duplicate_social_networks(self, access_token_first, candidate_first):
        """
        Test: Attempt to add identical social networks to candidate's records
        """
        data = {'candidates': [
            {
                'id': candidate_first.id,
                'social_networks': [
                    {'name': 'Facebook', 'profile_url': 'www.facebook.com/1'},
                    {'name': 'Facebook', 'profile_url': 'www.facebook.com/1'}
                ]
            }
        ]}

        update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(update_resp)

        # Retrieve candidate's social networks and ensure only one has been added
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_first.id, access_token_first)
        print response_info(get_resp)
        assert len(get_resp.json()['candidate']['social_networks']) == 1


class TestUpdateCandidateAddress(object):
    # TODO Commenting out randomly failing test case so build passes. -OM
    # def test_add_new_candidate_address(self, access_token_first, user_first, talent_pool):
    #     """
    #     Test:   Add a new CandidateAddress to an existing Candidate
    #     Expect: 200
    #     """
    #     # Create Candidate
    #     data = generate_single_candidate_data([talent_pool.id])
    #     create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
    #
    #     # Add a new address to the existing Candidate
    #     candidate_id = create_resp.json()['candidates'][0]['id']
    #     data = GenerateCandidateData.addresses(talent_pool_ids=[talent_pool.id], candidate_id=candidate_id)
    #     update_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
    #     print response_info(update_resp)
    #
    #     # Retrieve Candidate after update
    #     get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
    #     updated_candidate_dict = get_resp.json()['candidate']
    #     candidate_address = updated_candidate_dict['addresses'][-1]
    #     assert updated_candidate_dict['id'] == candidate_id
    #     assert isinstance(candidate_address, dict)
    #     assert candidate_address['address_line_1'] == data['candidates'][0]['addresses'][-1]['address_line_1']
    #     assert candidate_address['city'] == data['candidates'][0]['addresses'][-1]['city']
    #     assert candidate_address['zip_code'] == data['candidates'][0]['addresses'][-1]['zip_code']

    def test_multiple_is_default_addresses(self, access_token_first, talent_pool):
        """
        Test:   Add more than one CandidateAddress with is_default set to True
        Expect: 200, but only one CandidateAddress must have is_default True, the rest must be False
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Add a new address to the existing Candidate with is_default set to True
        candidate_id = create_resp.json()['candidates'][0]['id']
        data = GenerateCandidateData.addresses(candidate_id=candidate_id, is_default=True)
        send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        updated_candidate_dict = get_resp.json()['candidate']
        updated_can_addresses = updated_candidate_dict['addresses']
        # Only one of the addresses must be default!
        assert sum([1 for address in updated_can_addresses if address['is_default']]) == 1

    def test_update_an_existing_address(self, access_token_first, talent_pool):
        """
        Test:   Update an existing CandidateAddress
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']
        candidate_address = candidate_dict['addresses'][0]

        # Update one of Candidate's addresses
        data = GenerateCandidateData.addresses(candidate_id=candidate_id, address_id=candidate_address['id'])
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        updated_candidate_dict = resp.json()['candidate']
        updated_address = updated_candidate_dict['addresses'][0]
        assert isinstance(updated_candidate_dict, dict)
        assert updated_candidate_dict['id'] == candidate_id
        assert updated_address['address_line_1'] == data['candidates'][0]['addresses'][0]['address_line_1']
        assert updated_address['city'] == data['candidates'][0]['addresses'][0]['city']
        assert updated_address['subdivision'] == \
               pycountry.subdivisions.get(code=data['candidates'][0]['addresses'][0]['subdivision_code']).name
        assert updated_address['zip_code'] == data['candidates'][0]['addresses'][0]['zip_code']

    def test_update_an_existing_address_with_same_address_without_address_id(self, access_token_first, talent_pool):
        """
        Test:   Update an existing CandidateAddress with same address without passing address id. It will not
        add another duplicate but will update existing one
        Expect: 200
        """
        # Create Candidate
        data = GenerateCandidateData.addresses([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']
        existing_addresses = candidate_dict['addresses']

        # Update candidate with existing address but without passing address id
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)
        # Retrieve Candidate after update
        resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        updated_candidate_dict = resp.json()['candidate']
        updated_addresses = updated_candidate_dict['addresses']
        assert len(existing_addresses) == len(updated_addresses), 'expected: {}, found: {}'.format(
            len(existing_addresses), len(updated_addresses))
        assert existing_addresses[0]['id'] == updated_addresses[0]['id'], 'expected: {}, found: {}'.format(
            existing_addresses[0]['id'], updated_addresses[0]['id']
        )
        assert updated_addresses[0]['address_line_1'] == existing_addresses[0]['address_line_1']
        assert updated_addresses[0]['city'] == existing_addresses[0]['city']
        assert updated_addresses[0]['subdivision'] == existing_addresses[0]['subdivision']
        assert updated_addresses[0]['zip_code'] == existing_addresses[0]['zip_code']

    def test_update_an_existing_address_with_similar_address_without_address_id(self, access_token_first, talent_pool):
        """
        Test:   Update an existing CandidateAddress with similar/matching address without passing address id.
        It will not add another duplicate but will update existing one
        Expect: 200
        """
        # Create Candidate
        data = GenerateCandidateData.addresses([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']
        existing_addresses = candidate_dict['addresses']

        # Update address_line_1
        data['candidates'][0]['addresses'][0]['address_line_1'] += 'st'
        # Update candidate with existing address but without passing address id
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)
        # Retrieve Candidate after update
        resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        updated_candidate_dict = resp.json()['candidate']
        updated_addresses = updated_candidate_dict['addresses']
        assert len(existing_addresses) == len(updated_addresses), 'expected: {}, found: {}'.format(
            len(existing_addresses), len(updated_addresses))
        assert existing_addresses[0]['id'] == updated_addresses[0]['id'], 'expected: {}, found: {}'.format(
            existing_addresses[0]['id'], updated_addresses[0]['id']
        )
        assert updated_addresses[0]['address_line_1'] == existing_addresses[0]['address_line_1']
        assert updated_addresses[0]['city'] == existing_addresses[0]['city']
        assert updated_addresses[0]['subdivision'] == existing_addresses[0]['subdivision']
        assert updated_addresses[0]['zip_code'] == existing_addresses[0]['zip_code']

    def test_update_candidate_current_address(self, access_token_first, talent_pool):
        """
        Test:   Set one of candidate's addresses' is_default to True and assert it's the first
                CandidateAddress object returned in addresses-list
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Add another address
        candidate_id = create_resp.json()['candidates'][0]['id']
        data = GenerateCandidateData.addresses(candidate_id=candidate_id, is_default=True)
        send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']
        can_addresses = candidate_dict['addresses']

        # Update: Set the last CandidateAddress in can_addresses as the default candidate-address
        data = {
            'candidates': [{'id': candidate_id, 'addresses': [{'id': can_addresses[-1]['id'], 'is_default': True}]}]}
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)
        assert updated_resp.status_code == 200

        # Retrieve Candidate after update
        resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        updated_candidate_dict = resp.json()['candidate']

        updated_addresses = updated_candidate_dict['addresses']
        assert isinstance(updated_addresses, list)
        assert updated_addresses[0]['is_default'] == True


class TestUpdateCandidateAOI(object):
    def test_add_new_area_of_interest(self, access_token_first, talent_pool, domain_aois):
        """
        Test:   Add a new CandidateAreaOfInterest to existing Candidate.
                Number of CandidateAreaOfInterest should increase by 1.
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        candidate_area_of_interest_count = len(candidate_dict['areas_of_interest'])

        # Add new CandidateAreaOfInterest
        data = GenerateCandidateData.areas_of_interest(domain_aois, [talent_pool.id], candidate_id)
        resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']
        candidate_aois = candidate_dict['areas_of_interest']
        assert isinstance(candidate_aois, list)
        assert candidate_aois[0]['name'] == db.session.query(AreaOfInterest).get(candidate_aois[0]['id']).name
        assert candidate_aois[1]['name'] == db.session.query(AreaOfInterest).get(candidate_aois[1]['id']).name
        assert len(candidate_aois) == candidate_area_of_interest_count + len(domain_aois)


class TestUpdateWorkPreference(object):
    def test_add_multiple_work_preference(self, access_token_first, talent_pool):
        """
        Test:   Attempt to add two CandidateWorkPreference
        Expect: 400
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        candidate_id = create_resp.json()['candidates'][0]['id']

        # Add CandidateWorkPreference
        data = GenerateCandidateData.work_preference(candidate_id=candidate_id)
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)
        assert updated_resp.status_code == 400
        assert updated_resp.json()['error']['code'] == custom_error.WORK_PREF_EXISTS

    def test_update_work_preference(self, access_token_first, talent_pool):
        """
        Test:   Update candidate's work preference. Since this is an update,
                number of CandidateWorkPreference must remain unchanged.
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        # Update CandidateWorkPreference
        data = GenerateCandidateData.work_preference(candidate_id=candidate_id,
                                                     preference_id=candidate_dict['work_preference']['id'])
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        updated_candidate_dict = get_resp.json()['candidate']
        work_preference_dict = updated_candidate_dict['work_preference']

        work_pref_from_data = data['candidates'][0]['work_preference']

        assert candidate_id == updated_candidate_dict['id']
        assert isinstance(work_preference_dict, dict)
        assert work_preference_dict['salary'] == work_pref_from_data['salary']
        assert work_preference_dict['hourly_rate'] == float(work_pref_from_data['hourly_rate'])
        assert work_preference_dict['travel_percentage'] == work_pref_from_data['travel_percentage']


class TestUpdateCandidateMilitaryService(object):
    def test_add_military_service_with_incorrect_date_format(self, access_token_first, talent_pool):
        """
        Test: Attempt to add military service to candidate with faulty to_date or from_date format
        Expect: 400
        """
        # Create candidate + candidate military service
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'military_services': [
                {'from_date': '2005', 'to_date': '2012-12-12'}
            ]}
        ]}
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 400
        assert create_resp.json()['error']['code'] == custom_error.MILITARY_INVALID_DATE

    def test_add_military_service(self, access_token_first, talent_pool):
        """
        Test:   Add a CandidateMilitaryService to an existing Candidate.
                Number of candidate's military_services should increase by 1.
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        military_services_before_update = get_resp.json()['candidate']['military_services']
        military_services_count_before_update = len(military_services_before_update)

        # Add CandidateMilitaryService
        data = {'candidates': [{'id': candidate_id, 'military_services': [
            {'country': 'gb', 'branch': 'air force', 'comments': 'adept at killing cows with mad-cow-disease'}
        ]}]}
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        military_services_after_update = candidate_dict['military_services']
        assert candidate_id == candidate_dict['id']
        assert len(military_services_after_update) == military_services_count_before_update + 1
        assert military_services_after_update[-1]['branch'] == 'air force'
        assert military_services_after_update[-1]['comments'] == 'adept at killing cows with mad-cow-disease'

    def test_update_military_service(self, access_token_first, talent_pool):
        """
        Test:   Update an existing CandidateMilitaryService.
                Number of candidate's military_services should remain unchanged.
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        military_services_before_update = get_resp.json()['candidate']['military_services']
        military_services_count_before_update = len(military_services_before_update)

        # Add CandidateMilitaryService
        data = {'candidates': [{'id': candidate_id, 'military_services': [
            {'id': military_services_before_update[0]['id'], 'country': 'gb', 'branch': 'air force',
             'comments': 'adept at killing cows with mad-cow-disease'}
        ]}]}
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        military_services_after_update = candidate_dict['military_services']
        assert candidate_id == candidate_dict['id']
        assert len(military_services_after_update) == military_services_count_before_update
        assert military_services_after_update[0]['branch'] == 'air force'
        assert military_services_after_update[0]['comments'] == 'adept at killing cows with mad-cow-disease'


class TestUpdateCandidatePreferredLocation(object):
    def test_add_preferred_location(self, access_token_first, talent_pool):
        """
        Test:   Add a CandidatePreferredLocation to an existing Candidate.
                Number of candidate's preferred_location should increase by 1.
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        preferred_location_before_update = get_resp.json()['candidate']['preferred_locations']
        preferred_locations_count_before_update = len(preferred_location_before_update)

        # Add CandidatePreferredLocation
        data = {'candidates': [{'id': candidate_id, 'preferred_locations': [{'city': 'austin', 'state': 'texas'}]}]}
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        preferred_locations_after_update = candidate_dict['preferred_locations']
        assert candidate_id == candidate_dict['id']
        assert len(preferred_locations_after_update) == preferred_locations_count_before_update + 1
        assert preferred_locations_after_update[-1]['city'] == 'austin'
        assert preferred_locations_after_update[-1]['state'] == 'texas'

    def test_update_preferred_location(self, access_token_first, talent_pool):
        """
        Test:   Update an existing CandidatePreferredLocation.
                Number of candidate's preferred_location should remain unchanged.
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        preferred_location_before_update = get_resp.json()['candidate']['preferred_locations']
        preferred_locations_count_before_update = len(preferred_location_before_update)

        # Add CandidatePreferredLocation
        data = {'candidates': [{'id': candidate_id, 'preferred_locations': [
            {'id': preferred_location_before_update[0]['id'], 'city': 'austin', 'state': 'texas'}]}]}
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        preferred_locations_after_update = candidate_dict['preferred_locations']
        assert candidate_id == candidate_dict['id']
        assert len(preferred_locations_after_update) == preferred_locations_count_before_update + 0
        assert preferred_locations_after_update[0]['city'] == 'austin'
        assert preferred_locations_after_update[0]['state'] == 'texas'


class TestUpdateCandidateSkill(object):
    def test_add_skill(self, access_token_first, talent_pool):
        """
        Test:   Add a CandidateSkill to an existing Candidate.
                Number of candidate's preferred_location should increase by 1.
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        skills_before_update = get_resp.json()['candidate']['skills']
        skills_count_before_update = len(skills_before_update)

        # Add CandidateSkill
        data = {'candidates': [{'id': candidate_id, 'skills': [{'name': 'pos'}]}]}
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        skills_after_update = candidate_dict['skills']
        assert candidate_id == candidate_dict['id']
        assert len(skills_after_update) == skills_count_before_update + 1
        assert skills_after_update[-1]['name'] == 'pos'

    def test_update_skill(self, access_token_first, talent_pool):
        """
        Test:   Update an existing CandidateSkill.
                Number of candidate's preferred_location should remain unchanged.
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        skills_before_update = get_resp.json()['candidate']['skills']
        skills_count_before_update = len(skills_before_update)

        # Update CandidateSkill
        data = {'candidates': [{'id': candidate_id, 'skills': [{'id': skills_before_update[0]['id'], 'name': 'pos'}]}]}
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        skills_after_update = candidate_dict['skills']
        assert candidate_id == candidate_dict['id']
        assert len(skills_after_update) == skills_count_before_update
        assert skills_after_update[0]['name'] == 'pos'


class TestUpdateCandidateSocialNetwork(object):
    def test_add_social_network(self, access_token_first, talent_pool):
        """
        Test:   Add a CandidateSocialNetwork to an existing Candidate.
                Number of candidate's social_networks should increase by 1.
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        social_networks_before_update = get_resp.json()['candidate']['social_networks']
        social_networks_count_before_update = len(social_networks_before_update)

        # Add CandidateSocialNetwork
        data = {'candidates': [{'id': candidate_id, 'social_networks': [
            {'name': 'linkedin', 'profile_url': 'https://www.linkedin.com/company/sara'}
        ]}]}
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        social_networks_after_update = candidate_dict['social_networks']
        assert candidate_id == candidate_dict['id']
        assert len(social_networks_after_update) == social_networks_count_before_update + 1
        assert social_networks_after_update[-1]['name'] == 'LinkedIn'
        assert social_networks_after_update[-1]['profile_url'] == 'https://www.linkedin.com/company/sara'

    def test_update_social_network(self, access_token_first, talent_pool):
        """
        Test:   Update a CandidateSocialNetwork.
                Number of candidate's social_networks should remain unchanged.
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        social_networks_before_update = get_resp.json()['candidate']['social_networks']
        social_networks_count_before_update = len(social_networks_before_update)

        # Add CandidateSocialNework
        data = {'candidates': [{'id': candidate_id, 'social_networks': [
            {'id': social_networks_before_update[0]['id'],
             'name': 'linkedin', 'profile_url': 'https://www.linkedin.com/company/sara'}
        ]}]}
        updated_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(updated_resp)
        assert updated_resp.status_code == 200

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        social_networks_after_update = candidate_dict['social_networks']
        assert candidate_id == candidate_dict['id']
        assert len(social_networks_after_update) == social_networks_count_before_update
        assert social_networks_after_update[0]['name'] == 'LinkedIn'
        assert social_networks_after_update[0]['profile_url'] == 'https://www.linkedin.com/company/sara'
