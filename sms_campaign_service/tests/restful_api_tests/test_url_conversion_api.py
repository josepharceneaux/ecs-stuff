# Third Party Imports
import requests

# Application Specific
from sms_campaign_service import flask_app as app

API_URL = app.config['APP_URL']


def test_get_with_invalid_token():
    response = requests.get(API_URL + '/url_conversion',
                            headers=dict(Authorization='Bearer %s' % 'invalid_token'))
    assert response.status_code == 401, 'It should be unauthorized (401)'
    assert 'short_url' not in response.json()


def test_get_with_valid_token_and_no_data(auth_token):
    response = requests.get(API_URL + '/url_conversion',
                            headers=dict(Authorization='Bearer %s' % auth_token))
    assert response.status_code == 400, 'Status should be Bad request (400)'


def test_get_with_valid_token_and_valid_data(auth_token):
    response = requests.get(API_URL + '/url_conversion',
                            headers=dict(Authorization='Bearer %s' % auth_token),
                            data={"long_url": 'https://webdev.gettalent.com/web/default/angular#!/'}
                            )
    assert response.status_code == 200, 'Status should be Bad request (400)'
    assert 'short_url' in response.json()


def test_get_with_valid_token_and_invalid_data(auth_token):
    response = requests.get(API_URL + '/url_conversion',
                            headers=dict(Authorization='Bearer %s' % auth_token),
                            data={"long_url": API_URL}
                            )
    assert response.status_code == 500, 'Status should be (500)'
    assert response.json()['error']['code'] == 5004  # custom exception for Google API Error


def test_for_post_request(auth_token):
    response = requests.post(API_URL + '/url_conversion',
                             headers=dict(Authorization='Bearer %s' % auth_token))
    assert response.status_code == 405, 'POST method should not be allowed (405)'


def test_for_delete_request(auth_token):
    response = requests.delete(API_URL + '/url_conversion',
                               headers=dict(Authorization='Bearer %s' % auth_token))
    assert response.status_code == 405, 'DELETE method should not be allowed (405)'
