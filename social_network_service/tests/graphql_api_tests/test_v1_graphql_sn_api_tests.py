"""
This file contain tests for Social network service Graphql endpoint. It's a single endpoint that
wil return different data base on given query.
"""
# App specific imports
from social_network_service.common.models.user import User
from social_network_service.common.models.venue import Venue
from social_network_service.common.models.event import Event
from social_network_service.common.models.candidate import SocialNetwork
from social_network_service.common.models.event_organizer import EventOrganizer
from social_network_service.tests.helper_functions import get_graphql_data, assert_valid_response, match_data
from social_network_service.common.utils.graphql_utils import (get_query, validate_graphql_response)


def test_get_me(token_first, user_first):
    """
    In this test we are validating that graphql endpoint returns logged-in user's data.
    """
    fields = User.get_fields()
    query = get_query('me', fields)
    response = get_graphql_data(query, token_first)
    assert 'errors' not in response, 'Response: %s\nQuery: %s' % (response, query)
    validate_graphql_response('me', response['data'], fields)
    me = response['data']['me']
    assert me['id'] == user_first['id']
    assert me['email'] == user_first['email']


def test_get_event(token_first, eventbrite_event):
    """
    Validate that Graphql endpoint is working fine for `event` and `events` queries.
    Also match data for single event.
    """
    response = assert_valid_response('event', Event, token_first, eventbrite_event['id'])
    event = response['data']['event']
    match_data(event, eventbrite_event, Event.get_fields(exclude=('organizer_id', 'url')))


def test_get_events_pagination(token_first, eventbrite_event, meetup_event):
    """
    Validate that pagination is working fine. There are two events created by test user.
    We will get 2 events in first page and then no events in second page (request)
    """
    assert_valid_response('event', Event, token_first, eventbrite_event['id'])
    fields = Event.get_fields()
    query = get_query('events', fields, args=dict(page=1, per_page=10))
    response = get_graphql_data(query, token_first)
    assert 'errors' not in response, 'Response: %s\nQuery: %s' % (response, query)
    validate_graphql_response('events', response['data'], fields, is_array=True)

    # Since there were only two events created, now getting events for second page will return no events
    query = get_query('events', fields, args=dict(page=2, per_page=10))
    response = get_graphql_data(query, token_first)
    assert 'errors' not in response, 'Response: %s\nQuery: %s' % (response, query)
    assert response['data']['events'] == []


def test_get_event_relationship_objects(token_first, eventbrite_event, organizer_in_db):
    """
    This test validates that by adding model relationships and their fields will work and Graphql will return those
    relationships data as well. e.g. in this case, we are getting event_organizer data inside events data
    """
    fields = Event.get_fields(relationships=('event_organizer',))
    query = get_query('events', fields)
    response = get_graphql_data(query, token_first)
    assert 'errors' not in response, 'Response: %s\nQuery: %s' % (response, query)
    validate_graphql_response('events', response['data'], fields, is_array=True)


def test_get_venue(token_first, eventbrite_venue):
    """
    Get a list of venues and a single venue by id. Match response data from expected data.
    """
    response = assert_valid_response('venue', Venue, token_first, eventbrite_venue['id'])
    venue = response['data']['venue']
    assert venue['id'] == eventbrite_venue['id']


def test_get_organizer(token_first, organizer_in_db):
    """
    This test validates that `organizer` and `organizers` queries are working fine. it also matches requested
     organizer's id with returned data.
    """
    response = assert_valid_response('organizer', EventOrganizer, token_first, organizer_in_db['id'])
    assert response['data']['organizer']['id'] == organizer_in_db['id']


def test_get_social_network(token_first, eventbrite):
    """
    This test validates that `social_network` and `social_networks` queries are working fine. it also matches
     eventbrite id with returned data.
    """
    assert_valid_response('social_network', SocialNetwork, token_first, eventbrite['id'], ignore_id_test=True)
    fields = SocialNetwork.get_fields()
    query = get_query('social_network', fields, args=dict(name='Eventbrite'))
    response = get_graphql_data(query, token_first)
    assert 'errors' not in response, 'Response: %s\nQuery: %s' % (response, query)
    validate_graphql_response('social_network', response['data'], fields)
    assert response['data']['social_network']['id'] == eventbrite['id']


def test_get_subscribed_social_network(token_first):
    """
    This test validates that `subscribedSocialNetwork` query is returning a list of subscribed social networks.
    """
    assert_valid_response('subscribed_social_network', SocialNetwork, token_first, None, ignore_id_test=True)


def test_get_meetup_groups(token_first):
    """
    This test validates that `meetup_groups` query is returning a list of user's groups on meetup.
    """
    fields = ['id', 'name', 'urlname']
    query = get_query('meetup_groups', fields)
    response = get_graphql_data(query, token_first)
    assert 'errors' not in response, 'Response: %s\nQuery: %s' % (response, query)
    validate_graphql_response('meetup_groups', response['data'], fields, is_array=True)


def test_get_timezones(token_first):
    """
    Validate that `timezone` query will return a list of timezones containing `name` and `value` fields.
    """
    fields = ['name', 'value']
    query = get_query('timezones', fields)
    response = get_graphql_data(query, token_first)
    assert 'errors' not in response, 'Response: %s\nQuery: %s' % (response, query)
    validate_graphql_response('timezones', response['data'], fields, is_array=True)


def test_get_sn_token_status(token_first, eventbrite):
    """
    Validate that Graphql endpoint will return token status for given social network id for `sn_token_status` query.
    In this case, Eventbrite is the social_network and token status should be True.
    """
    fields = ['status']
    query = get_query('sn_token_status', fields, args=dict(id=eventbrite['id']))
    response = get_graphql_data(query, token_first)
    assert 'errors' not in response, 'Response: %s\nQuery: %s' % (response, query)
    validate_graphql_response('sn_token_status', response['data'], fields)
    assert response['data']['sn_token_status']['status'] is True

