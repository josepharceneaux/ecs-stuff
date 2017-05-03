__author__ = 'Erik Farmer'
# Standard Library
from datetime import datetime
from datetime import timedelta
import json
# Third Party
import requests
# Application Specific
from activity_service.common.utils.handy_functions import random_word
from activity_service.common.models.misc import Activity
from activity_service.common.routes import ActivityApiUrl
from activity_service.tests import constants as C
# TODO change this to test conf
from activity_service.common.tests.conftest import access_token_first
from activity_service.common.tests.conftest import domain_first
from activity_service.common.tests.conftest import domain_source
from activity_service.common.tests.conftest import first_group
from activity_service.common.tests.conftest import sample_client
from activity_service.common.tests.conftest import talent_pool
from activity_service.common.tests.conftest import user_first

DATE_INPUT_FORMAT = '%Y-%m-%dT%H:%M:%S'


def test_call_requires_auth(user_first):
    test_url = 'http://127.0.0.1:8002/v2/activities/{}/user/{}'.format(1, user_first.id)
    response = requests.get(test_url, headers={'Authorization': 'Bearer bad_token'})
    assert response.status_code == requests.codes.unauthorized


def test_cant_get_other_domain_activities(access_token_first, user_first):
    test_url = 'http://127.0.0.1:8002/v2/activities/{}/user/{}'.format(1, user_first.id - 1)
    response = requests.get(test_url, headers={'Authorization': 'Bearer {}'.format(access_token_first)})
    assert response.status_code == requests.codes.unauthorized


def test_can_get_activities(access_token_first, user_first):
    test_url = 'http://127.0.0.1:8002/v2/activities/{}/user/{}'.format(1, user_first.id)
    response = requests.get(test_url, headers={'Authorization': 'Bearer {}'.format(access_token_first)})
    print response.content
    assert response.status_code == requests.codes.ok


def test_default_pagination(access_token_first, user_first):
    CREATE_URL = ActivityApiUrl.ACTIVITIES
    HEADERS = {'Authorization': 'Bearer {}'.format(access_token_first), 'content-type': 'application/json'}

    for i in xrange(25):
        payload = json.dumps(
            dict(
                user_id=user_first.id,
                type=Activity.MessageIds.CANDIDATE_CREATE_WEB,
                source_table='test',
                source_id='1337',
                params={'formatted_name': random_word(6)}))
        requests.post(CREATE_URL, headers=HEADERS, data=payload)

    read_url = 'http://127.0.0.1:8002/v2/activities/{}/user/{}'.format(1, user_first.id)
    response = requests.get(read_url, headers={'Authorization': 'Bearer {}'.format(access_token_first)})
    print response.content
    assert len(json.loads(response.content)['items']) == 20
    assert response.status_code == requests.codes.ok


def test_custom_pagination(access_token_first, user_first):
    CREATE_URL = ActivityApiUrl.ACTIVITIES
    HEADERS = {'Authorization': 'Bearer {}'.format(access_token_first), 'content-type': 'application/json'}

    for i in xrange(25):
        payload = json.dumps(
            dict(
                user_id=user_first.id,
                type=Activity.MessageIds.CANDIDATE_CREATE_WEB,
                source_table='test',
                source_id='1337',
                params={'formatted_name': random_word(6)}))
        requests.post(CREATE_URL, headers=HEADERS, data=payload)

    read_url = 'http://127.0.0.1:8002/v2/activities/{}/user/{}?qty=25'.format(1, user_first.id)
    response = requests.get(read_url, headers={'Authorization': 'Bearer {}'.format(access_token_first)})
    print response.content
    assert len(json.loads(response.content)['items']) == 25
    assert response.status_code == requests.codes.ok
