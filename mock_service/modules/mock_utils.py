"""
Mock API class for handling mock responses by validating expected headers or expected payload
and on success or fail return different response.
"""

# Third Party
from requests import codes

# App specific
from mock_service.common.error_handling import InternalServerError


def _validate_payload(mocked_json, payload):
    """
    Validate expected payload with original request payload
    :param dict mocked_json: Already mocked hard coded json dict from where response data needs to be extracted
    :param dict payload: Original payload sent to mock api. If not None, then match validate it with mock_json
    expected payload
    """
    expected_payload = mocked_json.get('expected_payload')
    if not expected_payload:
        return None
    fields_to_ignore = expected_payload.get('ignore', [])
    is_matched = _match_dicts(expected_payload['payload'], payload, ignore=fields_to_ignore)
    try:
        return codes.OK if is_matched else expected_payload['on_fail']
    except KeyError:
        raise InternalServerError('Mocked JSON is not implemented for payload.')


def _validate_headers(mocked_json, headers):
    """
    Validate expected headers with original request headers
    :param dict mocked_json: Already mocked hard coded json dict from where response data needs to be extracted
    :param dict headers: Original headers sent to mock api. If not None, then match validate it with mock_json
    expected headers
    """
    expected_headers = mocked_json.get('expected_headers')
    if not expected_headers:
        return None
    auth_header = {'Authorization': headers.get('Authorization')}

    is_matched = _match_dicts(expected_headers['headers'], auth_header)
    try:
        return codes.OK if is_matched else expected_headers['on_fail']
    except KeyError:
        raise InternalServerError('Mocked JSON is not implemented for headers.')


def _match_dicts(original_data, expected_data=None, ignore=None):
    """
    Match all entries of expected dict with original dict
    :param dict|None expected_data: expected dict with key value pair
    :param dict original_data: original dict with key value pair
    :param list ignore: list of keys to ignore in original data when validating. Default will check all expected
    data with original data
    """
    if not ignore:
        ignore = []
    if expected_data:
        for k, v in expected_data.iteritems():
            if not v == original_data[k] and k not in ignore:
                return False
    return True


def get_mock_response(mocked_json, payload=None, headers=None):
    """
    Get mocked response of a request in dict
        - Check if expected and request headers is same. If not, then send on_fail response
        - Check if expected and request payload is same. If not, then send on_fail response
        - If everything's fine, then return OK response by default
    Called by mock api endpoint
    :param dict mocked_json: Already mocked hard coded json dict from where response data needs to be extracted
    :param dict|None payload: Original payload sent to mock api. If not None, then match validate it with mock_json
    expected payload
    :param dict|None headers: Original headers sent to mock api. If not None, then match validate it with mock_json
    expected headers
    """
    for response_code in [_validate_headers(mocked_json, headers), _validate_payload(mocked_json, payload)]:
        if response_code and not response_code == codes.OK:
            response = mocked_json[response_code]
            return response['response'], response_code

    response = mocked_json[codes.OK]
    return response.get('response', {}), response['status_code']

