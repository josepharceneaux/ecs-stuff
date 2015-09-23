__author__ = 'Erik Farmer'

import pytest
from datetime import datetime
from datetime import timedelta
import json

from activities_app import app
from activities_app.models import db, Client, Token, User, Candidate, Activity
db.init_app(app)

ISO_FORMAT = '%Y-%m-%d %H:%M'
APP = app.test_client()

@pytest.fixture
def auth_user_fill(request):
    test_client = Client(client_id='fakeclient', client_secret='s00pers3kr37')
    db.session.add(test_client)
    db.session.commit()
    test_user = User(domainId=1, firstName='Jamtry', lastName='Jonas',
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
                     params=json.dumps({'lastName': 'Larzzz', 'firstName': 'Griffon'}))
    ]
    for a in activities:
        db.session.add(a)
    db.session.commit()
    def fin():
        created_test_client = Client.query.filter_by(client_id='fakeclient').first()
        created_test_token = Token.query.filter_by(client_id='fakeclient').first()
        created_test_user = User.query.filter_by(firstName='Jamtry').first()
        created_test_candidate = Candidate.query.filter_by(formattedName='Griffon Larz').first()
        db.session.delete(created_test_token)
        db.session.commit()
        db.session.delete(created_test_client)
        db.session.delete(created_test_user)
        db.session.delete(created_test_candidate)
        db.session.query(Activity).filter(Activity.userId == created_test_user.id).delete()
        db.session.commit()

    request.addfinalizer(fin)


def test_call_requires_auth(auth_user_fill):
    response = APP.post('/activities/1', headers={'Authorization': 'Bearer good_token'}, data={}, follow_redirects=True)
    assert response.status_code == 200
    response = APP.post('/activities/1', headers={'Authorization': 'Bearer bad_token'}, data={}, follow_redirects=True)
    assert response.status_code == 400


def test_reponse_is_user_filtered(auth_user_fill):
    response = APP.post('/activities/1', headers={'Authorization': 'Bearer good_token'}, data={}, follow_redirects=True)
    assert len(json.loads(response.data)['items']) == 3


def test_response_can_be_time_filtered(auth_user_fill):
    response = APP.post('/activities/1', headers={'Authorization': 'Bearer good_token'}, data={
        'start': datetime.strftime(datetime.today(), ISO_FORMAT)
    }, follow_redirects=True)
    assert len(json.loads(response.data)['items']) == 2