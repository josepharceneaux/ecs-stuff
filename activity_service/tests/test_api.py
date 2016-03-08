__author__ = 'Erik Farmer'
# Standard Library
from datetime import datetime
from datetime import timedelta
import json
# Third Party
import requests
# Application Specific
from activity_service.common.utils.handy_functions import random_word
from activity_service.common.routes import ActivityApiUrl
from .fixtures import activities_fixture
from .fixtures import candidate_fixture
from .fixtures import candidate_source_fixture
from .fixtures import client_fixture
from .fixtures import culture_fixture
from .fixtures import domain_fixture
from .fixtures import org_fixture
from .fixtures import token_fixture
from .fixtures import user_fixture


def test_call_requires_auth(token_fixture):
    # this should become a test for non-aggregate responses.
    test_url = ActivityApiUrl.ACTIVITIES_PAGE % '1'
    response = requests.get(test_url, headers={'Authorization': 'Bearer {}'.format(
        token_fixture.access_token)})
    assert response.status_code == 200
    #this should become its own test
    response = requests.get(test_url, headers={'Authorization': 'Bearer bad_token'})
    assert response.status_code == 401


def test_reponse_is_user_filtered(token_fixture):
    test_url = ActivityApiUrl.ACTIVITIES_PAGE % '1'
    response = requests.get(test_url, headers={'Authorization': 'Bearer {}'.format(
        token_fixture.access_token)})
    assert json.loads(response.content)['total_count'] == 4


def test_response_can_be_time_filtered(token_fixture):
    today = (datetime.today() + timedelta(minutes=-1)).isoformat()
    test_url = ActivityApiUrl.ACTIVITIES_PAGE % '1?start_time={}'.format(today)
    response = requests.get(test_url, headers={'Authorization': 'Bearer {}'.format(
        token_fixture.access_token)})
    assert json.loads(response.content)['total_count'] == 3


def test_basic_post(user_fixture, token_fixture):
    test_url = ActivityApiUrl.ACTIVITIES
    response = requests.post(test_url,
                             headers={
                                 'Authorization': 'Bearer {}'.format(token_fixture.access_token),
                                 'content-type': 'application/json'},
                             data=json.dumps(dict(
                                 user_id=user_fixture.id,
                                 type=99,
                                 source_table='test',
                                 source_id='1337',
                                 params={'lastName': random_word(6), 'firstName': random_word(8)}
                             )))
    assert response.status_code == 200


def test_recent_readable(token_fixture):
    test_url = ActivityApiUrl.ACTIVITIES_PAGE % '1?aggregate=1'
    response = requests.get(test_url,
                            headers={'Authorization': 'Bearer {}'.format(token_fixture.access_token)})
    assert response.status_code == 200
    assert len(json.loads(response.content)['activities']) == 1
    assert json.loads(response.content)['activities'][0]['count'] == 4
    assert json.loads(response.content)['activities'][0]['image'] == 'notification.png'
    assert json.loads(response.content)['activities'][0]['readable_text'] == '4 users have joined'


def test_pipeline_create_and_read(user_fixture, token_fixture):
    # Create a pipeline activity.
    create_url = ActivityApiUrl.ACTIVITIES
    post_response = requests.post(create_url,
                             headers={
                                 'Authorization': 'Bearer {}'.format(token_fixture.access_token),
                                 'content-type': 'application/json'},
                             data=json.dumps(dict(
                                 user_id=user_fixture.id,
                                 type=31,
                                 source_table='talent_pipeline',
                                 source_id='1337',
                                 params={'username': user_fixture.first_name, 'name': 'test_PL1'}
                             )))
    assert post_response.status_code == 200
    # Fetch the recent readable data
    aggregate_url = ActivityApiUrl.ACTIVITIES_PAGE % '1?aggregate=1'
    aggregate_response = requests.get(aggregate_url,
                            headers={'Authorization': 'Bearer {}'.format(token_fixture.access_token)})
    assert aggregate_response.status_code == 200
    activities = json.loads(aggregate_response.content)
    assert {u'count': 1, u'image': u'pipeline.png', u'readable_text': u'You created a pipeline: <b>test_PL1</b>.'} in activities['activities']

def test_talentPool_create_and_read(user_fixture, token_fixture):
    # Create a talent pool activity.
    create_url = ActivityApiUrl.ACTIVITIES
    post_response = requests.post(create_url,
                             headers={
                                 'Authorization': 'Bearer {}'.format(token_fixture.access_token),
                                 'content-type': 'application/json'},
                             data=json.dumps(dict(
                                 user_id=user_fixture.id,
                                 type=33,
                                 source_table='talent_pool',
                                 source_id='1337',
                                 params={'username': user_fixture.first_name, 'name': 'test_pool1'}
                             )))
    assert post_response.status_code == 200
    # Fetch the recent readable data
    aggregate_url = ActivityApiUrl.ACTIVITIES_PAGE % '1?aggregate=1'
    aggregate_response = requests.get(aggregate_url,
                            headers={'Authorization': 'Bearer {}'.format(token_fixture.access_token)})
    assert aggregate_response.status_code == 200
    activities = json.loads(aggregate_response.content)
    assert {u'count': 1, u'image': u'talent_pool.png', u'readable_text': u'You created a Talent Pool: <b>test_pool1</b>.'} in activities['activities']


def test_health_check():
    response = requests.get(ActivityApiUrl.HEALTH_CHECK)
    assert response.status_code == 200

    # Testing Health Check URL with trailing slash
    response = requests.get(ActivityApiUrl.HEALTH_CHECK + '/')
    assert response.status_code == 200
