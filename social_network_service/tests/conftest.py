import os
from gt_common.models.config import GTSQLAlchemy
if not GTSQLAlchemy.db_session:
    folder = os.path.dirname(__file__)
    app_cfg = os.path.abspath(os.path.join(folder, '../app.cfg'))
    logging_cfg = os.path.abspath(os.path.join(folder, '../logging.conf'))
    GTSQLAlchemy(app_config_path=app_cfg,
                 logging_config_path=logging_cfg)
import pytest
import datetime
from gt_common.models.venue import Venue
from gt_common.models.organizer import Organizer
from social_network_service.manager import process_event, delete_events
from social_network_service.app import app as _app
from werkzeug.security import gen_salt
from gt_common.models.event import Event
from gt_common.models.social_network import SocialNetwork
from gt_common.models.user import User
from gt_common.models.token import Token
from gt_common.models.event import Event
from gt_common.models.client import Client
from gt_common.models.domain import Domain
from gt_common.models.culture import Culture
from gt_common.models.organization import Organization
from gt_common.models.social_network import SocialNetwork
from social_network_service.manager import process_event, delete_events
from social_network_service.app import app as _app

from werkzeug.security import gen_salt
from mixer._faker import faker
from mixer.backend.sqlalchemy import Mixer

db_session = GTSQLAlchemy.db_session

TESTDB = 'test_project.db'
TESTDB_PATH = "/tmp/{}".format(TESTDB)
TEST_DATABASE_URI = 'sqlite:///' + TESTDB_PATH
APP_URL = 'http://127.0.0.1:5000/'

OAUTH_SERVER = 'http://127.0.0.1:8888/oauth2/authorize'
GET_TOKEN_URL = 'http://127.0.0.1:8888/oauth2/token'
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

EVENT_DATA = {
    "organizer_id": 1,
    "venue_id": 1,
    "title": "Test Event",
    "description": "Test Event Description",
    "registration_instruction": "Just Come",
    "end_datetime": (datetime.datetime.now() + datetime.timedelta(days=20)).strftime('%Y-%m-%d %H:%M:%S'),
    "group_url_name": "QC-Python-Learning",
    "social_network_id": 13,
    "timezone": "Asia/Karachi",
    "cost": 0,
    "start_datetime":(datetime.datetime.now() + datetime.timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S'),
    "currency": "USD",
    "group_id": 18837246,
    "max_attendees": 10
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

    def delete_doamin():
        Domain.delete(domain.id)

    request.addfinalizer(delete_doamin)
    return domain


@pytest.fixture(scope='session')
def organization(request):
    mixer = Mixer(session=db_session, commit=True)
    organization = mixer.blend('gt_common.models.organization.Organization')

    def delete_organization():
        Organization.delete(organization.id)
    request.addfinalizer(delete_organization)

    return organization


@pytest.fixture(scope='session')
def user(request, culture):
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
def auth_data(user):
    # TODO; make the URL constant, create client_id and client_secret on the fly
    # auth_service_url = GET_TOKEN_URL

    token = Token.get_by_user_id(user.id)[0]

    # client_credentials = token.client
    # data = dict(client_id=client_credentials.client_id,
    #             client_secret=client_credentials.client_secret, username=user.email,
    #             password='Iamzohaib123', grant_type='password')
    # headers = {'content-type': 'application/x-www-form-urlencoded'}
    # response = requests.post(auth_service_url, data=data, headers=headers)
    # assert response.status_code == 200
    # assert response.json().has_key('access_token')
    # assert response.json().has_key('refresh_token')
    # return response.json()
    return token.to_json()


@pytest.fixture(scope='session')
def meetup_event_data(request, user, meetup):
    data = EVENT_DATA.copy()
    data['social_network_id'] = meetup.id

    def delete_event():
        # delete event if it was created by API. In that case, data contains id of that event
        if 'id' in data:
            event_id = data['id']
            del data['id']
            delete_events(user.id, [event_id])

    request.addfinalizer(delete_event)
    return data


@pytest.fixture(scope='session')
def eventbrite_event_data(eventbrite):
    data = EVENT_DATA.copy()
    data['social_network_id'] = eventbrite.id
    return data


@pytest.fixture(scope='session')
def events(request, user,  meetup, eventbrite):
    events = []
    event = EVENT_DATA.copy()
    event['title'] = 'Meetup ' + event['title']
    event['social_network_id'] = meetup.id
    event['venue_id'] = 1
    event_id = process_event(event, user.id)
    event = Event.get_by_id(event_id)
    events.append(event)

    event = EVENT_DATA.copy()
    event['title'] = 'Eventbrite ' + event['title']
    event['social_network_id'] = eventbrite.id
    event['venue_id'] = 2
    event_id = process_event(event, user.id)
    event = Event.get_by_id(event_id)
    events.append(event)
    Event.session.commit()

    # def delete_test_events():
    #     event_ids = [event.id for event in events]
    #     delete_events(user.id, event_ids)
    #
    # request.addfinalizer(delete_test_events)
    return events


@pytest.fixture(params=['Meetup', 'Eventbrite'])
def event_in_db(request, events):
    if request.param == 'Meetup':
        return events[0]
    if request.param == 'Eventbrite':
        return events[1]


@pytest.fixture(scope='session')
def venues(request, user, meetup, eventbrite):
    venues = []
    meetup_venue = {
        "social_network_id": meetup.id,
        "user_id": user.id,
        "zipcode": "95014",
        "address_line2": "",
        "address_line1": "Infinite Loop",
        "latitude": 0,
        "longitude": 0,
        "state": "CA",
        "city": "Cupertino",
        "country": "us"
    }
    meetup_venue = Venue(**meetup_venue)
    Venue.save(meetup_venue)
    venues.append(meetup_venue)

    eventbrite_venue = {
        "social_network_id": eventbrite.id,
        "user_id": user.id,
        "zipcode": "54600",
        "address_line2": "H# 163, Block A",
        "address_line1": "New Muslim Town",
        "latitude": 0,
        "longitude": 0,
        "state": "Punjab",
        "city": "Lahore",
        "country": "Pakistan"
    }

    eventbrite_venue = Venue(**eventbrite_venue)
    Venue.save(eventbrite_venue)
    Venue.session.commit()
    venues.append(eventbrite_venue)
    return venues


@pytest.fixture(params=['Meetup', 'Eventbrite'])
def venue_in_db(request, venues):
    if request.param == 'Meetup':
        return venues[0]
    if request.param == 'Eventbrite':
        return venues[1]


@pytest.fixture(scope='session')
def organizer_in_db(request, user):
    organizer = {
        "user_id": user.id,
        "name": "Test Organizer",
        "email": "testemail@gmail.com",
        "about": "He is a testing engineer"
    }
    organizer = Organizer(**organizer)
    Organizer.save(organizer)
    Organizer.session.commit()
    return organizer


@pytest.fixture(scope='session')
def get_test_events(request, user, meetup, eventbrite, venues):

    meetup_event_data = EVENT_DATA.copy()
    meetup_event_data['social_network_id'] = meetup.id
    meetup_event_data['venue_id'] = venues[0].id
    eventbrite_event_data = EVENT_DATA.copy()
    eventbrite_event_data['social_network_id'] = eventbrite.id
    eventbrite_event_data['venue_id'] = venues[1].id

    def delete_test_event():
        # delete event if it was created by API. In that case, data contains id of that event
        if 'id' in meetup_event_data:
            event_id = meetup_event_data['id']
            del meetup_event_data['id']
            delete_events(user.id, [event_id])

        if 'id' in eventbrite_event_data:
            event_id = eventbrite_event_data['id']
            del eventbrite_event_data['id']
            delete_events(user.id, [event_id])

    request.addfinalizer(delete_test_event)
    return meetup_event_data, eventbrite_event_data


@pytest.fixture(params=['Meetup', 'Eventbrite'])
def test_event(request, get_test_events):
    if request.param == 'Meetup':
        return get_test_events[0]

    if request.param == 'Eventbrite':
        return get_test_events[1]


@pytest.fixture(params=['title', 'description',
                        'end_datetime', 'timezone',
                        'start_datetime', 'currency'])
def eventbrite_missing_data(request, eventbrite_event_data):

    return request.param, eventbrite_event_data


@pytest.fixture(params=['title', 'description', 'group_id',
                        'group_url_name', 'start_datetime', 'max_attendees'])
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
