"""
This module contains tests for functions in handy_functions.py module.
"""

from ..utils.handy_functions import snake_case_to_camel_case


def test_snake_case_to_camel_case():
    """
    In this test, we will verify that snake_case_to_camel_case() method converts strings
    according to our requirements, i.e. converts from snake case to camel case
    :return:
    """
    # test one
    assert snake_case_to_camel_case('social_network_id') == 'socialNetworkId'
    assert snake_case_to_camel_case('start_date') == 'startDate'
    assert snake_case_to_camel_case('address_line_1') == 'addressLine1'
    assert snake_case_to_camel_case('social_network_event_id') == 'socialNetworkEventId'
    assert snake_case_to_camel_case('event_id') == 'eventId'
    assert snake_case_to_camel_case('access_token') == 'accessToken'
    assert snake_case_to_camel_case('refresh__token') == 'refreshToken'
    assert snake_case_to_camel_case('_refresh_token') == 'RefreshToken'
