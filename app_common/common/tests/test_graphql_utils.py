from ..utils.models_utils import init_talent_app
from ..utils.graphql_utils import get_fields, get_query
from ..models.venue import Venue

test_app, logger = init_talent_app('test_app')


def test_get_fields():
    """
    This test validates `get_fields()` function.
    """
    # Simple scenario
    fields = get_fields(Venue)
    expected_fields = ['id', 'social_network_id', 'social_network_venue_id', 'user_id', 'address_line_1',
                       'address_line_2', 'city', 'state', 'zip_code', 'country', 'longitude', 'latitude']
    assert fields == expected_fields

    # Get specific fields
    fields = get_fields(Venue, include=('address_line_1', 'city', 'country'))
    expected_fields = ['address_line_1', 'city', 'country']
    assert fields == expected_fields

    # Exclude specific fields and get all except those
    fields = get_fields(Venue, exclude=('address_line_2', 'zip_code', 'user_id'))
    expected_fields = ['id', 'social_network_id', 'social_network_venue_id', 'address_line_1',
                       'city', 'state', 'country', 'longitude', 'latitude']
    assert fields == expected_fields

    # Get specific fields plus a relationship and it's fields. events in this case
    fields = get_fields(Venue, include=('address_line_1', 'city', 'country'), relationships=('events',))
    expected_fields = ['address_line_1', 'city', 'country',
                       'events', ['social_network_event_id', 'social_network_id', 'user_id', 'organizer_id',
                                  'venue_id', 'social_network_group_id', 'group_url_name', 'start_datetime',
                                  'end_datetime', 'registration_instruction', 'max_attendees', 'tickets_id', 'id',
                                  'title', 'description', 'url', 'cost', 'currency', 'timezone']
                       ]
    assert fields == expected_fields


def test_get_query():
    query = get_query('events', ['title', 'cost', 'start_datetime'])
    expected_query = {
        'query': '{ events  { title cost start_datetime } }'
    }
    assert query == expected_query

    query = get_query('events', ['title', 'cost', 'start_datetime'], return_str=True)
    expected_query = '{ events  { title cost start_datetime } }'
    assert query == expected_query

    query = get_query('event', ['title', 'cost', 'start_datetime'], args=dict(id=123))
    expected_query = {
        'query': '{ event ( id : 123 ) { title cost start_datetime } }'
    }
    assert query == expected_query

    query = get_query('events', ['title', 'cost', 'start_datetime'], args=dict(page=1, per_page=10))
    expected_query = {
        'query': '{ events ( per_page : 10, page : 1 ) { title cost start_datetime } }'
    }
    assert query == expected_query
