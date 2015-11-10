"""
Test cases for candidate-restful-services
"""
# Candidate Service app instance
from candidate_service.candidate_app import app

# Models
from candidate_service.common.models.user import User
from candidate_service.common.models.candidate import Candidate

# Conftest
from common.tests.conftest import UserAuthentication
from common.tests.conftest import *

# Helper functions
from helpers import (test_response, post_to_candidate_resource, get_from_candidate_resource)

####################################
# test cases for GETting candidate #
####################################
def test_get_candidate_without_authed_user(sample_user, user_auth):
    """
    Test:   attempt to retrieve candidate with bad access_token
    Expect: 401
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get auth token for sample_user
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)

    # Create Candidate
    resp = post_to_candidate_resource(access_token=auth_token_row['access_token'])
    resp_dict = resp.json()
    print test_response(resp.request, resp_dict, resp.status_code)
    assert resp.status_code == 201

    # Retrieve Candidate
    resp = get_from_candidate_resource(access_token=None,
                                       candidate_id=resp_dict['candidates'][0]['id'])
    resp_dict = resp.json()
    print test_response(resp.request, resp_dict, resp.status_code)
    assert resp.status_code == 401
    assert 'error' in resp_dict


def test_get_candidate_without_id_or_email(sample_user, user_auth):
    """
    Test:   attempt to retrieve candidate without providing ID or Email
    Expect: 400
    :type sample_user:  User
    :type user_auth:    UserAuthentication
    """
    # Get auth token for sample_user
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)

    # Create Candidate
    resp = post_to_candidate_resource(access_token=auth_token_row['access_token'])
    resp_dict = resp.json()
    print test_response(resp.request, resp_dict, resp.status_code)
    assert resp.status_code == 201

    # Retrieve Candidate without providing ID or Email
    resp = get_from_candidate_resource(access_token=auth_token_row['access_token'],
                                       candidate_id=None, candidate_email=None)
    resp_dict = resp.json()
    print test_response(resp.request, resp_dict, resp.status_code)
    assert resp.status_code == 400
    assert 'error' in resp_dict


def test_get_candidate_from_forbidden_domain(sample_user, user_auth, sample_user_2):
    """
    Test:   attempt to retrieve a candidate outside of logged-in-user's domain
    Expect: 403 status_code

    :type sample_user:      User
    :type sample_user_2:    User
    :type user_auth:        UserAuthentication
    """
    # Get auth token for sample_user
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)

    # Create Candidate
    resp = post_to_candidate_resource(access_token=auth_token_row['access_token'])
    resp_dict = resp.json()
    print test_response(resp.request, resp_dict, resp.status_code)
    assert resp.status_code == 201
    assert 'candidates' in resp_dict and 'id' in resp_dict['candidates'][0]

    # Get auth token for sample_user_2
    auth_token_row = user_auth.get_auth_token(sample_user_2, get_bearer_token=True)

    # Retrieve candidate from a different domain
    resp = get_from_candidate_resource(access_token=auth_token_row['access_token'],
                                       candidate_id=resp_dict['candidates'][0]['id'])
    resp_dict = resp.json()
    print test_response(resp.request, resp_dict, resp.status_code)
    assert resp.status_code == 403
    assert 'error' in resp_dict


def test_get_candidate_via_invalid_email(sample_user, user_auth):
    """
    Test:   retrieve candidate via an invalid email address
    Expect: 400
    """
    # Get auth token for sample_user
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)

    # Retrieve candidate via candidate's email
    resp = get_from_candidate_resource(access_token=auth_token_row['access_token'],
                                       candidate_email='bad_email.com')
    print test_response(resp.request, resp.json(), resp.status_code)
    assert resp.status_code == 400
    assert 'error' in resp.json()


def test_get_candidate_via_id_and_email(sample_user, user_auth):
    """
    Test:   retrieve candidate via candidate's ID and candidate's Email address
    Expect: 200 in both cases
    :type sample_user:    User
    :type user_auth:      UserAuthentication
    """
    # Get auth token
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)

    # Create candidate
    resp = post_to_candidate_resource(access_token=auth_token_row['access_token'])
    resp_dict = resp.json()
    print test_response(resp.request, resp_dict, resp.status_code)

    db.session.commit()

    # Candidate ID & Email
    candidate_id = resp_dict['candidates'][0]['id']
    candidate_email = db.session.query(Candidate).get(candidate_id).candidate_emails[0].address

    # Get candidate via Candidate ID
    resp = get_from_candidate_resource(access_token=auth_token_row['access_token'],
                                       candidate_id=candidate_id)
    resp_dict = resp.json()
    print test_response(resp.request, resp_dict, resp.status_code)
    assert resp.status_code == 200
    assert 'candidate' in resp_dict and 'id' in resp_dict['candidate']

    # Get candidate via Candidate Email
    resp = get_from_candidate_resource(access_token=auth_token_row['access_token'],
                                       candidate_email=candidate_email)
    resp_dict = resp.json()
    print test_response(resp.request, resp_dict, resp.status_code)
    assert resp.status_code == 200
    assert 'candidate' in resp_dict and 'id' in resp_dict['candidate']

#######################################
# test cases for POSTing candidate(s) #
#######################################
def test_create_candidate(sample_user, user_auth):
    """
    Test:   create a new candidate and candidate's info
    Expect: 200
    :type   sample_user:  User
    :type   user_auth:    UserAuthentication
    """
    # Get auth token
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)

    # Create Candidate
    resp = post_to_candidate_resource(access_token=auth_token_row['access_token'])
    resp_dict = resp.json()
    print test_response(resp.request, resp_dict, resp.status_code)
    assert resp.status_code == 201
    assert 'candidates' in resp_dict and 'id' in resp_dict['candidates'][0]


    # # Update candidate
    # can_dict = resp_dict2['candidate']
    # sample_candidate_data_2 = candidate_data_for_update(
    #     can_dict['id'],
    #     can_dict['emails'][0]['id'], can_dict['emails'][1]['id'],
    #     can_dict['phones'][0]['id'], can_dict['phones'][1]['id'],
    #     can_dict['addresses'][0]['id'], can_dict['addresses'][1]['id'],
    #     can_dict['work_preference'][0]['id'],
    #     can_dict['work_experiences'][0]['id'],
    #     # can_dict['work_experiences'][0]['work_experience_bullets'][0]['id'],
    #     can_dict['educations'][0]['id'], can_dict['educations'][0]['degree_details'][0]['id'],
    #     # can_dict['educations'][0]['degree_details'][0]['degree_bullets'][0]['id'],
    #     can_dict['military_services'][0]['id'],
    #     can_dict['preferred_locations'][0]['id'], can_dict['preferred_locations'][1]['id'],
    #     can_dict['skills'][0]['id'], can_dict['skills'][1]['id'], can_dict['skills'][2]['id'],
    #     can_dict['social_networks'][0]['id'], can_dict['social_networks'][1]['id']
    # )
    # print "\n sample_candidate_2 = %s" % sample_candidate_data_2
    # r = requests.patch(
    #     url=BASE_URI,
    #     data=json.dumps(sample_candidate_data_2),
    #     headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    # )
    # print "\n resp_status_code: %s" % r.status_code
    # print "\n resp_dict: %s" % r.json()


    # assert r.status_code == 201
    # assert 'candidates' in resp_object
    # assert isinstance(resp_object, dict)
    # assert isinstance(resp_object['candidates'], list)

# def test_create_already_existing_candidate(sample_user, user_auth):
#     """
#     Test:   create an already existing candidate
#     Expect: 400
#     :type   sample_user:    User
#     :type   user_auth:      UserAuthentication
#     :return:
#     """
#     auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
#     data = {'candidates': [
#         {'emails': [{'label': 'work', 'address': 'temp@gettalent.com'}]}
#     ]}
#     r = requests.post(
#         url=BASE_URI,
#         data=json.dumps(data),
#         headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
#     )
#     resp_object = r.json()
#
#     db.session.commit()
#
#     candidate = Candidate.query.get(resp_object.get('candidates')[0].get('id'))
#     data = {'candidates': [
#         {'emails': [{'label': 'work', 'address': candidate.candidate_emails[0].address}]}
#     ]}
#     r = requests.post(
#         url=BASE_URI,
#         data=json.dumps(data),
#         headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
#     )

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
