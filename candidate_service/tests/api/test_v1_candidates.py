from common.tests.conftest import UserAuthentication
from common.tests.conftest import *

USER_PASSWORD = 'Talent15'

def generate_single_candidate_data():
    data = {'candidates': [
        {
            'first_name': 'Wu Tang',
            'last_name': 'Clan',
            'emails': [{'label': 'Primary', 'address': 'wutangclan_%s@hiphop.com' % str(uuid.uuid4())[0:8]}],
            'phones': [{'label': 'mobile', 'value': '4084096677'}],
            'addresses': [{'address_line_1': '%s S. third St.' % random.randint(100, 9999),
                           'city': 'San Jose', 'state': 'CA', 'zip_code': '95118', 'country': 'US'}],
            'work_preference': {"relocate": "true", "authorization": "US Citizen", "telecommute": "true",
                                "travel": 25, "hourly_rate": 35.50, "salary": 75000,
                                "tax_terms": "full-time employment", "security_clearance": "none",
                                "third_party": "false"},
            'educations': [{'school_name': 'SJSU', 'city': 'San Jose', 'country': 'USA'}]
        }
    ]}
    return data


def generate_multiple_candidates_data():
    data = {'candidates': [
        {'first_name': 'John', 'last_name': 'Kennedy',
         'emails': [{'label': 'Primary', 'address': 'j.kennedy_%s@test.com' % str(uuid.uuid4())[0:8]}]},
        {'first_name': 'Amir', 'last_name': 'Beheshty',
         'emails': [{'label': 'Primary', 'address': 'j.kennedy_%s@test.com' % str(uuid.uuid4())[0:8]}]},
        {'first_name': 'Nancy', 'last_name': 'Grey',
         'emails': [{'label': 'Primary', 'address': 'j.kennedy_%s@test.com' % str(uuid.uuid4())[0:8]}]}
    ]}
    return data

####################################
# test cases for GETting candidate #
####################################
BASE_URI = "http://127.0.0.1:8005/v1/candidates"
def test_get_candidate_from_forbidden_domain(sample_user, user_auth):
    """
    :param sample_user: user-row
    :type user_auth:    UserAuthentication
    """
    # todo: once POST is complete, will need to create candidate first and then retrieve it
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    candidate_id = 3
    resp = requests.get(
        url=BASE_URI + "/%s" % candidate_id,
        headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )
    assert resp.status_code == 403
    print "\nresp = %s" % resp
    print "\nresp = %s" % resp.json()


# ###############################################
# # test cases for GETting email_campaign_sends #
# ###############################################
# def test_get_email_campaign_sends():
#     candidate_id = 208
#     email_campaign_id = 3
#     r = requests.get('http://127.0.0.1:8005/v1/candidates/%s/email_campaigns/%s/email_campaign_sends'
#                      % (candidate_id, email_campaign_id))
#     print "resp = %s" % r
#     print "resp_json = %s" % r.text


#######################################
# test cases for POSTing candidate(s) #
#######################################


#########################################
# test cases for DELETEing candidate(s) #
#########################################