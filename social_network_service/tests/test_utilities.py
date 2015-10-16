__author__ = 'zohaib'
from social_network_service.utilities import camel_case_to_snake_case
from social_network_service.utilities import snake_case_to_camel_case
from social_network_service.utilities import camel_case_to_title_case
from social_network_service.utilities import convert_keys_to_snake_case
from social_network_service.utilities import convert_keys_to_camel_case


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
    assert camel_case_to_snake_case('CamelCase') == 'camel_case'
    assert camel_case_to_snake_case('CamelCamelCase') == 'camel_camel_case'
    assert camel_case_to_snake_case('Camel2Camel2Case') == 'camel2_camel2_case'
    assert camel_case_to_snake_case('getHTTPResponseCode') == 'get_http_response_code'
    assert camel_case_to_snake_case('get2HTTPResponseCode') == 'get2_http_response_code'
    assert camel_case_to_snake_case('HTTPResponseCode') == 'http_response_code'
    assert camel_case_to_snake_case('HTTPResponseCodeXYZ') == 'http_response_code_xyz'

