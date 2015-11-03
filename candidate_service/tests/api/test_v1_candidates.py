"""
Test cases for candidate-restful-services
"""
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
    # auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    candidate_id = 3
    resp = requests.get(
        url=BASE_URI + "/%s" % candidate_id
        # headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )
    assert resp.status_code == 403
    print "\nresp = %s" % resp.json()


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


def test_get_candidate_via_id_and_email():
    """
    Test:   retrieve candidate via candidate's ID and candidate's Email address
    Expect: 200 in both cases
    """
    resp = requests.get(
        url=BASE_URI + '/%s' % 4
    )
    assert resp.status_code == 200
    print "\n resp = %s" % resp.json()

#######################################
# test cases for POSTing candidate(s) #
#######################################
def test_post_candidate():
    import json
    from common.tests.fake_data import generate_single_candidate_data
    r = requests.post(
        url=BASE_URI,
        data=json.dumps(generate_single_candidate_data())
    )
    print "resp_status = %s" % r.status_code
    print "resp = %s" % r

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
