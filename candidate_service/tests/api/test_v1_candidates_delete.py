"""
Test cases for CandidateResource/delete()
"""
# Candidate Service app instance
from candidate_service.candidate_app import app

# Models
from candidate_service.common.models.user import User
from candidate_service.common.models.candidate import CandidateCustomField, CandidateEmail

# Conftest
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import (response_info, AddUserRoles)
from candidate_service.tests.api.candidate_sample_data import generate_single_candidate_data
from candidate_service.common.utils.test_utils import send_request

# Url
from candidate_service.common.routes import CandidateApiUrl

# Custom errors
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error


class TestDeleteCandidate(object):
    def test_delete_non_existing_candidate(self, access_token_first, user_first):
        """
        Test: Attempt to delete a candidate that isn't recognized via ID or Email
        Expect: 404
        """
        AddUserRoles.delete(user_first)
        last_candidate = Candidate.query.order_by(Candidate.id.desc()).first()
        non_existing_candidate_id = last_candidate.id * 100

        # Delete non existing candidate via ID
        resp = send_request('delete', CandidateApiUrl.CANDIDATE % non_existing_candidate_id, access_token_first)
        print response_info(resp)
        assert resp.status_code == 404
        assert resp.json()['error']['code'] == custom_error.CANDIDATE_NOT_FOUND

        # Delete non existing candidate via Email
        bogus_email = '{}_{}'.format(fake.word(), fake.safe_email())
        assert not CandidateEmail.get_by_address(email_address=bogus_email)

        resp = send_request('delete', CandidateApiUrl.CANDIDATE % bogus_email, access_token_first)
        print response_info(resp)
        assert resp.status_code == 404
        assert resp.json()['error']['code'] == custom_error.EMAIL_NOT_FOUND

    def test_delete_candidate_and_retrieve_it(self, access_token_first, user_first, talent_pool):
        """
        Test:   Delete a Candidate and then retrieve Candidate
        Expect: 404, Not Found error
        """
        # Create Candidate
        AddUserRoles.all_roles(user=user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Hide Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        hide_data = {'candidates': [{'id': candidate_id, 'hide': True}]}
        resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, hide_data)
        print response_info(resp)

        # Retrieve Candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 404
        assert get_resp.json()['error']['code'] == custom_error.CANDIDATE_IS_HIDDEN

    def test_delete_candidate_via_email(self, access_token_first, user_first, talent_pool):
        """
        Test:   Delete a Candidate via candidate's email
        Expect: 200
        """
        # Create Candidate
        AddUserRoles.all_roles(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']

        # Hide Candidate
        hide_data = {'candidates': [{'id': candidate_id, 'hide': True}]}
        resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, hide_data)
        print response_info(resp)
        assert resp.status_code == 200
        assert resp.json()['hidden_candidate_ids'][0] == candidate_id

    def test_delete_candidate_via_unrecognized_email(self, access_token_first, user_first):
        """
        Test:   "Delete" a Candidate via an email that does not exist in db
        Expect: 404
        """
        # Delete Candidate
        AddUserRoles.delete(user_first)
        candidate_email='email_not_found_45623@simple.com'
        resp = send_request('delete', CandidateApiUrl.CANDIDATE % candidate_email, access_token_first)
        print response_info(resp)
        assert resp.status_code == 404
        assert resp.json()['error']['code'] == custom_error.EMAIL_NOT_FOUND

    def test_delete_candidate_from_a_diff_domain(self, access_token_first, user_first, talent_pool,
                                                 access_token_second, user_second):
        """
        Test:   Delete a Candidate via candidate's email
        Expect: 200
        """
        AddUserRoles.all_roles(user_first)
        AddUserRoles.all_roles(user_second)

        # Create Candidate with user_first
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        candidate_1_id = create_resp.json()['candidates'][0]['id']

        # Retrieve Candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_1_id, access_token_first, data)
        candidate_dict = get_resp.json()['candidate']

        # Delete Candidate with user_second
        resp = send_request('delete', CandidateApiUrl.CANDIDATE % candidate_dict['id'], access_token_second)
        print response_info(resp)
        assert resp.status_code == 403
        assert resp.json()['error']['code'] == custom_error.CANDIDATE_FORBIDDEN


class TestDeleteCandidateAddress(object):
    def test_non_logged_in_user_delete_can_address(self):
        """
        Test:   Delete candidate's address without logging in
        Expect: 401
        """
        # Delete Candidate's addresses
        resp = send_request('delete', CandidateApiUrl.ADDRESSES % 5, None)
        print response_info(resp)
        assert resp.status_code == 401
        assert resp.json()['error']['code'] == 11

    def test_delete_candidate_address_with_bad_input(self):
        """
        Test:   Attempt to delete candidate address with non integer values for candidate_id & address_id
        Expect: 404
        """
        # Delete Candidate's addresses
        resp = send_request('delete', CandidateApiUrl.ADDRESSES % 'x', access_token_second)
        print response_info(resp)
        assert resp.status_code == 404

        # Delete Candidate's address
        resp = send_request('delete', CandidateApiUrl.ADDRESS % ('x', 6), access_token_second)
        print response_info(resp)
        assert resp.status_code == 404

    def test_delete_address_of_a_candidate_belonging_to_a_diff_user(
            self, access_token_first, user_first,talent_pool, user_same_domain, access_token_same):
        """
        Test:   Delete the address of a Candidate that belongs to a different user in the same domain
        Expect: 204
        """
        AddUserRoles.add(user_first)
        AddUserRoles.add_and_delete(user_same_domain)

        # Create candidate_1 & candidate_2 with user_first & user_first_2
        data = generate_single_candidate_data([talent_pool.id])
        create_resp_1 = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve candidate_1
        candidate_1_id = create_resp_1.json()['candidates'][0]['id']

        # Delete candidate_1's address with user_first_2 logged in
        updated_resp = send_request('delete', CandidateApiUrl.ADDRESSES % candidate_1_id, access_token_same)
        print response_info(updated_resp)
        assert updated_resp.status_code == 204

    def test_delete_address_of_a_diff_candidate(self, access_token_first, user_first, talent_pool):
        """
        Test:   Attempt to delete the address of a different Candidate
        Expect: 403
        """
        AddUserRoles.all_roles(user_first)
        data_1 = generate_single_candidate_data([talent_pool.id])
        data_2 = generate_single_candidate_data([talent_pool.id])

        # Create candidate_1 and candidate_2
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data_1)
        candidate_1_id = create_resp.json()['candidates'][0]['id']
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data_2)
        candidate_2_id = create_resp.json()['candidates'][0]['id']

        # Retrieve candidate_2's addresses
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_2_id, access_token_first)
        can_2_addresses = get_resp.json()['candidate']['addresses']

        # Delete candidate_2's id using candidate_1_id
        url = CandidateApiUrl.ADDRESS % (candidate_1_id, can_2_addresses[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403
        assert updated_resp.json()['error']['code'] == custom_error.ADDRESS_FORBIDDEN

    def test_delete_can_address(self, access_token_first, user_first, talent_pool):
        """
        Test:   Remove Candidate's address from db
        Expect: 204, Candidate's addresses must be less 1
        """
        # Create Candidate
        AddUserRoles.all_roles(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_addresses = get_resp.json()['candidate']['addresses']

        # Number of Candidate's addresses
        can_addresses_count = len(can_addresses)

        # Remove one of Candidate's addresses
        url = CandidateApiUrl.ADDRESS % (candidate_id, can_addresses[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']
        assert updated_resp.status_code == 204
        assert len(can_dict_after_update['addresses']) == can_addresses_count - 1

    def test_delete_all_of_candidates_addresses(self, access_token_first, user_first, talent_pool):
        """
        Test:   Remove all of candidate's addresses from db
        Expect: 204, Candidate should not have any addresses left
        """
        # Create Candidate
        AddUserRoles.all_roles(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Remove all of Candidate's addresses
        candidate_id = create_resp.json()['candidates'][0]['id']
        updated_resp = send_request('delete', CandidateApiUrl.ADDRESSES % candidate_id, access_token_first, data)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']

        assert updated_resp.status_code == 204
        assert len(can_dict_after_update['addresses']) == 0


####################### CandidateAreaOfInterest ########################
def test_non_logged_in_user_delete_can_aoi():
    """
    Test:   Delete candidate's aoi without logging in
    Expect: 401
    """
    # Delete Candidate's areas of interest
    resp = request_to_candidate_aoi_resource(None, 'delete', 5, True)
    print response_info(resp)
    assert resp.status_code == 401


def test_delete_candidate_aoi_with_bad_input():
    """
    Test:   Attempt to delete candidate aoi with non integer values for candidate_id & aoi_id
    Expect: 404
    """
    # Delete Candidate's areas of interest
    resp = request_to_candidate_aoi_resource(None, 'delete', candidate_id='x', all_aois=True)
    print response_info(resp)
    assert resp.status_code == 404

    # Delete Candidate's area of interest
    resp = request_to_candidate_aoi_resource(None, 'delete', candidate_id=5, aoi_id='x')
    print response_info(resp)
    assert resp.status_code == 404


def test_delete_can_aoi_of_a_candidate_belonging_to_a_diff_user(self, access_token_first, user_first,
                                                                talent_pool, user_second,
                                                                access_token_second):
    """
    Test:   Attempt to delete the aois of a Candidate that belongs to a user in a diff domain
    Expect: 204
    """
    AddUserRoles.add(user=user_first)
    AddUserRoles.delete(user=user_second)

    # Create candidate_1 & candidate_2 with user_first & user_first_2
    data = generate_single_candidate_data([talent_pool.id])
    create_resp_1 = request_to_candidates_resource(access_token_first, 'post', data)
    candidate_1_id = create_resp_1.json()['candidates'][0]['id']

    # Delete candidate_1's areas of interest with user_first_2 logged in
    updated_resp = request_to_candidate_aoi_resource(access_token_second, 'delete',
                                                     candidate_1_id, all_aois=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 403
    assert updated_resp.json()['error']['code'] == custom_error.CANDIDATE_FORBIDDEN


def test_delete_candidate_aoi_with_no_id(access_token_first, user_first, talent_pool):
    """
    Test:   Attempt to delete Candidate's aoi without providing area_of_interest_id
    Expect: 404
    """
    # Remove one of Candidate's areas of interest without an id
    candidate_id = 5 # This is arbitrary since a 404 is expected
    updated_resp = request_to_candidate_aoi_resource(access_token_first, 'delete', candidate_id)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_all_of_candidates_areas_of_interest(access_token_first, user_first,
                                                    talent_pool, domain_aoi):
    """
    Test:   Remove all of candidate's aois from db
    Expect: 204, Candidate should not have any aois left
    """
    # Create Candidate
    AddUserRoles.all_roles(user=user_first)
    data = generate_single_candidate_data([talent_pool.id], domain_aoi)
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate's aois
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_aois = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']['areas_of_interest']

    # Remove all of Candidate's areas of interest
    updated_resp = request_to_candidate_aoi_resource(access_token_first, 'delete', candidate_id, True)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = request_to_candidate_resource(access_token_first, 'get', candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['areas_of_interest']) == 0
    assert AreaOfInterest.query.get(can_aois[0]['id']) # AreaOfInterest should still be in db
    assert AreaOfInterest.query.get(can_aois[1]['id']) # AreaOfInterest should still be in db


def test_delete_can_area_of_interest(access_token_first, user_first, talent_pool, domain_aoi):
    """
    Test:   Remove Candidate's area of interest from db
    Expect: 204, Candidate's aois must be less 1 AND no AreaOfInterest should be deleted
    """
    AddUserRoles.all_roles(user=user_first)

    # Create Candidate
    data = generate_single_candidate_data([talent_pool.id], domain_aoi)
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate areas of interest
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_aois = request_to_candidate_resource(access_token_first, 'get', candidate_id).\
        json()['candidate']['areas_of_interest']

    # Current number of Candidate's areas of interest
    candidate_aois_count = len(can_aois)

    # Remove one of Candidate's area of interest
    updated_resp = request_to_candidate_aoi_resource(access_token_first, 'delete', candidate_id,
                                                     aoi_id=can_aois[0]['id'])
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['areas_of_interest']) == candidate_aois_count - 1
    assert AreaOfInterest.query.get(can_aois[0]['id']) # AreaOfInterest should still be in db
    assert AreaOfInterest.query.get(can_aois[1]['id']) # AreaOfInterest should still be in db


######################## CandidateCustomFields ########################
def test_non_logged_in_user_delete_can_custom_field():
    """
    Test:   Delete candidate's custom fields without logging in
    Expect: 401
    """
    # Delete Candidate's custom fields
    resp = request_to_candidate_custom_field_resource(None, 'delete', 5, True)
    print response_info(resp)
    assert resp.status_code == 401


def test_delete_candidate_custom_field_with_bad_input():
    """
    Test:   Attempt to delete candidate custom_field with non integer values for candidate_id & custom_field_id
    Expect: 404
    """
    # Delete Candidate's custom fields
    resp = request_to_candidate_custom_field_resource(None, 'delete', 'x', True)
    print response_info(resp)
    assert resp.status_code == 404

    # Delete Candidate's custom field
    resp = request_to_candidate_custom_field_resource(None, 'delete', 5, custom_field_id='x')
    print response_info(resp)
    assert resp.status_code == 404


def test_delete_custom_fields_of_a_candidate_belonging_to_a_diff_user(access_token_first,
                                                                      user_first, talent_pool,
                                                                      user_second,
                                                                      access_token_second,
                                                                      domain_custom_fields):
    """
    Test:   Delete custom fields of a Candidate that belongs to a user in a different domain
    Expect: 204
    """
    AddUserRoles.add(user=user_first)
    AddUserRoles.delete(user=user_second)

    # Create candidate_1 & candidate_2 with user_first & user_first_2
    data = generate_single_candidate_data([talent_pool.id], custom_fields=domain_custom_fields)
    create_resp_1 = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve candidate_1
    candidate_1_id = create_resp_1.json()['candidates'][0]['id']

    # Delete candidate_1's custom fields with user_first_2 logged in
    updated_resp = request_to_candidate_custom_field_resource(
            access_token_second, 'delete', candidate_1_id, all_custom_fields=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 403
    assert updated_resp.json()['error']['code'] == custom_error.CANDIDATE_FORBIDDEN


def test_delete_candidates_custom_fields(access_token_first, user_first, talent_pool, domain_custom_fields):
    """
    Test:   Remove all of candidate's custom fields from db
    Expect: 204, Candidate should not have any custom fields left AND no CustomField should be deleted
    """
    # Create Candidate
    AddUserRoles.all_roles(user=user_first)
    data = generate_single_candidate_data([talent_pool.id], custom_fields=domain_custom_fields)
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate's custom fields
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_custom_fields = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']['custom_fields']
    db.session.commit()
    custom_field_id_1 = CandidateCustomField.query.get(can_custom_fields[0]['id']).custom_field_id
    custom_field_id_2 = CandidateCustomField.query.get(can_custom_fields[1]['id']).custom_field_id

    # Remove all of Candidate's custom fields
    updated_resp = request_to_candidate_custom_field_resource(access_token_first, 'delete', candidate_id, True)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['custom_fields']) == 0
    assert CustomField.query.get(custom_field_id_1) # CustomField should still be in db
    assert CustomField.query.get(custom_field_id_2) # CustomField should still be in db


def test_delete_can_custom_field(access_token_first, user_first, talent_pool, domain_custom_fields):
    """
    Test:   Remove Candidate's custom field from db
    Expect: 204, Candidate's custom fields must be less 1 AND no CustomField should be deleted
    """
    # Create Candidate
    AddUserRoles.all_roles(user=user_first)
    data = generate_single_candidate_data([talent_pool.id], custom_fields=domain_custom_fields)
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate custom fields
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_custom_fields = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']['custom_fields']
    db.session.commit()
    custom_field_id_1 = CandidateCustomField.get_by_id(can_custom_fields[0]['id']).custom_field_id
    custom_field_id_2 = CandidateCustomField.get_by_id(can_custom_fields[1]['id']).custom_field_id

    # Remove one of Candidate's custom field
    updated_resp = request_to_candidate_custom_field_resource(access_token_first, 'delete', candidate_id,
                                                      custom_field_id=can_custom_fields[0]['id'])
    print response_info(updated_resp)
    assert updated_resp.status_code == 204
    assert CustomField.query.get(custom_field_id_1) # CustomField should still be in db
    assert CustomField.query.get(custom_field_id_2) # CustomField should still be in db


######################## CandidateEducation ########################
def test_non_logged_in_user_delete_can_education():
    """
    Test:   Delete candidate's education without logging in
    Expect: 401
    """
    # Delete Candidate's educations
    resp = request_to_candidate_education_resource(None, 'delete', 5, True)
    print response_info(resp)
    assert resp.status_code == 401


def test_delete_candidate_education_with_bad_input():
    """
    Test:   Attempt to delete candidate education with non integer values for candidate_id & education_id
    Expect: 404
    """
    # Delete Candidate's educations
    resp = request_to_candidate_education_resource(None, 'delete', candidate_id='x', all_educations=True)
    print response_info(resp)
    assert resp.status_code == 404

    # Delete Candidate's education
    resp = request_to_candidate_education_resource(None, 'delete', candidate_id=5, education_id='x')
    print response_info(resp)
    assert resp.status_code == 404


def test_delete_education_of_a_candidate_in_same_domain(access_token_first, user_first, talent_pool,
                                                        user_second, access_token_second):
    """
    Test:   Attempt to delete the education of a Candidate that belongs to a user in a different domain
    Expect: 204, deletion must be prevented
    """
    AddUserRoles.all_roles(user=user_first)
    AddUserRoles.all_roles(user=user_second)

    # Create candidate_1 & candidate_2 with user_first & user_first_2
    data = generate_single_candidate_data([talent_pool.id])
    create_resp_1 = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve candidate_1
    candidate_1_id = create_resp_1.json()['candidates'][0]['id']

    # Delete candidate_1's education with user_first_2 logged in
    updated_resp = request_to_candidate_education_resource(access_token_second, 'delete', candidate_1_id,
                                                           all_educations=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 403
    assert updated_resp.json()['error']['code'] == custom_error.CANDIDATE_FORBIDDEN


def test_delete_education_of_a_different_candidate(access_token_first, user_first, talent_pool):
    """
    Test:   Attempt to delete the education of a different Candidate in the same domain
    Expect: 403
    """
    # Create candidate_1 and candidate_2
    AddUserRoles.all_roles(user=user_first)
    data_1 = generate_single_candidate_data([talent_pool.id])
    data_2 = generate_single_candidate_data([talent_pool.id])
    candidate_1_id = request_to_candidates_resource(access_token_first, 'post', data_1)\
        .json()['candidates'][0]['id']
    candidate_2_id = request_to_candidates_resource(access_token_first, 'post', data_2)\
        .json()['candidates'][0]['id']

    # Retrieve candidate_2's educations
    can_2_educations = request_to_candidate_resource(access_token_first, 'get', candidate_2_id)\
        .json()['candidate']['educations']

    # Delete candidate_2's id using candidate_1_id
    updated_resp = request_to_candidate_education_resource(access_token_first, 'delete', candidate_1_id,
                                                           education_id=can_2_educations[0]['id'])
    print response_info(updated_resp)
    assert updated_resp.status_code == 403
    assert updated_resp.json()['error']['code'] == custom_error.EDUCATION_FORBIDDEN


def test_delete_candidate_education_with_no_id(access_token_first, user_first, talent_pool):
    """
    Test:   Attempt to delete Candidate's education without providing education_id
    Expect: 404
    """
    # Remove one of Candidate's educations without an id
    candidate_id = 5 # This is arbitrary since a 404 is expected
    updated_resp = request_to_candidate_education_resource(access_token_first, 'delete', candidate_id)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_candidate_educations(access_token_first, user_first, talent_pool):
    """
    Test:   Remove all of candidate's educations from db
    Expect: 204, Candidate should not have any educations left
    """
    # Create Candidate
    AddUserRoles.all_roles(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Remove all of Candidate's educations
    candidate_id = create_resp.json()['candidates'][0]['id']
    updated_resp = request_to_candidate_education_resource(
            access_token_first, 'delete', candidate_id, True)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = request_to_candidate_resource(
            access_token_first, 'get', candidate_id).json()['candidate']
    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['educations']) == 0


def test_delete_candidates_education(access_token_first, user_first, talent_pool):
    """
    Test:   Remove Candidate's education from db
    Expect: 204, Candidate's education must be less 1
    """
    # Create Candidate
    AddUserRoles.all_roles(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']
    candidate_educations = candidate_dict['educations']

    # Current number of Candidate's educations
    candidate_educations_count = len(candidate_educations)

    # Remove one of Candidate's education
    updated_resp = request_to_candidate_education_resource(access_token_first, 'delete', candidate_id,
                                                           education_id=candidate_educations[0]['id'])
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = request_to_candidate_resource(
            access_token_first, 'get', candidate_id).json()['candidate']
    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['educations']) == candidate_educations_count - 1


###################### CandidateEducationDegree ########################
def test_non_logged_in_user_delete_can_edu_degree():
    """
    Test:   Delete Candidate's education degree without logging in
    Expect: 401
    """
    # Delete Candidate's education degrees
    resp = request_to_candidate_education_degree_resource(None, 'delete', 5, 5, True)
    print response_info(resp)
    assert resp.status_code == 401


def test_delete_candidate_education_degrees_with_bad_input():
    """
    Test:   Attempt to delete Candidate's education-degree with non integer values
            for candidate_id & degree_id
    Expect: 404
    """
    # Delete Candidate's education degrees
    resp = request_to_candidate_education_degree_resource(None, 'delete', candidate_id='x',
                                                          education_id=5, all_degrees=True)
    print response_info(resp)
    assert resp.status_code == 404

    # Delete Candidate's education degree
    resp = request_to_candidate_education_degree_resource(None, 'delete', candidate_id=5,
                                                          education_id=5, degree_id='x')
    print response_info(resp)
    assert resp.status_code == 404


def test_delete_edu_degree_of_a_candidate_belonging_to_a_diff_user(access_token_first, user_first,
                                                                   talent_pool, user_second,
                                                                   access_token_second):
    """
    Test:   Attempt to delete the education-degrees of a Candidate that belongs to user from a diff domain
    Expect: 403, deletion must be prevented
    """
    AddUserRoles.add_and_get(user=user_first)
    AddUserRoles.delete(user=user_second)

    # Create candidate_1 & candidate_2 with user_first & user_first_2
    data = generate_single_candidate_data([talent_pool.id])
    create_resp_1 = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve candidate_1
    candidate_1_id = create_resp_1.json()['candidates'][0]['id']
    can_1_edu_id = request_to_candidate_resource(access_token_first, 'get', candidate_1_id).\
        json()['candidate']['educations'][0]['id']

    # Delete candidate_1's education degree with user_first_2 logged in
    updated_resp = request_to_candidate_education_degree_resource(
            access_token_second, 'delete', candidate_1_id,
            education_id=can_1_edu_id, all_degrees=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 403
    assert updated_resp.json()['error']['code'] == custom_error.CANDIDATE_FORBIDDEN


def test_delete_education_degree_of_a_different_candidate(access_token_first, user_first,
                                                          talent_pool):
    """
    Test:   Attempt to delete the education-degrees of a different Candidate
    Expect: 403
    """
    # Create candidate_1 and candidate_2
    AddUserRoles.all_roles(user=user_first)
    data_1 = generate_single_candidate_data([talent_pool.id])
    data_2 = generate_single_candidate_data([talent_pool.id])
    candidate_1_id = request_to_candidates_resource(access_token_first, 'post', data_1)\
        .json()['candidates'][0]['id']
    candidate_2_id = request_to_candidates_resource(access_token_first, 'post', data_2)\
        .json()['candidates'][0]['id']

    # Retrieve candidate_2's education degrees
    can_2_educations = request_to_candidate_resource(access_token_first, 'get', candidate_2_id).\
        json()['candidate']['educations']

    # Delete candidate_2's id using candidate_1_id
    updated_resp = request_to_candidate_education_degree_resource(
            access_token_first, 'delete', candidate_1_id,
            can_2_educations[0]['id'], all_degrees=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 403
    assert updated_resp.json()['error']['code'] == custom_error.EDUCATION_FORBIDDEN


def test_delete_candidate_edu_degree_with_no_id(access_token_first, user_first, talent_pool):
    """
    Test:   Attempt to delete Candidate's education-degree without providing degree_id
    Expect: 404
    """
    # Remove one of Candidate's education-degrees without an id
    candidate_id, education_id = 5, 6 # These are arbitrary since a 404 is expected
    updated_resp = request_to_candidate_education_degree_resource(access_token_first, 'delete', candidate_id, education_id)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404



def test_delete_candidate_education_degrees(access_token_first, user_first, talent_pool):
    """
    Test:   Remove all of candidate's degrees from db
    Expect: 204; Candidate should not have any degrees left; Candidate's Education should not be removed
    """
    # Create Candidate
    AddUserRoles.all_roles(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_educations = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']['educations']

    # Current number of candidate educations
    count_of_edu_degrees_before_deleting = len(can_educations[0])

    # Remove all of Candidate's degrees
    updated_resp = request_to_candidate_education_degree_resource(
            access_token_first, 'delete', candidate_id, can_educations[0]['id'], True)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = request_to_candidate_resource(
            access_token_first, 'get', candidate_id).json()['candidate']
    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['educations'][0]['degrees']) == 0
    assert len(can_dict_after_update['educations'][0]) == count_of_edu_degrees_before_deleting


def test_delete_candidates_education_degree(access_token_first, user_first, talent_pool):
    """
    Test:   Remove Candidate's education from db
    Expect: 204, Candidate's education must be less 1
    """
    # Create Candidate
    AddUserRoles.all_roles(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']
    candidate_educations = candidate_dict['educations']

    # Current number of Candidate's educations
    candidate_educations_count = len(candidate_educations)

    # Remove one of Candidate's education
    updated_resp = request_to_candidate_education_resource(access_token_first, 'delete', candidate_id,
                                                           education_id=candidate_educations[0]['id'])
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']
    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['educations']) == candidate_educations_count - 1


######################## CandidateEducationDegreeBullet ########################
def test_non_logged_in_user_delete_can_edu_degree_bullets():
    """
    Test:   Delete candidate's degree-bullets without logging in
    Expect: 401
    """
    # Delete Candidate's degree-bullets
    resp = request_to_candidate_education_degree_bullet_resource(None, 'delete', 5, 5, 5, all_bullets=True)
    print response_info(resp)
    assert resp.status_code == 401
    assert resp.json()['error']['code'] == 11


def test_delete_candidate_edu_degree_bullets_with_bad_input():
    """
    Test:   Attempt to delete candidate degree-bullets with non integer values for candidate_id & education_id
    Expect: 404
    """
    # Delete Candidate's degree-bullets
    resp = request_to_candidate_education_degree_bullet_resource(None, 'delete',
                                                                 candidate_id='x', all_bullets=True)
    print response_info(resp)
    assert resp.status_code == 404

    # Delete Candidate's degree-bullets
    resp = request_to_candidate_education_degree_bullet_resource(None, 'delete',
                                                                 candidate_id=5, bullet_id='x')
    print response_info(resp)
    assert resp.status_code == 404


def test_delete_degree_bullets_of_a_candidate_belonging_to_a_diff_user(
        access_token_first, user_first, talent_pool, user_second, access_token_second):
    """
    Test:   Attempt to delete degree-bullets of a Candidate that belongs to a user from a diff domain
    Expect: 204
    """
    AddUserRoles.add_and_get(user=user_first)
    AddUserRoles.delete(user=user_second)

    # Create candidate_1 & candidate_2 with user_first & user_first_2
    data = generate_single_candidate_data([talent_pool.id])
    create_resp_1 = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve candidate_1
    candidate_1_id = create_resp_1.json()['candidates'][0]['id']
    can_1_educations = request_to_candidate_resource(access_token_first, 'get', candidate_1_id)\
        .json()['candidate']['educations']

    # Delete candidate_1's degree-bullets with user_first_2 logged in
    updated_resp = request_to_candidate_education_degree_bullet_resource(
            access_token_second, 'delete', candidate_1_id, can_1_educations[0]['id'],
            can_1_educations[0]['degrees'][0]['id'], all_bullets=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 403
    assert updated_resp.json()['error']['code'] == custom_error.CANDIDATE_FORBIDDEN


def test_delete_can_edu_degree_bullets_of_a_different_candidate(access_token_first, user_first, talent_pool):
    """
    Test:   Attempt to delete degree-bullets of a different Candidate
    Expect: 403
    """
    # Create candidate_1 and candidate_2
    AddUserRoles.all_roles(user=user_first)
    data_1 = generate_single_candidate_data([talent_pool.id])
    data_2 = generate_single_candidate_data([talent_pool.id])
    candidate_1_id = request_to_candidates_resource(access_token_first,'post', data_1)\
        .json()['candidates'][0]['id']
    candidate_2_id = request_to_candidates_resource(access_token_first,'post', data_2)\
        .json()['candidates'][0]['id']

    # Retrieve candidate_2's degree-bullets
    can_2_edu = request_to_candidate_resource(access_token_first, 'get', candidate_2_id)\
        .json()['candidate']['educations'][0]
    can_2_edu_degree = can_2_edu['degrees'][0]
    can_2_edu_degree_bullet = can_2_edu['degrees'][0]['bullets'][0]

    # Delete candidate_2's id using candidate_1_id
    updated_resp = request_to_candidate_education_degree_bullet_resource(
            access_token_first, 'delete', candidate_1_id, can_2_edu['id'],
            can_2_edu_degree['id'], bullet_id=can_2_edu_degree_bullet['id'])
    print response_info(updated_resp)
    assert updated_resp.status_code == 404
    assert updated_resp.json()['error']['code'] == custom_error.DEGREE_NOT_FOUND


def test_delete_candidate_education_degree_bullets(access_token_first, user_first, talent_pool):
    """
    Test:   Remove all of candidate's degree_bullets from db
    Expect: 204; Candidate should not have any degrees left; Candidate's
    Education and degrees should not be removed
    """
    # Create Candidate
    AddUserRoles.all_roles(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_educations = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']['educations']

    # Current number of candidate educations & degrees
    count_of_educations_before_deleting = len(can_educations[0])
    count_of_edu_degrees_before_deleting = len(can_educations[0]['degrees'])

    # Remove all of Candidate's degree_bullets
    updated_resp = request_to_candidate_education_degree_bullet_resource(
            access_token_first, 'delete', candidate_id, can_educations[0]['id'],
            can_educations[0]['degrees'][0]['id'], True)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']
    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['educations'][0]['degrees'][0]['bullets']) == 0
    assert len(can_dict_after_update['educations'][0]) == count_of_educations_before_deleting
    assert len(can_dict_after_update['educations'][0]['degrees']) == count_of_edu_degrees_before_deleting


def test_delete_candidates_education_degree_bullet(access_token_first, user_first, talent_pool):
    """
    Test:   Remove Candidate's degree_bullet from db
    Expect: 204, Candidate's degree_bullet must be less 1. Candidate's education and degrees
            should not be removed
    """
    # Create Candidate
    AddUserRoles.all_roles(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']
    candidate_educations = candidate_dict['educations']

    # Current number of Candidate's educations, degrees, and bullets
    educations_count_before_delete = len(candidate_educations)
    degrees_count_before_delete = len(candidate_educations[0]['degrees'])
    degree_bullets_count_before_delete = len(candidate_educations[0]['degrees'][0]['bullets'])

    # Remove one of Candidate's education
    updated_resp = request_to_candidate_education_degree_bullet_resource(
        access_token=access_token_first, request='delete', candidate_id=candidate_id,
        education_id=candidate_educations[0]['id'],
        degree_id=candidate_educations[0]['degrees'][0]['id'],
        bullet_id=candidate_educations[0]['degrees'][0]['bullets'][0]['id']
    )
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = request_to_candidate_resource(access_token_first, 'get', candidate_id)\
        .json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['educations']) == educations_count_before_delete
    assert len(can_dict_after_update['educations'][0]['degrees']) == degrees_count_before_delete
    assert len(can_dict_after_update['educations'][0]['degrees'][0]['bullets']) == degree_bullets_count_before_delete - 1



