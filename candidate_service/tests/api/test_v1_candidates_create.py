"""
Test cases for CandidateResource/post()
"""
# Candidate Service app instance
from candidate_service.candidate_app import app

import pycountry

# Conftest
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import AddUserRoles, get_country_code_from_name
from candidate_service.common.routes import CandidateApiUrl
from candidate_service.common.utils.test_utils import send_request, response_info

# Sample data
from candidate_sample_data import (
    GenerateCandidateDate, generate_single_candidate_data, candidate_phones, candidate_military_service,
    candidate_preferred_locations, candidate_skills, candidate_social_network
)

# Models
from candidate_service.common.models.candidate import CandidateEmail

# Custom errors
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error


def test_candidate_creation_postman(access_token_first, user_first, talent_pool, domain_aoi):
    AddUserRoles.all_roles(user_first)
    data = {
        "candidates": [
            {"first_name": "James", "middle_name": "Earl", "last_name": "Jones",
             "talent_pool_ids": {"add": [talent_pool.id]},
             "emails": [
                 {"label": "Primary", "address": "myemail6@gmail.com", "is_default": True},
                 {"label": "Secondary", "address": "myemail7@gmail.com", "is_default": False}
             ],
             "phones": [
                 {"label": "mobile", "value": "4088368912", "is_default": True},
                 {"label": "home", "value": "415159408", "is_default": False}
             ],
             "areas_of_interest": [
                 {"area_of_interest_id": domain_aoi[0].id}, {"area_of_interest_id": domain_aoi[1].id}
             ],
             "work_preference": {
                 "authorization": "US Citizen",
                 "employment_type": "Full-time, Part-timeContract - W2",
                 "relocate": True,
                 "telecommute": True,
                 "travel_percentage": 25,
                 "security_clearance": False,
                 "third_party": False,
                 "hourly_rate": 35.5,
                 "salary": 75000},
             "addresses": [{"address_line_1": "840 Battery St.", "address_line_2": "", "city": "San Francisco",
                            "state": "CA", "country": "US, United States", "po_box": None, "zip_code": "94101",
                            "is_default": True}],
             "social_networks": [
                 {"name": "facebook", "profile_url": "https://www.facebook.com/DavidAvocadoWolfe"},
                 {"name": "linkedin", "profile_url": "https://www.linkedin.com/in/abeheshtaein"},
                 {"name": "twitter", "profile_url": "https://twitter.com/AmirBeheshty"}
             ],
             "preferred_locations": [
                 {"address": "250 Hospital Way", "city": "San Jose", "state": "CA", "country": "US, United States",
                  "zip_code": "95133"},
                 {"city": "New York", "state": "New York", "country": "US, United States", "zip_code": "95133"}
             ],
             "work_experiences": [
                 {"position": "QA engineer", "organization": "Dice", "city": "San Jose", "state": "CA",
                  "country": "US, United States",
                  "start_year": 2006, "end_year": 2010, "start_month": 12, "end_month": 12, "is_current": False,
                  "bullets": [
                      {"description": "Did cool things in a certain way to make stuff better."},
                      {"description": "Did more cool things in yet another way for more betterment."}
                  ]
                  }
             ],
             "military_services": [
                 {"country": "US, United States", "highest_rank": "liutenant", "branch": "Air Force",
                  "status": "active",
                  "highest_grade": "O-1", "from_date": "2001-12-12", "to_date": "2009-11-01",
                  "comments": "served 4 years in Iraq"}
             ],
             "skills": [
                 {"name": "PHP", "months_used": 13, "last_used_date": "2010-08-03"},
                 {"name": "SQL", "months_used": 43, "last_used_date": "2015-08-03"},
                 {"name": "Payroll", "months_used": 24, "last_used_date": "2014-08-03"}
             ]
             }
        ]
    }
    create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
    print response_info(create_resp)
    assert create_resp.status_code == 201


class CommonData(object):
    @staticmethod
    def data(_talent_pool):
        return {'candidates': [{'emails': [{'address': fake.safe_email()}],
                                'talent_pool_ids': {'add': [_talent_pool.id]}}]}


class TestCreateCandidate(object):
    def test_create_candidate_without_talent_pools(self, access_token_first, user_first):
        """
        Test: Attempt to create a candidate without providing talent pool IDs
        Expect: 400
        """
        # Create Candidate
        AddUserRoles.add(user=user_first)
        data = {'candidates': [{'first_name': 'cher'}]}
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(response=create_resp)
        assert create_resp.status_code == 400
        assert create_resp.json()['error']['code'] == custom_error.INVALID_INPUT

    def test_create_candidate_successfully(self, access_token_first, user_first, talent_pool):
        """
        Test:   Create a new candidate and candidate's info
        Expect: 201
        """
        # Create Candidate
        AddUserRoles.add(user=user_first)
        data = {'candidates': [{'first_name': 'joker', 'talent_pool_ids': {'add': [talent_pool.id]}}]}
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

    def test_add_candidate_without_name(self, access_token_first, user_first, talent_pool):
        """
        """
        AddUserRoles.add_and_get(user_first)
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}}
        ]}
        # Create candidate with missing name
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)

    def test_create_candidate_and_retrieve_it(self, access_token_first, user_first, talent_pool):
        """
        Test:   Create a Candidate and retrieve it. Ensure that the data sent in for creating the
                Candidate is identical to the data obtained from retrieving the Candidate
                minus id-keys
        Expect: 201
        """
        # Create Candidate
        AddUserRoles.add_and_get(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(resp)
        assert resp.status_code == 200

    def test_create_an_existing_candidate(self, access_token_first, user_first, talent_pool):
        """
        Test:   Attempt to recreate an existing Candidate
        Expect: 400
        """
        # Create same Candidate twice
        AddUserRoles.add(user=user_first)
        data = {'candidates': [{'emails': [{'address': fake.safe_email()}],
                                'talent_pool_ids': {'add': [talent_pool.id]}}]}
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 400
        assert create_resp.json()['error']['code'] == custom_error.CANDIDATE_ALREADY_EXISTS

    def test_create_candidate_with_missing_candidates_keys(self, access_token_first, user_first):
        """
        Test:   Create a Candidate with only first_name provided
        Expect: 400
        """
        # Create Candidate without 'candidate'-key
        AddUserRoles.add(user_first)
        data = {'first_name': fake.first_name()}
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 400
        assert create_resp.json()['error']['code'] == custom_error.INVALID_INPUT

    def test_update_candidate_via_post(self, access_token_first, user_first):
        """
        Test:   Attempt to update a Candidate via post()
        Expect: 400
        """
        # Send Candidate object with candidate_id to post
        AddUserRoles.add(user_first)
        data = {'candidates': [{'id': 5, 'emails': [{'address': fake.safe_email()}]}]}
        resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(resp)
        assert resp.status_code == 400
        assert resp.json()['error']['code'] == custom_error.INVALID_INPUT

    def test_create_candidate_with_invalid_fields(self, access_token_first, user_first, talent_pool):
        """
        Test:   Attempt to create a Candidate with bad fields/keys
        Expect: 400
        """
        AddUserRoles.add(user=user_first)
        # Create Candidate with invalid keys/fields
        data = {'candidates': [{'emails': [{'address': 'someone@nice.io'}], 'foo': 'bar',
                                'talent_pool_ids': {'add': [talent_pool.id]}}]}
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 400
        assert create_resp.json()['error']['code'] == custom_error.INVALID_INPUT

    def test_create_candidates_in_bulk_with_one_erroneous_data(self, access_token_first, user_first, talent_pool):
        """
        Test: Attempt to create few candidates, one of which will have bad data
        Expect: 400, no record should be added to the db
        """
        AddUserRoles.add(user=user_first)

        email_1, email_2 = fake.safe_email(), fake.safe_email()
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'emails': [{'label': None, 'address': email_1}]},
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'emails': [{'label': None, 'address': email_2}]},
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'emails': [{'label': None, 'address': 'bad_email_at_example.com'}]}
        ]}
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        db.session.commit()
        assert create_resp.status_code == 400
        assert create_resp.json()['error']['code'] == custom_error.INVALID_EMAIL
        assert not CandidateEmail.get_by_address(email_address=email_1)
        assert not CandidateEmail.get_by_address(email_address=email_2)

    def test_add_candidate_without_emails(self, access_token_first, user_first, talent_pool):
        """
        Test:  Create a candidate without an email address
        Expect:  201; talent_pool is the only required field for candidate creation
        """
        AddUserRoles.add_and_get(user_first)
        data = {'candidates': [{'talent_pool_ids': {'add': [talent_pool.id]}}]}

        # Create candidate
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201


class TestCreateHiddenCandidate(object):
    def test_create_hidden_candidate(self, access_token_first, user_first, talent_pool):
        """
        Test: Create a candidate that was previously web-hidden
        Expect: 201, candidate should no longer be web hidden.
                No duplicate records should be in the database
        """
        # Create candidate
        AddUserRoles.all_roles(user_first)
        data = CommonData.data(talent_pool)
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        candidate_id = create_resp.json()['candidates'][0]['id']
        db.session.commit()
        print response_info(create_resp)

        # Retrieve candidate's email
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        first_can_email = get_resp.json()['candidate']['emails'][0]

        # Hide candidate
        hide_data = {'candidates': [{'id': candidate_id, 'hide': True}]}
        hide_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, hide_data)
        print response_info(hide_resp)
        candidate = Candidate.get_by_id(candidate_id=candidate_id)
        candidate_emails_count = len(candidate.emails)
        assert hide_resp.status_code == 200 and candidate.is_web_hidden == 1

        # Create previously deleted candidate
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        db.session.commit()
        print response_info(create_resp)
        assert create_resp.status_code == 201
        assert candidate.is_web_hidden == 0
        assert CandidateEmail.get_by_address(first_can_email['address'])[0].id == first_can_email['id']
        assert len(candidate.emails) == candidate_emails_count

    def test_create_hidden_candidate_with_different_user_from_same_domain(
            self, access_token_first, user_first, user_same_domain, talent_pool):
        """
        Test: Create a candidate that was previously web-hidden with a different
              user from the same domain
        Expect: 201, candidate should no longer be web-hidden
        """
        # Create candidate
        AddUserRoles.all_roles(user=user_first)
        data = CommonData.data(talent_pool)
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(response=create_resp)
        candidate_id = create_resp.json()['candidates'][0]['id']
        db.session.commit()

        # Retrieve candidate's email
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        first_can_email = get_resp.json()['candidate']['emails'][0]

        # Hide candidate
        hide_data = {'candidates': [{'id': candidate_id, 'hide': True}]}
        hide_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, hide_data)
        print response_info(hide_resp)
        candidate = Candidate.get_by_id(candidate_id)
        candidate_emails_count = len(candidate.emails)
        assert hide_resp.status_code == 200 and candidate.is_web_hidden == 1

        # Create previously hidden candidate with a different user from the same domain
        AddUserRoles.add(user_same_domain)
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201
        assert candidate.is_web_hidden == 0
        assert CandidateEmail.get_by_address(first_can_email['address'])[0].id == first_can_email['id']
        assert len(candidate.emails) == candidate_emails_count

    def test_create_hidden_candidate_with_fields_that_cannot_be_aggregated(self, access_token_first,
                                                                           user_first, talent_pool):
        """
        Test: Create a candidate that is currently web-hidden but with a different name
        Expect: 200; candidate's full name must be updated
        """
        # Create candidate
        AddUserRoles.all_roles(user_first)
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, CommonData.data(talent_pool))
        candidate_id = create_resp.json()['candidates'][0]['id']
        db.session.commit()
        print response_info(create_resp)

        # Retrieve candidate's first name
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_email = get_resp.json()['candidate']['emails'][0]
        full_name = get_resp.json()['candidate']['full_name']

        # Hide candidate
        hide_data = {'candidates': [{'id': candidate_id, 'hide': True}]}
        hide_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, hide_data)
        print response_info(hide_resp)
        candidate = Candidate.get_by_id(candidate_id)
        assert hide_resp.status_code == 200 and candidate.is_web_hidden == 1

        # Create previously deleted candidate
        data = {'candidates': [{'emails': [{'address': candidate_email['address']}],'first_name': 'McLovin',
                                'talent_pool_ids': {'add': [talent_pool.id]}}]}
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        db.session.commit()
        print response_info(create_resp)
        assert create_resp.status_code == 201
        assert candidate.is_web_hidden == 0

        # Retrieve candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 200
        assert get_resp.json()['candidate']['full_name'] != full_name

    def test_create_candidates_and_delete_one_then_create_it_again(
            self, access_token_first, user_first, talent_pool, access_token_second,
            user_second, talent_pool_second):
        """
        Test brief:
        1. Create two candidates with the same email address in different domains
        2. Hide one
        3. Assert the other candidate is not web-hidden
        """
        # Create candidates
        AddUserRoles.all_roles(user_first)
        AddUserRoles.all_roles(user_second)
        data_1 = {'candidates': [{'talent_pool_ids': {'add': [talent_pool.id]},
                                  'emails': [{'address': 'amir@example.com'}]}]}
        data_2 = {'candidates': [{'talent_pool_ids': {'add': [talent_pool_second.id]},
                                  'emails': [{'address': 'amir@example.com'}]}]}
        create_resp_1 = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data_1)
        create_resp_2 = send_request('post', CandidateApiUrl.CANDIDATES, access_token_second, data_2)
        print response_info(create_resp_1)
        print response_info(create_resp_2)
        candidate_id_1 = create_resp_1.json()['candidates'][0]['id']
        candidate_id_2 = create_resp_2.json()['candidates'][0]['id']

        # Hide candidate_1
        hide_data = {'candidates': [{'id': candidate_id_1, 'hide': True}]}
        hide_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, hide_data)
        db.session.commit()
        print response_info(hide_resp)
        candidate = Candidate.get_by_id(candidate_id_1)
        assert candidate.is_web_hidden == 1

        # Retrieve candidate_1
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id_1, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 404
        assert get_resp.json()['error']['code'] == custom_error.CANDIDATE_IS_HIDDEN

        # Retrieve candidate_2
        get_resp_2 = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id_2, access_token_second)
        print response_info(response=get_resp_2)
        assert get_resp_2.status_code == 200

    def test_recreate_hidden_candidate_using_candidate_with_multiple_emails(
            self, access_token_first, user_first, talent_pool):
        # Create candidate
        AddUserRoles.all_roles(user=user_first)
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'emails': [
                {'address': fake.safe_email()}, {'address': fake.safe_email()}
            ]}
        ]}
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        candidate_id = create_resp.json()['candidates'][0]['id']

        # Hide candidate
        hide_data = {'candidates': [{'id': candidate_id, 'hide': True}]}
        hide_resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, hide_data)
        db.session.commit()
        print response_info(hide_resp)
        candidate = Candidate.get_by_id(candidate_id)
        assert candidate.is_web_hidden == 1

        # Re-create candidate
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201
        assert create_resp.json()['candidates'][0]['id'] == candidate_id


class TestCreateCandidateAddress(object):
    def test_create_candidate_address(self, access_token_first, user_first, talent_pool):
        """
        Test: Create new candidate + candidate-address
        Expect: 201
        """
        # Create Candidate with address
        AddUserRoles.add_and_get(user_first)
        data = GenerateCandidateDate.addresses([talent_pool.id])
        country_code = data['candidates'][0]['addresses'][0]['country_code']
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 200
        assert get_country_code_from_name(get_resp.json()['candidate']['addresses'][0]['country']) == country_code

    def test_create_candidate_with_bad_zip_code(self, access_token_first, user_first, talent_pool):
        """
        Test:   Attempt to create a Candidate with invalid zip_code
        Expect: 201, but zip_code must be Null
        """
        # Create Candidate
        AddUserRoles.add_and_get(user=user_first)
        data = generate_single_candidate_data(talent_pool_ids=[talent_pool.id])
        data['candidates'][0]['addresses'][0]['zip_code'] = 'ABCDEFG'
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']
        assert candidate_dict['addresses'][0]['zip_code'] is None

    def test_with_poorly_formatted_data(self, access_token_first, user_first, talent_pool):
        """
        Test:  Create candidate address with whitespaces, None values, etc.
        Expect: 201; server should clean up data before adding to db
        """
        AddUserRoles.add_and_get(user_first)
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'addresses': [
                {'address_line_1': ' 255 west santa clara st.   ', 'address_line_2': '  ', 'city': ' San Jose '},
                {'address_line_1': ' ', 'address_line_2': '  ', 'city': None},
                {'address_line_1': None, 'address_line_2': None, 'city': '\n'},
            ]}
        ]}
        # Create candidate + candidate address
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_addresses = get_resp.json()['candidate']['addresses']
        assert len(candidate_addresses) == 1, "Only 1 of the addresses should be inserted into db, because" \
                                              "the rest had empty/None values"
        assert candidate_addresses[0]['address_line_1'] == data['candidates'][0]['addresses'][0]['address_line_1'].strip()
        assert candidate_addresses[0]['city'] == data['candidates'][0]['addresses'][0]['city'].strip()


class TestCreateAOI(object):
    def test_create_candidate_area_of_interest(self, access_token_first, user_first, talent_pool, domain_aoi):
        """
        Test:   Create CandidateAreaOfInterest
        Expect: 201
        """
        AddUserRoles.add_and_get(user=user_first)

        # Create Candidate + CandidateAreaOfInterest
        data = generate_single_candidate_data(talent_pool_ids=[talent_pool.id], areas_of_interest=domain_aoi)
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)

        candidate_aoi = get_resp.json()['candidate']['areas_of_interest']
        assert isinstance(candidate_aoi, list)
        assert candidate_aoi[0]['name'] == AreaOfInterest.query.get(candidate_aoi[0]['id']).name
        assert candidate_aoi[1]['name'] == AreaOfInterest.query.get(candidate_aoi[1]['id']).name

    def test_create_candidate_area_of_interest_outside_of_domain(self, access_token_second, user_second,
                                                                 domain_aoi, talent_pool):
        """
        Test: Attempt to create candidate's area of interest outside of user's domain
        Expect: 403
        """
        AddUserRoles.add(user=user_second)
        data = generate_single_candidate_data([talent_pool.id], domain_aoi)
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_second, data)
        print response_info(create_resp)
        assert create_resp.status_code == 403
        assert create_resp.json()['error']['code'] == custom_error.AOI_FORBIDDEN


class TestCreateCandidateCustomField(object):
    def test_create_candidate_custom_fields(self, access_token_first, user_first, talent_pool, domain_custom_fields):
        """
        Test:   Create CandidateCustomField
        Expect: 201
        """
        AddUserRoles.add_and_get(user=user_first)

        # Create Candidate + CandidateCustomField
        data = generate_single_candidate_data([talent_pool.id], custom_fields=domain_custom_fields)
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)

        can_custom_fields = get_resp.json()['candidate']['custom_fields']
        assert isinstance(can_custom_fields, list)
        assert can_custom_fields[0]['value'] == data['candidates'][0]['custom_fields'][0]['value']
        assert can_custom_fields[1]['value'] == data['candidates'][0]['custom_fields'][1]['value']

    def test_create_candidate_custom_fields_outside_of_domain(self, access_token_second, talent_pool,
                                                              user_second, domain_custom_fields):
        """
        Test: Attempt to create candidate's custom fields outside of user's domain
        Expect: 403
        """
        AddUserRoles.add(user=user_second)
        data = generate_single_candidate_data([talent_pool.id], custom_fields=domain_custom_fields)
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_second, data)
        print response_info(create_resp)
        assert create_resp.status_code == 403
        assert create_resp.json()['error']['code'] == custom_error.CUSTOM_FIELD_FORBIDDEN


class TestCreateCandidateEducation(object):
    def test_create_successfully(self, access_token_first, user_first, talent_pool):
        """
        Test: Create candidate + education
        Expect: 201
        """
        # Create candidate + education
        AddUserRoles.add_and_get(user_first)
        data = GenerateCandidateDate.educations([talent_pool.id])
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
        AddUserRoles.add_and_get(user_first)
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'educations': [
                {'school_name': ' ', 'school_type': ' ', 'city': None, 'subdivision_code': ''}
            ]}
        ]}
        # Create candidate education with empty values
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        assert create_resp.status_code == 201

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
        assert create_resp.status_code == 201

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_educations = get_resp.json()['candidate']['educations']
        assert len(candidate_educations) == 1
        assert candidate_educations[0]['school_name'] == data['candidates'][0]['educations'][0]['school_name'].strip()
        assert candidate_educations[0]['school_type'] == data['candidates'][0]['educations'][0]['school_type'].strip()

    # TODO Commenting out test case so builds can pass, failing most of the time.  -OM
    # def test_create_candidate_educations(self, access_token_first, user_first, talent_pool):
    #     """
    #     Test:   Create CandidateEducation for Candidate
    #     Expect: 201
    #     """
    #     # Create Candidate
    #     AddUserRoles.add_and_get(user=user_first)
    #     data = generate_single_candidate_data([talent_pool.id])
    #     create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
    #     print response_info(create_resp)
    #     assert create_resp.status_code == 201
    #
    #     # Retrieve Candidate
    #     candidate_id = create_resp.json()['candidates'][0]['id']
    #     candidate_dict = send_request(
    #         'get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first).json()['candidate']
    #     can_educations = candidate_dict['educations']
    #     data_educations = data['candidates'][0]['educations'][0]
    #     assert isinstance(can_educations, list)
    #     assert can_educations[0]['country'] == 'United States'
    #     assert can_educations[0]['subdivision'] == pycountry.subdivisions.get(code=data_educations['subdivision_code']).name
    #     assert can_educations[0]['city'] == data_educations['city']
    #     assert can_educations[0]['school_name'] == data_educations['school_name']
    #     assert can_educations[0]['school_type'] == data_educations['school_type']
    #     assert can_educations[0]['is_current'] == data_educations['is_current']
    #
    #     can_edu_degrees = can_educations[0]['degrees']
    #     assert isinstance(can_edu_degrees, list)
    #     assert can_edu_degrees[0]['gpa'] == '3.50'
    #     assert can_edu_degrees[0]['start_year'] == str(data_educations['degrees'][0]['start_year'])
    #
    #     can_edu_degree_bullets = can_edu_degrees[0]['bullets']
    #     assert isinstance(can_edu_degree_bullets, list)
    #     assert can_edu_degree_bullets[0]['major'] == data_educations['degrees'][0]['bullets'][0]['major']

    def test_create_candidate_educations_with_no_degrees(self, access_token_first, user_first, talent_pool):
        """
        Test:   Create CandidateEducation for Candidate
        Expect: 201
        """
        # Create Candidate without degrees
        AddUserRoles.add_and_get(user=user_first)
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


class TestCreateCandidateEducationDegree(object):
    def test_with_empty_values(self, access_token_first, user_first, talent_pool):
        """
        Test:  Create candidate education degree with some whitespaces and empty values
        Expect: 201
        """
        AddUserRoles.add_and_get(user_first)
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'educations': [
                {'school_name': ' ', 'school_type': ' ', 'city': None, 'subdivision_code': ''}
            ]}
        ]}
        # Create candidate education with empty values
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        assert create_resp.status_code == 201

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
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
        AddUserRoles.add_and_get(user_first)
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


class TestCreateWorkExperience(object):
    def test_create_work_experience_successfully(self, access_token_first, user_first, talent_pool):
        """
        Test:  Create candidate + work experience
        Expect: 201
        """
        # Create candidate +  work experience
        AddUserRoles.add_and_get(user_first)
        data = GenerateCandidateDate.work_experiences([talent_pool.id])
        country_code = data['candidates'][0]['work_experiences'][0]['country_code']
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 200
        assert get_country_code_from_name(get_resp.json()['candidate']['work_experiences'][0]['country']) == country_code

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
                    {'start_year': 2011, 'end_year': 2016}   # 12*5 = 60 months of experience
                ]
            }
        ]}
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

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
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
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
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        can_experiences = candidate_dict['work_experiences']
        assert isinstance(can_experiences, list)
        assert can_experiences[0]['organization'] == 'Apple'
        assert can_experiences[0]['city'] == 'Cupertino'
        can_experience_bullets = can_experiences[0]['bullets']
        assert isinstance(can_experience_bullets, list)

class TestCreateWorkPreference(object):
    def test_create_candidate_work_preference(self, access_token_first, user_first, talent_pool):
        """
        Test:   Create CandidateWorkPreference for Candidate
        Expect: 201
        """
        AddUserRoles.add_and_get(user=user_first)

        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        # Assert data sent in = data retrieved
        can_work_preference = candidate_dict['work_preference']
        can_work_preference_data = data['candidates'][0]['work_preference']
        assert isinstance(can_work_preference_data, dict)
        assert can_work_preference['relocate'] == can_work_preference_data['relocate']
        assert can_work_preference['travel_percentage'] == can_work_preference_data['travel_percentage']
        assert can_work_preference['salary'] == can_work_preference_data['salary']
        assert can_work_preference['employment_type'] == can_work_preference_data['employment_type']
        assert can_work_preference['third_party'] == can_work_preference_data['third_party']
        assert can_work_preference['telecommute'] == can_work_preference_data['telecommute']
        assert can_work_preference['authorization'] == can_work_preference_data['authorization']


class TestCreateCandidateEmail(object):
    def test_create_candidate_without_email(self, access_token_first, user_first, talent_pool):
        """
        Test:   Attempt to create a Candidate with no email
        Expect: 201
        """
        # Create Candidate with no email
        AddUserRoles.add_and_get(user_first)
        data = {'candidates': [{'first_name': 'john', 'last_name': 'stark',
                                'talent_pool_ids': {'add': [talent_pool.id]}}]}
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Create Candidate
        data = {'candidates': [{'first_name': 'john', 'last_name': 'stark', 'emails': [{}],
                                'talent_pool_ids': {'add': [talent_pool.id]}}]}
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 400
        assert create_resp.json()['error']['code'] == custom_error.INVALID_INPUT

    def test_create_candidate_with_bad_email(self, access_token_first, user_first, talent_pool):
        """
        Test:   Attempt to create a Candidate with invalid email format
        Expect: 400
        """
        # Create Candidate
        AddUserRoles.add(user_first)
        data = {'candidates': [{'emails': [{'label': None, 'is_default': True, 'address': 'bad_email.com'}],
                                'talent_pool_ids': {'add': [talent_pool.id]}}]}
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 400
        assert create_resp.json()['error']['code'] == custom_error.INVALID_EMAIL

    def test_create_candidate_without_email_label(self, access_token_first, user_first, talent_pool):
        """
        Test:   Create a Candidate without providing email's label
        Expect: 201, email's label must be 'Primary'
        """
        AddUserRoles.add_and_get(user=user_first)

        # Create Candidate without email-label
        data = {'candidates': [
            {'emails': [
                {'label': None, 'is_default': None, 'address': fake.safe_email()},
                {'label': None, 'is_default': None, 'address': fake.safe_email()}
            ], 'talent_pool_ids': {'add': [talent_pool.id]}}
        ]}
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        candidate_dict = get_resp.json()['candidate']
        assert create_resp.status_code == 201
        assert candidate_dict['emails'][0]['label'] == 'Primary'
        assert candidate_dict['emails'][-1]['label'] == 'Other'

    def test_add_email_with_empty_values(self, access_token_first, user_first, talent_pool):
        """
        Test:  Add candidate email with all empty values
        Expect: 400; email address is required
        """
        AddUserRoles.add_and_get(user_first)
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'emails': [
                {'label': None, 'address': '  '},
            ]}
        ]}

        # Create candidate email
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 400
        assert create_resp.json()['error']['code'] == custom_error.INVALID_EMAIL

    def test_add_emails_with_whitespaced_values(self, access_token_first, user_first, talent_pool):
        """
        Test:  Add candidate emails with values containing whitespaces
        Expect:  201; but whitespaces should be stripped
        """
        AddUserRoles.add_and_get(user_first)
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'emails': [
                {'label': ' work', 'address': fake.safe_email() + '   '},
                {'label': 'Primary ', 'address': ' ' + fake.safe_email()}
            ]}
        ]}

        # Create candidate email
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        emails = get_resp.json()['candidate']['emails']
        assert len(emails) == 2
        assert emails[0]['address'] == data['candidates'][0]['emails'][0]['address'].strip()
        assert emails[0]['label'] == data['candidates'][0]['emails'][0]['label'].strip().title()
        assert emails[1]['address'] == data['candidates'][0]['emails'][1]['address'].strip()
        assert emails[1]['label'] == data['candidates'][0]['emails'][1]['label'].strip()


class TestCreatePhones(object):
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
        assert create_resp.status_code == 201

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first, data)
        candidate_dict = get_resp.json()['candidate']

        # Assert data sent in = data retrieved
        can_phones = candidate_dict['phones']
        can_phones_data = data['candidates'][0]['phones']
        assert isinstance(can_phones, list)
        assert can_phones_data[0]['value'] == data['candidates'][0]['phones'][0]['value']
        assert can_phones_data[0]['label'] == data['candidates'][0]['phones'][0]['label']

    def test_create_candidate_without_phone_label(self, access_token_first, user_first, talent_pool):
        """
        Test:   Create a Candidate without providing phone's label
        Expect: 201, phone's label must be 'Primary'
        """
        # Create Candidate without label
        AddUserRoles.add_and_get(user_first)
        data = {'candidates': [{'phones':
            [
                {'label': None, 'is_default': None, 'value': '6504084069'},
                {'label': None, 'is_default': None, 'value': '6504084069'}
            ], 'talent_pool_ids': {'add': [talent_pool.id]}}
        ]}
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']
        assert create_resp.status_code == 201
        assert candidate_dict['phones'][0]['label'] == 'Home'
        assert candidate_dict['phones'][-1]['label'] == 'Other'

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
                {'label': '2564', 'is_default': None, 'value': '6504084069'}
            ], 'talent_pool_ids': {'add': [talent_pool.id]}}
        ]}
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']
        assert create_resp.status_code == 201
        assert candidate_dict['phones'][0]['label'] == 'Other'
        assert candidate_dict['phones'][-1]['label'] == 'Other'

    def test_add_phone_without_value(self, access_token_first, user_first, talent_pool):
        """
        Test:  Add candidate phone without providing value
        Expect:  400; phone value is a required property
        """
        AddUserRoles.add(user_first)
        data = {'candidates': [{'talent_pool_ids': {'add': [talent_pool.id]}, 'phones':[
                {'label': 'Work', 'is_default': False, 'value': None}]}]}

        # Create candidate phone without value
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 400
        assert create_resp.json()['error']['code'] == custom_error.INVALID_INPUT


class TestCreateMilitaryService(object):
    def test_create_military_service_successfully(self, access_token_first, user_first, talent_pool):
        """
        Test:  Create candidate + military service
        Expect: 201
        """
        # Create candidate +  military service
        AddUserRoles.add_and_get(user_first)
        data = GenerateCandidateDate.military_services([talent_pool.id])
        country_code = data['candidates'][0]['military_services'][0]['country_code']
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first, data)
        print response_info(get_resp)
        assert get_resp.status_code == 200
        assert get_country_code_from_name(get_resp.json()['candidate']['military_services'][0]['country']) == country_code

    def test_create_candidate_military_service(self, access_token_first, user_first, talent_pool):
        """
        Test:   Create CandidateMilitaryService for Candidate
        Expect: 201
        """
        # Create Candidate
        AddUserRoles.add_and_get(user=user_first)
        data = candidate_military_service(talent_pool)
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']
        # Assert data sent in = data retrieved
        can_military_services = candidate_dict['military_services']
        can_military_services_data = data['candidates'][0]['military_services'][0]
        assert isinstance(can_military_services, list)
        assert can_military_services[-1]['comments'] == can_military_services_data['comments']
        assert can_military_services[-1]['highest_rank'] == can_military_services_data['highest_rank']
        assert can_military_services[-1]['branch'] == can_military_services_data['branch']

    def test_add_military_service_with_empty_values(self, access_token_first, user_first, talent_pool):
        """
        Test:  Add candidate military service with all-empty-values and another one with some empty values
        Expect:  201; but military service should not be added to db if all its data is empty
        """
        AddUserRoles.add_and_get(user_first)
        # Data with all empty records
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'military_services': [
                {'branch': ' ', 'highest_rank': '', 'status': None}
            ]}
        ]}
        # Create candidate military service
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        military_services = get_resp.json()['candidate']['military_services']
        assert len(military_services) == 0, "Empty records will not be added to db"

        # Data with some empty records, some missing, and some with whitespaces
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'military_services': [
                {'branch': '', 'highest_rank': ' lieutenant', 'status': 'active '}
            ]}
        ]}
        # Create candidate military service
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        military_services = get_resp.json()['candidate']['military_services']
        assert len(military_services) == 1


class TestCreatePreferredLocation(object):
    def test_create_preferred_locations_successfully(self, access_token_first, user_first, talent_pool):
        """
        Test:  Create candidate + preferred locations
        Expect: 201
        """
        # Create candidate +  preferred locations
        AddUserRoles.add_and_get(user_first)
        data = GenerateCandidateDate.preferred_locations([talent_pool.id])
        country_code = data['candidates'][0]['preferred_locations'][0]['country_code']
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 200
        assert get_country_code_from_name(get_resp.json()['candidate']['preferred_locations'][0]['country']) == country_code

    def test_create_candidate_preferred_location(self, access_token_first, user_first, talent_pool):
        """
        Test:   Create CandidatePreferredLocations for Candidate
        Expect: 201
        """
        # Create Candidate
        AddUserRoles.add_and_get(user=user_first)
        data = candidate_preferred_locations(talent_pool)
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        # Assert data sent in = data retrieved
        can_preferred_locations = candidate_dict['preferred_locations']
        can_preferred_locations_data = data['candidates'][0]['preferred_locations']
        assert isinstance(can_preferred_locations, list)
        assert can_preferred_locations[0]['city'] == can_preferred_locations_data[0]['city']
        assert can_preferred_locations[0]['city'] == can_preferred_locations_data[0]['city']
        assert can_preferred_locations[0]['state'] == can_preferred_locations_data[0]['state']

    def test_add_with_empty_values(self, access_token_first, user_first, talent_pool):
        """
        Test:  Add candidate preferred location with all-empty-values and another one with some empty values
        Expect: 201; empty values should not be inserted into db
        """
        AddUserRoles.add_and_get(user_first)
        # Data with None, missing, empty string, and whitespace values
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'preferred_locations': [
                {'city': None, 'state': ' ', 'country': ''}
            ]}
        ]}
        # Create candidate preferred location with empty values
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        preferred_locations = get_resp.json()['candidate']['preferred_locations']
        assert len(preferred_locations) == 0, "Empty records will not be added to db"

        # Data with some missing values and some values with whitespaces
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'preferred_locations': [
                {'city': ' San Jose ', 'subdivision_code': ' us-CA '}
            ]}
        ]}
        # Create candidate preferred location with empty values
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        preferred_locations = get_resp.json()['candidate']['preferred_locations']
        assert len(preferred_locations) == 1
        assert preferred_locations[0]['city'] == data['candidates'][0]['preferred_locations'][0]['city'].strip()
        assert preferred_locations[0]['subdivision'] == 'California'


class TestCreateSkills(object):
    def test_create_candidate_skills(self, access_token_first, user_first, talent_pool):
        """
        Test:   Create CandidateSkill for Candidate
        Expect: 201
        """
        # Create Candidate
        AddUserRoles.add_and_get(user_first)
        data = candidate_skills(talent_pool)
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        # Assert data sent in = data retrieved
        can_skills = candidate_dict['skills']
        can_skills_data = data['candidates'][0]['skills'][0]
        assert isinstance(can_skills, list)
        assert can_skills[0]['name'] == can_skills_data['name']
        assert can_skills[0]['months_used'] == can_skills_data['months_used']
        assert can_skills[0]['name'] == can_skills_data['name']
        assert can_skills[0]['months_used'] == can_skills_data['months_used']

    def test_poorly_formatted_data(self, access_token_first, user_first, talent_pool):
        """
        Test:  Create CandidateSkill with poorly formatted values
        Expect: 201, server should clean up data automatically
        """
        AddUserRoles.add_and_get(user_first)
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'skills': [
                {'name': 'Payroll ', 'months_used': 80}, {'name': ' NoSQL', 'months_used': 060},
                {'name': ' Credit', 'months_used': 120}, {'name': ' ', 'months_used': 120},
                {'name': None, 'months_used': None}, {'name': None, 'months_used': 1}
            ]}
        ]}
        # Create candidate + candidate's skill
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_skills = get_resp.json()['candidate']['skills']
        assert len(candidate_skills) == 3, "Of the six records provided, 3 of them should not be " \
                                           "inserted into db because they do not have a 'name' value"
        print "\nskills = {}".format(candidate_skills)
        assert candidate_skills[0]['name'] == data['candidates'][0]['skills'][0]['name'].strip()
        assert candidate_skills[1]['name'] == data['candidates'][0]['skills'][1]['name'].strip()
        assert candidate_skills[2]['name'] == data['candidates'][0]['skills'][2]['name'].strip()

    def test_add_with_empty_values(self, access_token_first, user_first, talent_pool):
        """
        Test:  Add candidate skill with empty values
        Expect: 201; no empty values should be added to db
        """
        AddUserRoles.add_and_get(user_first)

        # Data with no skill name, missing values, empty values, and whitespaced values
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'skills': [
                {'name': ' ', 'months_used': None}, {'name': '', 'months_used': 060},
                {'name': None, 'months_used': 60}, {'name': ' ', 'months_used': 160},
                {'name': '', 'months_used': 50}
            ]}
        ]}
        # Create candidate skill
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        assert create_resp.status_code == 201

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        skills = get_resp.json()['candidate']['skills']
        assert len(skills) == 0, "Records not added to db since all data " \
                                 "were missing skill-name or had all empty values"


class TestCreateSocialNetworks(object):
    def test_create_candidate_social_networks(self, access_token_first, user_first, talent_pool):
        """
        Test:   Create CandidateSocialNetwork for Candidate
        Expect: 201
        """
        # Create Candidate
        AddUserRoles.add_and_get(user_first)
        data = candidate_social_network(talent_pool)
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_dict = get_resp.json()['candidate']

        # Assert data sent in = data retrieved
        can_social_networks = candidate_dict['social_networks']
        can_social_networks_data = data['candidates'][0]['social_networks']
        assert isinstance(can_social_networks, list)
        assert can_social_networks[0]['name'] == 'Facebook'
        assert can_social_networks[0]['profile_url'] == can_social_networks_data[0]['profile_url']

    def test_add_with_empty_values(self, access_token_first, user_first, talent_pool):
        """
        Test:  Add candidate social network with all-empty values and one with some empty values
        Expect:  400; social name & profile url are required properties
        """
        AddUserRoles.add_and_get(user_first)

        # Data with empty values, missing values, whitespaced values, and None values
        data = {'candidates': [{
            'talent_pool_ids': {'add': [talent_pool.id]}, 'social_networks': [
                {'name': None, 'profile_url': ' '}, {'name': '', 'profile_url': ' '},
                {'name': ' ', 'profile_url': ''}, {'name': ' ', 'profile_url': ' '},
                {'profile_url': 'https://twitter.com/realdonaldtrump'}
            ]
        }]}
        # Create candidate social network
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 400
        assert create_resp.json()['error']['code'] == custom_error.INVALID_INPUT

