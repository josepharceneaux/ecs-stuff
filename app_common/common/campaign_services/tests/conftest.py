"""
Here are fixtures to be used across campaign-services.
"""
import json
import pytest
from requests import codes
from datetime import datetime, timedelta

from ...models.db import db
from ...constants import MEETUP
from ...tests.app import test_app
from ...redis_cache import redis_store2
from ...models.candidate import SocialNetwork
from ..tests_helpers import CampaignsTestsHelpers
from ...talent_config_manager import TalentConfigKeys
from ...utils.handy_functions import send_request
from ...utils.datetime_utils import DatetimeUtils
from ...models.user import UserSocialNetworkCredential
from ...routes import SocialNetworkApiUrl, EmailCampaignApiUrl
from social_network_service.modules.social_network.meetup import Meetup

from ...tests.api_conftest import (user_first, token_first, talent_pool_session_scope, user_same_domain,
                                   token_same_domain, user_second, token_second, test_data,
                                   headers, headers_other)

__author__ = 'basit'


# This is common data for creating test events

EVENT_DATA = {
    "organizer_id": '',  # will be updated in fixture 'meetup_event_data' or 'eventbrite_event_data'
    "venue_id": '',  # will be updated in fixture 'meetup_event_data' or 'eventbrite_event_data'
    "title": "Test Event",
    "description": "Test Event Description",
    "registration_instruction": "Just Come",
    "start_datetime": (datetime.utcnow() + timedelta(days=2)).strftime(DatetimeUtils.ISO8601_FORMAT),
    "end_datetime": (datetime.utcnow() + timedelta(days=3)).strftime(DatetimeUtils.ISO8601_FORMAT),
    "group_url_name": "QC-Python-Learning",
    "social_network_id": '',  # will be updated in fixture 'meetup_event_data' or 'eventbrite_event_data'
    "timezone": "Asia/Karachi",
    "cost": 0,
    "currency": "USD",
    "social_network_group_id": 18837246,
    "max_attendees": 10
}


@pytest.fixture(scope="session")
def meetup():
    """
    This fixture returns Social network model object id for meetup in getTalent database
    """
    return {'id': SocialNetwork.get_by_name(MEETUP.title()).id}


@pytest.fixture(scope="session")
def meetup_venue(meetup, user_first, token_first):
    """
    This fixture returns meetup venue in getTalent database
    """
    social_network_id = meetup['id']
    venue = {
        "social_network_id": social_network_id,
        "user_id": user_first['id'],
        "zip_code": "95014",
        "group_url_name": 'Python-Learning-Meetup',
        "address_line_2": "",
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


@pytest.fixture(scope="session", autouse=True)
def test_meetup_credentials(user_first, meetup):
    """
    Create meetup social network credentials for this user so we can create event on Meetup.com
    """
    # Create a redis object and add meetup access_token and refresh_token entry with 1.5 hour expiry time.
    meetup_key = MEETUP.title()

    # If there is no entry with name 'Meetup' then create one using app config
    if not redis_store2.get(meetup_key):
        redis_store2.set(meetup_key,
                         json.dumps(dict(
                             access_token=test_app.config[TalentConfigKeys.MEETUP_ACCESS_TOKEN],
                             refresh_token=test_app.config[TalentConfigKeys.MEETUP_REFRESH_TOKEN]
                         )))

    # Get the key value pair of access_token and refresh_token
    meetup_kv = json.loads(redis_store2.get(meetup_key))

    social_network_id = meetup['id']
    user_credentials = UserSocialNetworkCredential.get_by_user_and_social_network_id(user_first['id'],
                                                                                     social_network_id)

    if not user_credentials:
        user_credentials = UserSocialNetworkCredential(
            social_network_id=social_network_id,
            user_id=int(user_first['id']),
            access_token=meetup_kv['access_token'],
            refresh_token=meetup_kv['refresh_token'])
        UserSocialNetworkCredential.save(user_credentials)

    with test_app.app_context():
        # Validate token expiry and generate a new token if expired
        Meetup(user_id=int(user_first['id']))
        db.session.commit()

    # Get the updated user_credentials
    user_credentials = UserSocialNetworkCredential.get_by_user_and_social_network_id(
        social_network_id=social_network_id,
        user_id=int(user_first['id']))

    # If token is changed, then update the new token in redis too
    if meetup_kv['access_token'] != user_credentials.access_token:
        redis_store2.set(meetup_key,
                         json.dumps(dict(
                             access_token=user_credentials.access_token,
                             refresh_token=user_credentials.refresh_token
                         )))
    return user_credentials


@pytest.fixture(scope="session")
def meetup_group(test_meetup_credentials, token_first):
    """
    This gets all the groups of user_first created on Meetup website. It then picks first group and returns it.
    """
    resp = send_request('get', SocialNetworkApiUrl.MEETUP_GROUPS, token_first)
    assert resp.status_code == codes.OK
    # return first group
    return resp.json()['groups'][0]


@pytest.fixture(scope="session")
def meetup_event_data(meetup, meetup_venue, meetup_group):
    """
    This fixture creates a dictionary containing event data to
    create event on Meetup social network.
    It uses meetup SocialNetwork model object, venue for meetup
    and an organizer to create event data
    """
    data = EVENT_DATA.copy()
    if data.get('organizer_id'):
        del data['organizer_id']
    data['social_network_id'] = meetup['id']
    data['venue_id'] = meetup_venue['id']
    data['group_url_name'] = meetup_group['urlname']
    data['social_network_group_id'] = meetup_group['id']

    return data


@pytest.fixture(scope="session")
def meetup_event(test_meetup_credentials, meetup, meetup_venue, token_first, meetup_event_data):
    """
    This creates an event for Meetup for user_first
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


@pytest.fixture()
def base_campaign(token_first):
    """
    Data is valid. Base campaign should be created
    """
    data = CampaignsTestsHelpers.base_campaign_data()
    response = send_request('post', EmailCampaignApiUrl.BASE_CAMPAIGNS, token_first, data)
    assert response.status_code == codes.CREATED
    assert response.json()['id']
    return response.json()
