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
from .fixtures import activities_fixture
from .fixtures import candidate_fixture
from .fixtures import candidate_source_fixture
from .fixtures import client_fixture
from .fixtures import culture_fixture
from .fixtures import domain_fixture
from .fixtures import org_fixture
from .fixtures import token_fixture
from .fixtures import user_fixture

DATE_INPUT_FORMAT = '%Y-%m-%dT%H:%M:%S'


def test_call_requires_auth(token_fixture):
    # this should become a test for non-aggregate responses.
    test_url = ActivityApiUrl.ACTIVITIES_PAGE % '1'
    response = requests.get(test_url, headers={'Authorization': 'Bearer {}'.format(token_fixture.access_token)})
    assert response.status_code == requests.codes.ok
    #this should become its own test
    response = requests.get(test_url, headers={'Authorization': 'Bearer bad_token'})
    assert response.status_code == requests.codes.unauthorized


def test_response_is_user_filtered(token_fixture):
    test_url = ActivityApiUrl.ACTIVITIES_PAGE % '1'
    response = requests.get(test_url, headers={'Authorization': 'Bearer {}'.format(token_fixture.access_token)})
    assert json.loads(response.content)['total_count'] == 32


def test_response_can_exclude_user(token_fixture):
    test_url = ActivityApiUrl.ACTIVITIES_PAGE % '1' + '?exclude_current_user=1'
    response = requests.get(test_url, headers={'Authorization': 'Bearer {}'.format(token_fixture.access_token)})
    assert json.loads(response.content)['total_count'] == 0


def test_response_can_be_time_filtered(token_fixture):
    today = (datetime.today() + timedelta(minutes=-1)).strftime(DATE_INPUT_FORMAT)
    test_url = ActivityApiUrl.ACTIVITIES_PAGE % '1?start_datetime={}'.format(today)
    response = requests.get(test_url, headers={'Authorization': 'Bearer {}'.format(token_fixture.access_token)})
    assert json.loads(response.content)['total_count'] == 3


def test_basic_post(user_fixture, token_fixture):
    test_url = ActivityApiUrl.ACTIVITIES
    response = requests.post(
        test_url,
        headers={'Authorization': 'Bearer {}'.format(token_fixture.access_token),
                 'content-type': 'application/json'},
        data=json.dumps(
            dict(
                user_id=user_fixture.id,
                type=Activity.MessageIds.CANDIDATE_CREATE_WEB,
                source_table='test',
                source_id='1337',
                params={'lastName': random_word(6),
                        'firstName': random_word(8)})))
    assert response.status_code == requests.codes.created


def test_recent_readable(token_fixture):
    test_url = ActivityApiUrl.ACTIVITIES_PAGE % '1?aggregate=1'
    response = requests.get(test_url, headers={'Authorization': 'Bearer {}'.format(token_fixture.access_token)})
    assert response.status_code == requests.codes.ok
    response_content = json.loads(response.content)
    assert len(response_content['activities']) == 5
    assert response_content['activities'][0]['count'] == 4
    assert response_content['activities'][0]['readable_text'] == '4 users have joined'


def test_recent_readable_with_limit(token_fixture):
    test_url = ActivityApiUrl.ACTIVITIES_PAGE % '1?aggregate=1&aggregate_limit=3'
    response = requests.get(test_url, headers={'Authorization': 'Bearer {}'.format(token_fixture.access_token)})
    assert response.status_code == requests.codes.ok
    response_content = json.loads(response.content)
    assert len(response_content['activities']) == 3
    assert response_content['activities'][0]['count'] == 4
    assert response_content['activities'][0]['readable_text'] == '4 users have joined'


def test_recent_readable_with_dates(token_fixture):
    TEST_URL = ActivityApiUrl.ACTIVITIES_PAGE % '1?aggregate=1'
    HEADERS = {'Authorization': 'Bearer {}'.format(token_fixture.access_token)}

    response = requests.get(TEST_URL, headers=HEADERS)
    response_content = json.loads(response.content)
    activities = response_content['activities']
    assert response.status_code == requests.codes.ok
    assert len(activities) == 5
    for aggregate in activities:
        start_dt = datetime.strptime(aggregate['start'], DATE_INPUT_FORMAT)
        end_dt = datetime.strptime(aggregate['end'], DATE_INPUT_FORMAT)
        if 'You updated' in aggregate['readable_text']:
            assert start_dt.day == C.CANDIDATE_UPDATE_START.day
            assert end_dt.day == (start_dt + timedelta(days=6)).day
        if 'You deleted' in aggregate['readable_text']:
            assert start_dt.day == C.SMARTLIST_DELETE_START.day
            assert end_dt.day == (start_dt + timedelta(days=6)).day
        if 'You created' in aggregate['readable_text']:
            assert start_dt.day == C.EVENT_CREATE_START.day
            assert end_dt.day == (start_dt + timedelta(days=6)).day
        if 'candidates opened' in aggregate['readable_text']:
            assert start_dt.day == C.CAMPAIGN_EMAIL_OPEN_START.day
            assert end_dt.day == (start_dt + timedelta(days=6)).day


def test_bulk_create_and_read(user_fixture, token_fixture):
    CREATE_URL = ActivityApiUrl.ACTIVITIES
    READ_URL = ActivityApiUrl.ACTIVITIES_PAGE % '1?aggregate=1'
    HEADERS = {'Authorization': 'Bearer {}'.format(token_fixture.access_token), 'content-type': 'application/json'}

    # Test `bulk` async write
    for i in xrange(200):
        payload = json.dumps(
            dict(
                user_id=user_fixture.id,
                type=Activity.MessageIds.CANDIDATE_CREATE_WEB,
                source_table='test',
                source_id='1337',
                params={'lastName': random_word(6),
                        'firstName': random_word(8)}))
        response = requests.post(CREATE_URL, headers=HEADERS, data=payload)
        assert response.status_code == requests.codes.created

    # Test `bulk` async read
    for _ in xrange(5):
        response = requests.get(READ_URL, headers={'Authorization': 'Bearer {}'.format(token_fixture.access_token)})
        assert response.status_code == requests.codes.ok


def test_pipeline_create_and_read(user_fixture, token_fixture):
    # Create a pipeline activity.
    create_url = ActivityApiUrl.ACTIVITIES
    post_response = requests.post(
        create_url,
        headers={'Authorization': 'Bearer {}'.format(token_fixture.access_token),
                 'content-type': 'application/json'},
        data=json.dumps(
            dict(
                user_id=user_fixture.id,
                type=Activity.MessageIds.PIPELINE_CREATE,
                source_table='talent_pipeline',
                source_id='1337',
                params={'username': user_fixture.first_name,
                        'name': 'test_PL1'})))
    assert post_response.status_code == requests.codes.created
    # Fetch the recent readable data
    aggregate_url = ActivityApiUrl.ACTIVITIES_PAGE % '1?aggregate=1'
    aggregate_response = requests.get(
        aggregate_url, headers={'Authorization': 'Bearer {}'.format(token_fixture.access_token)})
    assert aggregate_response.status_code == requests.codes.ok
    activities = json.loads(aggregate_response.content)
    assert any(activity['readable_text'] == u'<b>You</b> created a pipeline: <b>test_PL1</b>.'
               for activity in activities['activities'])


def test_talentPool_create_and_read(user_fixture, token_fixture):
    # Create a talent pool activity.
    create_url = ActivityApiUrl.ACTIVITIES
    post_response = requests.post(
        create_url,
        headers={'Authorization': 'Bearer {}'.format(token_fixture.access_token),
                 'content-type': 'application/json'},
        data=json.dumps(
            dict(
                user_id=user_fixture.id,
                type=Activity.MessageIds.TALENT_POOL_CREATE,
                source_table='talent_pool',
                source_id='1337',
                params={'username': user_fixture.first_name,
                        'name': 'test_pool1'})))
    assert post_response.status_code == requests.codes.created
    # Fetch the recent readable data
    aggregate_url = ActivityApiUrl.ACTIVITIES_PAGE % '1?aggregate=1'
    aggregate_response = requests.get(
        aggregate_url, headers={'Authorization': 'Bearer {}'.format(token_fixture.access_token)})
    assert aggregate_response.status_code == requests.codes.ok
    activities = json.loads(aggregate_response.content)
    assert any(activity['readable_text'] == u'<b>You</b> created a Talent Pool: <b>test_pool1</b>.'
               for activity in activities['activities'])


def test_dumblist_create_and_read(user_fixture, token_fixture):
    # Create a talent pool activity.
    create_url = ActivityApiUrl.ACTIVITIES
    post_response = requests.post(
        create_url,
        headers={'Authorization': 'Bearer {}'.format(token_fixture.access_token),
                 'content-type': 'application/json'},
        data=json.dumps(
            dict(
                user_id=user_fixture.id,
                type=Activity.MessageIds.DUMBLIST_CREATE,
                source_table='smart_list',
                source_id='1337',
                params={'name': 'dumblist1'})))
    assert post_response.status_code == requests.codes.created
    # Fetch the recent readable data
    aggregate_url = ActivityApiUrl.ACTIVITIES_PAGE % '1?aggregate=1'
    aggregate_response = requests.get(
        aggregate_url, headers={'Authorization': 'Bearer {}'.format(token_fixture.access_token)})
    assert aggregate_response.status_code == requests.codes.ok
    activities = json.loads(aggregate_response.content)
    assert any(activity['readable_text'] == u'<b>You</b> created a list: <b>dumblist1</b>.'
               for activity in activities['activities'])


def test_health_check():
    response = requests.get(ActivityApiUrl.HEALTH_CHECK)
    assert response.status_code == requests.codes.ok

    # Testing Health Check URL with trailing slash
    response = requests.get(ActivityApiUrl.HEALTH_CHECK + '/')
    assert response.status_code == requests.codes.ok
