"""
Test cases for CandidateResource/delete()
"""
# Candidate Service app instance

# Models
from candidate_service.common.models.candidate import CandidateCustomField, CandidateEmail, \
    CandidateTextComment, CandidateReference
from candidate_service.common.models.tag import CandidateTag
from candidate_service.common.routes import CandidateApiUrl
from candidate_service.common.tests.conftest import *
from candidate_service.common.utils.test_utils import send_request, response_info
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error
from candidate_service.tests.api.candidate_sample_data import generate_single_candidate_data


class TestDeleteCandidate(object):
    """
    Test cases for deleting candidate(s) via Delete v1/candidates
    """
    def test_delete_candidate_with_full_profile(self, access_token_first, user_first, talent_pool, domain_aois, domain_custom_fields):
        """
        Test: Create a candidate with all fields and delete it
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        # Create candidate with full profile
        data = generate_single_candidate_data(talent_pool_ids=[talent_pool.id], areas_of_interest=domain_aois,
                                              custom_fields=domain_custom_fields)
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)

        candidate_id = create_resp.json()['candidates'][0]['id']

        # Notes
        data = {'notes': [{'title': fake.word(), 'comment': 'something nice'}]}
        create_resp = send_request('post', CandidateApiUrl.NOTES % candidate_id, access_token_first, data)
        print response_info(create_resp)

        # Tags
        data = {'tags': [{'name': 'software-stuff'}]}
        create_resp = send_request('post', CandidateApiUrl.TAGS % candidate_id, access_token_first, data)
        print response_info(create_resp)

        # References
        data = {'candidate_references': [
            {
                'name': fake.name(), 'position_title': fake.job(), 'comments': 'Do not hire this guy!',
                'reference_email': {'is_default': None, 'address': fake.safe_email(), 'label': None},
                'reference_phone': {'is_default': True, 'value': '14055689944'},
                'reference_web_address': {'url': fake.url(), 'description': fake.bs()}
            }
        ]}
        create_resp = send_request('post', CandidateApiUrl.REFERENCES % candidate_id, access_token_first, data)
        print response_info(create_resp)

        # Delete candidate
        del_resp = send_request('delete', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(del_resp)
        assert del_resp.status_code == requests.codes.NO_CONTENT

        # Retrieve candidate. Expect NOT FOUND error
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == requests.codes.NOT_FOUND

        # Candidate should no longer have any notes in db
        candidate_notes = CandidateTextComment.get_by_candidate_id(candidate_id)
        assert candidate_notes == []

        # Candidate should no longer have any tags in db
        candidate_tags = CandidateTag.get_all(candidate_id)
        assert candidate_tags == []

        # Candidate should no longer have any references in db
        candidate_references = CandidateReference.get_all(candidate_id)
        assert candidate_references == []

    def test_delete_non_existing_candidate(self, access_token_first, user_first):
        """
        Test: Attempt to delete a candidate that isn't recognized via ID or Email
        Expect: 404
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        last_candidate = Candidate.query.order_by(Candidate.id.desc()).first()
        non_existing_candidate_id = str(last_candidate.id * 100)

        # Delete non existing candidate via ID
        resp = send_request('delete', CandidateApiUrl.CANDIDATE % non_existing_candidate_id, access_token_first)
        print response_info(resp)
        assert resp.status_code == requests.codes.NOT_FOUND
        assert resp.json()['error']['code'] == custom_error.CANDIDATE_NOT_FOUND

        # Delete non existing candidate via Email
        bogus_email = '{}_{}'.format(fake.word(), fake.safe_email())
        assert not CandidateEmail.get_by_address(email_address=bogus_email)

        resp = send_request('delete', CandidateApiUrl.CANDIDATE % bogus_email, access_token_first)
        print response_info(resp)
        assert resp.status_code == requests.codes.NOT_FOUND
        assert resp.json()['error']['code'] == custom_error.EMAIL_NOT_FOUND

    def test_delete_candidate_via_unrecognized_email(self, access_token_first, user_first):
        """
        Test:   Delete a Candidate via an email that does not exist in db
        Expect: 404
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        # Delete Candidate
        candidate_email = "{unique}{email}".format(unique=str(uuid.uuid4())[:5], email=fake.safe_email())
        resp = send_request('delete', CandidateApiUrl.CANDIDATE % candidate_email, access_token_first)
        print response_info(resp)
        assert resp.status_code == requests.codes.NOT_FOUND
        assert resp.json()['error']['code'] == custom_error.EMAIL_NOT_FOUND

    def test_delete_candidate_from_a_diff_domain(self, access_token_second, user_second, candidate_first):
        """
        Test:   Delete a Candidate via candidate's email
        """
        user_second.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        # Delete Candidate with user_second
        resp = send_request('delete', CandidateApiUrl.CANDIDATE % candidate_first.id, access_token_second)
        print response_info(resp)
        assert resp.status_code == requests.codes.FORBIDDEN
        assert resp.json()['error']['code'] == custom_error.CANDIDATE_FORBIDDEN


class TestBulkDelete(object):
    def test_bulk_delete_using_ids(self, user_first, access_token_first, talent_pool):
        """
        Test: Delete candidates in bulk
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        # Create 50 candidates
        number_of_candidates = 50
        candidates_data = generate_single_candidate_data(talent_pool_ids=[talent_pool.id],
                                                         number_of_candidates=number_of_candidates)
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, candidates_data)
        assert create_resp.status_code == requests.codes.CREATED
        print response_info(create_resp)
        created_candidates = create_resp.json()['candidates']
        assert len(created_candidates) == number_of_candidates

        # Delete all 50 candidates
        candidates_for_delete = dict(_candidate_ids=[candidate['id'] for candidate in created_candidates])
        bulk_del_resp = send_request('delete', CandidateApiUrl.CANDIDATES, access_token_first, candidates_for_delete)
        print response_info(bulk_del_resp)
        assert bulk_del_resp.status_code == requests.codes.NO_CONTENT

    def test_bulk_delete_using_email_addresses(self, user_first, access_token_first, talent_pool):
        """
        Test: Delete candidates in bulk
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        # Create 50 candidates
        number_of_candidates = 3
        candidates_data = generate_single_candidate_data(talent_pool_ids=[talent_pool.id],
                                                         number_of_candidates=number_of_candidates)
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, candidates_data)
        assert create_resp.status_code == requests.codes.CREATED
        print response_info(create_resp)
        created_candidates = create_resp.json()['candidates']
        assert len(created_candidates) == number_of_candidates

        db.session.commit()

        candidate_ids = {candidate['id'] for candidate in created_candidates}
        candidate_emails_from_ids = [candidate_email.address for candidate_email in
                                     CandidateEmail.query.join(Candidate).filter(Candidate.id.in_(candidate_ids)).all()]

        # Delete all 50 candidates
        candidates_for_delete = dict(_candidate_emails=candidate_emails_from_ids)
        bulk_del_resp = send_request('delete', CandidateApiUrl.CANDIDATES, access_token_first, candidates_for_delete)
        print response_info(bulk_del_resp)
        assert bulk_del_resp.status_code == requests.codes.NO_CONTENT

    def test_delete_candidates_with_same_emails_from_diff_domains(self, user_first, access_token_first, talent_pool,
                                                                  talent_pool_second, access_token_second):
        """
        Test: Create two candidates with identical email addresses in different domains, then delete one them
        """
        user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
        db.session.commit()

        identical_email = fake.safe_email()

        def _candidate_data(talent_pool_id):
            return {
                'candidates': [
                    {
                        'talent_pool_ids': {'add': [talent_pool_id]},
                        'emails': [{'address': identical_email}]
                    }
                ]
            }

        # Create first candidate in user_first's domain
        candidate_first_data = _candidate_data(talent_pool.id)
        create_first = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, candidate_first_data)
        print response_info(create_first)
        assert create_first.status_code == requests.codes.CREATED

        # Create second candidate in user_second's domain
        candidate_second_data = _candidate_data(talent_pool_second.id)
        create_second = send_request('post', CandidateApiUrl.CANDIDATES, access_token_second, candidate_second_data)
        print response_info(create_second)
        assert create_second.status_code == requests.codes.CREATED

        # Delete user_first's candidate using candidate's email address
        data = {'_candidate_emails': [identical_email]}
        del_first = send_request('delete', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(del_first)
        assert del_first.status_code == requests.codes.NO_CONTENT

        # Candidate second should not have been deleted
        candidate_second_id = create_second.json()['candidates'][0]['id']
        get_candidate_second = send_request('get', CandidateApiUrl.CANDIDATE % candidate_second_id, access_token_second)
        print response_info(get_candidate_second)
        assert get_candidate_second.status_code == requests.codes.OK


class TestHideCandidate(object):
    """
    Test Cases for hiding candidate(s) via patch v1/candidates
    """
    def test_hide_candidate_and_retrieve_it(self, access_token_first, talent_pool):
        """
        Test:   Hide a Candidate and then retrieve it
        Expect: 404, Not Found error
        """
        # Create Candidate
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
        assert get_resp.status_code == requests.codes.NOT_FOUND
        assert get_resp.json()['error']['code'] == custom_error.CANDIDATE_IS_HIDDEN

    def test_hide_candidate_via_email(self, access_token_first, talent_pool):
        """
        Test:   Hide a Candidate via candidate's email
        Expect: 200
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate
        candidate_id = create_resp.json()['candidates'][0]['id']

        # Hide Candidate
        hide_data = {'candidates': [{'id': candidate_id, 'hide': True}]}
        resp = send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, hide_data)
        print response_info(resp)
        assert resp.status_code == requests.codes.OK
        assert resp.json()['hidden_candidate_ids'][0] == candidate_id


class TestDeleteCandidateAddress(object):
    def test_non_logged_in_user_delete_can_address(self):
        """
        Test:   Delete candidate's address without logging in
        Expect: 401
        """
        # Delete Candidate's addresses
        resp = send_request('delete', CandidateApiUrl.ADDRESSES % '5', None)
        print response_info(resp)
        assert resp.status_code == requests.codes.UNAUTHORIZED
        # assert resp.json()['error']['code'] == 11  # TODO: move service custom error codes into common and use mapping

    def test_delete_candidate_address_with_bad_input(self, access_token_second):
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
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)

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


class TestDeleteCandidateAOI(object):

    def test_delete_candidate_aoi_with_bad_input(self):
        """
        Test:   Attempt to delete candidate aoi with non integer values for candidate_id & aoi_id
        Expect: 404
        """
        # Delete Candidate's areas of interest
        resp = send_request('delete', CandidateApiUrl.AOIS % 'x', None)
        print response_info(resp)
        assert resp.status_code == 404

        # Delete Candidate's area of interest
        resp = send_request('delete', CandidateApiUrl.AOI % (5, 'x'), None)
        print response_info(resp)
        assert resp.status_code == 404

    def test_delete_can_aoi_of_a_candidate_belonging_to_a_diff_user(
            self, access_token_first, user_first, talent_pool, user_second, access_token_second):
        """
        Test:   Attempt to delete the aois of a Candidate that belongs to a user in a diff domain
        Expect: 204
        """

        # Create candidate_1 & candidate_2 with user_first & user_first_2
        data = generate_single_candidate_data([talent_pool.id])
        create_resp_1 = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        candidate_1_id = create_resp_1.json()['candidates'][0]['id']

        # Delete candidate_1's areas of interest with user_first_2 logged in
        updated_resp = send_request('delete', CandidateApiUrl.AOIS % candidate_1_id, access_token_second)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403
        assert updated_resp.json()['error']['code'] == custom_error.CANDIDATE_FORBIDDEN

    def test_delete_all_of_candidates_areas_of_interest(self, access_token_first, user_first, talent_pool, domain_aois):
        """
        Test:   Remove all of candidate's aois from db
        Expect: 204, Candidate should not have any aois left
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id], domain_aois)

        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate's aois
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_aois = get_resp.json()['candidate']['areas_of_interest']

        # Remove all of Candidate's areas of interest
        updated_resp = send_request('delete', CandidateApiUrl.AOIS % candidate_id, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']

        assert updated_resp.status_code == 204
        assert len(can_dict_after_update['areas_of_interest']) == 0
        assert AreaOfInterest.query.get(can_aois[0]['id']) # AreaOfInterest should still be in db
        assert AreaOfInterest.query.get(can_aois[1]['id']) # AreaOfInterest should still be in db

    def test_delete_can_area_of_interest(self, access_token_first, user_first, talent_pool, domain_aois):
        """
        Test:   Remove Candidate's area of interest from db
        Expect: 204, Candidate's aois must be less 1 AND no AreaOfInterest should be deleted
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id], domain_aois)
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate areas of interest
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_aois = get_resp.json()['candidate']['areas_of_interest']

        # Current number of Candidate's areas of interest
        candidate_aois_count = len(can_aois)

        # Remove one of Candidate's area of interest
        url = CandidateApiUrl.AOI % (candidate_id, can_aois[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']

        assert updated_resp.status_code == 204
        assert len(can_dict_after_update['areas_of_interest']) == candidate_aois_count - 1
        assert AreaOfInterest.query.get(can_aois[0]['id']) # AreaOfInterest should still be in db
        assert AreaOfInterest.query.get(can_aois[1]['id']) # AreaOfInterest should still be in db


class TestDeleteCandidateCustomField(object):

    def test_delete_candidate_custom_field_with_bad_input(self):
        """
        Test:   Attempt to delete candidate custom_field with non integer values for candidate_id & custom_field_id
        Expect: 404
        """
        # Delete Candidate's custom fields
        resp = send_request('delete', CandidateApiUrl.CUSTOM_FIELDS % 'x', None)
        print response_info(resp)
        assert resp.status_code == 404

        # Delete Candidate's custom field
        resp = send_request('delete', CandidateApiUrl.CUSTOM_FIELD % (5, 'x'), None)
        print response_info(resp)
        assert resp.status_code == 404

    def test_delete_custom_fields_of_a_candidate_belonging_to_a_diff_user(self, access_token_first, user_first,
                                                                          talent_pool, user_second, access_token_second,
                                                                          domain_custom_fields):
        """
        Test:   Delete custom fields of a Candidate that belongs to a user in a different domain
        Expect: 204
        """

        # Create candidate_1 & candidate_2 with user_first & user_first_2
        data = generate_single_candidate_data([talent_pool.id], custom_fields=domain_custom_fields)
        create_resp_1 = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve candidate_1
        candidate_1_id = create_resp_1.json()['candidates'][0]['id']

        # Delete candidate_1's custom fields with user_first_2 logged in
        url = CandidateApiUrl.CUSTOM_FIELDS % candidate_1_id
        updated_resp = send_request('delete', url, access_token_second)
        print response_info(updated_resp)
        assert updated_resp.status_code == 403
        assert updated_resp.json()['error']['code'] == custom_error.CANDIDATE_FORBIDDEN

    def test_delete_candidates_custom_fields(self, access_token_first, user_first, talent_pool, domain_custom_fields):
        """
        Test:   Remove all of candidate's custom fields from db
        Expect: 204, Candidate should not have any custom fields left AND no CustomField should be deleted
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id], custom_fields=domain_custom_fields)
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate's custom fields
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_custom_fields = get_resp.json()['candidate']['custom_fields']
        db.session.commit()
        custom_field_id_1 = CandidateCustomField.query.get(can_custom_fields[0]['id']).custom_field_id
        custom_field_id_2 = CandidateCustomField.query.get(can_custom_fields[1]['id']).custom_field_id

        # Remove all of Candidate's custom fields
        updated_resp = send_request('delete', CandidateApiUrl.CUSTOM_FIELDS % candidate_id, access_token_first)
        print response_info(updated_resp)

        # Retrieve Candidate after update
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_dict_after_update = get_resp.json()['candidate']

        assert updated_resp.status_code == 204
        assert len(can_dict_after_update['custom_fields']) == 0
        assert CustomField.query.get(custom_field_id_1) # CustomField should still be in db
        assert CustomField.query.get(custom_field_id_2) # CustomField should still be in db

    def test_delete_can_custom_field(self, access_token_first, user_first, talent_pool, domain_custom_fields):
        """
        Test:   Remove Candidate's custom field from db
        Expect: 204, Candidate's custom fields must be less 1 AND no CustomField should be deleted
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id], custom_fields=domain_custom_fields)
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

        # Retrieve Candidate custom fields
        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        can_custom_fields = get_resp.json()['candidate']['custom_fields']
        db.session.commit()
        custom_field_id_1 = CandidateCustomField.get_by_id(can_custom_fields[0]['id']).custom_field_id
        custom_field_id_2 = CandidateCustomField.get_by_id(can_custom_fields[1]['id']).custom_field_id

        # Remove one of Candidate's custom field
        url = CandidateApiUrl.CUSTOM_FIELD % (candidate_id, can_custom_fields[0]['id'])
        updated_resp = send_request('delete', url, access_token_first)
        print response_info(updated_resp)
        assert updated_resp.status_code == 204
        assert CustomField.query.get(custom_field_id_1) # CustomField should still be in db
        assert CustomField.query.get(custom_field_id_2) # CustomField should still be in db
