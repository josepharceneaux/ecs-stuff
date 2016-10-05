from ..utils.models_utils import init_talent_app
from ..utils.graphql_utils import get_fields, get_query, validate_graphql_response
from ..models.venue import Venue

test_app, logger = init_talent_app('test_app')


def test_get_fields():
    """
    This test validates `get_fields()` function.
    """
    # Simple scenario
    fields = get_fields(Venue)
    expected_fields = ['id', 'socialNetworkId', 'socialNetworkVenueId', 'userId', 'addressLine1', 'addressLine2',
                       'city', 'state', 'zipCode', 'country', 'longitude', 'latitude']
    assert fields == expected_fields

    # Get specific fields
    fields = get_fields(Venue, include=('addressLine1', 'city', 'country'))
    expected_fields = ['addressLine1', 'city', 'country']
    assert fields == expected_fields

    # Exclude specific fields and get all except those
    fields = get_fields(Venue, exclude=('addressLine2', 'zipCode', 'userId'))
    expected_fields = ['id', 'socialNetworkId', 'socialNetworkVenueId', 'addressLine1',
                       'city', 'state', 'country', 'longitude', 'latitude']
    assert fields == expected_fields

    # Get specific fields plus a relationship and it's fields. events in this case
    fields = get_fields(Venue, include=('addressLine1', 'city', 'country'), relationships=('events',))
    expected_fields = ['addressLine1', 'city', 'country',
                       'events', ['socialNetworkEventId', 'socialNetworkId', 'userId', 'organizerId',
                                  'venueId', 'socialNetworkGroupId', 'groupUrlName', 'startDatetime', 'endDatetime',
                                  'registrationInstruction', 'maxAttendees', 'ticketsId', 'id', 'title', 'description',
                                  'url', 'cost', 'currency', 'timezone']
                       ]
    assert fields == expected_fields


def test_get_query():
    query = get_query('events', ['title', 'cost', 'startDatetime'])
    expected_query = {
        'query': '{ events  { title cost startDatetime } }'
    }
    assert query == expected_query

    query = get_query('events', ['title', 'cost', 'startDatetime'], return_str=True)
    expected_query = '{ events  { title cost startDatetime } }'
    assert query == expected_query

    query = get_query('event', ['title', 'cost', 'startDatetime'], args=dict(id=123))
    expected_query = {
        'query': '{ event ( id : 123 ) { title cost startDatetime } }'
    }
    assert query == expected_query

    query = get_query('events', ['title', 'cost', 'startDatetime'], args=dict(page=1, perPage=10))
    expected_query = {
        'query': '{ events ( perPage : 10, page : 1 ) { title cost startDatetime } }'
    }
    assert query == expected_query
