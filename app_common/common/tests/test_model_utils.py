"""
This module contains tests for model_utils functions. Tests validate that these functions are working fine
and are not broken by any change in this code or any other code.
"""
# importing test_app to use models
from .app import test_app
from ..models.venue import Venue


def test_get_fields():
    """
    This test validates `get_fields()` function.
    """
    # Simple scenario
    fields = Venue.get_fields()
    expected_fields = ['id', 'social_network_id', 'social_network_venue_id', 'user_id', 'address_line_1',
                       'address_line_2', 'city', 'state', 'zip_code', 'added_datetime', 'updated_datetime', 'country',
                       'longitude', 'latitude']
    assert fields == expected_fields

    # Get specific fields
    fields = Venue.get_fields(include=('address_line_1', 'city', 'country'))
    expected_fields = ['address_line_1', 'city', 'country']
    assert fields == expected_fields

    # Exclude specific fields and get all except those
    fields = Venue.get_fields(exclude=('address_line_2', 'zip_code', 'user_id', 'added_datetime', 'updated_datetime'))
    expected_fields = ['id', 'social_network_id', 'social_network_venue_id', 'address_line_1',
                       'city', 'state', 'country', 'longitude', 'latitude']
    assert fields == expected_fields

    # Get specific fields plus a relationship and it's fields. events in this case
    fields = Venue.get_fields(include=('address_line_1', 'city', 'country'), relationships=('events',))
    expected_fields = ['address_line_1', 'city', 'country', 'events', ['social_network_event_id', 'social_network_id',
                                                                       'user_id', 'organizer_id', 'venue_id',
                                                                       'social_network_group_id', 'group_url_name',
                                                                       'start_datetime', 'end_datetime',
                                                                       'registration_instruction', 'max_attendees',
                                                                       'tickets_id', 'is_hidden', 'added_datetime',
                                                                       'updated_datetime', 'id', 'title', 'description',
                                                                       'url', 'cost', 'currency', 'timezone']]
    assert fields == expected_fields
