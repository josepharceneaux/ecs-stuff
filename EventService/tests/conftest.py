import os
import pytest
from gt_models.client import Client
from gt_models.client import Token
import datetime
import requests

from app import app as _app
from gt_models.config import init_db, db_session
from werkzeug.security import generate_password_hash
from werkzeug.security import gen_salt
from gt_models.event import Event
from gt_models.social_network import SocialNetwork
from gt_models.user import User
from gt_models.domain import Domain
from gt_models.culture import Culture
from gt_models.organization import Organization
from mixer._faker import faker
from mixer.backend.sqlalchemy import Mixer

init_db()

TESTDB = 'test_project.db'
TESTDB_PATH = "/tmp/{}".format(TESTDB)
TEST_DATABASE_URI = 'sqlite:///' + TESTDB_PATH
APP_URL = 'http://127.0.0.1:5000/'

OAUTH_SERVER = 'http://127.0.0.1:8888/oauth2/authorize'
GET_TOKEN_URL = 'http://127.0.0.1:8888/oauth2/token'
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

EVENT_DATA = {
    'eventTitle': 'Test Event',
    'aboutEventOrganizer': 'Zohaib Ijaz',
    'registrationInstruction': 'Just Come',
    'eventDescription': 'Test Event Description',
    'organizerEmail': u'',
    'eventEndDatetime': '15 Oct, 2015 04:51 pm',
    'groupUrlName': 'QC-Python-Learning',
    'eventCountry': 'us',
    'organizerName': u'',
    'socialNetworkId': 13,
    'eventZipCode': '95014',
    'eventAddressLine2': u'',
    'eventAddressLine1': 'Infinite Loop',
    'eventTimeZone': 'UTC',
    'eventState': 'CA',
    'eventCost': 0,
    'eventCity': 'Cupertino',
    'eventStartDatetime': '29 Sep, 2015 04:50 pm',
    'eventCurrency': 'USD',
    'groupId': 18837246,
    'maxAttendees': 10
    }


@pytest.fixture(scope='session')
def base_url():
    return APP_URL


@pytest.fixture(scope='session')
def app(request):
    """
    Create a Flask app, and override settings, for the whole test session.
    """

    _app.app.config.update(
        TESTING=True,
        # SQLALCHEMY_DATABASE_URI=TEST_DATABASE_URI,
        LIVESERVER_PORT=6000
    )

    return _app.app.test_client()


@pytest.fixture(scope='session')
def client(request):
    """
    Get the test_client from the app, for the whole test session.
    """
    # Add test client in Client DB
    client_id = gen_salt(40)
    client_secret = gen_salt(50)
    test_client = Client(
        client_id=client_id,
        client_secret=client_secret
    )
    Client.save(test_client)

    def delete_client():
        Client.delete(test_client.client_id)

    request.addfinalizer(delete_client)
    return test_client


@pytest.fixture(scope='session')
def culture():
    mixer = Mixer(session=db_session, commit=True)
    culture = Culture.get_by_code('en-us')
    if culture:
        return culture
    else:
        culture = mixer.blend('gt_models.culture.Culture', code='en-us')
    return culture


@pytest.fixture(scope='session')
def domain(request, organization, culture):
    now_timestamp = datetime.datetime.now().strftime("%Y:%m:%d %H:%M:%S")
    mixer = Mixer(session=db_session, commit=True)
    domain = mixer.blend(Domain, organization=organization, culture=culture,
                         name=faker.nickname(), addedTime=now_timestamp)

    return domain


@pytest.fixture(scope='session')
def organization(request):
    mixer = Mixer(session=db_session, commit=True)
    organization = mixer.blend('gt_models.organization.Organization')

    return organization


@pytest.fixture(scope='session')
def user(request, culture, domain):
    mixer = Mixer(session=db_session, commit=True)

    user = mixer.blend(User, domain=domain, culture=culture, firstName=faker.nickname(),
                       lastName=faker.nickname(), email=faker.email_address(),
                       password=generate_password_hash('A123456', method='pbkdf2:sha512'))

    return user


@pytest.fixture(scope='session')
def client_credentials(request, user):
    client_id = gen_salt(40)
    client_secret = gen_salt(50)
    client = Client(client_id=client_id, client_secret=client_secret)
    Client.save(client)
    return client


@pytest.fixture(scope='session')
def auth_data(user, base_url, client_credentials):
    # TODO; make the URL constant, create client_id and client_secret on the fly
    auth_service_url = GET_TOKEN_URL

    data = dict(client_id=client_credentials.client_id,
                client_secret=client_credentials.client_secret, username=user.email,
                password='A123456', grant_type='password')
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    response = requests.post(auth_service_url, data=data, headers=headers)
    assert response.status_code == 200
    assert response.json().has_key('access_token')
    assert response.json().has_key('refresh_token')
    return response.json()


@pytest.fixture(scope='session')
def meetup():
    return SocialNetwork.get_by_name('Meetup')


@pytest.fixture(scope='session')
def eventbrite():
    return SocialNetwork.get_by_name('Eventbrite')


@pytest.fixture(scope='session')
def facebook():
    return SocialNetwork.get_by_name('Facebook')


@pytest.fixture(scope='session')
def meetup_event_data(meetup):
    data = EVENT_DATA.copy()
    data['socialNetworkId'] = meetup.id
    return data


@pytest.fixture(scope='session')
def eventbrite_event_data(eventbrite):
    data = EVENT_DATA.copy()
    data['socialNetworkId'] = eventbrite.id
    return data


@pytest.fixture(scope='session')
def events(request, sample_event_data):
    events = []
    for index in range(1, 11):
        event = sample_event_data.copy()
        event['eventTitle'] %= index
        event = Event(**event)
        Event.save(event)
        events.append(event)

    def delete_events():
        for event in events:
            Event.delete(event.id)

    request.addfinalizer(delete_events)
    return events


@pytest.fixture(scope='session')
def get_test_events():

    meetup_event = EVENT_DATA.copy()
    eventbrite_event = EVENT_DATA.copy()
    eventbrite_event['socialNetworkId'] = 18

    return meetup_event, eventbrite_event


@pytest.fixture(params=get_test_events())
def test_event(request):
    return request.param


@pytest.fixture(params=['eventTitle', 'eventDescription',
                        'eventEndDatetime', 'eventTimeZone',
                        'eventStartDatetime', 'eventCurrency'])
def eventbrite_missing_data(request, meetup_event_data):

    return request.param, meetup_event_data


@pytest.fixture(params=['eventTitle', 'eventDescription', 'groupId',
                        'groupUrlName', 'eventStartDatetime', 'maxAttendees',
                        'eventAddressLine1', 'eventCountry', 'eventState',
                        'eventZipCode'])
def meetup_missing_data(request, eventbrite_event_data):
    return request.param, eventbrite_event_data


def teardown_fixtures(user, client_credentials, domain, organization):
    tokens = Token.get_by_user_id(user.id)
    for token in tokens:
        Token.delete(token.id)
    Client.delete(client_credentials.client_id)
    User.delete(user.id)
    Domain.delete(domain.id)
    Organization.delete(organization.id)
