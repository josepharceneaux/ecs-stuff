__author__ = 'Erik Farmer'
# Standard Library
from datetime import datetime
from datetime import timedelta
import json
# Third Party
import requests
# Application Specific
from activity_service.common.utils.handy_functions import random_word
from .fixtures import activities_fixture
from .fixtures import candidate_fixture
from .fixtures import candidate_source_fixture
from .fixtures import client_fixture
from .fixtures import culture_fixture
from .fixtures import domain_fixture
from .fixtures import org_fixture
from .fixtures import token_fixture
from .fixtures import user_fixture

APP_ENDPOINT = 'http://127.0.0.1:8002'


def test_call_requires_auth(token_fixture):
    test_url = '{}/activities/1'.format(APP_ENDPOINT)
    response = requests.get(test_url, headers={'Authorization': 'Bearer {}'.format(
        token_fixture.access_token)})
    assert response.status_code == 200
    response = requests.get(test_url, headers={'Authorization': 'Bearer bad_token'})
    assert response.status_code == 401


def test_reponse_is_user_filtered(token_fixture):
    test_url = '{}/activities/1'.format(APP_ENDPOINT)
    response = requests.get(test_url, headers={'Authorization': 'Bearer {}'.format(
        token_fixture.access_token)})
    assert json.loads(response.content)['total_count'] == 4


def test_response_can_be_time_filtered(token_fixture):
    today = (datetime.today() + timedelta(minutes=-1)).isoformat()
    test_url = '{}/activities/1?start_time={}'.format(APP_ENDPOINT, today)
    response = requests.get(test_url, headers={'Authorization': 'Bearer {}'.format(
        token_fixture.access_token)})
    assert json.loads(response.content)['total_count'] == 3


def test_basic_post(user_fixture, token_fixture):
    test_url = '{}/activities/'.format(APP_ENDPOINT)
    response = requests.post(test_url,
                             headers={
                                 'Authorization': 'Bearer {}'.format(token_fixture.access_token),
                                 'content-type': 'application/json'},
                             data=json.dumps(dict(
                                 user_id=user_fixture.id,
                                 type=99,
                                 source_table='test',
                                 source_id='1337',
                                 params=str({'lastName': random_word(6),
                                             'firstName': random_word(8)})
                             )))
    assert response.status_code == 200


def test_recent_readable(token_fixture):
    test_url = '{}/activities/1?aggregate=1'.format(APP_ENDPOINT)
    response = requests.get(test_url,
                            headers={'Authorization': 'Bearer {}'.format(token_fixture.access_token)})
    assert response.status_code == 200
    assert len(json.loads(response.content)['activities']) == 1
    assert json.loads(response.content)['activities'][0]['count'] == 4
    assert json.loads(response.content)['activities'][0]['image'] == 'notification.png'
    assert json.loads(response.content)['activities'][0]['readable_text'] == '4 users have joined'


def test_health_check():
    import requests
    response = requests.get('{}/healthcheck'.format(APP_ENDPOINT))
    assert response.status_code == 200
