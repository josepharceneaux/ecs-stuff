"""
Test cases for CandidateResource/get()
"""
# Candidate Service app instance
from candidate_service.candidate_app import app
# Conftest
from candidate_service.common.tests.conftest import *
# Helper functions
from helpers import (
    response_info, request_to_candidates_resource, request_to_candidate_resource, AddUserRoles
)
from candidate_service.tests.api.candidate_sample_data import generate_single_candidate_data
# Routes
from candidate_service.common.routes import CandidateApiUrl
# Custom Errors
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error


######################## Candidate ########################
class TestGetCandidate(object):
    @staticmethod
    def create_candidate(access_token_first, user_first, talent_pool, data=None):
        AddUserRoles.add(user=user_first)
        if data is None:
            data = generate_single_candidate_data([talent_pool.id])
        return request_to_candidates_resource(access_token_first, 'post', data)

    def test_create_candidate_with_empty_input(self, access_token_first, user_first, talent_pool):
        """
        Test: Retrieve user's candidate(s) by providing empty string for data
        Expect: 400
        """
        # Create candidate
        AddUserRoles.add(user=user_first)
        resp = requests.post(
            url=CandidateApiUrl.CANDIDATES,
            headers={'Authorization': 'Bearer {}'.format(access_token_first),
                     'content-type': 'application/json'}
        )
        print response_info(response=resp)
        assert resp.status_code == 400
        assert resp.json()['error']['code'] == custom_error.MISSING_INPUT

    def test_create_candidate_with_non_json_data(self, access_token_first, user_first, talent_pool):
        """
        Test: Send post request with non json data
        Expect: 400
        """
        # Create candidate
        AddUserRoles.add(user=user_first)
        resp = requests.post(
            url=CandidateApiUrl.CANDIDATES,
            headers={'Authorization': 'Bearer {}'.format(access_token_first),
                     'content-type': 'application/xml'},
            data=generate_single_candidate_data([talent_pool.id])
        )
        print response_info(response=resp)
        assert resp.status_code == 400
        assert resp.json()['error']['code'] == custom_error.INVALID_INPUT


def test_get_candidate_without_authed_user(access_token_first, user_first, talent_pool):
    """
    Test:   Attempt to retrieve candidate with no access token
    Expect: 401
    """
    # Create Candidate
    AddUserRoles.add_and_get(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    create_resp = request_to_candidates_resource(access_token_first, 'post', data)
    resp_dict = create_resp.json()
    print response_info(create_resp)
    assert create_resp.status_code == 201

    # Retrieve Candidate
    candidate_id = resp_dict['candidates'][0]['id']
    resp = request_to_candidate_resource(None, 'get', candidate_id)
    print response_info(resp)
    assert resp.status_code == 401
    assert resp.json()['error']['code'] == 11 # Bearer token not found


def test_get_candidate_without_id_or_email(access_token_first, user_first, talent_pool):
    """
    Test:   Attempt to retrieve candidate without providing ID or Email
    Expect: 400
    """
    # Create Candidate
    AddUserRoles.add_and_get(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    resp = request_to_candidates_resource(access_token_first, 'post', data)
    print response_info(resp)
    assert resp.status_code == 201

    # Retrieve Candidate without providing ID or Email
    resp = requests.get(url=CandidateApiUrl.CANDIDATE,
                        headers={'Authorization': 'Bearer {}'.format(access_token_first)})
    print response_info(resp)
    assert resp.status_code == 400
    assert resp.json()['error']['code'] == custom_error.INVALID_EMAIL


def test_get_candidate_from_forbidden_domain(access_token_first, user_first, talent_pool,
                                             access_token_second, user_second):
    """
    Test:   Attempt to retrieve a candidate outside of logged-in-user's domain
    Expect: 403 status_code
    """
    AddUserRoles.add(user=user_first)
    AddUserRoles.get(user=user_second)

    # Create Candidate
    data = generate_single_candidate_data([talent_pool.id])
    resp = request_to_candidates_resource(access_token_first, 'post', data)
    resp_dict = resp.json()
    print response_info(resp)

    # Retrieve candidate from a different domain
    candidate_id = resp_dict['candidates'][0]['id']
    resp = request_to_candidate_resource(access_token_second, 'get', candidate_id)
    print response_info(resp)
    assert resp.status_code == 403
    assert resp.json()['error']['code'] == custom_error.CANDIDATE_FORBIDDEN


def test_get_candidate_via_invalid_email(access_token_first, user_first, talent_pool):
    """
    Test:   Retrieve candidate via an invalid email address
    Expect: 400
    """
    AddUserRoles.get(user=user_first)

    # Retrieve Candidate via candidate's email
    resp = request_to_candidate_resource(access_token_first, 'get', candidate_email='bad_email.com')
    print response_info(resp)
    assert resp.status_code == 400
    assert resp.json()['error']['code'] == custom_error.INVALID_EMAIL


def test_get_can_via_id_and_email(access_token_first, user_first, talent_pool):
    """
    Test:   Retrieve candidate via candidate's ID and candidate's Email address
    Expect: 200 in both cases
    """
    # Create candidate
    AddUserRoles.add_and_get(user=user_first)
    data = generate_single_candidate_data([talent_pool.id])
    resp = request_to_candidates_resource(access_token_first, 'post', data)
    resp_dict = resp.json()
    print response_info(resp)

    db.session.commit()

    # Candidate ID & Email
    candidate_id = resp_dict['candidates'][0]['id']
    candidate_email = Candidate.get_by_id(candidate_id).emails[0].address

    # Get candidate via Candidate ID
    resp = request_to_candidate_resource(access_token_first, 'get', candidate_id)

    resp_dict = resp.json()
    print response_info(resp)
    assert resp.status_code == 200
    assert isinstance(resp_dict, dict)

    # Get candidate via Candidate Email
    resp = request_to_candidate_resource(access_token_first, 'get', candidate_email=candidate_email)

    resp_dict = resp.json()
    print response_info(resp)
    assert resp.status_code == 200
    assert isinstance(resp_dict, dict)


def test_get_non_existing_candidate(access_token_first, user_first, talent_pool):
    """
    Test: Attempt to retrieve a candidate that doesn't exists or is web-hidden
    """
    # Retrieve non existing candidate
    AddUserRoles.all_roles(user=user_first)
    last_candidate = Candidate.query.order_by(Candidate.id.desc()).first()
    non_existing_candidate_id = last_candidate.id * 100
    resp = request_to_candidate_resource(access_token_first, 'get', non_existing_candidate_id)
    print response_info(resp)
    assert resp.status_code == 404
    assert resp.json()['error']['code'] == custom_error.CANDIDATE_NOT_FOUND

    # Create Candidate and hide it
    data = generate_single_candidate_data([talent_pool.id])
    candidate_id = request_to_candidates_resource(access_token_first, 'post', data)\
        .json()['candidates'][0]['id']
    request_to_candidate_resource(access_token_first, 'delete', candidate_id)
    # Retrieve web-hidden candidate
    resp = request_to_candidate_resource(access_token_first, 'get', candidate_id)
    print response_info(resp)
    assert resp.status_code == 404
    assert resp.json()['error']['code'] == custom_error.CANDIDATE_IS_HIDDEN
