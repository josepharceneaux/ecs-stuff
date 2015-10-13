import json
import uuid
# from activity_service.tests.api_tests import *


USER_PASSWORD = 'temp976892'

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
import requests
def test_get_user_without_authentication():
    # Get user
    user_id = 5
    resp = requests.get('http://127.0.0.1:5000/v1/users/%s' % user_id)
    print resp
    assert resp.status_code == 401


def test_user_authentication(test_user):
    print "*" * 100
    user = test_user
    print user
    print "*" * 100
    # Login user
    user_id = 1
    resp = requests.get('http://127.0.0.1:5000/v1/users/%s' % user_id)
    print resp
    assert resp.status_code == 200


def _test_get_user_with_admin_user_in_domain(sample_admin_user, webclient):
    """
    :type webclient: TalentWebClient
    """
    # Login admin user
    admin_user = sample_admin_user
    webclient.cas_login(admin_user['email'], USER_PASSWORD)
    assert webclient.status == 200

    # Create user
    webclient.call_controller_function('api', 'users.json/%s', data=json.dumps(generate_user_data()))
    print webclient.json()
    user_id = webclient.json()['users'][0]['id']
    assert webclient.status == 200

    # Get user
    webclient.call_controller_function('api', 'users.json/%s' % user_id)
    assert webclient.status == 200
    assert 'id' in webclient.json()['user']
    assert 'first_name' and 'last_name' and 'email' in webclient.json()['user']
    assert 'password' not in webclient.json()['user']
    assert 'registration_key' not in webclient.json()['user']
    assert 'reset_password_key' not in webclient.json()['user']
