__author__ = 'Erik Farmer'

import pytest
from datetime import datetime

from activities_app import app
from activities_app.models import db, Client, Token, User
db.init_app(app)

APP = app.test_client()

@pytest.fixture
def auth_user_fill(request):
    test_client = Client(client_id='fakeclient', client_secret='s00pers3kr37')
    test_token = Token(client_id='fakeclient', user_id=1, token_type='bearer', access_token='fooz',
                       refresh_token='barz', expires=datetime(2050, 4, 26))
    test_user = User(domainId=1, firstName='Jamtry', lastName='Jonas',
                     password='pbkdf2(1000,64,sha512)$bd913bac5e55a39b$ea5a0a2a2d156003faaf7986ea4cba3f25607e43ecffb36e0d2b82381035bbeaded29642a1dd6673e922f162d322862459dd3beedda4501c90f7c14b3669cd72',
                     addedTime=datetime(2050, 4, 26))
    db.session.add(test_client)
    db.session.commit()
    db.session.add(test_token)
    db.session.commit()
    db.session.add(test_user)
    db.session.commit()

    def fin():
        created_test_client = Client.query.filter_by(client_id='fakeclient').first()
        created_test_token = Token.query.filter_by(client_id='fakeclient').first()
        created_test_user = User.query.filter_by(firstName='Jamtry').first()
        db.session.delete(created_test_token)
        db.session.commit()
        db.session.delete(created_test_client)
        db.session.commit()
        db.session.delete(created_test_user)
        db.session.commit()

    request.addfinalizer(fin)


def test_valid_token_has_user(auth_user_fill):
    response = APP.post('/activities', headers={'Authorization': 'Bearer fooz'}, data={}, follow_redirects=True)
    assert response.status_code is 200