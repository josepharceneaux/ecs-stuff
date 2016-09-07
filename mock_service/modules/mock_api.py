"""
Mock API class for handling mock responses by validating expected headers or expected payload
and on success or fail return different response.
"""

# Third Party
from requests import codes

# App specific
from mock_service.common.error_handling import InternalServerError


class MockApi(object):
    """
    MockAPI class for validating headers, payload and returning expected response
    """
    def __init__(self, mocked_json, payload=None, headers=None):
        """
        This class handles mock response by validating expected headers or expected payload and on success/fail
        return different response.
        :param dict mocked_json: Already mocked hard coded json dict from where response data needs to be extracted
        :param dict payload: Original payload sent to mock api. If not None, then match validate it with mock_json
        expected payload
        :param dict headers: Original headers sent to mock api. If not None, then match validate it with mock_json
        expected headers
        """
        self.payload = payload
        self.headers = headers
        self.mocked_json = mocked_json

    def _match_dicts(self, expected_data, original_data, ignore=[]):
        """
        Match all entries of expected dict with original dict
        :param dict expected_data: expected dict with key value pair
        :param dict original_data: original dict with key value pair
        :param list ignore: list of keys to ignore in original data when validating. Default will check all expected
        data with original data
        """
        if expected_data:
            for k, v in expected_data.iteritems():
                if not v == original_data[k] and k not in ignore:
                    return False
        return True

    def _validate_headers(self):
        """
        Validate expected headers with original request headers
        """
        expected_headers = self.mocked_json.get('expected_headers')
        if not expected_headers:
            return None
        fields_to_ignore = expected_headers.get('ignore', [])
        is_matched = self._match_dicts(expected_headers['headers'], self.headers, ignore=fields_to_ignore)
        try:
            return codes.OK if is_matched else expected_headers['on_fail']
        except KeyError:
            raise InternalServerError('Mocked JSON is not implemented for headers.')

    def _validate_payload(self):
        """
        Validate expected payload with original request payload
        """
        expected_payload = self.mocked_json.get('expected_payload')
        if not expected_payload:
            return None
        fields_to_ignore = expected_payload.get('ignore', [])
        is_matched = self._match_dicts(expected_payload['payload'], self.payload, ignore=fields_to_ignore)
        try:
            return codes.OK if is_matched else expected_payload['on_fail']
        except KeyError:
            raise InternalServerError('Mocked JSON is not implemented for payload.')

    def get_response(self):
        """ Get mocked response of a request in dict
        - Check if expected and request headers is same. If not, then send on_fail response
        - Check if expected and request payload is same. If not, then send on_fail response
        - If everything's fine, then return OK response by default
        :return: Returns response based on mocked_json validation
        :rtype: tuple
        """

        for _validate_method in [self._validate_headers, self._validate_payload]:
            response_code = _validate_method()
            if response_code and not response_code == codes.OK:
                response = self.mocked_json[response_code]
                return response['response'], response_code

        response = self.mocked_json[codes.OK]
        return response.get('response', {}), response['status_code']
