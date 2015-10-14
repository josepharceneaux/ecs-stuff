import os
import string
from common.models.db import db
from social_network_service import init_app

app = init_app()
import pytest
import random

from social_network_service.utilities import process_event, delete_events
from datetime import datetime, timedelta
from common.models.venue import Venue
from common.models.organizer import Organizer
from common.models.user import User, UserCredentials
from common.models.user import Token
from common.models.event import Event
from common.models.user import Client
from common.models.domain import Domain
from common.models.culture import Culture
from common.models.organization import Organization
from common.models.social_network import SocialNetwork

from werkzeug.security import gen_salt, generate_password_hash
from mixer._faker import faker
from mixer.backend.sqlalchemy import Mixer

db_session = db.session

TESTDB = 'test_project.db'
TESTDB_PATH = "/tmp/{}".format(TESTDB)
TEST_DATABASE_URI = 'sqlite:///' + TESTDB_PATH
APP_URL = app.config['APP_URL']

OAUTH_SERVER = app.config['OAUTH_SERVER_URI']
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

EVENT_DATA = {
    "organizer_id": '',  # will be updated in fixture 'meetup_event_data' or 'eventbrite_event_data'
    "venue_id": '',  # will be updated in fixture 'meetup_event_data' or 'eventbrite_event_data'
    "title": "Test Event",
    "description": "Test Event Description",
    "registration_instruction": "Just Come",
    "start_datetime": (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d %H:%M:%S'),
    "end_datetime": (datetime.now() + timedelta(days=22)).strftime('%Y-%m-%d %H:%M:%S'),
    "group_url_name": "QC-Python-Learning",
    "social_network_id": '',  # will be updated in fixture 'meetup_event_data' or 'eventbrite_event_data'
    "timezone": "Asia/Karachi",
    "cost": 0,
    "currency": "USD",
    "group_id": 18837246,
    "max_attendees": 10
}


@pytest.fixture(scope='session')
def base_url():
    return APP_URL


# @pytest.fixture(scope='session')
# def app(request):
#     """
#     Create a Flask app, and override settings, for the whole test session.
#     """
#
#     app.config.update(
#         TESTING=True,
#         # SQLALCHEMY_DATABASE_URI=TEST_DATABASE_URI,
#         LIVESERVER_PORT=6000
#     )
#
#     return app.test_client()


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
def test_client(request):
    """
    Get the test_client from the app, for the whole test session.
    """
    # Add test client in Client DB
    client_id = gen_salt(40)
    client_secret = gen_salt(50)
    client = Client(
        client_id=client_id,
        client_secret=client_secret
    )
    Client.save(test_client)

    def delete_client():
        Client.delete(client.client_id)

    request.addfinalizer(delete_client)
    return client


@pytest.fixture(scope='session')
def test_culture(request):
    mixer = Mixer(session=db_session, commit=True)
    culture = mixer.blend(Culture, description=faker.nickname(), code=randomword(5))

    def fin():
        Culture.delete(culture.id)

    request.addfinalizer(fin)
    return culture


@pytest.fixture(scope='session')
def test_organization(request):
    mixer = Mixer(session=db_session, commit=True)
    organization = mixer.blend(Organization, name=faker.nickname(), notes='')

    def delete_organization():
        Organization.delete(organization.id)

    request.addfinalizer(delete_organization)

    return organization


@pytest.fixture(scope='session')
def test_domain(request, test_organization, test_culture):
    now_timestamp = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
    mixer = Mixer(session=db_session, commit=True)
    domain = mixer.blend(Domain, organization=test_organization, culture=test_culture,
                         name=faker.nickname(), addedTime=now_timestamp)

    def delete_doamin():
        Domain.delete(domain.id)

    request.addfinalizer(delete_doamin)
    return domain


@pytest.fixture(scope='session')
def test_user(request, test_domain):
    mixer = Mixer(session=db_session, commit=True)
    user = mixer.blend(User, domain=test_domain, firstName=faker.nickname(),
                       lastName=faker.nickname(), email=faker.email_address(),
                       password=generate_password_hash('A123456', method='pbkdf2:sha512'))

    def fin():
        User.delete(user.id)

    request.addfinalizer(fin)
    return user


@pytest.fixture(scope='session')
def test_token(request, test_user):
    mixer = Mixer(session=db_session, commit=True)
    token = mixer.blend(Token,
                        user=test_user,
                        token_type='Bearer',
                        access_token=randomword(20),
                        refresh_token=randomword(20),
                        expires=datetime(year=2050, month=1, day=1))

    def fin():
        Token.delete(token)

    request.addfinalizer(fin)
    return token


@pytest.fixture(scope='session')
def test_eventbrite_credentials(request, test_user):
    mixer = Mixer(session=db_session, commit=True)
    sn = SocialNetwork.get_by_name('Eventbrite')
    user_credentials = mixer.blend(UserCredentials,
                                   social_network=sn,
                                   user=test_user,
                                   access_token=app.config['EVENTBRITE_ACCESS_TOKEN'],
                                   refresh_token=app.config['EVENTBRITE_REFRESH_TOKEN'])

    def fin():
        UserCredentials.delete(user_credentials.id)

    request.addfinalizer(fin)
    return user_credentials


@pytest.fixture(scope='session')
def test_meetup_credentials(request, test_user):
    mixer = Mixer(session=db_session, commit=True)
    sn = SocialNetwork.get_by_name('Meetup')
    user_credentials = mixer.blend(UserCredentials,
                                   social_network=sn,
                                   user=test_user,
                                   access_token=app.config['MEETUP_ACCESS_TOKEN'],
                                   refresh_token=app.config['MEETUP_REFRESH_TOKEN'])

    def fin():
        UserCredentials.delete(user_credentials.id)

    request.addfinalizer(fin)
    return user_credentials


@pytest.fixture(scope='session')
def auth_data(test_user, test_eventbrite_credentials, test_meetup_credentials, test_token):
    token = test_token
    return token.to_json()


@pytest.fixture(scope='session')
def meetup_event_data(request, test_user, meetup, meetup_venue, test_meetup_credentials, organizer_in_db):
    data = EVENT_DATA.copy()
    data['social_network_id'] = meetup.id
    data['venue_id'] = meetup_venue.id
    data['organizer_id'] = organizer_in_db.id

    def delete_event():
        # delete event if it was created by API. In that case, data contains id of that event
        if 'id' in data:
            event_id = data['id']
            del data['id']
            delete_events(test_user.id, [event_id])

    request.addfinalizer(delete_event)
    return data


@pytest.fixture(scope='session')
def eventbrite_event_data(request, eventbrite, test_user, eventbrite_venue, test_eventbrite_credentials,
                          organizer_in_db):
    data = EVENT_DATA.copy()
    data['social_network_id'] = eventbrite.id
    data['venue_id'] = eventbrite_venue.id
    data['organizer_id'] = organizer_in_db.id

    def delete_event():
        # delete event if it was created by API. In that case, data contains id of that event
        if 'id' in data:
            event_id = data['id']
            del data['id']
            delete_events(test_user.id, [event_id])

    request.addfinalizer(delete_event)
    return data


@pytest.fixture(scope='function')
def meetup_event(request, test_user, test_meetup_credentials, meetup,
                 venues, organizer_in_db):
    event = EVENT_DATA.copy()
    event['title'] = 'Meetup ' + event['title']
    event['social_network_id'] = meetup.id
    event['venue_id'] = venues[0].id
    event['organizer_id'] = organizer_in_db.id
    event_id = process_event(event, test_user.id)
    event = Event.get_by_id(event_id)
    event_in_db = {'event': event}

    def fin():
        """
        This is finalizer for meetup event. Once test is passed, we need to
        delete the newly created event from website of social network. After
        test has been passed, we insert the 'id' of event in our db in
        'event_in_db' dict. If 'id' is present in 'event_in_db', we call
        delete_event() function to delete the event both from social network
        and from our database.
        """
        if 'id' in event_in_db:
            delete_events(test_user.id, [event_in_db['id']])
    request.addfinalizer(fin)
    return event_in_db


@pytest.fixture(scope='session')
def eventbrite_event(request, test_user, test_eventbrite_credentials,
                     eventbrite, venues, organizer_in_db):
    event = EVENT_DATA.copy()
    event['title'] = 'Eventbrite ' + event['title']
    event['social_network_id'] = eventbrite.id
    event['venue_id'] = venues[1].id
    event['organizer_id'] = organizer_in_db.id
    event_id = process_event(event, test_user.id)
    event = Event.get_by_id(event_id)

    def fin():
        """
        This is finalizer for meetup event. Once test is passed, we need to
        delete the newly created event from website of social network. After
        test has been passed, we insert the 'id' of event in our db in
        'event_in_db' dict. If 'id' is present in 'event_in_db', we call
        delete_event() function to delete the event both from social network
        and from our database.
        """
        delete_events(test_user.id, [event_id])
    request.addfinalizer(fin)
    return event

    # def delete_test_events():
    #     event_ids = [event.id for event in events]
    #     delete_events(user.id, event_ids)
    #
    # request.addfinalizer(delete_test_events)
    # return events


# @pytest.fixture(scope='session')
# def meetup_event_in_db(events):
#     return events[0]
#
#
@pytest.fixture(params=['Eventbrite', 'Meetup'])
def event_in_db(request, eventbrite_event, meetup_event):
    if request.param == 'Eventbrite':
        return eventbrite_event
    elif request.param == 'Meetup':
        return meetup_event


@pytest.fixture(scope='session')
def venues(request, test_user, meetup, eventbrite):
    venues = []
    meetup_venue = {
        "social_network_id": meetup.id,
        "user_id": test_user.id,
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
        "user_id": test_user.id,
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
    venues.append(eventbrite_venue)
    return venues


@pytest.fixture(params=['Meetup', 'Eventbrite'])
def venue_in_db(request, venues):
    if request.param == 'Meetup':
        return venues[0]
    if request.param == 'Eventbrite':
        return venues[1]


@pytest.fixture(scope='session')
def meetup_venue(request, venues):
    return venues[0]


@pytest.fixture(scope='session')
def eventbrite_venue(request, venues):
    return venues[1]


@pytest.fixture(scope='session')
def organizer_in_db(request, test_user):
    organizer = {
        "user_id": test_user.id,
        "name": "Test Organizer",
        "email": "testemail@gmail.com",
        "about": "He is a testing engineer"
    }
    organizer = Organizer(**organizer)
    Organizer.save(organizer)
    return organizer


@pytest.fixture(scope='session')
def get_test_events(request, test_user, meetup, eventbrite, venues, test_eventbrite_credentials,
           test_meetup_credentials, organizer_in_db):
    meetup_event_data = EVENT_DATA.copy()
    meetup_event_data['social_network_id'] = meetup.id
    meetup_event_data['venue_id'] = venues[0].id
    meetup_event_data['organizer_id'] = organizer_in_db.id
    eventbrite_event_data = EVENT_DATA.copy()
    eventbrite_event_data['social_network_id'] = eventbrite.id
    eventbrite_event_data['venue_id'] = venues[1].id
    eventbrite_event_data['organizer_id'] = organizer_in_db.id

    def delete_test_event():
        # delete event if it was created by API. In that case, data contains id of that event
        if 'id' in meetup_event_data:
            event_id = meetup_event_data['id']
            del meetup_event_data['id']
            delete_events(test_user.id, [event_id])

        if 'id' in eventbrite_event_data:
            event_id = eventbrite_event_data['id']
            del eventbrite_event_data['id']
            delete_events(test_user.id, [event_id])

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


@pytest.fixture(scope='session')
def is_subscribed_test_data(request, test_user):
    old_records = SocialNetwork.query.filter(SocialNetwork.name.in_(['SN1', 'SN2'])).all()
    for sn in old_records:
        SocialNetwork.delete(sn.id)
    test_social_network1 = SocialNetwork(name='SN1', url='www.SN1.com')
    SocialNetwork.save(test_social_network1)
    test_social_network2 = SocialNetwork(name='SN2', url='www.SN1.com')
    SocialNetwork.save(test_social_network2)

    test_social_network1_credentials = UserCredentials(user_id=test_user.id,
                                                       social_network_id=test_social_network1.id,
                                                       access_token='lorel ipsum',
                                                       refresh_token='lorel ipsum')
    UserCredentials.save(test_social_network1_credentials)

    def fin():
        UserCredentials.delete(test_social_network1_credentials.id)
        SocialNetwork.delete(test_social_network1.id)
        SocialNetwork.delete(test_social_network2.id)

    request.addfinalizer(fin)
    return test_social_network1, test_social_network2, test_social_network1_credentials


def teardown_fixtures(user, client_credentials, domain, organization):
    tokens = Token.get_by_user_id(user.id)
    for token in tokens:
        Token.delete(token.id)
    Client.delete(client_credentials.client_id)
    User.delete(user.id)
    Domain.delete(domain.id)
    Organization.delete(organization.id)


def randomword(length):
    return ''.join(random.choice(string.lowercase) for i in xrange(length))
