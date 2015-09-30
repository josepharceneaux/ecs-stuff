import os
import pytest
from social_network_service.manager import process_event, delete_events
from gt_common.models.client import Client
from gt_common.models.client import Token
import datetime
import requests

from social_network_service.app import app as _app
from gt_common.models.config import init_db, db_session
from werkzeug.security import generate_password_hash
from werkzeug.security import gen_salt
from gt_common.models.event import Event
from gt_common.models.social_network import SocialNetwork
from gt_common.models.user import User
from gt_common.models.domain import Domain
from gt_common.models.culture import Culture
from gt_common.models.organization import Organization
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
    'event_title': 'Test Event',
    'about_event_organizer': 'Zohaib Ijaz',
    'registration_instruction': 'Just Come',
    'event_description': 'Test Event Description',
    'organizer_email': u'',
    'event_end_datetime': (datetime.datetime.now() + datetime.timedelta(days=20)).strftime('%Y-%m-%d %H:%M:%S'),
    'group_url_name': 'QC-Python-Learning',
    'event_country': 'us',
    'organizer_name': u'',
    'social_network_id': 13,
    'event_zip_code': '95014',
    'event_address_line2': u'',
    'event_address_line1': 'Infinite Loop',
    'event_latitude': 0,
    'event_longitude': 0,
    'event_time_zone': 'Asia/Karachi',
    'event_state': 'CA',
    'event_cost': 0,
    'tickets_id': 0,
    'event_city': 'Cupertino',
    'event_start_datetime': (datetime.datetime.now() + datetime.timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S'),
    'event_currency': 'USD',
    'group_id': 18837246,
    'max_attendees': 10
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
def meetup():
    return SocialNetwork.get_by_name('Meetup')


@pytest.fixture(scope='session')
def eventbrite():
    return SocialNetwork.get_by_name('Eventbrite')


@pytest.fixture(scope='session')
def facebook():
    return SocialNetwork.get_by_name('Facebook')

# @pytest.fixture(scope='session')
# def client(request):
#     """
#     Get the test_client from the app, for the whole test session.
#     """
#     # Add test client in Client DB
#     client_id = gen_salt(40)
#     client_secret = gen_salt(50)
#     test_client = Client(
#         client_id=client_id,
#         client_secret=client_secret
#     )
#     Client.save(test_client)
#
#     def delete_client():
#         Client.delete(test_client.client_id)
#
#     request.addfinalizer(delete_client)
#     return test_client


@pytest.fixture(scope='session')
def culture():
    mixer = Mixer(session=db_session, commit=True)
    culture = Culture.get_by_code('en-us')
    if culture:
        return culture
    else:
        culture = mixer.blend('common.gt_models.culture.Culture', code='en-us')
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
    organization = mixer.blend('common.gt_models.organization.Organization')

    return organization


@pytest.fixture(scope='session')
def user(request, culture, domain):
    mixer = Mixer(session=db_session, commit=True)
    user = User.get_by_id(1)
    # user = mixer.blend(User, domain=domain, culture=culture, firstName=faker.nickname(),
    #                    lastName=faker.nickname(), email=faker.email_address(),
    #                    password=generate_password_hash('A123456', method='pbkdf2:sha512'))

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

    token = Token.get_by_user_id(user.id)
    client_credentials = token.client
    data = dict(client_id=client_credentials.client_id,
                client_secret=client_credentials.client_secret, username=user.email,
                password='Iamzohaib123', grant_type='password')
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    response = requests.post(auth_service_url, data=data, headers=headers)
    assert response.status_code == 200
    assert response.json().has_key('access_token')
    assert response.json().has_key('refresh_token')
    return response.json()


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
def events(request, user,  meetup, eventbrite):
    events = []
    event = EVENT_DATA.copy()
    event['event_title'] = 'Meetup ' + event['event_title']
    event['social_network_id'] = meetup.id
    event_id = process_event(event, user.id)
    event = Event.get_by_id(event_id)
    events.append(event)

    event = EVENT_DATA.copy()
    event['event_title'] = 'Eventbrite ' + event['event_title']
    event['social_network_id'] = eventbrite.id
    event_id = process_event(event, user.id)
    event = Event.get_by_id(event_id)
    events.append(event)

    def delete_test_events():
        event_ids = [event.id for event in events]
        delete_events(user.id, event_ids)

    request.addfinalizer(delete_test_events)
    return events


@pytest.fixture(params=['Meetup', 'Eventbrite'])
def event_in_db(request, events):
    if request.param == 'Meetup':
        return events[0]
    if request.param == 'Eventbrite':
        return events[1]


@pytest.fixture(scope='session')
def get_test_events(meetup, eventbrite):

    meetup_event = EVENT_DATA.copy()
    meetup_event['social_network_id'] = meetup.id
    eventbrite_event = EVENT_DATA.copy()
    eventbrite_event['social_network_id'] = eventbrite.id

    return meetup_event, eventbrite_event


@pytest.fixture(params=['Meetup', 'Eventbrite'])
def test_event(request, get_test_events):
    if request.param == 'Meetup':
        return get_test_events[0]
    if request.param == 'Eventbrite':
        return get_test_events[1]


@pytest.fixture(params=['event_title', 'event_description',
                        'event_end_datetime', 'event_time_zone',
                        'event_start_datetime', 'event_currency'])
def eventbrite_missing_data(request, eventbrite_event_data):

    return request.param, eventbrite_event_data


@pytest.fixture(params=['event_title', 'event_description', 'group_id',
                        'group_url_name', 'event_start_datetime', 'max_attendees',
                        'event_address_line1', 'event_country', 'event_state',
                        'event_zip_code'])
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
