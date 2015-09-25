__author__ = 'Erik Farmer'

import pytest
from datetime import datetime
from datetime import timedelta
import json

from activities_app import app
from activities_app.models import db, Activity, Candidate, Client, Domain, Token, User
db.init_app(app)

ISO_FORMAT = '%Y-%m-%d %H:%M'
APP = app.test_client()

@pytest.fixture
def auth_user_fill(request):
    test_client = Client(client_id='fakeclient', client_secret='s00pers3kr37')
    db.session.add(test_client)
    db.session.commit()
    test_domain = Domain(name='ThunderDome', usageLimitation=-1, addedTime=datetime.today(), organizationId=1,
                         isFairCheckOn=0, isActive=1, defaultCultureId=1)
    db.session.add(test_domain)
    db.session.commit()
    test_user = User(domainId=test_domain.id, firstName='Jamtry', lastName='Jonas',
                     password='pbkdf2(1000,64,sha512)$bd913bac5e55a39b$ea5a0a2a2d156003faaf7986ea4cba3f25607e43ecffb36e0d2b82381035bbeaded29642a1dd6673e922f162d322862459dd3beedda4501c90f7c14b3669cd72',
                     addedTime=datetime(2050, 4, 26))
    db.session.add(test_user)
    db.session.commit()
    test_token = Token(client_id='fakeclient', user_id=test_user.id, token_type='bearer', access_token='good_token',
                           refresh_token='barz', expires=datetime(2050, 4, 26))
    db.session.add(test_token)
    db.session.commit()
    test_candidate = Candidate(firstName='Griffon', lastName='Larz', formattedName='Griffon Larz', isWebHidden=0,
              isMobileHidden=0, addedTime=datetime.today(), ownerUserId=test_user.id, domainCanRead=1,
              domainCanWrite=1, sourceId=23, sourceProductId=2, objective='Fix broken code', cultureId=1)
    db.session.add(test_candidate)
    db.session.commit()
    today = datetime.today()
    activities = [
        Activity(addedTime=today + timedelta(hours=-2), sourceTable='user', sourceId=1, type=12, userId=test_user.id,
                 params=json.dumps({'lastName': 'Larz', 'firstName': 'Griffon'})),
        Activity(addedTime=today, sourceTable='user', sourceId=1, type=12, userId=test_user.id,
                     params=json.dumps({'lastName': 'Larzz', 'firstName': 'Griffon'})),
        Activity(addedTime=today, sourceTable='user', sourceId=1, type=12, userId=test_user.id,
                     params=json.dumps({'lastName': 'Larzzz', 'firstName': 'Griffon'})),
        Activity(addedTime=today, sourceTable='user', sourceId=1, type=12, userId=1,
                     params=json.dumps({'lastName': 'Larzzz', 'firstName': 'Griffon'}))
    ]
    for a in activities:
        db.session.add(a)
    db.session.commit()
    def fin():
        created_test_client = Client.query.filter_by(client_id='fakeclient').first()
        created_test_token = Token.query.filter_by(client_id='fakeclient').first()
        created_test_user = User.query.filter_by(firstName='Jamtry').first()
        created_test_domain = Domain.query.filter_by(name='ThunderDome').first()
        db.session.delete(created_test_token)
        db.session.commit()
        db.session.query(Activity).filter(Activity.userId == created_test_user.id).delete()
        db.session.delete(created_test_client)
        db.session.delete(created_test_user)
        db.session.delete(created_test_domain)
        db.session.commit()

    request.addfinalizer(fin)


def test_call_requires_auth(auth_user_fill):
    response = APP.get('/activities/1', headers={'Authorization': 'Bearer good_token'}, data={}, follow_redirects=True)
    assert response.status_code == 200
    response = APP.get('/activities/1', headers={'Authorization': 'Bearer bad_token'}, data={}, follow_redirects=True)
    assert response.status_code == 401


def test_reponse_is_user_filtered(auth_user_fill):
    response = APP.get('/activities/1', headers={'Authorization': 'Bearer good_token'}, data={}, follow_redirects=True)
    assert json.loads(response.data)['total_count'] == 3


def test_response_can_be_time_filtered(auth_user_fill):
    today = (datetime.today()+ timedelta(minutes=-1)).isoformat() 
    url_with_date = '/activities/1?start_time={}'.format(today)
    response = APP.get(url_with_date, headers={'Authorization': 'Bearer good_token'}, follow_redirects=True)
    assert json.loads(response.data)['total_count'] == 2


def test_basic_post(auth_user_fill):
    test_user_id = User.query.filter_by(firstName='Jamtry').first().id
    response = APP.post('/activities/', headers={'Authorization': 'Bearer good_token'}, data=dict(
        userId=test_user_id,
        type=99,
        sourceTable='test',
        sourceId='1337',
        params=json.dumps({'lastName': 'Larzzzzz', 'firstName': 'Griffon'})
    ), follow_redirects=True)
    assert response.status_code == 200


def test_recent_readable(auth_user_fill):
    response = APP.get('/activities/1?aggregate=1', headers={'Authorization': 'Bearer good_token'}, data={}, follow_redirects=True)
    assert response.status_code == 200
    assert len(json.loads(response.data)['activities']) == 1
    assert json.loads(response.data)['activities'][0]['count'] == 3
    assert json.loads(response.data)['activities'][0]['image'] == 'notification.png'
    assert json.loads(response.data)['activities'][0]['readable_text'] == '3 users have joined'