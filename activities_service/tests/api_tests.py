__author__ = 'Erik Farmer'

# Standard Library
from datetime import datetime
from datetime import timedelta
import json

# Third Party
import pytest

# Application Specific
from activities_service.activities_app import app
from activities_service.models.db import db
from activities_service.models.misc import Activity
from activities_service.models.candidate import Candidate
from activities_service.models.user import Client
from activities_service.models.user import Domain
from activities_service.models.user import Token
from activities_service.models.user import User


ISO_FORMAT = '%Y-%m-%d %H:%M'
APP = app.test_client()


@pytest.fixture(autouse=True)
def test_domain(request):
    test_domain = Domain(name='ThunderDome', usage_limitation=-1, added_time=datetime.today(), organization_id=1,
                         is_fair_check_on=0, is_active=1, default_culture_id=1)
    try:
       db.session.add(test_domain)
       db.session.commit()
    except Exception:  # TODO This is to handle 'Duplicate entry' MySQL errors. We should instead check for existing Client/Token before inserting
       pass
    def fin():
        try:
            db.session.delete(test_domain)
            db.session.commit()
        except Exception:
            pass
    request.addfinalizer(fin)
    return test_domain


@pytest.fixture(autouse=True)
def test_client(request):
    test_client = Client(client_id='fakeclient', client_secret='s00pers3kr37')
    try:
        db.session.add(test_client)
        db.session.commit()
    except Exception:
        pass

    def fin():
        try:
            db.session.delete(test_client)
            db.session.commit()
        except Exception:
            pass
    request.addfinalizer(fin)
    return test_client


@pytest.fixture(autouse=True)
def test_token(test_client, request):
    test_token = Token(client_id=test_client.client_id, user_id=1, token_type='bearer', access_token='good_token',
                       refresh_token='barz', expires=datetime(2050, 4, 26))
    try:
       db.session.add(test_token)
       db.session.commit()
    except Exception:  # TODO This is to handle 'Duplicate entry' MySQL errors. We should instead check for existing Client/Token before inserting
       pass

    def fin():
        try:
            db.session.delete(test_token)
            db.session.commit()
        except Exception:
            pass
    request.addfinalizer(fin)
    return test_token


@pytest.fixture(autouse=True)
def test_user(test_domain, request):
    test_user = User(domain_id=test_domain.id, first_name='Jamtry', last_name='Jonas',
                     password='pbkdf2(1000,64,sha512)$bd913bac5e55a39b$ea5a0a2a2d156003faaf7986ea4cba3f25607e43ecffb36e0d2b82381035bbeaded29642a1dd6673e922f162d322862459dd3beedda4501c90f7c14b3669cd72',
                     email='jamtry@gmail.com',added_time=datetime(2050, 4, 26))
    try:
       db.session.add(test_user)
       db.session.commit()
    except Exception:  # TODO This is to handle 'Duplicate entry' MySQL errors. We should instead check for existing Client/Token before inserting
       pass

    def fin():
        try:
            db.session.delete(test_user)
            db.session.commit()
        except Exception:
            pass
    request.addfinalizer(fin)
    return test_user


@pytest.fixture(autouse=True)
def test_candidate(test_user, request):
    test_candidate = Candidate(first_name='Griffon', last_name='Larz', formatted_name='Griffon Larz', is_web_hidden=0,
              is_mobile_hidden=0, added_time=datetime.today(), user_id=test_user.id, domain_can_read=1,
              domain_can_write=1, source_id=23, source_product_id=2, objective='Fix broken code', culture_id=1)
    try:
       db.session.add(test_candidate)
       db.session.commit()
    except Exception:  # TODO This is to handle 'Duplicate entry' MySQL errors. We should instead check for existing Client/Token before inserting
       pass

    def fin():
        try:
            db.session.delete(test_candidate)
            db.session.commit()
        except Exception:
            pass
    request.addfinalizer(fin)
    return test_candidate


@pytest.fixture(autouse=True)
def test_activities(test_user, request):
    today = datetime.today()
    activities = [
        Activity(added_time=today + timedelta(hours=-2), source_table='user', source_id=1, type=12,
                 user_id=test_user.id, params=json.dumps({'lastName': 'Larz', 'firstName': 'Griffon'})),
        Activity(added_time=today, source_table='user', source_id=1, type=12, user_id=test_user.id,
                     params=json.dumps({'lastName': 'Larzz', 'firstName': 'Griffon'})),
        Activity(added_time=today, source_table='user', source_id=1, type=12, user_id=test_user.id,
                     params=json.dumps({'lastName': 'Larzzz', 'firstName': 'Griffon'})),
        Activity(added_time=today, source_table='user', source_id=1, type=12, user_id=1,
                     params=json.dumps({'lastName': 'Larzzz', 'firstName': 'Griffon'}))
    ]
    try:
       db.session.bulk_save_objects(activities)
    except Exception:  # TODO This is to handle 'Duplicate entry' MySQL errors. We should instead check for existing Client/Token before inserting
       pass

    def fin():
        try:
            db.session.query(Activity).filter(Activity.userId == test_user.id).delete()
            db.session.commit()
        except Exception:
            pass
    request.addfinalizer(fin)
    return True


def test_call_requires_auth():
    response = APP.get('/activities/1', headers={'Authorization': 'Bearer good_token'}, data={}, follow_redirects=True)
    assert response.status_code == 200
    response = APP.get('/activities/1', headers={'Authorization': 'Bearer bad_token'}, data={}, follow_redirects=True)
    assert response.status_code == 401


def test_reponse_is_user_filtered():
    response = APP.get('/activities/1', headers={'Authorization': 'Bearer good_token'}, data={}, follow_redirects=True)
    assert json.loads(response.data)['total_count'] == 3


def test_response_can_be_time_filtered():
    today = (datetime.today()+ timedelta(minutes=-1)).isoformat()
    url_with_date = '/activities/1?start_time={}'.format(today)
    response = APP.get(url_with_date, headers={'Authorization': 'Bearer good_token'}, follow_redirects=True)
    assert json.loads(response.data)['total_count'] == 2


def test_basic_post():
    test_user_id = User.query.filter_by(firstName='Jamtry').first().id
    response = APP.post('/activities/', headers={'Authorization': 'Bearer good_token'}, data=dict(
        userId=test_user_id,
        type=99,
        sourceTable='test',
        sourceId='1337',
        params=json.dumps({'lastName': 'Larzzzzz', 'firstName': 'Griffon'})
    ), follow_redirects=True)
    assert response.status_code == 200


def test_recent_readable():
    response = APP.get('/activities/1?aggregate=1', headers={'Authorization': 'Bearer good_token'}, data={}, follow_redirects=True)
    assert response.status_code == 200
    assert len(json.loads(response.data)['activities']) == 1
    assert json.loads(response.data)['activities'][0]['count'] == 3
    assert json.loads(response.data)['activities'][0]['image'] == 'notification.png'
    assert json.loads(response.data)['activities'][0]['readable_text'] == '3 users have joined'
