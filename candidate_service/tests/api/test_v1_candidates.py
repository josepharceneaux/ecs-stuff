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
# def test_get_candidate(sample_user, user_auth):
#     """
#     :param sample_user: user-row
#     :type user_auth:    UserAuthentication
#     """
#     user = sample_user
#
#     candidate_id = 4
#     r = requests.get("http://127.0.0.1:8005/v1/candidates/%s" % candidate_id)
#
#     assert r.status_code == 200
#     assert 'candidate' in r.json()
#     assert 'id', 'emails' in r.json()['candidate']
#     print "\nresp = %s" % r.json()


####################################
# test cases for POSTing candidate #
####################################
def test_create_candidate(sample_user, user_auth):
    """
    :param sample_user: user-row
    :type  user_auth:   UserAuthentication
    """
    user = sample_user

    authenticate = user_auth.get_auth_token(user_row=sample_user, get_bearer_token=True)
    print "-" * 100
    print "authentication = %s" % authenticate

    import json
    r = requests.post(
        url='http://127.0.0.1:8005/v1/candidates',
        data=json.dumps(generate_single_candidate_data()),
        headers={'Authorization': authenticate['access_token']}
    )
    print "\nresp = %s" % r
    print "\nresp = %s" % r.json()