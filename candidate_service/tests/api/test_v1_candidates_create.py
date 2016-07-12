"""
Test cases for CandidateResource/post()
"""
# Candidate Service app instance
from candidate_service.candidate_app import app

import time

# Conftest
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import AddUserRoles, get_country_code_from_name, order_military_services, order_work_experiences
from candidate_service.common.routes import CandidateApiUrl
from candidate_service.common.utils.test_utils import send_request, response_info
from candidate_service.common.utils.validators import get_phone_number_extension_if_exists
from candidate_service.common.utils.iso_standards import get_country_name

# Sample data
from candidate_sample_data import (
    GenerateCandidateData, generate_single_candidate_data, candidate_phones, candidate_military_service,
    candidate_preferred_locations, candidate_skills, candidate_social_network
)

# Models
from candidate_service.common.models.candidate import CandidateEmail

# Custom errors
from candidate_service.custom_error_codes import CandidateCustomErrors as candidate_errors
from auth_service.custom_error_codes import AuthServiceCustomErrorCodes as auth_errors

CANDIDATES_URL = CandidateApiUrl.CANDIDATES
CANDIDATE_URL = CandidateApiUrl.CANDIDATE

class CommonData(object):
    @staticmethod
    def data(talent_pool_):
        return {'candidates': [
            {
                'emails': [{'address': fake.safe_email()}],
                'talent_pool_ids': {'add': [talent_pool_.id]}
            }
        ]}


class TestCreateCandidateSuccessfully(object):
    """
    Class contains functional tests that are expected to create candidate(s) successfully
    """
    def test_create_candidate_with_all_fields(self, access_token_first, user_first, talent_pool,
                                              domain_aois, domain_custom_fields):
        """
        Test:  Create candidate with all fields populated and assert on every data retrieved
        """
        AddUserRoles.add_and_get(user_first)

        # Generate candidate's data
        data = generate_single_candidate_data([talent_pool.id], areas_of_interest=domain_aois,
                                              custom_fields=domain_custom_fields)

        # Create candidate with all fields accepted by the endpoint
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED
        assert create_resp.json()['candidates'][0]['id']  # candidate's ID must be provided

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CANDIDATE_URL % candidate_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.OK

        # Assert on created candidate's data
        data_sent_in = data['candidates'][0]
        candidate_data = get_resp.json()['candidate']

        # Candidate's primary information
        assert candidate_data['id'] == candidate_id
        assert candidate_data['first_name'] == data_sent_in['first_name']
        assert candidate_data['middle_name'] == data_sent_in['middle_name']
        assert candidate_data['last_name'] == data_sent_in['last_name']
        assert candidate_data['full_name'] == data_sent_in['first_name'] + ' ' + data_sent_in['middle_name'] + ' ' \
                                              + data_sent_in['last_name']
        assert candidate_data['owner_id'] == user_first.id
        assert candidate_data['status_id'] == data_sent_in['status_id']
        assert candidate_data['objective'] == data_sent_in['objective']
        assert candidate_data['summary'] == data_sent_in['summary']
        # assert candidate_data['resume_url'] == data_sent_in['resume_url']  # TODO: point to s3 bucket

        # Candidate's addresses
        addresses = candidate_data['addresses']
        assert isinstance(addresses, list)
        assert addresses[0]['id']
        assert addresses[0]['address_line_1'] == data_sent_in['addresses'][0]['address_line_1']
        assert addresses[0]['address_line_2'] == data_sent_in['addresses'][0]['address_line_2']
        assert addresses[0]['city'] == data_sent_in['addresses'][0]['city']
        assert addresses[0]['state'] == data_sent_in['addresses'][0]['state']
        assert addresses[0]['country'] == get_country_name(data_sent_in['addresses'][0]['country_code'])
        assert addresses[0]['po_box'] == data_sent_in['addresses'][0]['po_box']
        assert addresses[0]['zip_code'] == data_sent_in['addresses'][0]['zip_code']
        assert addresses[0]['is_default'] == data_sent_in['addresses'][0]['is_default']
        assert addresses[1]['id']
        assert addresses[1]['address_line_1'] == data_sent_in['addresses'][1]['address_line_1']
        assert addresses[1]['address_line_2'] == data_sent_in['addresses'][1]['address_line_2']
        assert addresses[1]['city'] == data_sent_in['addresses'][1]['city']
        assert addresses[1]['state'] == data_sent_in['addresses'][1]['state']
        assert addresses[1]['country'] == get_country_name(data_sent_in['addresses'][1]['country_code'])
        assert addresses[1]['po_box'] == data_sent_in['addresses'][1]['po_box']
        assert addresses[1]['zip_code'] == data_sent_in['addresses'][1]['zip_code']
        assert addresses[1]['is_default'] == data_sent_in['addresses'][1]['is_default']

        # Candidate's areas of interests
        areas_of_interest = candidate_data['areas_of_interest']
        assert isinstance(areas_of_interest, list)
        assert areas_of_interest[0]['id'] == data_sent_in['areas_of_interest'][0]['area_of_interest_id']
        assert areas_of_interest[1]['id'] == data_sent_in['areas_of_interest'][1]['area_of_interest_id']

        # Candidate's custom fields
        custom_fields = candidate_data['custom_fields']
        assert isinstance(custom_fields, list)
        assert custom_fields[0]['value'] == data_sent_in['custom_fields'][0]['value']
        assert custom_fields[0]['custom_field_id'] == data_sent_in['custom_fields'][0]['custom_field_id']
        assert custom_fields[1]['value'] == data_sent_in['custom_fields'][1]['value']
        assert custom_fields[1]['custom_field_id'] == data_sent_in['custom_fields'][1]['custom_field_id']

        # Candidate's educations
        educations = candidate_data['educations']
        assert isinstance(educations, list)
        assert educations[0]['id']
        assert educations[0]['city'] == data_sent_in['educations'][0]['city']
        assert educations[0]['country'] == get_country_name(data_sent_in['educations'][0]['country_code'])
        assert educations[0]['is_current'] == data_sent_in['educations'][0]['is_current']
        assert educations[0]['school_name'] == data_sent_in['educations'][0]['school_name']
        assert educations[0]['school_type'] == data_sent_in['educations'][0]['school_type']
        assert educations[0]['state'] == data_sent_in['educations'][0]['state']
        assert educations[0]['degrees'][0]['id']
        assert educations[0]['degrees'][0]['title'] == data_sent_in['educations'][0]['degrees'][0]['title']
        assert educations[0]['degrees'][0]['type'] == data_sent_in['educations'][0]['degrees'][0]['type']
        assert educations[0]['degrees'][0]['gpa'] == '{0:.2f}'.format(data_sent_in['educations'][0]['degrees'][0]['gpa'])
        assert educations[0]['degrees'][0]['start_year'] == str(data_sent_in['educations'][0]['degrees'][0]['start_year'])
        assert educations[0]['degrees'][0]['start_year'] == str(data_sent_in['educations'][0]['degrees'][0]['start_year'])
        assert educations[0]['degrees'][0]['start_month'] == str(data_sent_in['educations'][0]['degrees'][0]['start_month'])
        assert educations[0]['degrees'][0]['end_year'] == str(data_sent_in['educations'][0]['degrees'][0]['end_year'])
        assert educations[0]['degrees'][0]['end_month'] == str(data_sent_in['educations'][0]['degrees'][0]['end_month'])
        assert educations[0]['degrees'][0]['bullets'][0]['id']
        assert educations[0]['degrees'][0]['bullets'][0]['major'] == data_sent_in['educations'][0]['degrees'][0]['bullets'][0]['major']
        assert educations[0]['degrees'][0]['bullets'][0]['comments'] == data_sent_in['educations'][0]['degrees'][0]['bullets'][0]['comments']
        assert educations[1]['id']
        assert educations[1]['city'] == data_sent_in['educations'][1]['city']
        assert educations[1]['country'] == get_country_name(data_sent_in['educations'][1]['country_code'])
        assert educations[1]['is_current'] == data_sent_in['educations'][1]['is_current']
        assert educations[1]['school_name'] == data_sent_in['educations'][1]['school_name']
        assert educations[1]['school_type'] == data_sent_in['educations'][1]['school_type']
        assert educations[1]['state'] == data_sent_in['educations'][1]['state']
        assert educations[1]['degrees'][0]['id']
        assert educations[1]['degrees'][0]['title'] == data_sent_in['educations'][1]['degrees'][0]['title']
        assert educations[1]['degrees'][0]['type'] == data_sent_in['educations'][1]['degrees'][0]['type']
        assert educations[1]['degrees'][0]['gpa'] == '{0:.2f}'.format(data_sent_in['educations'][1]['degrees'][0]['gpa'])
        assert educations[1]['degrees'][0]['start_year'] == str(data_sent_in['educations'][1]['degrees'][0]['start_year'])
        assert educations[1]['degrees'][0]['start_year'] == str(data_sent_in['educations'][1]['degrees'][0]['start_year'])
        assert educations[1]['degrees'][0]['start_month'] == str(data_sent_in['educations'][1]['degrees'][0]['start_month'])
        assert educations[1]['degrees'][0]['end_year'] == str(data_sent_in['educations'][1]['degrees'][0]['end_year'])
        assert educations[1]['degrees'][0]['end_month'] == str(data_sent_in['educations'][1]['degrees'][0]['end_month'])
        assert educations[1]['degrees'][0]['bullets'][0]['id']
        assert educations[1]['degrees'][0]['bullets'][0]['major'] == data_sent_in['educations'][1]['degrees'][0]['bullets'][0]['major']
        assert educations[1]['degrees'][0]['bullets'][0]['comments'] == data_sent_in['educations'][1]['degrees'][0]['bullets'][0]['comments']

        # Candidate's phones
        phones = candidate_data['phones']
        assert isinstance(phones, list)
        assert phones[0]['id']
        assert phones[0]['label'] == data_sent_in['phones'][0]['label']
        parsed_number_from_data_sent_in = get_phone_number_extension_if_exists(data_sent_in['phones'][0]['value'])
        assert phones[0]['value'] == parsed_number_from_data_sent_in[0]
        assert phones[0]['extension'] == parsed_number_from_data_sent_in[2]
        assert phones[1]['id']
        assert phones[1]['label'] == data_sent_in['phones'][1]['label']
        assert phones[1]['value'] == data_sent_in['phones'][1]['value']  # second phone object does not have an extension

        # Candidate's emails
        emails = candidate_data['emails']
        assert isinstance(emails, list)
        assert emails[0]['id']
        assert emails[0]['address'] == data_sent_in['emails'][0]['address']
        assert emails[0]['label'] == data_sent_in['emails'][0]['label']
        assert emails[0]['is_default'] == data_sent_in['emails'][0]['is_default']
        assert emails[1]['id']
        assert emails[1]['address'] == data_sent_in['emails'][1]['address']
        assert emails[1]['label'] == data_sent_in['emails'][1]['label']
        assert emails[1]['is_default'] == data_sent_in['emails'][1]['is_default']
        assert emails[2]['id']
        assert emails[2]['address'] == data_sent_in['emails'][2]['address']
        assert emails[2]['label'] == data_sent_in['emails'][2]['label']
        assert emails[2]['is_default'] is None  # last email obj doesn't have is_default key

        # Candidate's Work Experience
        experiences = candidate_data['work_experiences']
        assert isinstance(experiences, list)
        # order of data returned depends on experience's is_current, start_year, and start_month values, respectively
        order_work_experiences(data_sent_in['work_experiences'])
        assert experiences[0]['id']
        assert experiences[0]['city'] == data_sent_in['work_experiences'][0]['city']
        assert experiences[0]['country'] == get_country_name(data_sent_in['work_experiences'][0]['country_code'])
        assert experiences[0]['is_current'] == data_sent_in['work_experiences'][0]['is_current']
        assert experiences[0]['state'] == data_sent_in['work_experiences'][0]['state']
        assert experiences[0]['organization'] == data_sent_in['work_experiences'][0]['organization']
        assert experiences[0]['position'] == data_sent_in['work_experiences'][0]['position']
        assert experiences[0]['bullets'][0]['id']
        assert experiences[0]['bullets'][0]['description'] == data_sent_in['work_experiences'][0]['bullets'][0]['description']
        assert experiences[1]['id']
        assert experiences[1]['city'] == data_sent_in['work_experiences'][1]['city']
        assert experiences[1]['country'] == get_country_name(data_sent_in['work_experiences'][1]['country_code'])
        assert experiences[1]['is_current'] == data_sent_in['work_experiences'][1]['is_current']
        assert experiences[1]['state'] == data_sent_in['work_experiences'][1]['state']
        assert experiences[1]['organization'] == data_sent_in['work_experiences'][1]['organization']
        assert experiences[1]['position'] == data_sent_in['work_experiences'][1]['position']
        assert experiences[1]['bullets'][0]['id']
        assert experiences[1]['bullets'][0]['description'] == data_sent_in['work_experiences'][1]['bullets'][0]['description']

        # Candidate's work preference
        work_preference = candidate_data['work_preference']
        assert isinstance(work_preference, dict)
        assert work_preference['id']
        assert work_preference['employment_type'] == data_sent_in['work_preference']['employment_type']
        assert work_preference['hourly_rate'] == data_sent_in['work_preference']['hourly_rate']
        assert work_preference['salary'] == data_sent_in['work_preference']['salary']
        assert work_preference['telecommute'] == data_sent_in['work_preference']['telecommute']
        assert work_preference['travel_percentage'] == data_sent_in['work_preference']['travel_percentage']

        # Candidate's military services
        military_services = candidate_data['military_services']
        # order of data return depends on to_date value
        order_military_services(data_sent_in['military_services'])
        assert isinstance(military_services, list)
        assert military_services[0]['id']
        assert military_services[0]['branch'] == data_sent_in['military_services'][0]['branch']
        assert military_services[0]['comments'] == data_sent_in['military_services'][0]['comments']
        assert military_services[0]['highest_rank'] == data_sent_in['military_services'][0]['highest_rank']
        assert military_services[0]['highest_grade'] == data_sent_in['military_services'][0]['highest_grade']
        assert military_services[0]['status'] == data_sent_in['military_services'][0]['status']
        assert military_services[0]['from_date'] == data_sent_in['military_services'][0]['from_date']
        assert military_services[0]['to_date'] == data_sent_in['military_services'][0]['to_date']
        assert military_services[0]['country'] == get_country_name(data_sent_in['military_services'][0]['country_code'])
        assert military_services[1]['id']
        assert military_services[1]['branch'] == data_sent_in['military_services'][1]['branch']
        assert military_services[1]['comments'] == data_sent_in['military_services'][1]['comments']
        assert military_services[1]['highest_rank'] == data_sent_in['military_services'][1]['highest_rank']
        assert military_services[1]['highest_grade'] == data_sent_in['military_services'][1]['highest_grade']
        assert military_services[1]['status'] == data_sent_in['military_services'][1]['status']
        assert military_services[1]['from_date'] == data_sent_in['military_services'][1]['from_date']
        assert military_services[1]['to_date'] == data_sent_in['military_services'][1]['to_date']
        assert military_services[1]['country'] == get_country_name(data_sent_in['military_services'][1]['country_code'])

        # Candidate's skills
        skills = candidate_data['skills']
        assert isinstance(skills, list)
        assert skills[0]['id']
        assert skills[0]['name'] == data_sent_in['skills'][0]['name']
        assert skills[0]['last_used_date'] == data_sent_in['skills'][0]['last_used_date']
        assert skills[0]['months_used'] == data_sent_in['skills'][0]['months_used']
        assert skills[1]['id']
        assert skills[1]['name'] == data_sent_in['skills'][1]['name']
        assert skills[1]['last_used_date'] == data_sent_in['skills'][1]['last_used_date']
        assert skills[1]['months_used'] == data_sent_in['skills'][1]['months_used']

        # Candidate's social networks
        social_networks = candidate_data['social_networks']
        assert isinstance(social_networks, list)
        assert social_networks[0]['id']
        assert social_networks[0]['name'] == data_sent_in['social_networks'][0]['name']
        assert social_networks[0]['profile_url'] == data_sent_in['social_networks'][0]['profile_url']
        assert social_networks[1]['id']
        assert social_networks[1]['name'] == data_sent_in['social_networks'][1]['name']
        assert social_networks[1]['profile_url'] == data_sent_in['social_networks'][1]['profile_url']

        # Candidate's preferred locations
        preferred_locations = candidate_data['preferred_locations']
        assert isinstance(preferred_locations, list)
        assert preferred_locations[0]['id']
        assert preferred_locations[0]['city'] == data_sent_in['preferred_locations'][0]['city']
        assert preferred_locations[0]['state'] == data_sent_in['preferred_locations'][0]['state']
        assert preferred_locations[0]['country'] == get_country_name(data_sent_in['preferred_locations'][0]['country_code'])
        assert preferred_locations[1]['id']
        assert preferred_locations[1]['city'] == data_sent_in['preferred_locations'][1]['city']
        assert preferred_locations[1]['state'] == data_sent_in['preferred_locations'][1]['state']
        assert preferred_locations[1]['country'] == get_country_name(data_sent_in['preferred_locations'][1]['country_code'])

    def test_add_candidate_with_names_and_talent_pool_id(self, user_first, access_token_first, talent_pool):
        """
        Test: Create a new candidate with only talent pool ID + candidate's names provided
        """
        AddUserRoles.add(user_first)

        # Create Candidate
        data = {'candidates': [
            {
                'first_name': fake.first_name(), 'last_name': fake.last_name(),
                'talent_pool_ids': {'add': [talent_pool.id]}
            }
        ]}
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED

    def test_add_candidate_with_names_and_talent_pool_id_and_resume_url(self, user_first, access_token_first,
                                                                        talent_pool):
        """
        Test: Create a new candidate with talent pool ID, candidate's names and resume url
        """
        AddUserRoles.add(user_first)

        # Create Candidate
        data = {'candidates': [
            {
                'first_name': fake.first_name(), 'last_name': fake.last_name(),
                'talent_pool_ids': {'add': [talent_pool.id]},
                'resume_url': fake.url()
            }
        ]}
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED


class TestCreateInvalidCandidates(object):
    """
    Class contains functional tests that will result in the following errors
        - json schema violation (400)
        - invalid data (400)
        - unauthorized access (401)
        - forbidden access (403)
        - non existing data (404)
    """
    def test_create_candidate_with_expired_token(self, access_token_first, user_first):
        """
        Test: Attempt to create a candidate using an expired bearer token
        Expect: 401; failed authentication
        """
        AddUserRoles.add(user_first)

        # Set access_token_first's expiration to 10 seconds ago
        token = Token.get_token(access_token_first)
        token.expires = datetime.fromtimestamp(time.time() - 10)
        db.session.commit()

        # Create candidate with expired access token
        data = {}  # since an error should be raised early on, the content of data is irrelevant
        resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(resp)
        assert resp.status_code == requests.codes.UNAUTHORIZED
        assert resp.json()['error']['code'] == auth_errors.TOKEN_EXPIRED

    def test_create_with_invalid_access_token(self, user_first):
        """
        Test: Attempt to create a candidate using an invalid access token
        Expect: 401; failed authentication
        """
        AddUserRoles.add(user_first)

        # Create candidate with invalid access token
        data = {}  # since an error should be raised early on, the content of data is irrelevant
        resp = send_request('post', CANDIDATES_URL, 'invalid_access_token', data)
        print response_info(resp)
        assert resp.status_code == requests.codes.UNAUTHORIZED
        assert resp.json()['error']['code'] == auth_errors.TOKEN_NOT_FOUND

    def test_create_candidate_with_empty_dict(self, user_first, access_token_first):
        """
        Test: Attempt to create a candidate without providing any content in data
        Expect: 400
        """
        AddUserRoles.add(user_first)

        # Create candidate with empty data
        data = {}
        resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        assert resp.status_code == requests.codes.BAD
        assert resp.json()['error']['code'] == candidate_errors.INVALID_INPUT

        # Create candidate with candidate key provided but no candidate data
        data = {'candidates': [{}]}
        resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        assert resp.status_code == requests.codes.BAD
        assert resp.json()['error']['code'] == candidate_errors.INVALID_INPUT

    def test_create_candidate_without_talent_pools(self, access_token_first, user_first):
        """
        Test: Attempt to create a candidate without providing talent pool IDs
        Expect: 400
        """
        AddUserRoles.add(user_first)

        # Create Candidate without providing talent pool ID
        data = {'candidates': [{'first_name': fake.first_name()}]}
        resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(response=resp)
        assert resp.status_code == requests.codes.BAD
        assert resp.json()['error']['code'] == candidate_errors.INVALID_INPUT

    def test_create_candidate_with_incorrect_value_for_source_id(self, user_first, access_token_first, talent_pool):
        """
        Test: Attempt to Create candidate by providing a string value for source ID
        Expect: 400
        """
        AddUserRoles.add(user_first)

        # Create candidate using non integer data type for source ID
        incorrect_data_types = ['2', 'string', [], {}, 5.3]
        data = {'candidates': [{
            'talent_pool_ids': {'add': [talent_pool.id]}, 'source_id': random.choice(incorrect_data_types)
        }]}

        resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(resp)
        assert resp.status_code == requests.codes.BAD
        assert resp.json()['error']['code'] == candidate_errors.INVALID_INPUT

    def test_create_candidate_with_incorrect_name_data_type(self, user_first, access_token_first, talent_pool):
        """
        Test: Attempt to create a candidate by using incorrect data type for candidate's names
        Expect: 400
        """
        AddUserRoles.add(user_first)

        # Create candidate using a non string value for candidate's names
        incorrect_data_types = [2, False, [], {}, 4.3]
        data = {'candidates': [{
            'talent_pool_ids': {'add': [talent_pool.id]}, 'full_name': random.choice(incorrect_data_types)
        }]}

        resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(resp)
        assert resp.status_code == requests.codes.BAD
        assert resp.json()['error']['code'] == candidate_errors.INVALID_INPUT

    def test_create_an_existing_candidate(self, access_token_first, user_first, talent_pool):
        """
        Test:   Attempt to recreate an existing Candidate
        Expect: 400
        """
        AddUserRoles.add(user_first)

        # Create same Candidate twice
        data = {'candidates': [{'emails': [{'address': fake.safe_email()}],
                                'talent_pool_ids': {'add': [talent_pool.id]}}]}
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED

        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.BAD
        assert create_resp.json()['error']['code'] == candidate_errors.CANDIDATE_ALREADY_EXISTS

    def test_create_candidate_without_providing_talent_pool_ids(self, access_token_first, user_first):
        """
        Test:   Create a Candidate without talent pool ID
        """
        AddUserRoles.add(user_first)

        # Data only has candidate's first name
        data = {'first_name': fake.first_name()}
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.BAD
        assert create_resp.json()['error']['code'] == candidate_errors.INVALID_INPUT

    def test_update_candidate_via_post(self, access_token_first, user_first):
        """
        Test:   Attempt to update a Candidate via post()
        """
        AddUserRoles.add(user_first)

        # Send Candidate object with candidate_id to post
        # candidate's ID is arbitrary since the API should raise an error early on
        candidate_id = random.randint(1, 100)
        data = {'candidates': [{'id': candidate_id, 'emails': [{'address': fake.safe_email()}]}]}
        resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(resp)
        assert resp.status_code == requests.codes.BAD
        assert resp.json()['error']['code'] == candidate_errors.INVALID_INPUT

    def test_create_candidate_with_invalid_fields(self, access_token_first, user_first, talent_pool):
        """
        Test:   Attempt to create a Candidate with bad fields/keys
        """
        AddUserRoles.add(user_first)

        # Create Candidate with invalid keys/fields
        data = {'candidates': [{'emails': [{'address': 'someone@nice.io'}], 'invalid_key': 'whatever',
                                'talent_pool_ids': {'add': [talent_pool.id]}}]}
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.BAD
        assert create_resp.json()['error']['code'] == candidate_errors.INVALID_INPUT

    def test_create_candidates_in_bulk_with_one_erroneous_data(self, access_token_first, user_first, talent_pool):
        """
        Test: Attempt to create few candidates, one of which will have bad data
        Expect: 400, no record should be added to the db
        """
        AddUserRoles.add(user_first)

        # Candidate data with one erroneous email address
        email_1, email_2 = fake.safe_email(), fake.safe_email()
        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'emails': [{'label': None, 'address': email_1}]},
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'emails': [{'label': None, 'address': email_2}]},
            {'talent_pool_ids': {'add': [talent_pool.id]},
             'emails': [{'label': None, 'address': 'bad_email_at_example.com'}]}
        ]}
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        db.session.commit()
        assert create_resp.status_code == requests.codes.BAD
        assert create_resp.json()['error']['code'] == candidate_errors.INVALID_EMAIL


class TestCreateHiddenCandidate(object):
    def test_create_hidden_candidate(self, access_token_first, user_first, talent_pool):
        """
        Test: Create a candidate that was previously web-hidden
        Expect: 201, candidate should no longer be web hidden.
                No duplicate records should be in the database
        """
        AddUserRoles.all_roles(user_first)

        # Create candidate
        data = CommonData.data(talent_pool)
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        candidate_id = create_resp.json()['candidates'][0]['id']
        db.session.commit()
        print response_info(create_resp)

        # Retrieve candidate's email
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        first_can_email = get_resp.json()['candidate']['emails'][0]

        # Hide candidate
        hide_data = {'candidates': [{'id': candidate_id, 'hide': True}]}
        hide_resp = send_request('patch', CANDIDATES_URL, access_token_first, hide_data)
        print response_info(hide_resp)
        candidate = Candidate.get(candidate_id)
        candidate_emails_count = len(candidate.emails)
        assert hide_resp.status_code == requests.codes.OK
        assert candidate.is_web_hidden

        # Create previously deleted candidate
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        db.session.commit()
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED
        assert not candidate.is_web_hidden
        assert CandidateEmail.get_by_address(first_can_email['address'])[0].id == first_can_email['id']
        assert len(candidate.emails) == candidate_emails_count

    def test_create_hidden_candidate_with_different_user_from_same_domain(
            self, access_token_first, user_first, user_same_domain, talent_pool):
        """
        Test: Create a candidate that was previously web-hidden with a different
              user from the same domain
        Expect: 201, candidate should no longer be web-hidden
        """
        AddUserRoles.all_roles(user_first)

        # Create candidate
        data = CommonData.data(talent_pool)
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        candidate_id = create_resp.json()['candidates'][0]['id']
        db.session.commit()

        # Retrieve candidate's email
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        first_can_email = get_resp.json()['candidate']['emails'][0]

        # Hide candidate
        hide_data = {'candidates': [{'id': candidate_id, 'hide': True}]}
        hide_resp = send_request('patch', CANDIDATES_URL, access_token_first, hide_data)
        print response_info(hide_resp)
        candidate = Candidate.get_by_id(candidate_id)
        candidate_emails_count = len(candidate.emails)
        assert hide_resp.status_code == requests.codes.OK
        assert candidate.is_web_hidden

        # Create previously hidden candidate with a different user from the same domain
        AddUserRoles.add(user_same_domain)
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED
        assert not candidate.is_web_hidden
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
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, CommonData.data(talent_pool))
        candidate_id = create_resp.json()['candidates'][0]['id']
        db.session.commit()
        print response_info(create_resp)

        # Retrieve candidate's first name
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_email = get_resp.json()['candidate']['emails'][0]
        full_name = get_resp.json()['candidate']['full_name']

        # Hide candidate
        hide_data = {'candidates': [{'id': candidate_id, 'hide': True}]}
        hide_resp = send_request('patch', CANDIDATES_URL, access_token_first, hide_data)
        print response_info(hide_resp)
        candidate = Candidate.get_by_id(candidate_id)
        assert hide_resp.status_code == requests.codes.OK
        assert candidate.is_web_hidden

        # Create previously deleted candidate
        data = {'candidates': [{'emails': [{'address': candidate_email['address']}], 'first_name': 'McLovin',
                                'talent_pool_ids': {'add': [talent_pool.id]}}]}
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        db.session.commit()
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED
        assert not candidate.is_web_hidden

        # Retrieve candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.OK
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
        create_resp_1 = send_request('post', CANDIDATES_URL, access_token_first, data_1)
        create_resp_2 = send_request('post', CANDIDATES_URL, access_token_second, data_2)
        print response_info(create_resp_1)
        print response_info(create_resp_2)
        candidate_id_1 = create_resp_1.json()['candidates'][0]['id']
        candidate_id_2 = create_resp_2.json()['candidates'][0]['id']

        # Hide candidate_1
        hide_data = {'candidates': [{'id': candidate_id_1, 'hide': True}]}
        hide_resp = send_request('patch', CANDIDATES_URL, access_token_first, hide_data)
        db.session.commit()
        print response_info(hide_resp)
        candidate = Candidate.get_by_id(candidate_id_1)
        assert candidate.is_web_hidden

        # Retrieve candidate_1
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id_1, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.NOT_FOUND
        assert get_resp.json()['error']['code'] == candidate_errors.CANDIDATE_IS_HIDDEN

        # Retrieve candidate_2
        get_resp_2 = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id_2, access_token_second)
        print response_info(response=get_resp_2)
        assert get_resp_2.status_code == requests.codes.OK

    def test_recreate_hidden_candidate_using_candidate_with_multiple_emails(self, access_token_first,
                                                                            user_first, talent_pool):
        # Create candidate
        AddUserRoles.all_roles(user_first)

        data = {'candidates': [
            {'talent_pool_ids': {'add': [talent_pool.id]}, 'emails': [
                {'address': fake.safe_email()}, {'address': fake.safe_email()}
            ]}
        ]}
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)

        # Hide candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        hide_data = {'candidates': [{'id': candidate_id, 'hide': True}]}
        hide_resp = send_request('patch', CANDIDATES_URL, access_token_first, hide_data)
        db.session.commit()
        print response_info(hide_resp)
        candidate = Candidate.get_by_id(candidate_id)
        assert candidate.is_web_hidden == 1

        # Re-create candidate
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED
        assert create_resp.json()['candidates'][0]['id'] == candidate_id


class TestCreateCandidateAddress(object):
    def test_create_candidate_address(self, access_token_first, user_first, talent_pool):
        """
        Test: Create new candidate + candidate-address
        Expect: 201
        """
        # Create Candidate with address
        AddUserRoles.add_and_get(user_first)
        data = GenerateCandidateData.addresses([talent_pool.id])
        country_code = data['candidates'][0]['addresses'][0]['country_code']
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.OK
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
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED

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
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_addresses = get_resp.json()['candidate']['addresses']
        assert len(candidate_addresses) == 1, "Only 1 of the addresses should be inserted into db, because" \
                                              "the rest had empty/None values"
        assert candidate_addresses[0]['address_line_1'] == data['candidates'][0]['addresses'][0][
            'address_line_1'].strip()
        assert candidate_addresses[0]['city'] == data['candidates'][0]['addresses'][0]['city'].strip()


class TestCreateAOI(object):
    def test_create_candidate_area_of_interest(self, access_token_first, user_first, talent_pool, domain_aois):
        """
        Test:   Create CandidateAreaOfInterest
        Expect: 201
        """
        AddUserRoles.add_and_get(user=user_first)

        # Create Candidate + CandidateAreaOfInterest
        data = generate_single_candidate_data(talent_pool_ids=[talent_pool.id], areas_of_interest=domain_aois)
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
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
                                                                 domain_aois, talent_pool):
        """
        Test: Attempt to create candidate's area of interest outside of user's domain
        Expect: 403
        """
        AddUserRoles.add(user=user_second)
        data = generate_single_candidate_data([talent_pool.id], domain_aois)
        create_resp = send_request('post', CANDIDATES_URL, access_token_second, data)
        print response_info(create_resp)
        assert create_resp.status_code == 403
        assert create_resp.json()['error']['code'] == candidate_errors.AOI_FORBIDDEN


class TestCreateCandidateCustomField(object):
    def test_create_candidate_custom_fields(self, access_token_first, user_first, talent_pool, domain_custom_fields):
        """
        Test:   Create CandidateCustomField
        Expect: 201
        """
        AddUserRoles.add_and_get(user=user_first)

        # Create Candidate + CandidateCustomField
        data = generate_single_candidate_data([talent_pool.id], custom_fields=domain_custom_fields)
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
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
        create_resp = send_request('post', CANDIDATES_URL, access_token_second, data)
        print response_info(create_resp)
        assert create_resp.status_code == 403
        assert create_resp.json()['error']['code'] == candidate_errors.CUSTOM_FIELD_FORBIDDEN


class TestCreateWorkPreference(object):
    def test_create_candidate_work_preference(self, access_token_first, user_first, talent_pool):
        """
        Test:   Create CandidateWorkPreference for Candidate
        Expect: 201
        """
        AddUserRoles.add_and_get(user=user_first)

        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED

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


class TestCreateMilitaryService(object):
    def test_create_military_service_successfully(self, access_token_first, user_first, talent_pool):
        """
        Test:  Create candidate + military service
        Expect: 201
        """
        # Create candidate +  military service
        AddUserRoles.add_and_get(user_first)
        data = GenerateCandidateData.military_services([talent_pool.id])
        country_code = data['candidates'][0]['military_services'][0]['country_code']
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first, data)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.OK
        assert get_country_code_from_name(
            get_resp.json()['candidate']['military_services'][0]['country']) == country_code

    def test_create_candidate_military_service(self, access_token_first, user_first, talent_pool):
        """
        Test:   Create CandidateMilitaryService for Candidate
        Expect: 201
        """
        # Create Candidate
        AddUserRoles.add_and_get(user=user_first)
        data = candidate_military_service(talent_pool)
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED

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
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED

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
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED

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
        data = GenerateCandidateData.preferred_locations([talent_pool.id])
        country_code = data['candidates'][0]['preferred_locations'][0]['country_code']
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED

        # Retrieve candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.OK
        assert get_country_code_from_name(
            get_resp.json()['candidate']['preferred_locations'][0]['country']) == country_code

    def test_create_candidate_preferred_location(self, access_token_first, user_first, talent_pool):
        """
        Test:   Create CandidatePreferredLocations for Candidate
        Expect: 201
        """
        # Create Candidate
        AddUserRoles.add_and_get(user=user_first)
        data = candidate_preferred_locations(talent_pool)
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED

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
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED

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
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED

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
        create_resp = send_request('post', CANDIDATES_URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == requests.codes.CREATED

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
        assert create_resp.status_code == requests.codes.CREATED

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        candidate_skills = get_resp.json()['candidate']['skills']
        assert len(candidate_skills) == 3, "Of the six records provided, 3 of them should not be " \
                                           "inserted into db because they do not have a 'name' value"

        print "\ncandidate_skills = {}".format(candidate_skills)
        print "\ndata_skills = {}".format(data['candidates'])

        candidate_skill_names = [skill['name'] for skill in candidate_skills]
        data_skill_names = [skill['name'] for skill in data['candidates'][0]['skills']]
        cleaned_data_skill_names = [skill.strip() for skill in data_skill_names if (skill or '').strip()]
        assert set(candidate_skill_names).issubset(cleaned_data_skill_names)

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
        assert create_resp.status_code == requests.codes.CREATED

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
        assert create_resp.status_code == requests.codes.CREATED

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
        assert create_resp.json()['error']['code'] == candidate_errors.INVALID_INPUT
