"""
Test cases for CandidateResource/delete()
"""
# Candidate Service app instance
from candidate_service.candidate_app import app

# Models
from candidate_service.common.models.user import User
from candidate_service.common.models.candidate import CandidateCustomField

# Conftest
from candidate_service.common.tests.conftest import UserAuthentication
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import (
    response_info, post_to_candidate_resource, get_from_candidate_resource,
    request_to_candidate_resource, request_to_candidate_address_resource,
    request_to_candidate_aoi_resource, request_to_candidate_education_resource,
    request_to_candidate_education_degree_resource, request_to_candidate_education_degree_bullet_resource,
    request_to_candidate_custom_field_resource
)


######################## Candidate ########################
def test_delete_candidate_and_retrieve_it(sample_user, user_auth):
    """
    Test:   "Delete" a Candidate by setting is_web_hidden to True, and then retrieve Candidate
    Expect: 404, Not Found error
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Delete (hide) Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    resp = request_to_candidate_resource(token, 'delete', candidate_id)
    print response_info(resp)

    # Retrieve Candidate
    get_resp = get_from_candidate_resource(token, candidate_id)
    print response_info(get_resp)
    assert get_resp.status_code == 404


def test_delete_candidate_without_id(sample_user, user_auth):
    """
    Test:   Attempt to delete a Candidate without providing its ID
    Expect: 400
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Delete Candidate
    resp = request_to_candidate_resource(token, 'delete')
    print response_info(resp)
    assert resp.status_code == 405


def test_delete_candidate_via_email(sample_user, user_auth):
    """
    Test:   "Delete" a Candidate via candidate's email
    Expect: 200
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_emails = get_from_candidate_resource(token, candidate_id).json()['candidate']['emails']

    # Delete (hide) Candidate
    resp = request_to_candidate_resource(token, 'delete', candidate_email=can_emails[0]['address'])
    print response_info(resp)


def test_delete_candidate_via_unrecognized_email(sample_user, user_auth):
    """
    Test:   "Delete" a Candidate via an email that does not exist in db
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Delete (hide) Candidate
    resp = request_to_candidate_resource(token, 'delete', candidate_email='email_not_found_45623@simple.com')
    print response_info(resp)
    assert resp.status_code == 404


def test_delete_someone_elses_candidate(sample_user, sample_user_2, user_auth):
    """
    Test:   "Delete" a Candidate via candidate's email
    Expect: 200
    :type sample_user:  User
    :type sample_user_2:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token_1 and token_2
    token_1 = user_auth.get_auth_token(sample_user, True)['access_token']
    token_2 = user_auth.get_auth_token(sample_user_2, True)['access_token']

    # Create Candidate with token_1 (belonging to sample_user)
    candidate_1_id = post_to_candidate_resource(token_1).json()['candidates'][0]['id']

    # Retrieve Candidate
    candidate_dict = get_from_candidate_resource(token_1, candidate_1_id).json()['candidate']

    # Delete (hide) Candidate with token_2 (sample_user_2)
    resp = request_to_candidate_resource(token_2, 'delete', candidate_dict['id'])
    print response_info(resp)
    assert resp.status_code == 403


######################## CandidateAddress ########################
def test_non_logged_in_user_delete_can_address():
    """
    Test:   Delete candidate's address without logging in
    Expect: 401
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Delete Candidate's addresses
    resp = request_to_candidate_address_resource(None, 'delete', 5, True)
    print response_info(resp)
    assert resp.status_code == 401


def test_delete_candidate_address_with_bad_input():
    """
    Test:   Attempt to delete candidate address with non integer values for candidate_id & address_id
    Expect: 404
    """
    # Delete Candidate's addresses
    resp = request_to_candidate_address_resource(None, 'delete', candidate_id='x', all_addresses=True)
    print response_info(resp)
    assert resp.status_code == 404

    # Delete Candidate's address
    resp = request_to_candidate_address_resource(None, 'delete', candidate_id=5, address_id='x')
    print response_info(resp)
    assert resp.status_code == 404


def test_delete_address_of_a_candidate_belonging_to_a_diff_user(sample_user, sample_user_2, user_auth):
    """
    Test:   Attempt to delete the address of a Candidate that belongs to a different user
    Expect: 403, deletion must be prevented
    :type sample_user:  User
    :type sampl_user_2: User
    :type user_auth:   UserAuthentication
    """
    # Get access token_1 & token_2 for sample_user & sample_user_2, respectively
    token_1 = user_auth.get_auth_token(sample_user, True)['access_token']
    token_2 = user_auth.get_auth_token(sample_user_2, True)['access_token']

    # Create candidate_1 & candidate_2 with sample_user & sample_user_2
    create_resp_1 = post_to_candidate_resource(token_1)

    # Retrieve candidate_1
    candidate_1_id = create_resp_1.json()['candidates'][0]['id']

    # Delete candidate_1's address with sample_user_2 logged in
    updated_resp = request_to_candidate_address_resource(token_2, 'delete', candidate_1_id, all_addresses=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_address_of_a_diff_candidate(sample_user, user_auth):
    """
    Test:   Attempt to delete the address of a different Candidate
    Expect: 403
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create candidate_1 and candidate_2
    candidate_1_id = post_to_candidate_resource(token).json()['candidates'][0]['id']
    candidate_2_id = post_to_candidate_resource(token).json()['candidates'][0]['id']

    # Retrieve candidate_2's addresses
    can_2_addresses = get_from_candidate_resource(token, candidate_2_id).json()['candidate']['addresses']

    # Delete candidate_2's id using candidate_1_id
    updated_resp = request_to_candidate_address_resource(token, 'delete', candidate_1_id,
                                                         address_id=can_2_addresses[0]['id'])
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_candidate_address_with_no_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's address without providing address_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's addresses without an id
    candidate_id = 5 # This is arbitrary since a 404 is expected
    updated_resp = request_to_candidate_address_resource(token, 'delete', candidate_id)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_candidate_addresses_without_candidate_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's address without providing candidate_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's addresses without an id
    updated_resp = request_to_candidate_address_resource(token, 'delete', all_addresses=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_can_address(sample_user, user_auth):
    """
    Test:   Remove Candidate's address from db
    Expect: 204, Candidate's addresses must be less 1
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_addresses = get_from_candidate_resource(token, candidate_id).json()['candidate']['addresses']

    # Number of Candidate's addresses
    can_addresses_count = len(can_addresses)

    # Remove one of Candidate's addresses
    updated_resp = request_to_candidate_address_resource(token, 'delete', candidate_id,
                                                         address_id=can_addresses[0]['id'])
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['addresses']) == can_addresses_count - 1


def test_delete_all_of_candidates_addresses(sample_user, user_auth):
    """
    Test:   Remove all of candidate's addresses from db
    Expect: 204, Candidate should not have any addresses left
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Remove all of Candidate's addresses
    candidate_id = create_resp.json()['candidates'][0]['id']
    updated_resp = request_to_candidate_address_resource(token, 'delete', candidate_id, True)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['addresses']) == 0


######################## CandidateAreaOfInterest ########################
def test_non_logged_in_user_delete_can_aoi():
    """
    Test:   Delete candidate's aoi without logging in
    Expect: 401
    :type sample_user:  User
    :type user_auth:    UserAuthentication
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


def test_delete_can_aoi_of_a_candidate_belonging_to_a_diff_user(sample_user, sample_user_2, user_auth):
    """
    Test:   Attempt to delete the candidate aois of a Candidate that belongs to a different user
    Expect: 403, deletion must be prevented
    :type sample_user:  User
    :type sampl_user_2: User
    :type user_auth:   UserAuthentication
    """
    # Get access token_1 & token_2 for sample_user & sample_user_2, respectively
    token_1 = user_auth.get_auth_token(sample_user, True)['access_token']
    token_2 = user_auth.get_auth_token(sample_user_2, True)['access_token']

    # Create candidate_1 & candidate_2 with sample_user & sample_user_2
    create_resp_1 = post_to_candidate_resource(token_1)

    # Retrieve candidate_1
    candidate_1_id = create_resp_1.json()['candidates'][0]['id']

    # Delete candidate_1's areas of interest with sample_user_2 logged in
    updated_resp = request_to_candidate_aoi_resource(token_2, 'delete', candidate_1_id, all_aois=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_candidate_aoi_with_no_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's aoi without providing area_of_interest_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's areas of interest without an id
    candidate_id = 5 # This is arbitrary since a 404 is expected
    updated_resp = request_to_candidate_aoi_resource(token, 'delete', candidate_id)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_candidate_aois_without_candidate_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's areas of interest without providing candidate_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's areas of interest without an id
    updated_resp = request_to_candidate_aoi_resource(token, 'delete', all_aois=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_all_of_candidates_areas_of_interest(sample_user, user_auth):
    """
    Test:   Remove all of candidate's aois from db
    Expect: 204, Candidate should not have any aois left
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token, domain_id=sample_user.domain_id)

    # Retrieve Candidate's aois
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_aois = get_from_candidate_resource(token, candidate_id).json()['candidate']['areas_of_interest']

    # Remove all of Candidate's areas of interest
    updated_resp = request_to_candidate_aoi_resource(token, 'delete', candidate_id, True)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['areas_of_interest']) == 0
    assert db.session.query(AreaOfInterest).get(can_aois[0]['id']) # AreaOfInterest should still be in db
    assert db.session.query(AreaOfInterest).get(can_aois[1]['id']) # AreaOfInterest should still be in db


def test_delete_can_area_of_interest(sample_user, user_auth):
    """
    Test:   Remove Candidate's area of interest from db
    Expect: 204, Candidate's aois must be less 1 AND no AreaOfInterest should be deleted
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token, domain_id=sample_user.domain_id)

    # Retrieve Candidate areas of interest
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_aois = get_from_candidate_resource(token, candidate_id).json()['candidate']['areas_of_interest']

    # Current number of Candidate's areas of interest
    candidate_aois_count = len(can_aois)

    # Remove one of Candidate's area of interest
    updated_resp = request_to_candidate_aoi_resource(token, 'delete', candidate_id, aoi_id=can_aois[0]['id'])
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['areas_of_interest']) == candidate_aois_count - 1
    assert db.session.query(AreaOfInterest).get(can_aois[0]['id']) # AreaOfInterest should still be in db
    assert db.session.query(AreaOfInterest).get(can_aois[1]['id']) # AreaOfInterest should still be in db


######################## CandidateCustomFields ########################
def test_non_logged_in_user_delete_can_custom_field():
    """
    Test:   Delete candidate's custom fields without logging in
    Expect: 401
    :type sample_user:  User
    :type user_auth:    UserAuthentication
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


def test_delete_custom_fields_of_a_candidate_belonging_to_a_diff_user(sample_user, sample_user_2, user_auth):
    """
    Test:   Attempt to delete custom fields of a Candidate that belongs to a different user
    Expect: 403, deletion must be prevented
    :type sample_user:  User
    :type sampl_user_2: User
    :type user_auth:   UserAuthentication
    """
    # Get access token_1 & token_2 for sample_user & sample_user_2, respectively
    token_1 = user_auth.get_auth_token(sample_user, True)['access_token']
    token_2 = user_auth.get_auth_token(sample_user_2, True)['access_token']

    # Create candidate_1 & candidate_2 with sample_user & sample_user_2
    create_resp_1 = post_to_candidate_resource(token_1)

    # Retrieve candidate_1
    candidate_1_id = create_resp_1.json()['candidates'][0]['id']

    # Delete candidate_1's custom fields with sample_user_2 logged in
    updated_resp = request_to_candidate_custom_field_resource(token_2, 'delete', candidate_1_id,
                                                              all_custom_fields=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_candidate_custom_fields_with_no_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's custom fields without providing custom_field_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's custom fields without a custom_field_id
    candidate_id = 5 # This is arbitrary since a 404 is expected
    updated_resp = request_to_candidate_custom_field_resource(token, 'delete', candidate_id)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_candidate_custom_fields_without_candidate_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's custom fields without providing candidate_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's custom fields without candidate_id
    updated_resp = request_to_candidate_custom_field_resource(token, 'delete', all_custom_fields=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_candidates_custom_fields(sample_user, user_auth):
    """
    Test:   Remove all of candidate's custom fields from db
    Expect: 204, Candidate should not have any custom fields left AND no CustomField should be deleted
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token, domain_id=sample_user.domain_id)

    # Retrieve Candidate's custom fields
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_custom_fields = get_from_candidate_resource(token, candidate_id).json()['candidate']['custom_fields']
    db.session.commit()
    custom_field_id_1 = db.session.query(CandidateCustomField).get(can_custom_fields[0]['id']).custom_field_id
    custom_field_id_2 = db.session.query(CandidateCustomField).get(can_custom_fields[1]['id']).custom_field_id

    # Remove all of Candidate's custom fields
    updated_resp = request_to_candidate_custom_field_resource(token, 'delete', candidate_id, True)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['custom_fields']) == 0
    assert db.session.query(CustomField).get(custom_field_id_1) # CustomField should still be in db
    assert db.session.query(CustomField).get(custom_field_id_2) # CustomField should still be in db


def test_delete_can_custom_field(sample_user, user_auth):
    """
    Test:   Remove Candidate's custom field from db
    Expect: 204, Candidate's custom fields must be less 1 AND no CustomField should be deleted
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token, domain_id=sample_user.domain_id)

    # Retrieve Candidate custom fields
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_custom_fields = get_from_candidate_resource(token, candidate_id).json()['candidate']['custom_fields']
    db.session.commit()
    custom_field_id_1 = db.session.query(CandidateCustomField).get(can_custom_fields[0]['id']).custom_field_id
    custom_field_id_2 = db.session.query(CandidateCustomField).get(can_custom_fields[1]['id']).custom_field_id

    # Current number of Candidate's custom fields
    can_custom_fields_count = len(can_custom_fields)

    # Remove one of Candidate's custom field
    updated_resp = request_to_candidate_custom_field_resource(token, 'delete', candidate_id,
                                                              custom_field_id=can_custom_fields[0]['id'])
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['custom_fields']) == can_custom_fields_count - 1
    assert db.session.query(CustomField).get(custom_field_id_1) # CustomField should still be in db
    assert db.session.query(CustomField).get(custom_field_id_2) # CustomField should still be in db


######################## CandidateEducation ########################
def test_non_logged_in_user_delete_can_education():
    """
    Test:   Delete candidate's education without logging in
    Expect: 401
    :type sample_user:  User
    :type user_auth:    UserAuthentication
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


def test_delete_education_of_a_candidate_belonging_to_a_diff_user(sample_user, sample_user_2, user_auth):
    """
    Test:   Attempt to delete the education of a Candidate that belongs to a different user
    Expect: 403, deletion must be prevented
    :type sample_user:  User
    :type sampl_user_2: User
    :type user_auth:   UserAuthentication
    """
    # Get access token_1 & token_2 for sample_user & sample_user_2, respectively
    token_1 = user_auth.get_auth_token(sample_user, True)['access_token']
    token_2 = user_auth.get_auth_token(sample_user_2, True)['access_token']

    # Create candidate_1 & candidate_2 with sample_user & sample_user_2
    create_resp_1 = post_to_candidate_resource(token_1)

    # Retrieve candidate_1
    candidate_1_id = create_resp_1.json()['candidates'][0]['id']

    # Delete candidate_1's education with sample_user_2 logged in
    updated_resp = request_to_candidate_education_resource(token_2, 'delete', candidate_1_id, all_educations=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_education_of_a_different_candidate(sample_user, user_auth):
    """
    Test:   Attempt to delete the education of a different Candidate
    Expect: 403
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create candidate_1 and candidate_2
    candidate_1_id = post_to_candidate_resource(token).json()['candidates'][0]['id']
    candidate_2_id = post_to_candidate_resource(token).json()['candidates'][0]['id']

    # Retrieve candidate_2's educations
    can_2_educations = get_from_candidate_resource(token, candidate_2_id).json()['candidate']['educations']

    # Delete candidate_2's id using candidate_1_id
    updated_resp = request_to_candidate_education_resource(token, 'delete', candidate_1_id,
                                                           education_id=can_2_educations[0]['id'])
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_candidate_education_with_no_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's education without providing education_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's educations without an id
    candidate_id = 5 # This is arbitrary since a 404 is expected
    updated_resp = request_to_candidate_education_resource(token, 'delete', candidate_id)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_candidate_educations_without_candidate_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's educations without providing candidate_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's educations without an id
    updated_resp = request_to_candidate_education_resource(token, 'delete', all_educations=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_candidate_educations(sample_user, user_auth):
    """
    Test:   Remove all of candidate's educations from db
    Expect: 204, Candidate should not have any educations left
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Remove all of Candidate's educations
    candidate_id = create_resp.json()['candidates'][0]['id']
    updated_resp = request_to_candidate_education_resource(token, 'delete', candidate_id, True)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['educations']) == 0


def test_delete_candidates_education(sample_user, user_auth):
    """
    Test:   Remove Candidate's education from db
    Expect: 204, Candidate's education must be less 1
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token, domain_id=sample_user.domain_id)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    candidate_educations = candidate_dict['educations']

    # Current number of Candidate's educations
    candidate_educations_count = len(candidate_educations)

    # Remove one of Candidate's education
    updated_resp = request_to_candidate_education_resource(token, 'delete', candidate_id,
                                                           education_id=candidate_educations[0]['id'])
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['educations']) == candidate_educations_count - 1


######################## CandidateEducationDegree ########################
def test_non_logged_in_user_delete_can_edu_degree():
    """
    Test:   Delete Candidate's education degree without logging in
    Expect: 401
    :type sample_user:  User
    :type user_auth:    UserAuthentication
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


def test_delete_edu_degree_of_a_candidate_belonging_to_a_diff_user(sample_user, sample_user_2, user_auth):
    """
    Test:   Attempt to delete the education-degrees of a Candidate that belongs to a different user
    Expect: 403, deletion must be prevented
    :type sample_user:  User
    :type sampl_user_2: User
    :type user_auth:   UserAuthentication
    """
    # Get access token_1 & token_2 for sample_user & sample_user_2, respectively
    token_1 = user_auth.get_auth_token(sample_user, True)['access_token']
    token_2 = user_auth.get_auth_token(sample_user_2, True)['access_token']

    # Create candidate_1 & candidate_2 with sample_user & sample_user_2
    create_resp_1 = post_to_candidate_resource(token_1)

    # Retrieve candidate_1
    candidate_1_id = create_resp_1.json()['candidates'][0]['id']
    can_1_edu_id = get_from_candidate_resource(token_1, candidate_1_id).json()['candidate']['educations'][0]['id']

    # Delete candidate_1's education degree with sample_user_2 logged in
    updated_resp = request_to_candidate_education_degree_resource(token_2, 'delete', candidate_1_id,
                                                                  education_id=can_1_edu_id, all_degrees=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_education_degree_of_a_different_candidate(sample_user, user_auth):
    """
    Test:   Attempt to delete the education-degrees of a different Candidate
    Expect: 403
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create candidate_1 and candidate_2
    candidate_1_id = post_to_candidate_resource(token).json()['candidates'][0]['id']
    candidate_2_id = post_to_candidate_resource(token).json()['candidates'][0]['id']

    # Retrieve candidate_2's education degrees
    can_2_educations = get_from_candidate_resource(token, candidate_2_id).json()['candidate']['educations']

    # Delete candidate_2's id using candidate_1_id
    updated_resp = request_to_candidate_education_degree_resource(token, 'delete', candidate_1_id,
                                                                  can_2_educations[0]['id'], all_degrees=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_candidate_edu_degree_with_no_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's education-degree without providing degree_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's education-degrees without an id
    candidate_id, education_id = 5, 6 # These are arbitrary since a 404 is expected
    updated_resp = request_to_candidate_education_degree_resource(token, 'delete', candidate_id, education_id)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_can_edu_degree_without_candidate_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's education-degrees without providing candidate_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's education degrees without an id
    updated_resp = request_to_candidate_education_degree_resource(token, 'delete', all_degrees=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_candidate_education_degrees(sample_user, user_auth):
    """
    Test:   Remove all of candidate's degrees from db
    Expect: 204; Candidate should not have any degrees left; Candidate's Education should not be removed
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_educations = get_from_candidate_resource(token, candidate_id).json()['candidate']['educations']

    # Current number of candidate educations
    count_of_edu_degrees_before_deleting = len(can_educations[0])

    # Remove all of Candidate's degrees
    updated_resp = request_to_candidate_education_degree_resource(token, 'delete', candidate_id,
                                                                  can_educations[0]['id'], True)
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['educations'][0]['degrees']) == 0
    assert len(can_dict_after_update['educations'][0]) == count_of_edu_degrees_before_deleting


def test_delete_candidates_education_degree(sample_user, user_auth):
    """
    Test:   Remove Candidate's education from db
    Expect: 204, Candidate's education must be less 1
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token, domain_id=sample_user.domain_id)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    candidate_educations = candidate_dict['educations']

    # Current number of Candidate's educations
    candidate_educations_count = len(candidate_educations)

    # Remove one of Candidate's education
    updated_resp = request_to_candidate_education_resource(token, 'delete', candidate_id,
                                                           education_id=candidate_educations[0]['id'])
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['educations']) == candidate_educations_count - 1


######################## CandidateEducationDegreeBullet ########################
def test_non_logged_in_user_delete_can_edu_degree_bullets():
    """
    Test:   Delete candidate's degree-bullets without logging in
    Expect: 401
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Delete Candidate's degree-bullets
    resp = request_to_candidate_education_degree_bullet_resource(None, 'delete', 5, 5, 5, all_bullets=True)
    print response_info(resp)
    assert resp.status_code == 401


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


def test_delete_degree_bullets_of_a_candidate_belonging_to_a_diff_user(sample_user, sample_user_2, user_auth):
    """
    Test:   Attempt to delete degree-bullets of a Candidate that belongs to a different user
    Expect: 403, deletion must be prevented
    :type sample_user:  User
    :type sampl_user_2: User
    :type user_auth:   UserAuthentication
    """
    # Get access token_1 & token_2 for sample_user & sample_user_2, respectively
    token_1 = user_auth.get_auth_token(sample_user, True)['access_token']
    token_2 = user_auth.get_auth_token(sample_user_2, True)['access_token']

    # Create candidate_1 & candidate_2 with sample_user & sample_user_2
    create_resp_1 = post_to_candidate_resource(token_1)

    # Retrieve candidate_1
    candidate_1_id = create_resp_1.json()['candidates'][0]['id']
    can_1_educations = get_from_candidate_resource(token_1, candidate_1_id).json()['candidate']['educations']

    # Delete candidate_1's degree-bullets with sample_user_2 logged in
    updated_resp = request_to_candidate_education_degree_bullet_resource(token_2, 'delete', candidate_1_id,
                                                                         can_1_educations[0]['id'],
                                                                         can_1_educations[0]['degrees'][0]['id'],
                                                                         all_bullets=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 403


def test_delete_can_edu_degree_bullets_of_a_different_candidate(sample_user, user_auth):
    """
    Test:   Attempt to delete degree-bullets of a different Candidate
    Expect: 403
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create candidate_1 and candidate_2
    candidate_1_id = post_to_candidate_resource(token).json()['candidates'][0]['id']
    candidate_2_id = post_to_candidate_resource(token).json()['candidates'][0]['id']

    # Retrieve candidate_2's degree-bullets
    can_2_edu = get_from_candidate_resource(token, candidate_2_id).json()['candidate']['educations'][0]
    can_2_edu_degree = can_2_edu['degrees'][0]
    can_2_edu_degree_bullet = can_2_edu['degrees'][0]['bullets'][0]

    # Delete candidate_2's id using candidate_1_id
    updated_resp = request_to_candidate_education_degree_bullet_resource(token, 'delete', candidate_1_id,
                                                                         can_2_edu['id'],
                                                                         can_2_edu_degree['id'],
                                                                         bullet_id=can_2_edu_degree_bullet['id'])
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_candidate_edu_degree_bullet_with_no_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's degree-bullet without providing bullet_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's degree-bullets without an id
    candidate_id, education_id, degree_id = 5, 5, 5 # This is arbitrary since a 404 is expected
    updated_resp = request_to_candidate_education_degree_bullet_resource(token, 'delete', candidate_id,
                                                                         education_id, degree_id)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_candidate_degree_bullets_without_candidate_id(sample_user, user_auth):
    """
    Test:   Attempt to delete Candidate's degree-bullets without providing candidate_id
    Expect: 404
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Remove one of Candidate's degree-bullets without providing candidate_id
    updated_resp = request_to_candidate_education_degree_bullet_resource(token, 'delete', all_bullets=True)
    print response_info(updated_resp)
    assert updated_resp.status_code == 404


def test_delete_candidate_education_degree_bullets(sample_user, user_auth):
    """
    Test:   Remove all of candidate's degree_bullets from db
    Expect: 204; Candidate should not have any degrees left; Candidate's
    Education and degrees should not be removed
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    can_educations = get_from_candidate_resource(token, candidate_id).json()['candidate']['educations']

    # Current number of candidate educations & degrees
    count_of_educations_before_deleting = len(can_educations[0])
    count_of_edu_degrees_before_deleting = len(can_educations[0]['degrees'])

    # Remove all of Candidate's degree_bullets
    updated_resp = request_to_candidate_education_degree_bullet_resource(
        token, 'delete', candidate_id, can_educations[0]['id'], can_educations[0]['degrees'][0]['id'],
        True
    )
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['educations'][0]['degrees'][0]['bullets']) == 0
    assert len(can_dict_after_update['educations'][0]) == count_of_educations_before_deleting
    assert len(can_dict_after_update['educations'][0]['degrees']) == count_of_edu_degrees_before_deleting


def test_delete_candidates_education_degree_bullet(sample_user, user_auth):
    """
    Test:   Remove Candidate's degree_bullet from db
    Expect: 204, Candidate's degree_bullet must be less 1. Candidate's education and degrees
            should not be removed
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get access token
    token = user_auth.get_auth_token(sample_user, True)['access_token']

    # Create Candidate
    create_resp = post_to_candidate_resource(token)

    # Retrieve Candidate
    candidate_id = create_resp.json()['candidates'][0]['id']
    candidate_dict = get_from_candidate_resource(token, candidate_id).json()['candidate']
    candidate_educations = candidate_dict['educations']

    # Current number of Candidate's educations, degrees, and bullets
    educations_count_before_delete = len(candidate_educations)
    degrees_count_before_delete = len(candidate_educations[0]['degrees'])
    degree_bullets_count_before_delete = len(candidate_educations[0]['degrees'][0]['bullets'])

    # Remove one of Candidate's education
    updated_resp = request_to_candidate_education_degree_bullet_resource(
        access_token=token, request='delete', candidate_id=candidate_id,
        education_id=candidate_educations[0]['id'],
        degree_id=candidate_educations[0]['degrees'][0]['id'],
        bullet_id=candidate_educations[0]['degrees'][0]['bullets'][0]['id']
    )
    print response_info(updated_resp)

    # Retrieve Candidate after update
    can_dict_after_update = get_from_candidate_resource(token, candidate_id).json()['candidate']

    assert updated_resp.status_code == 204
    assert len(can_dict_after_update['educations']) == educations_count_before_delete
    assert len(can_dict_after_update['educations'][0]['degrees']) == degrees_count_before_delete
    assert len(can_dict_after_update['educations'][0]['degrees'][0]['bullets']) == degree_bullets_count_before_delete - 1



