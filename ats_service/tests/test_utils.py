"""
Utilities for ATS tests.
"""


from requests import codes
from contracts import contract

from ats_service.common.error_handling import MissingRequiredField
from ats_service.common.utils.test_utils import send_request
from ats_service.common.routes import ATSServiceApi, ATSServiceApiUrl


def missing_field_test(data, key, token):
    """
    This function sends a POST request to the ATS account api with data which has one required field
    missing and checks that it MissingRequiredField 400
    :param dict data: ATS data
    :param string key: field key
    :param string token: auth token
    """
    del data[key]
    response = send_request('post', ATSServiceApiUrl.ACCOUNT, token, data)
    assert response.status_code == codes.BAD_REQUEST
    response = response.json()
    error = response['error']
    assert error['code'] == MissingRequiredField
    assert error['missing_fields'] == [key]
    assert True
