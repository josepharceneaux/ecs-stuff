
"""
test_utilities.py: helper methods for testing social network service endpoints
"""
__author__ = 'zohaib'

# Standard Library
from datetime import datetime
import json
import requests

# Third Party
import requests
from pytz import timezone
from dateutil.parser import parse

# Application Specific
from social_network_service.common.routes import SocialNetworkApiUrl
from social_network_service.modules.utilities import unix_time
from social_network_service.modules.utilities import snake_case_to_camel_case
from social_network_service.modules.utilities import camel_case_to_title_case
from social_network_service.modules.utilities import camel_case_to_snake_case
from social_network_service.modules.utilities import convert_keys_to_snake_case
from social_network_service.modules.utilities import convert_keys_to_camel_case
from social_network_service.modules.utilities import get_utc_datetime
from social_network_service.modules.utilities import import_from_dist_packages
from social_network_service.modules.utilities import milliseconds_since_epoch
from social_network_service.modules.utilities import milliseconds_since_epoch_to_dt
from social_network_service.tests.helper_functions import get_headers

TEST_DATE = datetime(2015, 1, 1)
UTC_TIMEZONE = timezone('UTC')
LOCAL_TIMEZONE = timezone('Asia/Karachi')
UTC_TEST_DATE = UTC_TIMEZONE.localize(TEST_DATE, is_dst=None)
LOCAL_TEST_DATE = LOCAL_TIMEZONE.localize(TEST_DATE, is_dst=None)
EPOCH_UTC_TEST_DATE_IN_SECONDS = 1420070400
EPOCH_UTC_TEST_DATE_IN_MILLISECONDS = 1420070400000
EPOCH_LOCAL_TEST_DATE_IN_MILLISECONDS = 1420052400000


def test_camel_case_to_snake_case():
    """
    In this test, we will verify that camel_case_to_snake_case() method converts strings
    according to our requirements, i.e. converts from camel case to snake case
    :return:
    """
    # test one
    assert camel_case_to_snake_case('CamelCase') == 'camel_case'
    assert camel_case_to_snake_case('CamelCamelCase') == 'camel_camel_case'
    assert camel_case_to_snake_case('Camel2Camel2Case') == 'camel_2_camel_2_case'
    assert camel_case_to_snake_case('getHTTPResponseCode') == 'get_http_response_code'
    assert camel_case_to_snake_case('get2HTTPResponseCode') == 'get_2_http_response_code'
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
    assert snake_case_to_camel_case('address_line_1') == 'addressLine1'
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
    assert camel_case_to_title_case('Camel2Camel2Case') == 'Camel 2 Camel 2 Case'
    assert camel_case_to_title_case('getHTTPResponseCode') == 'Get Http Response Code'
    assert camel_case_to_title_case('get2HTTPResponseCode') == 'Get 2 Http Response Code'
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
                           camel_2_camel_2_case='value3',
                           get_http_response_code=123,
                           get_2_http_response_code='name')

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

    # now = datetime(2015, 10, 16, 11, 11, 11, tzinfo=timezone('Asia/Karachi'))
    now = parse('2015-10-16T11:11:11Z')
    print now
    assert get_utc_datetime(now, 'Asia/Karachi') == '2015-10-16T11:11:11Z', \
        'UTC date time should be 5 hours behind Asia/Karachi timezone datetime'


def test_import_from_dist_packages():
    """
    - In this test, we will verify the working of
        import_from_dist_packages() function defined in
        social_network_service/utilities.py
    - We import facebook using test_import_from_dist_packages()
        and we should get facebook-sdk module from site-packages.
    """
    facebook_sdk_package = import_from_dist_packages('facebook')
    assert hasattr(facebook_sdk_package, 'GraphAPI')
    assert hasattr(facebook_sdk_package, 'GraphAPIError')
    assert hasattr(facebook_sdk_package, 'base64')
    assert hasattr(facebook_sdk_package, 'cgi')


def test_unix_time():
    """
    - In this test, we will verify the working of
        unix_time() function defined in social_network_service/utilities.py
    - We give a test date and assert its output to expected value
    """
    # case 1 - date is datetime.datetime object
    assert int(unix_time(UTC_TEST_DATE)) == EPOCH_UTC_TEST_DATE_IN_SECONDS
    # case 2 - date in string format
    try:
        unix_time(str(UTC_TEST_DATE))
    except TypeError as e:
        assert e.message.find('unsupported operand type') == 0
        assert 'str' in e.message


def test_milliseconds_since_epoch():
    """
    - In this test, we will verify the working of
        milliseconds_since_epoch() function defined in
        social_network_service/utilities.py
    - We give a test date and assert its output to expected value
    """
    # case 1 - date is datetime.datetime object
    assert int(milliseconds_since_epoch(UTC_TEST_DATE)) == EPOCH_UTC_TEST_DATE_IN_MILLISECONDS
    # case 2 - date in string format
    test_date_str = '2015-1-1'
    try:
        unix_time(test_date_str)
    except TypeError as e:
        assert e.message.find('unsupported operand type') == 0
        assert 'str' in e.message


def test_milliseconds_since_epoch_to_dt():
    """
    - In this test, we will verify the working of
        milliseconds_since_epoch_to_dt() function defined in
        social_network_service/utilities.py
    - We give an epoch and assert its output to expected date time object
    """
    # case 1 - we give epoch seconds in UTC, when it is converted in datetime
    # object, it should be same as UTC_TEST_DATE.
    converted_date_1 = milliseconds_since_epoch_to_dt(EPOCH_UTC_TEST_DATE_IN_MILLISECONDS)
    assert converted_date_1 == UTC_TEST_DATE
    # case 2 - we give epoch seconds using local time, and provide over local timezone info,
    # it should be same as date object given in LOCAL_TEST_DATE.
    converted_date_2 = milliseconds_since_epoch_to_dt(
        EPOCH_LOCAL_TEST_DATE_IN_MILLISECONDS, tz=LOCAL_TIMEZONE)
    assert converted_date_2 == LOCAL_TEST_DATE


def test_health_check():
    response = requests.get(SocialNetworkApiUrl.HEALTH_CHECK)
    assert response.status_code == 200


# TODO: Move these methods

def send_request(method, url, access_token, data=None, is_json=True):
    # This method is being used for test cases, so it is sure that method has
    #  a valid value like 'get', 'post' etc.
    request_method = getattr(requests, method)
    headers = dict(Authorization='Bearer %s' % access_token)
    if is_json:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data)
    return request_method(url, data=data, headers=headers)


def send_post_request(url, data, access_token):
    """
    This method sends a post request to a URL with given data using access_token for authorization in header
    :param url: URL where post data needs to be sent
    :param data: Data which needs to be sent
    :param access_token: User access_token for authorization
    :return:
    """
    return requests.post(url, data=json.dumps(data),
                         headers=get_headers(access_token))
