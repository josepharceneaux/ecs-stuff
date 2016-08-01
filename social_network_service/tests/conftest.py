# Standard Library

# Third Party
import json
from datetime import datetime, timedelta
import pytest

# App Settings
from social_network_service.common.redis_cache import redis_store
from social_network_service.common.tests.api_conftest import user_first, token_first, talent_pool
from social_network_service.modules.social_network.meetup import Meetup
from social_network_service.social_network_app import app

# Application Specific
from social_network_service.common.models.db import db
from social_network_service.common.models.user import User
from social_network_service.common.models.user import Token
from social_network_service.common.models.event import Event
from social_network_service.common.models.venue import Venue
from social_network_service.common.models.user import Client
from social_network_service.common.models.user import Domain
from social_network_service.common.models.event_organizer import EventOrganizer
from social_network_service.common.models.misc import Organization
from social_network_service.common.models.candidate import SocialNetwork
from social_network_service.common.models.user import UserSocialNetworkCredential
from social_network_service.modules.utilities import delete_events
from social_network_service.common.routes import SocialNetworkApiUrl
from social_network_service.common.talent_config_manager import TalentConfigKeys
from social_network_service.common.utils.handy_functions import send_request

# This is common data for creating test events
EVENT_DATA = {
    "organizer_id": '',  # will be updated in fixture 'meetup_event_data' or 'eventbrite_event_data'
    "venue_id": '',  # will be updated in fixture 'meetup_event_data' or 'eventbrite_event_data'
    "title": "Test Event",
    "description": "Test Event Description",
    "registration_instruction": "Just Come",
    # TODO: utcnow
    "start_datetime": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    # TODO: utcnow
    "end_datetime": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    "group_url_name": "QC-Python-Learning",
    "social_network_id": '',  # will be updated in fixture 'meetup_event_data' or 'eventbrite_event_data'
    "timezone": "Asia/Karachi",
    "cost": 0,
    "currency": "USD",
    "social_network_group_id": 18837246,
    "max_attendees": 10
}


@pytest.fixture(scope='session')
def base_url():
    """
    This fixture returns social network app url
    """
    return SocialNetworkApiUrl.HOST_NAME


@pytest.fixture()
def token(request, user_auth, user_first, talent_pool):
    """
    Returns the access token for a different user so that we can test forbidden error etc.
    :param user_auth: fixture in common/tests/conftest.py
    :param user_first: fixture in common/tests/conftest.py
    :return token
    """
    # TODO: Either define all params or define no one: Applies to more than one places
    auth_token_obj = user_auth.get_auth_token(user_first, get_bearer_token=True)
    return auth_token_obj['access_token']


@pytest.fixture()
def meetup():
    """
    This fixture returns Social network model object for meetup in getTalent database
    :return:
    """
    return SocialNetwork.get_by_name('Meetup')


@pytest.fixture()
def eventbrite():
    """
    This fixture returns Social network model object for eventbrite in getTalent database
    :return:
    """
    return SocialNetwork.get_by_name('Eventbrite')


@pytest.fixture(scope='session')
def facebook():
    """
    This fixture returns Social network model object for facebook in getTalent database
    :return:
    """
    return SocialNetwork.get_by_name('Facebook')


@pytest.fixture()
def test_eventbrite_credentials(request, user_first, eventbrite):
    """
    Create eventbrite social network credentials for this user so
    we can create event on Eventbrite.com
    :param request:
    :param user_first: fixture user
    :return:
    """
    social_network_id = eventbrite.id
    user_credentials = UserSocialNetworkCredential(
        social_network_id=social_network_id,
        user_id=user_first['id'],
        access_token=app.config[TalentConfigKeys.EVENTBRITE_ACCESS_TOKEN],
        refresh_token='')
    UserSocialNetworkCredential.save(user_credentials)

    def fin():
        """
        Delete credentials for eventbrite for test user object at the end of test session
        """
        with app.app_context():
            UserSocialNetworkCredential.delete(user_credentials)

    request.addfinalizer(fin)
    return user_credentials


@pytest.fixture()
def test_meetup_credentials(request, user_first, meetup):
    """
    Create meetup social network credentials for this user so
    we can create event on Meetup.com
    :param request:
    :param user_first: fixture user
    :return:
    """
    # Create a redis object and add meetup access_token and refresh_token entry with 1.5 hour expiry time.
    meetup_key = 'Meetup'

    # If there is no entry with name 'Meetup' then create one using app config
    if not redis_store.get(meetup_key):
        redis_store.set(meetup_key,
                           json.dumps(dict(
                                       access_token=app.config[TalentConfigKeys.MEETUP_ACCESS_TOKEN],
                                       refresh_token=app.config[TalentConfigKeys.MEETUP_REFRESH_TOKEN]
                           )))

    # Get the key value pair of access_token and refresh_token
    meetup_kv = json.loads(redis_store.get(meetup_key))

    social_network_id = meetup.id
    user_credentials = UserSocialNetworkCredential(
        social_network_id=social_network_id,
        user_id=int(user_first['id']),
        access_token=meetup_kv['access_token'],
        refresh_token=meetup_kv['refresh_token'])
    UserSocialNetworkCredential.save(user_credentials)

    # Validate token expiry and generate a new token if expired
    Meetup(user_id=int(user_first['id']))
    db.session.commit()

    # Get the updated user_credentials
    user_credentials = UserSocialNetworkCredential.get_by_user_and_social_network_id(social_network_id=social_network_id,
                                                                                     user_id=int(user_first['id']))

    # If token is changed, then update the new token in redis too
    if meetup_kv['access_token'] != user_credentials.access_token:
        redis_store.set(meetup_key,
                        json.dumps(dict(
                                       access_token=user_credentials.access_token,
                                       refresh_token=user_credentials.refresh_token
                           )))

    def fin():
        """
        Delete credentials for meetup for test user object at the end of test session
        """
        with app.app_context():
            UserSocialNetworkCredential.delete(user_credentials)

    request.addfinalizer(fin)
    return user_credentials


@pytest.fixture()
def meetup_group(test_meetup_credentials, token_first):
    resp = send_request('get', SocialNetworkApiUrl.MEETUP_GROUPS, token_first)
    assert resp.status_code == 200
    # return first group
    return resp.json()['groups'][0]


@pytest.fixture()
def meetup_event_data(request, user_first, meetup, meetup_venue, organizer_in_db, meetup_group):
    """
    This fixture creates a dictionary containing event data to
    create event on Meetup social network.
    It uses meetup SocialNetwork model object, venue for meetup
    and an organizer to create event data
    """
    data = EVENT_DATA.copy()
    data['social_network_id'] = meetup.id
    data['venue_id'] = meetup_venue.id
    data['organizer_id'] = organizer_in_db.id
    data['group_url_name'] = meetup_group['urlname']
    data['social_network_group_id'] = meetup_group['id']

    return data


@pytest.fixture()
def eventbrite_event_data(request, eventbrite, user_first, eventbrite_venue,
                          test_eventbrite_credentials, organizer_in_db):
    data = EVENT_DATA.copy()
    data['social_network_id'] = eventbrite.id
    data['venue_id'] = eventbrite_venue.id
    data['organizer_id'] = organizer_in_db.id

    return data


@pytest.fixture()
def meetup_event(request, user_first, test_meetup_credentials, meetup,
                 meetup_venue, organizer_in_db, token_first, meetup_event_data):
    response = send_request('post',
                            url=SocialNetworkApiUrl.EVENTS,
                            access_token=token_first,
                            data=meetup_event_data)

    assert response.status_code == 201

    data = response.json()
    db.session.commit()
    event = Event.get_by_id(data['id'])
    event_id = event.id

    def fin():
        """
        This is finalizer for meetup event. Once test is passed, we need to
        delete the newly created event from website of social network. After
        test has been passed, we call
        delete_event() function to delete the event both from social network
        and from our database.
        """
        response = send_request('delete', url=SocialNetworkApiUrl.EVENT % event_id,
                                access_token=token_first)
        assert response.status_code == 200 or response.status_code == 403
    request.addfinalizer(fin)
    return event


@pytest.fixture()
def meetup_event_with_user_first(request, user_first, test_meetup_credentials, meetup,
                 meetup_venue, organizer_in_db, token_first, meetup_event_data):
    response = send_request('post',
                            url=SocialNetworkApiUrl.EVENTS,
                            access_token=token_first,
                            data=meetup_event_data)

    assert response.status_code == 201

    data = response.json()
    db.session.commit()  # TODO: I don't think we need this
    event = Event.get_by_id(data['id'])
    event_id = event.id

    def fin():
        """
        This is finalizer for meetup event. Once test is passed, we need to
        delete the newly created event from website of social network. After
        test has been passed, we call
        delete_event() function to delete the event both from social network
        and from our database.
        """
        response = send_request('delete', url=SocialNetworkApiUrl.EVENT % event_id,
                                access_token=token_first)
        assert response.status_code == 200 or response.status_code == 403
    request.addfinalizer(fin)
    return event


@pytest.fixture()
def auth_header(request, token_first):
    """
    returns the header which contains bearer token and content type
    :param auth_data: fixture to get access token
    :return: header dict object
    """
    # TODO: request is unused: Applies to more than one places
    header = {'Authorization': 'Bearer ' + token_first,
              'Content-Type': 'application/json'}
    return header


@pytest.fixture()
def meetup_event_dict(request, user_first, meetup_event, talent_pool):
    """
    This puts meetup event in a dict 'meetup_event_in_db'.
    When event has been imported successfully, we add event_id in this dict.
    After test has passed, we delete this imported event both from social
    network website and database.
    :param request:
    :param meetup_event:
    :type request: flask.request
    :type meetup_event: pyTest fixture
    """
    meetup_event_in_db = {'event': meetup_event}

    def fin():
        """
        This is finalizer for meetup event. Once test is passed, we need to
        delete the newly created event from website of social network. After
        test has been passed, we insert the 'id' of event in our db in
        'event_in_db' dict. If 'id' is present in 'event_in_db', we call
        delete_event() function to delete the event both from social network
        and from our database.
        """

        if 'id' in meetup_event_in_db:
            delete_events(user_first['id'], [meetup_event_in_db['id']])
    return meetup_event_in_db


@pytest.fixture()
def eventbrite_event(request, test_eventbrite_credentials,
                     eventbrite, eventbrite_venue, organizer_in_db, token_first):
    """
    This method create a dictionary data to create event on eventbrite.
    It uses meetup SocialNetwork model object, venue for meetup
    and an organizer to create event data for
    """
    event = EVENT_DATA.copy()
    event['title'] = 'Eventbrite ' + event['title']
    event['social_network_id'] = eventbrite.id
    event['venue_id'] = eventbrite_venue.id

    event['organizer_id'] = organizer_in_db.id

    response = send_request('post',
                            url=SocialNetworkApiUrl.EVENTS,
                            access_token=token_first,
                            data=event)

    assert response.status_code == 201

    data = response.json()
    db.session.commit()
    event = Event.get_by_id(data['id'])
    event_id = event.id

    def fin():
        """
        This is finalizer for eventbrite event. Once test is passed, we need to
        delete the newly created event from website of social network. After
        test has been passed, we call
        delete_event() function to delete the event both from social network
        and from our database.
        """
        response = send_request('delete', url=SocialNetworkApiUrl.EVENT % event_id,
                                access_token=token_first)

        # If event is found and deleted successfully => 200
        # If event is not found => 403
        assert response.status_code == 200 or response.status_code == 403

    request.addfinalizer(fin)
    return event


@pytest.fixture(params=['Eventbrite', 'Meetup'])
def event_in_db(request, eventbrite_event, meetup_event):
    """
    This fixture returns meetup and eventbrite event.
    Any test that will use this fixture will get two events. First it will will return Eventbrite
    event and when that test finishes, it returns meetup test.
    :return:
    """
    if request.param == 'Eventbrite':
        return eventbrite_event
    elif request.param == 'Meetup':
        return meetup_event


@pytest.fixture(params=['Meetup', 'Eventbrite'])
def venue_in_db(request, meetup_venue, eventbrite_venue):
    """
    This fixture returns meetup and eventbrite event one by one depending on the param value.

    """
    if request.param == 'Meetup':
        return meetup_venue
    if request.param == 'Eventbrite':
        return eventbrite_venue


@pytest.fixture()
def meetup_venue(meetup, user_first):
    """
    This fixture returns meetup venue in getTalent database
    """
    social_network_id = meetup.id
    venue = {
        "social_network_id": social_network_id,
        "user_id": user_first['id'],
        "zip_code": "95014",
        "address_line_2": "",
        "address_line_1": "Infinite Loop",
        "latitude": 0,
        "longitude": 0,
        "state": "CA",
        "city": "Cupertino",
        "country": "us"
    }
    venue = Venue(**venue)
    Venue.save(venue)

    return venue


@pytest.fixture()
def eventbrite_venue(user_first, eventbrite):
    """
    This fixture returns eventbrite venue in getTalent database
    """
    social_network_id = eventbrite.id
    venue = {
    "social_network_id": social_network_id,
    "user_id": user_first['id'],
    "zip_code": "54600",
    "address_line_2": "H# 163, Block A",
    "address_line_1": "New Muslim Town",
    "latitude": 0,
    "longitude": 0,
    "state": "Punjab",
    "city": "Lahore",
    "country": "Pakistan"
    }
    venue = Venue(**venue)
    Venue.save(venue)

    return venue


@pytest.fixture()
def organizer_in_db(request, user_first):
    """
    This fixture returns an organizer in getTalent database
    """
    organizer = {
        "user_id": user_first['id'],
        "name": "Test Organizer",
        "email": "testemail@gmail.com",
        "about": "He is a testing engineer"
    }
    organizer = EventOrganizer(**organizer)
    EventOrganizer.save(organizer)

    def fin():
        try:
            EventOrganizer.delete(organizer.id)
        except:
            pass

    request.addfinalizer(fin)
    return organizer


@pytest.fixture()
def get_test_events(request, user_first, meetup, eventbrite, meetup_venue,
                    eventbrite_venue, test_eventbrite_credentials, meetup_group,
                    test_meetup_credentials, organizer_in_db, token_first):
    """
    This fixture returns data (dictionary) to create meetup and eventbrite events
    """
    # Data for Meetup
    meetup_dict = EVENT_DATA.copy()
    meetup_dict['social_network_id'] = meetup.id
    meetup_dict['venue_id'] = meetup_venue.id
    meetup_dict['organizer_id'] = organizer_in_db.id
    meetup_dict['user_id'] = user_first['id']
    meetup_dict['group_url_name'] = meetup_group['urlname']
    meetup_dict['social_network_group_id'] = meetup_group['id']
    # Data for Eventbrite
    eventbrite_dict = EVENT_DATA.copy()
    eventbrite_dict['social_network_id'] = eventbrite.id
    eventbrite_dict['venue_id'] = eventbrite_venue.id
    eventbrite_dict['organizer_id'] = organizer_in_db.id
    eventbrite_dict['user_id'] = user_first['id']

    def delete_test_event():
        # delete event if it was created by API. In that case, data contains id of that event
        if 'id' in meetup_dict:
            event_id = meetup_dict['id']
            del meetup_dict['id']
            response = send_request('delete', url=SocialNetworkApiUrl.EVENT % event_id,
                                    access_token=token_first)

            # If event is found and deleted successfully => 200
            # If event is not found => 403
            assert response.status_code == 200 or response.status_code == 403

        if 'id' in eventbrite_dict:
            event_id = eventbrite_dict['id']
            del eventbrite_dict['id']
            response = send_request('delete', url=SocialNetworkApiUrl.EVENT % event_id,
                                    access_token=token_first)

            # If event is found and deleted successfully => 200
            # If event is not found => 403
            assert response.status_code == 200 or response.status_code == 403

    request.addfinalizer(delete_test_event)
    return meetup_dict, eventbrite_dict


@pytest.fixture(params=['Meetup', 'Eventbrite'])
def test_event(request, get_test_events):
    """
    This fixture returns parameter based meetup or eventbrite data to create event
    :param get_test_events: a tuple containing data for both meetup and eventbrite with user_id
    events
    """
    if request.param == 'Meetup':
        return get_test_events[0]

    if request.param == 'Eventbrite':
        return get_test_events[1]


@pytest.fixture(params=['title', 'description',
                        'end_datetime', 'timezone',
                        'start_datetime', 'currency',
                        'venue_id', 'organizer_id'], scope='function')
def eventbrite_missing_data(request, eventbrite_event_data):
    """
    This fixture returns eventbrite data and a key will be deleted from data to test
    missing input fields exceptions
    :param request:
    :param eventbrite_event_data: dictionary for eventbrite event data
    :return:
    """
    return request.param, eventbrite_event_data.copy()


@pytest.fixture(params=['title', 'description', 'social_network_group_id',
                        'group_url_name', 'start_datetime', 'max_attendees',
                        'venue_id', 'organizer_id'], scope='function')
def meetup_missing_data(request, meetup_event_data):
    """
    This fixture returns meetup data and a key will be deleted from data to test
    missing input fields exceptions
    :param request:
    :param meetup_event_data: dictionary for meetup event data
    :return:
    """
    return request.param, meetup_event_data.copy()


@pytest.fixture()
def is_subscribed_test_data(request, user_first):
    """
    This fixture creates two social networks and add credentials for first social network.
    We actually want to test 'is_subscribed' field in social networks data from API.
    """
    old_records = SocialNetwork.query.filter(SocialNetwork.name.in_(['SN1', 'SN2'])).all()
    for sn in old_records:
        if sn.id is not None:
            try:
                SocialNetwork.delete(sn.id)
            except:
                db.session.rollback()
    test_social_network1 = SocialNetwork(name='SN1', url='www.SN1.com')
    SocialNetwork.save(test_social_network1)
    test_social_network2 = SocialNetwork(name='SN2', url='www.SN1.com')
    SocialNetwork.save(test_social_network2)

    test_social_network1_credentials = UserSocialNetworkCredential(
        user_id=user_first['id'],
        social_network_id=test_social_network1.id,
        access_token='lorel ipsum',
        refresh_token='lorel ipsum')
    UserSocialNetworkCredential.save(test_social_network1_credentials)

    def fin():
        """
        Delete social networks created for tests and UserSocialNetworkCredential record.
        """
        UserSocialNetworkCredential.delete(test_social_network1_credentials.id)
        SocialNetwork.delete(test_social_network1.id)
        SocialNetwork.delete(test_social_network2.id)

    request.addfinalizer(fin)
    return test_social_network1, test_social_network2, test_social_network1_credentials


def teardown_fixtures(user, client_credentials, domain, organization):
    tokens = Token.get_by_user_id(user.id)
    for token_first in tokens:
        Token.delete(token_first.id)
    Client.delete(client_credentials.client_id)
    User.delete(user.id)
    Domain.delete(domain.id)
    Organization.delete(organization.id)

