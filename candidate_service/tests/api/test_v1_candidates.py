"""
Test cases for candidate-restful-services
"""
# Standard library
import json

# Candidate Service app instance
from candidate_service.candidate_app import app

# Sample data
from common.tests.sample_data import generate_single_candidate_data, candidate_data_for_update

# Models
from common.models.candidate import Candidate
from candidate_service.common.models.user import User

# Conftest
from common.tests.conftest import UserAuthentication
from common.tests.conftest import *


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


def test_get_candidate_via_invalid_email(sample_user, user_auth):
    """
    Test:   retrieve candidate via an invalid email address
    Expect: 400
    """
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    resp = requests.get(
        url=BASE_URI + "/%s" % 'bad_email.com',
        headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )
    assert resp.status_code == 400
    print "\nresp = %s" % resp.json()


def test_get_candidate_via_id_and_email():
    """
    Test:   retrieve candidate via candidate's ID and candidate's Email address
    Expect: 200 in both cases
    """
    resp = requests.get(url=BASE_URI + '/4')
    assert resp.status_code == 200
    print "\n resp = %s" % resp.json()

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
    sample_candidate_data = generate_single_candidate_data()
    r = requests.post(
        url=BASE_URI,
        data=json.dumps(sample_candidate_data),
        headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )
    resp_dict = r.json()
    print "\n sample_candidate_1 = %s" % sample_candidate_data
    print "\n resp_status_code = %s" % r.status_code
    print "\n resp_object = %s" % resp_dict

    r2 = requests.get(
        url=BASE_URI + '/%s' % resp_dict['candidates'][0]['id'],
        headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )
    resp_dict2 = r2.json()
    print "\n resp_dict2 = %s" % resp_dict2

    # Update candidate
    can_dict = resp_dict2['candidate']
    sample_candidate_data_2 = candidate_data_for_update(
        can_dict['id'],
        can_dict['emails'][0]['id'], can_dict['emails'][1]['id'],
        can_dict['phones'][0]['id'], can_dict['phones'][1]['id'],
        can_dict['addresses'][0]['id'], can_dict['addresses'][1]['id'],
        can_dict['work_preference'][0]['id'],
        can_dict['work_experiences'][0]['id'],
        # can_dict['work_experiences'][0]['work_experience_bullets'][0]['id'],
        can_dict['educations'][0]['id'], can_dict['educations'][0]['degree_details'][0]['id'],
        # can_dict['educations'][0]['degree_details'][0]['degree_bullets'][0]['id'],
        can_dict['military_services'][0]['id'],
        can_dict['preferred_locations'][0]['id'], can_dict['preferred_locations'][1]['id'],
        can_dict['skills'][0]['id'], can_dict['skills'][1]['id'], can_dict['skills'][2]['id'],
        can_dict['social_networks'][0]['id'], can_dict['social_networks'][1]['id']
    )
    print "\n sample_candidate_2 = %s" % sample_candidate_data_2
    r = requests.patch(
        url=BASE_URI,
        data=json.dumps(sample_candidate_data_2),
        headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )
    print "\n resp_status_code: %s" % r.status_code
    print "\n resp_dict: %s" % r.json()


    # assert r.status_code == 201
    # assert 'candidates' in resp_object
    # assert isinstance(resp_object, dict)
    # assert isinstance(resp_object['candidates'], list)

def test_create_already_existing_candidate(sample_user, user_auth):
    """
    Test:   create an already existing candidate
    Expect: 400
    :type   sample_user:    User
    :type   user_auth:      UserAuthentication
    :return:
    """
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    data = {'candidates': [
        {'emails': [{'label': 'work', 'address': 'temp@gettalent.com'}]}
    ]}
    r = requests.post(
        url=BASE_URI,
        data=json.dumps(data),
        headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )
    resp_object = r.json()

    db.session.commit()

    candidate = Candidate.query.get(resp_object.get('candidates')[0].get('id'))
    data = {'candidates': [
        {'emails': [{'label': 'work', 'address': candidate.candidate_emails[0].address}]}
    ]}
    r = requests.post(
        url=BASE_URI,
        data=json.dumps(data),
        headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )
    resp_object = r.json()

# def test_create_candidate_without_inputs(sample_user, user_auth):
#     """
#     Test:   create a new candidate with empty candidate object
#     Expect: 400
#     :type   sample_user:    User
#     :type   user_auth:      UserAuthentication
#     :return:
#     """
#     auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
#     r = requests.post(
#         url=BASE_URI,
#         data=json.dumps({'candidates': [{}]}),
#         headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
#     )
#     resp_object = r.json()
#     print "\n resp_object = %s" % resp_object
#
#     current_number_of_candidates = db.session.query(Candidate).count()
#
#     assert r.status_code == 400
#     assert 'error' in resp_object
#     # Creation was unsuccessful, number of candidates must not increase
#     assert current_number_of_candidates == db.session.query(Candidate).count() #TODO: check count in domain not overall


# def test_create_already_existing_candidate(sample_user, user_auth):
#     """
#     Test:   create an already existing candidate
#     Expect: 400
#     :type   sample_user:    User
#     :type   user_auth:      UserAuthentication
#     :return:
#     """
#     # TODO: assume db is empty. Create a candidate, and then try to recreate it
#     auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
#     candidate = db.session.query(Candidate).first()
#     candidate_email = candidate.candidate_emails[0].address
#     data = {'candidates': [
#         {'emails': [{'label': 'work', 'address': candidate_email}]}
#     ]}
#     r = requests.post(
#         url=BASE_URI,
#         data=json.dumps(data),
#         headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
#     )
#     resp_object = r.json()
#     print "\n resp_object = %s" % resp_object
#
#     assert r.status_code == 400
#     assert 'error' in resp_object

    db.session.delete(candidate)
    db.session.commit()

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
