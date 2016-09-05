# Third Party
from requests import codes

# App specific
from mock_service.common.error_handling import InternalServerError


class MockApi(object):
    """
    MockAPI class for validating headers, payload and returning expected response
    """
    def __init__(self, mocked_json, payload=None, headers=None):
        self.payload = payload
        self.headers = headers
        self.mocked_json = mocked_json

    def _match_dicts(self, expected_data, original_data, ignore=[]):
        """
        Match all entries of expected dict with original dict
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
        if expected_headers:
            fields_to_ignore = expected_headers.get('ignore', [])
            is_matched = self._match_dicts(expected_headers['headers'], self.headers, ignore=fields_to_ignore)
            try:
                if is_matched:
                    return codes.OK
                return expected_headers['on_fail']
            except KeyError:
                raise InternalServerError('Mocked JSON is not implemented for headers.')
        return None

    def _validate_payload(self):
        """
        Validate expected payload with original request payload
        """
        expected_payload = self.mocked_json.get('expected_payload')
        if expected_payload:
            fields_to_ignore = expected_payload.get('ignore', [])
            is_matched = self._match_dicts(expected_payload['payload'], self.payload, ignore=fields_to_ignore)
            try:
                if is_matched:
                    return codes.OK
                return expected_payload['on_fail']
            except KeyError:
                raise InternalServerError('Mocked JSON is not implemented for payload.')
        return None

    def get_response(self):
        """
        - Check if expected and request headers is same. If not, then send on_fail response
        - Check if expected and request payload is same. If not, then send on_fail response
        - If everything's fine, then return OK response by default
        :return: Returns response based on mocked_json validation
        :rtype: dict
        """
        response_code = self._validate_headers()
        if response_code and not response_code == codes.OK:
            response = self.mocked_json[response_code]
            return response['response'], response_code

        response_code = self._validate_payload()
        if response_code and not response_code == codes.OK:
            response = self.mocked_json[response_code]
            return response['response'], response_code

        response = self.mocked_json[codes.OK]
        return response.get('response', {}), response['status_code']
