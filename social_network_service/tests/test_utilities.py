__author__ = 'zohaib'
from datetime import datetime, timedelta
from dateutil.parser import parse
from pytz import timezone

from social_network_service.utilities import camel_case_to_snake_case
from social_network_service.utilities import snake_case_to_camel_case
from social_network_service.utilities import camel_case_to_title_case
from social_network_service.utilities import convert_keys_to_snake_case
from social_network_service.utilities import convert_keys_to_camel_case
from social_network_service.utilities import get_utc_datetime


def test_camel_case_to_snake_case():
    """
    In this test, we will verify that camel_case_to_snake_case() method converts strings
    according to our requirements, i.e. converts from camel case to snake case
    :return:
    """
    # test one
    assert camel_case_to_snake_case('CamelCase') == 'camel_case'
    assert camel_case_to_snake_case('CamelCamelCase') == 'camel_camel_case'
    assert camel_case_to_snake_case('Camel2Camel2Case') == 'camel2_camel2_case'
    assert camel_case_to_snake_case('getHTTPResponseCode') == 'get_http_response_code'
    assert camel_case_to_snake_case('get2HTTPResponseCode') == 'get2_http_response_code'
    assert camel_case_to_snake_case('HTTPResponseCode') == 'http_response_code'
    assert camel_case_to_snake_case('HTTPResponseCodeXYZ') == 'http_response_code_xyz'


def test_snake_case_to_camel_case():
    """
    In this test, we will verify that snake_case_to_camel_case() method converts strings
    according to our requirements, i.e. converts from snake case to camel case
    :return:
    """
    # test one
    assert snake_case_to_camel_case('social_network_id') == 'socialNetworkId'
    assert snake_case_to_camel_case('start_date') == 'startDate'
    assert snake_case_to_camel_case('address_line1') == 'addressLine1'
    assert snake_case_to_camel_case('social_network_event_id') == 'socialNetworkEventId'
    assert snake_case_to_camel_case('event_id') == 'eventId'
    assert snake_case_to_camel_case('access_token') == 'accessToken'
    assert snake_case_to_camel_case('refresh__token') == 'refreshToken'
    assert snake_case_to_camel_case('_refresh_token') == 'RefreshToken'


def test_camel_case_to_title_case():
    """
    In this test, we will verify that camel_case_to_snake_case() method converts strings
    according to our requirements, i.e. converts from camel case to snake case
    :return:
    """
    # test one
    assert camel_case_to_title_case('CamelCase') == 'Camel Case'
    assert camel_case_to_title_case('CamelCamelCase') == 'Camel Camel Case'
    assert camel_case_to_title_case('Camel2Camel2Case') == 'Camel2 Camel2 Case'
    assert camel_case_to_title_case('getHTTPResponseCode') == 'Get Http Response Code'
    assert camel_case_to_title_case('get2HTTPResponseCode') == 'Get2 Http Response Code'
    assert camel_case_to_title_case('HTTPResponseCode') == 'Http Response Code'
    assert camel_case_to_title_case('HTTPResponseCodeXYZ') == 'Http Response Code Xyz'


def test_convert_keys_to_snake_case():
    """
    In this test, we will verify that convert_keys_to_snake_case() method converts dictionaries
    according to our requirements, i.e. converts from dictionary keys from
     camel case to snake case
    :return:
    """
    # test one
    camel_case_dict = dict(CamelCase='value1',
                           CamelCamelCase='value2',
                           Camel2Camel2Case='value3',
                           getHTTPResponseCode=123,
                           get2HTTPResponseCode='name')
    snake_case_dict = dict(camel_case='value1',
                           camel_camel_case='value2',
                           camel2_camel2_case='value3',
                           get_http_response_code=123,
                           get2_http_response_code='name')

    assert convert_keys_to_snake_case(camel_case_dict) == snake_case_dict


def test_convert_keys_to_camel_case():
    """
    In this test, we will verify that convert_keys_to_snake_case() method converts dictionaries
    according to our requirements, i.e. converts from dictionary keys from
     snake case to camel case
    :return:
    """
    snake_case_dict = dict(camel_case='value1',
                           camel_camel_case='value2',
                           camel2_camel2_case='value3',
                           get_http_response_code=123,
                           get2_http_response_code='name')

    camel_case_dict = dict(camelCase='value1',
                           camelCamelCase='value2',
                           camel2Camel2Case='value3',
                           getHttpResponseCode=123,
                           get2HttpResponseCode='name')

    assert convert_keys_to_camel_case(snake_case_dict) == camel_case_dict


def test_get_utc_datetime():
    """
    get_utc_datetime() returns utc datetime string
    This test is to test get_utc_datetime() function.
    We will pass different datetime objects and test different scenarios.
    :return:
    """
    now = datetime(2015, 10, 16, 12, 12, 12)
    assert get_utc_datetime(now, 'Asia/Karachi') == '2015-10-16T07:12:12Z', \
        'UTC date time should be 5 hours behind Asia/Karachi timezone datetime'

    now = datetime(2015, 10, 16, 11, 11, 11, tzinfo=timezone('Asia/Karachi'))
    print now
    assert get_utc_datetime(now, 'Asia/Karachi') == '2015-10-16T11:11:11Z', \
        'UTC date time should be 5 hours behind Asia/Karachi timezone datetime'
