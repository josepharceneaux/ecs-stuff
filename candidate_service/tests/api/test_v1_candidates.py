"""
Test cases for candidate-restful-services
"""
# Standard library
import json

# Sample data
from common.tests.sample_data import generate_single_candidate_data

# Models
from candidate_service.common.models.candidate import Candidate
from candidate_service.common.models.user import User

# Conftest
from common.tests.conftest import UserAuthentication
from common.tests.conftest import *

# Database connection. Note: This must be imported after importing * from conftest
# to ensure the db connection is not overridden
from candidate_service.candidate_app import db


BASE_URI = "http://127.0.0.1:8005/v1/candidates"

####################################
# test cases for GETting candidate #
####################################
def test_get_candidate_from_forbidden_domain(sample_user, user_auth):
    """
    Test:   attempt to retrieve a candidate outside of logged-in-user's domain
    Expect: 403 status_code

    :param sample_user: user-row
    :type user_auth:    UserAuthentication
    """
    # todo: once POST is complete, will need to create candidate first and then retrieve it
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    candidate_id = 4
    resp = requests.get(
        url=BASE_URI + "/%s" % candidate_id,
        headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )
    print "\nresp = %s" % resp.json()
    assert resp.status_code == 403


def test_get_candidate_via_invalid_email():
    """
    Test:   retrieve candidate via an invalid email address
    Expect: 400
    """
    resp = requests.get(
        url=BASE_URI + "/%s" % 'bad_email.com'
    )
    assert resp.status_code == 400
    print "\nresp = %s" % resp.json()


# def test_get_candidate_via_id_and_email():
#     """
#     Test:   retrieve candidate via candidate's ID and candidate's Email address
#     Expect: 200 in both cases
#     """
#     resp = requests.get(
#         url=BASE_URI + '/%s' % 4
#     )
#     assert resp.status_code == 200
#     print "\n resp = %s" % resp.json()

#######################################
# test cases for POSTing candidate(s) #
#######################################
def test_create_candidate(sample_user, user_auth):
    """
    Test:   create a new candidate and candidate's info
    Expect: 200
    :type   sample_user:  User
    :type   user_auth:    UserAuthentication
    :return {'candidates': [{'id': candidate_id}, ...]}
    """
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    r = requests.post(
        url=BASE_URI,
        data=json.dumps(generate_single_candidate_data()),
        headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )

    resp_object = r.json()
    print "\n resp_object = %s" % resp_object

    assert r.status_code == 201
    assert 'candidates' in resp_object
    assert isinstance(resp_object, dict)
    assert isinstance(resp_object['candidates'], list)


def test_create_candidate_without_inputs(sample_user, user_auth):
    """
    Test:   create a new candidate with empty candidate object
    Expect: 400
    :type   sample_user:    User
    :type   user_auth:      UserAuthentication
    :return:
    """
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    r = requests.post(
        url=BASE_URI,
        data=json.dumps({'candidates': [{}]}),
        headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )
    resp_object = r.json()
    print "\n resp_object = %s" % resp_object

    current_number_of_candidates = db.session.query(Candidate).count()

    assert r.status_code == 400
    assert 'error' in resp_object
    # Creation was unsuccessful, number of candidates must not increase
    assert current_number_of_candidates == db.session.query(Candidate).count() #TODO: check count in domain not overall


def test_create_already_existing_candidate(sample_user, user_auth):
    """
    Test:   create an already existing candidate
    Expect: 400
    :type   sample_user:    User
    :type   user_auth:      UserAuthentication
    :return:
    """
    # TODO: assume db is empty. Create a candidate, and then try to recreate it
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    candidate = db.session.query(Candidate).first()
    candidate_email = candidate.candidate_emails[0].address
    data = {'candidates': [
        {'emails': [{'label': 'work', 'address': candidate_email}]}
    ]}
    r = requests.post(
        url=BASE_URI,
        data=json.dumps(data),
        headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )
    resp_object = r.json()
    print "\n resp_object = %s" % resp_object

    assert r.status_code == 400
    assert 'error' in resp_object

########################################
# test cases for PATCHing candidate(s) #
########################################


#########################################
# test cases for DELETEing candidate(s) #
#########################################


###############################################
# test cases for GETting email_campaign_sends #
###############################################
# def test_get_email_campaign_sends():
#     candidate_id = 208
#     email_campaign_id = 3
#     r = requests.get('http://127.0.0.1:8005/v1/candidates/%s/email_campaigns/%s/email_campaign_sends'
#                      % (candidate_id, email_campaign_id))
#     print "resp = %s" % r
#     print "resp_json = %s" % r.text
