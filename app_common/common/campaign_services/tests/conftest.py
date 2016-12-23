"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

Here are fixtures to be used across campaign-services.
"""
# Packages
import json
import pytest
from copy import deepcopy
from requests import codes


# Application Specific

from ...models.db import db
from ...tests.app import test_app, logger
from ...tests.sample_data import fake
from ...redis_cache import redis_store2
from ...constants import (MEETUP, EVENTBRITE)
from ...models.event import MeetupGroup
from ...models.candidate import SocialNetwork
from ..tests_helpers import CampaignsTestsHelpers
from ...utils.handy_functions import send_request
from ...models.event_organizer import EventOrganizer
from ...talent_config_manager import TalentConfigKeys, TalentEnvs
from ...models.user import UserSocialNetworkCredential
from ...utils.test_utils import add_social_network_credentials, add_test_venue
from ...routes import (SocialNetworkApiUrl, EmailCampaignApiUrl)
from ..tests.modules.helper_functions import (EVENT_DATA, create_email_campaign_with_base_id,
                                              create_an_rsvp_in_database)
from ...tests.api_conftest import (user_first, token_first, talent_pool_session_scope, smartlist_first, talent_pool,
                                   candidate_first, talent_pipeline, user_same_domain, token_same_domain, user_second,
                                   token_second, test_data, headers, headers_other, headers_same_domain,
                                   smartlist_same_domain, candidate_same_domain)

__author__ = 'basit'

EVENTBRITE_CONFIG = {'skip': True,
                     'reason': 'In contact with Eventbrite support for increasing hit rate limit'}

# Add new vendor here to run tests for that particular social-network
VENDORS = [MEETUP.title(),
           pytest.mark.skipif(EVENTBRITE_CONFIG['skip'], reason=EVENTBRITE_CONFIG['reason'])(EVENTBRITE.title())]

"""
Fixtures related to Meetup
"""


@pytest.fixture(scope="session")
def meetup():
    """
    This fixture returns Social network model object id for meetup in getTalent database
    """
    return {'id': SocialNetwork.get_by_name(MEETUP.title()).id}


@pytest.fixture(scope="session")
def meetup_venue(meetup, user_first, token_first, test_meetup_credentials):
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


@pytest.fixture(scope="session", params=VENDORS)
def test_credentials(request):
    """
    This fixture creates credentials for vendors present in VENDORS list
    """
    return deepcopy(request.getfuncargvalue("test_{}_credentials".format(request.param.lower())))


@pytest.fixture(scope="session")
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

    # TODO: Commenting for now to avoid import from social-network-service
    # with test_app.app_context():
    #     # This is put here so Meetup object is not created unwillingly
    #     from social_network_service.modules.social_network.meetup import Meetup
    #     # Validate token expiry and generate a new token if expired
    #     Meetup(user_id=int(user_first['id']))
    #     db.session.commit()

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
def meetup_group(request, test_meetup_credentials, token_first, user_first):
    """
    This gets all the groups of user_first created on Meetup website. It then picks first group and returns it.
    """
    resp = send_request('get', SocialNetworkApiUrl.MEETUP_GROUPS, token_first)
    assert resp.status_code == codes.OK
    # return first group
    json_group = resp.json()['groups'][0]
    MeetupGroup.query.filter_by(name='test_group', group_id=json_group['id']).delete(synchronize_session=False)
    MeetupGroup.session.commit()
    group = MeetupGroup.save(MeetupGroup(group_id=json_group['id'], user_id=user_first['id'],
                                         url_name=json_group['urlname'], name='test_group'))

    def finalizer():
        MeetupGroup.delete(group)
    request.addfinalizer(finalizer)
    return json_group


@pytest.fixture(scope="session")
def meetup_event_data(meetup, meetup_venue, meetup_group):
    """
    This fixture creates a dictionary containing event data to
    create event on Meetup social network.
    It uses meetup SocialNetwork model object, venue for meetup
    and an organizer to create event data
    """
    data = EVENT_DATA.copy()
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


"""
Fixtures related to Eventbrite
"""


@pytest.fixture(scope="session")
def eventbrite():
    """
    This fixture returns Social network model object id for eventbrite in getTalent database
    """
    return {'id': SocialNetwork.get_by_name(EVENTBRITE.title()).id}


@pytest.fixture(scope="session")
def test_eventbrite_credentials(user_first, eventbrite):
    """
    Create eventbrite social network credentials for this user so
    we can create event on Eventbrite.com
    """
    return add_social_network_credentials(test_app, eventbrite, user_first)


@pytest.fixture(scope="session")
def test_eventbrite_credentials_same_domain(user_same_domain, eventbrite):
    """
    Create eventbrite social network credentials for this user so
    we can create event on Eventbrite.com
    """
    return add_social_network_credentials(test_app, eventbrite, user_same_domain)


@pytest.fixture(scope="session")
def eventbrite_venue(user_first, eventbrite, token_first):
    """
    This fixture returns eventbrite venue in getTalent database
    """
    return add_test_venue(token_first, user_first, eventbrite)


@pytest.fixture(scope="session")
def eventbrite_venue_same_domain(user_same_domain, eventbrite, token_same_domain):
    """
    This fixture returns eventbrite venue in getTalent database for user_same_domain
    """
    return add_test_venue(token_same_domain, user_same_domain, eventbrite)


@pytest.fixture(scope="session")
def organizer_in_db(user_first):
    """
    This fixture returns an organizer in getTalent database
    """
    social_network = SocialNetwork.get_by_name(EVENTBRITE.title())
    organizer = {
        "user_id": user_first['id'],
        "name": "Zohaib Ijaz 5555",
        "email": "testemail@gmail.com",
        "about": "He is a testing engineer",
        "social_network_id": social_network.id,
        "social_network_organizer_id": "11576432727"
    }

    organizer_obj = EventOrganizer(**organizer)
    db.session.add(organizer_obj)
    db.session.commit()
    organizer = dict(id=organizer_obj.id)

    return organizer


@pytest.fixture(scope="session")
def eventbrite_event(request, test_eventbrite_credentials, user_first, eventbrite, eventbrite_venue, token_first):
    """
    This method create a dictionary data to create event on eventbrite.
    It uses meetup SocialNetwork model object, venue for meetup
    and an organizer to create event data for
    """
    event = EVENT_DATA.copy()
    event['title'] = 'Eventbrite ' + event['title'] + fake.uuid4()
    event['social_network_id'] = eventbrite['id']
    event['venue_id'] = eventbrite_venue['id']
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

    def fin():
        try:
            from social_network_service.modules.event.eventbrite import Eventbrite as EventbriteEventBase
            from social_network_service.modules.social_network.eventbrite import Eventbrite as EventbriteSocialNetwork
            with test_app.app_context():
                # Delete events from vendor
                eventbrite_sn = EventbriteSocialNetwork(user_id=user_first['id'], social_network_id=eventbrite['id'])
                eventbrite_event_object = EventbriteEventBase(
                    headers=eventbrite_sn.headers, user_credentials=eventbrite_sn.user_credentials,
                    social_network=eventbrite_sn.user_credentials.social_network)
                events = eventbrite_event_object.get_events(status='draft,live')
                print 'Got %s events on Eventbrite website' % len(events)
                for vendor_event in events:
                    try:
                        eventbrite_event_object.unpublish_event(vendor_event['id'])
                    except Exception:
                        logger.exception('Unable to delete event from Eventbrite website')
        except Exception:
            logger.exception('Error occurred while deleting events from Eventbrite website')

    request.addfinalizer(fin)
    return _event


"""
Fixtures for different social-networks
"""


@pytest.fixture(scope="session", params=VENDORS)
def event_in_db(request):
    """
    This fixture creates an event on vendor basis and returns it.
    e.g. In case of Eventbrite, it will return fixture named as "eventbrite_event"
    """
    return deepcopy(request.getfuncargvalue("{}_event".format(request.param.lower())))


@pytest.fixture(scope="function", params=VENDORS)
def event_in_db_second(request):
    """
    This fixture creates an event on vendor basis and returns it.
    e.g. In case of Eventbrite, it will return fixture named as "eventbrite_event"
    """
    return deepcopy(request.getfuncargvalue("{}_event_second".format(request.param.lower())))


"""
Fixtures related to base-campaign
"""


@pytest.fixture()
def base_campaign(token_first):
    """
    Data is valid. Base campaign should be created.
    """
    data = CampaignsTestsHelpers.base_campaign_data()
    response = send_request('post', EmailCampaignApiUrl.BASE_CAMPAIGNS, token_first, data)
    assert response.status_code == codes.CREATED
    assert response.json()['id']
    return response.json()


@pytest.fixture()
def base_campaign_other(token_second):
    """
    Data is valid. Base campaign should be created.
    """
    data = CampaignsTestsHelpers.base_campaign_data()
    response = send_request('post', EmailCampaignApiUrl.BASE_CAMPAIGNS, token_second, data)
    assert response.status_code == codes.CREATED
    assert response.json()['id']
    return response.json()


@pytest.fixture()
def base_campaign_event(base_campaign, event_in_db, token_first):
    """
    This hits the API with valid event and base campaign and link both of them with each other.
    """
    response = send_request('post', EmailCampaignApiUrl.BASE_CAMPAIGN_EVENT % (base_campaign['id'],
                                                                               event_in_db['id']),
                            token_first)
    assert response.status_code == codes.CREATED, response.text
    assert response.json()['id']
    return response.json()


@pytest.fixture()
def base_campaign_event_second(base_campaign, event_in_db_second, token_first):
    """
    This hits the API with valid event and base campaign and link both of them with each other.
    """
    response = send_request('post', EmailCampaignApiUrl.BASE_CAMPAIGN_EVENT % (base_campaign['id'],
                                                                               event_in_db_second['id']),
                            token_first)
    assert response.status_code == codes.CREATED, response.text
    assert response.json()['id']
    return response.json()


@pytest.fixture()
def base_campaign_event_with_rsvp(base_campaign, candidate_first, event_in_db, token_first):
    """
    This links such an event with base-campaign. which has one RSVP associated with it.
    """
    response = send_request('post', EmailCampaignApiUrl.BASE_CAMPAIGN_EVENT % (base_campaign['id'],
                                                                               event_in_db['id']),
                            token_first)
    assert response.status_code == codes.CREATED, response.text
    assert response.json()['id']
    create_an_rsvp_in_database(candidate_first['id'], event_in_db['id'], token_first)
    return response.json()


@pytest.fixture()
def email_campaign_with_base_id(smartlist_first, base_campaign, token_first):
    """
    This creates an email-campaign with base_campaign_id. Currently when we create an email-campaign, it is
    also sent. So we assert on expected number of blasts and expected number of sends.
    """
    expected_blasts = 1
    expected_sends = 1
    email_campaign = create_email_campaign_with_base_id(smartlist_first['id'], base_campaign['id'], token_first)
    campaign_blast = CampaignsTestsHelpers.get_blasts_with_polling(email_campaign, token_first,
                                                                   EmailCampaignApiUrl.BLASTS % email_campaign['id'],
                                                                   count=expected_blasts)
    CampaignsTestsHelpers.assert_blast_sends(email_campaign, expected_sends,
                                             blast_url=EmailCampaignApiUrl.BLAST % (email_campaign['id'],
                                                                                    campaign_blast[0]['id']),
                                             access_token=token_first)
    return email_campaign


@pytest.fixture()
def email_campaign_same_domain(smartlist_same_domain, base_campaign, token_first):
    """
    This sends an email-campaign.
    """
    expected_blasts = 1
    expected_sends = 1
    email_campaign = create_email_campaign_with_base_id(smartlist_same_domain['id'], base_campaign['id'], token_first)
    campaign_blast = CampaignsTestsHelpers.get_blasts_with_polling(email_campaign, token_first,
                                                                   EmailCampaignApiUrl.BLASTS % email_campaign['id'],
                                                                   count=expected_blasts)
    CampaignsTestsHelpers.assert_blast_sends(email_campaign, expected_sends,
                                             blast_url=EmailCampaignApiUrl.BLAST % (email_campaign['id'],
                                                                                    campaign_blast[0]['id']),
                                             access_token=token_first)


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


@pytest.fixture(scope="function")
def eventbrite_venue_second(test_eventbrite_credentials, user_first, eventbrite, token_first):
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


@pytest.fixture(scope="function", params=VENDORS)
def event_in_db_second(request):
    """
    This fixture creates another event on vendor basis and returns it.
    e.g. In case of Eventbrite, it will return fixture named as "eventbrite_event_second"
    """
    return deepcopy(request.getfuncargvalue("{}_event_second".format(request.param.lower())))

