# Standard Library
from datetime import (datetime, timedelta)
import json, random, string, uuid, requests

# Third Party
import pytest
from sqlalchemy.sql.expression import ClauseElement

# Application Specific
from activity_service.activities_app import app
from activity_service.common.models.db import db
from activity_service.common.models.misc import (Activity, Culture, Organization)
from activity_service.common.models.candidate import Candidate
from activity_service.common.models.user import (Client, Domain, Token, User)

ISO_FORMAT = '%Y-%m-%d %H:%M'
APP = app.test_client()


# todo: authentication expires in 2 hours. For testing, we might need a referesh token unless if all tests run in two hours
@pytest.fixture()
def get_auth_token(test_user):
    """
    :param test_user:
    :return:
    """
    # client_id and client_secret can be any arbitrary string
    client_id = str(uuid.uuid4())[0:8]
    client_secret = str(uuid.uuid4())[0:8]

    new_client = Client(client_id=client_id, client_secret=client_secret)
    db.session.add(new_client)
    db.session.commit()
    print "get_auth_token test_user: %s" % test_user
    user_email = test_user['email']
    user_password = test_user['password']
    resp = requests.post('http://127.0.0.1:5000/oauth2/token', data=dict(grant_type='password',
                                                                         username=user_email,
                                                                         password=user_password,
                                                                         client_id='clientid',
                                                                         client_secret='clientsecret'))
    print "get_auth_token response: %s" % resp
    pass


def revoke_auth_token():
    pass


@pytest.fixture(autouse=True)
def test_candidate(test_user, test_culture, request):
    candidate_attrs = dict(
        first_name='Griffon', last_name='Larz', formatted_name='Griffon Larz', is_web_hidden=0,
        is_mobile_hidden=0, added_time=datetime.today(), user_id=test_user.id,
        domain_can_read=1, domain_can_write=1, source_id=23, source_product_id=2,
        objective='Fix broken code', culture_id=test_culture.id, is_dirty=0
    )
    test_candidate, created = get_or_create(db.session, Candidate, defaults=None, **candidate_attrs)
    if created:
        db.session.add(test_candidate)
        db.session.commit()

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
        Activity(added_time=today, source_table='user', source_id=1, type=12, user_id=test_user.id,
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


@pytest.fixture(autouse=True)
def test_user(test_domain, request):
    user_attrs = dict(
        domain_id=test_domain.id, first_name='Jamtry', last_name='Jonas',
        password='pbkdf2(1000,64,sha512)$bd913bac5e55a39b$ea5a0a2a2d156003faaf7986ea4cba3f25607e43ecffb36e0d2b82381035bbeaded29642a1dd6673e922f162d322862459dd3beedda4501c90f7c14b3669cd72',
        email='jamtry@{}.com'.format(randomword(7)), added_time=datetime(2050, 4, 26)
    )
    test_user, created = get_or_create(db.session, User, defaults=None, **user_attrs)
    if created:
        db.session.add(test_user)
        db.session.commit()

    def fin():
        try:
            db.session.delete(test_user)
            db.session.commit()
        except Exception:
            pass

    request.addfinalizer(fin)
    return test_user


@pytest.fixture(autouse=True)
def test_domain(test_org, test_culture, request):
    domain_attrs = dict(
        name=randomword(10).format(), usage_limitation=-1, added_time=datetime.today(),
        organization_id=test_org.id, is_fair_check_on=0, is_active=1,
        default_culture_id=test_culture.id, expiration=datetime(2050, 4, 26)
    )
    test_domain, created = get_or_create(db.session, Domain, defaults=None, **domain_attrs)
    if created:
        db.session.add(test_domain)
        db.session.commit()

    def fin():
        try:
            db.session.delete(test_domain)
            db.session.commit()
        except Exception:
            pass

    request.addfinalizer(fin)
    return test_domain


@pytest.fixture(autouse=True)
def test_culture(request):
    culture_attrs = dict(description='Foo {}'.format(randomword(12)), code=randomword(5))
    test_culture, created = get_or_create(db.session, Culture, defaults=None, **culture_attrs)
    if created:
        db.session.add(test_culture)
        db.session.commit()

    def fin():
        try:
            db.session.delete(test_culture)
            db.session.commit()
        except Exception:
            pass

    request.addfinalizer(fin)
    return test_culture


@pytest.fixture(autouse=True)
def test_org(request):
    org_attrs = dict(name='Rocket League All Stars - {}'.format(randomword(8)))
    test_org, created = get_or_create(session=db.session, model=Organization, defaults=None, org_attrs)
    if created:
        db.session.add(test_org)
        db.session.commit()

    def fin():
        try:
            db.session.delete(test_org)
            db.session.commit()
        except Exception:
            pass

    request.addfinalizer(fin)
    return test_org


@pytest.fixture(autouse=True)
def test_client(request):
    client_attrs = dict(client_id=randomword(30), client_secret='s00pers3kr37_{}'.format(randomword(12)))
    test_client, created = get_or_create(db.session, Client, defaults=None, **client_attrs)
    if created:
        db.session.add(test_client)
        db.session.commit()

    def fin():
        try:
            db.session.delete(test_client)
            db.session.commit()
        except Exception:
            pass

    request.addfinalizer(fin)
    return test_client


@pytest.fixture(autouse=True)
def test_token(test_client, test_user, request):
    # test_token = Token(client_id=test_client.client_id, user_id=test_user.id, token_type='bearer', access_token='good_token',
    #                    refresh_token='barz', expires=datetime(2050, 4, 26))
    token_attrs = dict(client_id=test_client.client_id, user_id=test_user.id,
                       token_type='bearer', access_token='good_token', refresh_token='barz',
                       expires=datetime(2050, 4, 26))
    test_token, created = get_or_create(db.session, Token, defaults=None, **token_attrs)
    if created:
        db.session.add(test_token)
        db.session.commit()

    def fin():
        try:
            db.session.delete(test_token)
            db.session.commit()
        except Exception:
            pass

    request.addfinalizer(fin)
    return test_token


def test_call_requires_auth():
    response = APP.get('/activities/1', headers={'Authorization': 'Bearer good_token'}, data={}, follow_redirects=True)
    assert response.status_code == 200
    response = APP.get('/activities/1', headers={'Authorization': 'Bearer bad_token'}, data={}, follow_redirects=True)
    assert response.status_code == 401


def test_reponse_is_user_filtered():
    response = APP.get('/activities/1', headers={'Authorization': 'Bearer good_token'}, data={}, follow_redirects=True)
    assert json.loads(response.data)['total_count'] == 4


def test_response_can_be_time_filtered():
    today = (datetime.today() + timedelta(minutes=-1)).isoformat()
    url_with_date = '/activities/1?start_time={}'.format(today)
    response = APP.get(url_with_date, headers={'Authorization': 'Bearer good_token'}, follow_redirects=True)
    assert json.loads(response.data)['total_count'] == 3


def test_basic_post(test_user):
    response = APP.post('/activities/', headers={'Authorization': 'Bearer good_token'}, data=dict(
        user_id=test_user.id,
        type=99,
        source_table='test',
        source_id='1337',
        params=str({'lastName': randomword(6), 'firstName': randomword(12)})
    ), follow_redirects=True)
    assert response.status_code == 200


def test_recent_readable():
    response = APP.get('/activities/1?aggregate=1', headers={'Authorization': 'Bearer good_token'}, data={},
                       follow_redirects=True)
    assert response.status_code == 200
    assert len(json.loads(response.data)['activities']) == 1
    assert json.loads(response.data)['activities'][0]['count'] == 4
    assert json.loads(response.data)['activities'][0]['image'] == 'notification.png'
    assert json.loads(response.data)['activities'][0]['readable_text'] == '4 users have joined'


def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.iteritems() if not isinstance(v, ClauseElement))
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        return instance, True


def randomword(length):
    return ''.join(random.choice(string.lowercase) for i in xrange(length))


