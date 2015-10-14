import requests
from common.tests.conftest import *


USER_PASSWORD = 'Talent15'

def generate_user_data():
    data = {'users': [
        {
            'first_name': 'Flipe',
            'last_name': 'Luiz',
            'email': 'f.luiz+%s@example.com' % str(uuid.uuid4())[0:8],
            'domain': '',
            'expiration_date': '',
            'brand': '',
            'department': '',
            'group': '',
            'KPI': ''
        }
    ]}
    return data


def update_user_data(user_id):
    return {'user_id': user_id, 'first_name': 'mohsen', 'last_name': 'johnson',
            'email': 'f.luiz+%s@example.com' % str(uuid.uuid4())[0:8]}


###############################
# test cases for GETting user #
###############################
def test_get_user_without_authentication():
    # Get user
    user_id = 5
    resp = requests.get('http://127.0.0.1:5000/v1/users/%s' % user_id)
    print resp
    assert resp.status_code == 401


def test_user_authentication(get_auth_token):
    # Login user
    user_login_credentials = get_auth_token

    print "user_login_credentials: %s" % user_login_credentials

    client_id = user_login_credentials['client_id']
    client_secret = user_login_credentials['client_secret']
    email = user_login_credentials['email']
    password = user_login_credentials['password']

    print "password: %s" % password
    print "email: %s" % email

    data = {'client_id':client_id,
            'client_secret': client_secret,
            'username': email,
            'password': USER_PASSWORD,
            'grant_type':'password'}

    resp = requests.post('http://localhost:5000/oauth2/token', data=data)
    print "resp: %s" % resp
    assert resp.status_code == 200


# def _test_get_user_with_admin_user_in_domain(sample_admin_user, webclient):
#     """
#     :type webclient: TalentWebClient
#     """
#     # Login admin user
#     admin_user = sample_admin_user
#     webclient.cas_login(admin_user['email'], USER_PASSWORD)
#     assert webclient.status == 200
#
#     # Create user
#     webclient.call_controller_function('api', 'users.json/%s', data=json.dumps(generate_user_data()))
#     print webclient.json()
#     user_id = webclient.json()['users'][0]['id']
#     assert webclient.status == 200
#
#     # Get user
#     webclient.call_controller_function('api', 'users.json/%s' % user_id)
#     assert webclient.status == 200
#     assert 'id' in webclient.json()['user']
#     assert 'first_name' and 'last_name' and 'email' in webclient.json()['user']
#     assert 'password' not in webclient.json()['user']
#     assert 'registration_key' not in webclient.json()['user']
#     assert 'reset_password_key' not in webclient.json()['user']
