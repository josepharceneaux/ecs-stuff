"""
Author:
        - Saad Abdullah, QC-Technologies, <saadfast.qc@gmail.com>
        - Zohaib Ijaz, QC-Technologies, <mzohaib.qc@gmail.com>
        - Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This file contains pyTest fixtures for tests of social-network-service.
"""
# Standard Library
from copy import deepcopy
import json

# Third Party
import pytest
import requests
from requests import codes

# Common conftests
from social_network_service.common.tests.conftest import user_auth
from social_network_service.common.tests.api_conftest import (user_first, token_first, talent_pool_session_scope,
                                                              user_same_domain, token_same_domain, user_second,
                                                              token_second, test_data)
from social_network_service.common.campaign_services.tests.conftest import (meetup, meetup_event,
                                                                            meetup_venue, test_meetup_credentials,
                                                                            meetup_event_data, meetup_group,
                                                                            EVENT_DATA, eventbrite_event,
                                                                            test_eventbrite_credentials, eventbrite,
                                                                            eventbrite_venue, event_in_db, VENDORS,
                                                                            test_eventbrite_credentials_same_domain,
                                                                            eventbrite_venue_same_domain,
                                                                            organizer_in_db, test_credentials,
                                                                            EVENTBRITE_CONFIG)

# Models
from social_network_service.common.models.db import db
from social_network_service.common.models.misc import Organization
from social_network_service.common.models.user import (User, Token, Client, Domain, UserSocialNetworkCredential)

# Common utils
from social_network_service.common.routes import SocialNetworkApiUrl
from social_network_service.common.models.candidate import SocialNetwork
from social_network_service.common.utils.handy_functions import send_request

# Application Specific
from social_network_service.modules.social_network.eventbrite import Eventbrite
from social_network_service.social_network_app import app
from social_network_service.common.constants import FACEBOOK, MEETUP
from social_network_service.social_network_app import logger
from social_network_service.tests.helper_functions import get_headers


@pytest.fixture(scope='session')
def base_url():
    """
    This fixture returns social network app url
    """
    return SocialNetworkApiUrl.HOST_NAME


@pytest.fixture(scope='session')
def facebook():
    """
    This fixture returns Social network model object for facebook in getTalent database
    """
    return SocialNetwork.get_by_name(FACEBOOK.title())


@pytest.fixture()
def eventbrite_event_data(eventbrite, eventbrite_venue, test_eventbrite_credentials):
    """
    This fixture creates a dictionary containing event data to create event on Eventbrite social network.
    It uses eventbrite SocialNetwork model object, venue for eventbrite and an organizer to create event data
    """
    data = EVENT_DATA.copy()
    data['social_network_id'] = eventbrite['id']
    data['venue_id'] = eventbrite_venue['id']

    return data


@pytest.fixture(scope="session")
def everbrite_webhook(test_eventbrite_credentials):
    with app.app_context():
        try:
            Eventbrite.create_webhook(test_eventbrite_credentials)
        except:
            pass


@pytest.fixture(scope="function")
def meetup_event_second(test_meetup_credentials, meetup, meetup_venue_second,
                        token_first, meetup_event_data):
    """
    This creates another event for Meetup for user_first
    """

    response = send_request('post', url=SocialNetworkApiUrl.EVENTS, access_token=token_first, data=meetup_event_data)

    assert response.status_code == codes.CREATED, "Response: {}".format(response.text)

    data = response.json()
    assert data['id']

    response_get = send_request('get', url=SocialNetworkApiUrl.EVENT % data['id'], access_token=token_first)

    assert response_get.status_code == codes.OK, response_get.text

    _event = response_get.json()['event']
    _event['venue_id'] = _event['venue']['id']
    del _event['venue']
    del _event['event_organizer']

    return _event


@pytest.fixture(scope="session")
def meetup_event_dict(meetup_event, talent_pool_session_scope):
    """
    This puts meetup event in a dict 'meetup_event_in_db'.
    When event has been imported successfully, we add event_id in this dict.
    After test has passed, we delete this imported event both from social
    network website and database.
    """
    meetup_event_in_db = {'event': meetup_event}

    return meetup_event_in_db


@pytest.fixture(scope="function")
def meetup_event_dict_second(meetup_event_second, talent_pool_session_scope):
    """
    This puts meetup event in a dict 'meetup_event_in_db'.
    When event has been imported successfully, we add event_id in this dict.
    After test has passed, we delete this imported event both from social
    network website and database.
    """
    meetup_event_in_db = {'event': meetup_event_second}

    return meetup_event_in_db


@pytest.fixture(scope="function")
def eventbrite_event_second(test_eventbrite_credentials, eventbrite, eventbrite_venue_second,
                            token_first):
    """
    This method create a dictionary data to create event on eventbrite.
    It uses meetup SocialNetwork model object, venue for meetup
    and an organizer to create event data for
    """
    event = EVENT_DATA.copy()
    event['title'] = 'Eventbrite ' + event['title']
    event['social_network_id'] = eventbrite['id']
    event['venue_id'] = eventbrite_venue_second['id']
    response = send_request('post', url=SocialNetworkApiUrl.EVENTS, access_token=token_first, data=event)
    assert response.status_code == codes.CREATED, "Response: {}".format(response.text)

    data = response.json()
    assert data['id']

    response_get = send_request('get', url=SocialNetworkApiUrl.EVENT % data['id'], access_token=token_first)

    assert response_get.status_code == codes.OK, response_get.text

    _event = response_get.json()['event']
    _event['venue_id'] = _event['venue']['id']
    del _event['venue']
    del _event['event_organizer']

    return _event


@pytest.fixture(scope="function")
def meetup_venue_second(meetup, user_first, token_first, test_meetup_credentials):
    """
    This fixture returns meetup venue in getTalent database
    """
    social_network_id = meetup['id']
    venue = {
        "social_network_id": social_network_id,
        "user_id": user_first['id'],
        "zip_code": "95014",
        "address_line_2": "",
        "group_url_name": 'Python-Learning-Meetup',
        "address_line_1": "Infinite Loop",
        "latitude": 0,
        "longitude": 0,
        "state": "CA",
        "city": "Cupertino",
        "country": "us"
    }

    response_post = send_request('POST', SocialNetworkApiUrl.VENUES, access_token=token_first, data=venue)

    data = response_post.json()
    if response_post.status_code == codes.bad:
        data = data['error']

    assert response_post.status_code == codes.created or response_post.status_code == codes.bad, response_post.text
    venue_id = data['id']

    return {'id': venue_id}


@pytest.fixture(scope="function")
def eventbrite_venue_second(user_first, eventbrite, token_first):
    """
    This fixture returns eventbrite venue in getTalent database
    """
    social_network_id = eventbrite['id']
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

    response_post = send_request('POST', SocialNetworkApiUrl.VENUES, access_token=token_first, data=venue)

    assert response_post.status_code == codes.created, response_post.text

    venue_id = response_post.json()['id']

    return {'id': venue_id}


@pytest.fixture(scope="function", params=VENDORS)
def event_in_db_second(request):
    """
    This fixture creates another event on vendor basis and returns it.
    e.g. In case of Eventbrite, it will return fixture named as "eventbrite_event_second"
    """
    return deepcopy(request.getfuncargvalue("{}_event_second".format(request.param.lower())))


@pytest.fixture(scope="session", params=VENDORS)
def venue_in_db(request):
    """
    This fixture creates a venue on vendor basis and returns it.
    e.g. In case of Eventbrite, it will return fixture named as "eventbrite_venue"
    """
    return request.getfuncargvalue("{}_venue".format(request.param.lower()))


@pytest.fixture(scope="function", params=VENDORS)
def venue_in_db_second(request):
    """
    This fixture creates another venue on vendor basis and returns it.
    e.g. In case of Eventbrite, it will return fixture named as "eventbrite_venue_second"
    """
    return request.getfuncargvalue("{}_venue_second".format(request.param.lower()))


@pytest.fixture()
def get_test_event_eventbrite(user_first, eventbrite, eventbrite_venue, token_first):
    """
    This fixture returns data (dictionary) to create eventbrite events
    """
    # Data for Eventbrite
    eventbrite_dict = EVENT_DATA.copy()
    eventbrite_dict['social_network_id'] = eventbrite['id']
    eventbrite_dict['venue_id'] = eventbrite_venue['id']
    eventbrite_dict['user_id'] = user_first['id']

    return eventbrite_dict


@pytest.fixture()
def get_test_event_meetup(user_first, meetup, meetup_venue, meetup_group, token_first):
    """
    This fixture returns data (dictionary) to create meetup and eventbrite events
    """
    # Data for Meetup
    meetup_dict = EVENT_DATA.copy()
    meetup_dict['social_network_id'] = meetup['id']
    meetup_dict['venue_id'] = meetup_venue['id']
    meetup_dict['user_id'] = user_first['id']
    meetup_dict['group_url_name'] = meetup_group['urlname']
    meetup_dict['social_network_group_id'] = meetup_group['id']

    return meetup_dict


@pytest.fixture(params=VENDORS)
def test_event(request):
    """
    This fixture creates an event (function based scope) on vendor basis and returns it.
    e.g. In case of Eventbrite, it will return fixture named as "get_test_event_eventbrite"
    """
    return request.getfuncargvalue("get_test_event_{}".format(request.param.lower()))


@pytest.fixture(params=VENDORS)
def event_data(request):
    """
    This fixture returns an event (function based scope) on vendor basis and returns it.
    """
    return request.getfuncargvalue("{}_event_data".format(request.param.lower()))


@pytest.fixture(params=['title', 'description', 'end_datetime', 'timezone', 'start_datetime', 'currency',
                        'venue_id'], scope='function')
def eventbrite_missing_data(request, eventbrite_event_data):
    """
    This fixture returns eventbrite data and a key will be deleted from data to test
    missing input fields exceptions
    """
    return request.param, eventbrite_event_data.copy()


@pytest.fixture(params=['description', 'social_network_group_id', 'group_url_name', 'start_datetime', 'max_attendees',
                        'venue_id'], scope='function')
def meetup_missing_data(request, meetup_event_data):
    """
    This fixture returns meetup data and a key will be deleted from data to test
    missing input fields exceptions
    """
    return request.param, meetup_event_data.copy()


@pytest.fixture()
def is_subscribed_test_data(user_first):
    """
    This fixture creates two social networks and add credentials for first social network.
    We actually want to test 'is_subscribed' field in social networks data from API.
    """
    old_records = SocialNetwork.query.filter(SocialNetwork.name.in_(['SN1', 'SN2'])).all()
    for sn in old_records:
        if sn.id is not None:
            try:
                SocialNetwork.delete(sn.id)
            except Exception:
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
    return test_social_network1, test_social_network2, test_social_network1_credentials


def teardown_fixtures(user, client_credentials, domain, organization):
    """
    Cleaning database tables Token, Client, User, Domain and Organization.
    """
    tokens = Token.get_by_user_id(user.id)
    for token_first in tokens:
        Token.delete(token_first.id)
    Client.delete(client_credentials.client_id)
    User.delete(user.id)
    Domain.delete(domain.id)
    Organization.delete(organization.id)
