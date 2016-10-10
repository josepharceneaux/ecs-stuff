"""
This module contains tests for graphql_utils functions. Tests validate that these functions are working fine
and are not broken by any change in this code or any other code.
"""
# importing test_app to use models
from .app import test_app
from ..models.venue import Venue
from ..utils.graphql_utils import get_query, validate_graphql_response


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


def test_validate_graphql_response():
    fields = Venue.get_fields()
    response = {
        "venue": {
            "id": 1,
            "social_network_id": 26,
            "social_network_venue_id": "16733267",
            "user_id": 266,
            "address_line_1": "New Muslim Town",
            "address_line_2": "163 A Block",
            "city": "Lahore",
            "state": None,
            "zip_code": "54000",
            "country": "Pakistan",
            "longitude": 74.3133,
            "latitude": 31.5105
        }
    }

    # this should validate this data for given fields
    validate_graphql_response('venue', response, fields, is_array=False)

    # validate ridiculously nested objects
    response = {
        "me": {
          "id": 266,
          "domain_id": 1,
          "events": [
            {
              "id": 1,
              "title": "Test Event",
              "venue": {
                "id": 1,
                "address_line_1": "New Muslim Town",
                "events": [
                  {
                    "id": 1
                  }
                ]
              }
            }
          ]
        }
    }
    fields = ['id', 'domain_id', 'events', ['id', 'title', 'venue', ['id', 'address_line_1', 'events', ['id']]]]
    validate_graphql_response('me', response, fields)

