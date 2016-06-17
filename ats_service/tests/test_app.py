import requests

from auth_service.common.routes import ATSServiceApiUrl

def test_healthcheck():
    """
    """
    response = requests.get(ATSServiceApiUrl.HEALTH_CHECK)
    assert response.status_code == 200

    # Testing Health Check URL with trailing slash
    response = requests.get(ATSServiceApiUrl.HEALTH_CHECK + '/')
    print response
    assert response.status_code == 200
