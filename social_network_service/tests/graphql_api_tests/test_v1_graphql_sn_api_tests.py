"""
This file contain tests for events api
"""
# App specific imports
from social_network_service.common.models.event import Event
from social_network_service.common.models.db import db
from social_network_service.common.models.event_organizer import EventOrganizer
from social_network_service.common.models.user import User
from social_network_service.common.models.venue import Venue
from social_network_service.common.models.candidate import SocialNetwork
from social_network_service.common.utils.graphql_utils import (get_query, validate_graphql_response, get_fields)
from social_network_service.tests.helper_functions import get_graphql_data


def test_get_me(token_first):
    fields = get_fields(User)
    query = get_query('me', fields)
    response = get_graphql_data(query, token_first)
    assert 'errors' not in response, 'Response: %s\nQuery: %s' % (response, query)
    validate_graphql_response('me', response, fields)


def test_get_event(token_first, eventbrite_event):
    assert_valid_response('event', Event, token_first, eventbrite_event['id'])


def test_get_events_pagination(token_first, eventbrite_event, meetup_event):
    assert_valid_response('event', Event, token_first, eventbrite_event['id'])
    fields = get_fields(Event)
    query = get_query('events', fields, args=dict(page=1, perPage=10))
    response = get_graphql_data(query, token_first)
    assert 'errors' not in response, 'Response: %s\nQuery: %s' % (response, query)
    validate_graphql_response('events', response, fields, is_array=True)

    # Since there were only two events created, now getting events for second page will return no events
    query = get_query('events', fields, args=dict(page=2, perPage=10))
    response = get_graphql_data(query, token_first)
    assert 'errors' not in response, 'Response: %s\nQuery: %s' % (response, query)
    assert response['data']['events'] == []


def test_get_event_relationship_objects(token_first):
    fields = get_fields(Event, relationships=('eventOrganizer',))
    query = get_query('events', fields)
    response = get_graphql_data(query, token_first)
    assert 'errors' not in response, 'Response: %s\nQuery: %s' % (response, query)
    validate_graphql_response('events', response, fields, is_array=True)


def test_get_venue(token_first, eventbrite_venue):
    assert_valid_response('venue', Venue, token_first, eventbrite_venue['id'])


def test_get_organizer(token_first, organizer_in_db):
    assert_valid_response('organizer', EventOrganizer, token_first, organizer_in_db['id'])


def test_get_social_network(token_first, eventbrite):
    assert_valid_response('socialNetwork', SocialNetwork, token_first, eventbrite['id'], ignore_id_test=True)
    fields = get_fields(SocialNetwork)
    query = get_query('socialNetwork', fields, args=dict(name='Eventbrite'))
    response = get_graphql_data(query, token_first)
    assert 'errors' not in response, 'Response: %s\nQuery: %s' % (response, query)
    validate_graphql_response('socialNetwork', response, fields)


def test_get_subscribed_social_network(token_first):
    assert_valid_response('subscribedSocialNetwork', SocialNetwork, token_first, None, ignore_id_test=True)


def test_get_meetup_groups(token_first):
    fields = ['id', 'name', 'urlname']
    query = get_query('meetupGroups', fields)
    response = get_graphql_data(query, token_first)
    assert 'errors' not in response, 'Response: %s\nQuery: %s' % (response, query)
    validate_graphql_response('meetupGroups', response, fields, is_array=True)


def test_get_timezones(token_first):
    fields = ['name', 'value']
    query = get_query('timezones', fields)
    response = get_graphql_data(query, token_first)
    assert 'errors' not in response, 'Response: %s\nQuery: %s' % (response, query)
    validate_graphql_response('timezones', response, fields, is_array=True)


def test_get_sn_token_status(token_first, eventbrite):
    fields = ['status']
    query = get_query('snTokenStatus', fields, args=dict(id=eventbrite['id']))
    response = get_graphql_data(query, token_first)
    assert 'errors' not in response, 'Response: %s\nQuery: %s' % (response, query)
    validate_graphql_response('snTokenStatus', response, fields, is_array=True)


def assert_valid_response(key, model, token, obj_id, ignore_id_test=False):
    fields = get_fields(model)
    query = get_query(key + 's', fields)
    response = get_graphql_data(query, token)
    assert 'errors' not in response, 'Response: %s\nQuery: %s' % (response, query)
    validate_graphql_response(key + 's', response, fields, is_array=True)
    if not ignore_id_test:
        query = get_query(key, fields, args=dict(id=obj_id))
        response = get_graphql_data(query, token)
        assert 'errors' not in response, 'Response: %s\nQuery: %s' % (response, query)
        validate_graphql_response(key, response, fields)


