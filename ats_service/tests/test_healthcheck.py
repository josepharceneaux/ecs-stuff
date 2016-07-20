import requests

from ats_service.common.routes import ATSServiceApiUrl

def test_healthcheck():
    """
    Test basic healthcheck request.
    """
    response = requests.get(ATSServiceApiUrl.HEALTH_CHECK)
    assert response.status_code == requests.codes.OK

    # Testing Health Check URL with trailing slash
    response = requests.get(ATSServiceApiUrl.HEALTH_CHECK + '/')
    assert response.status_code == requests.codes.OK
