"""
This module consists pyTests for SMS Campaign API.
"""

# Third Party Imports
import requests

# Application Specific
from sms_campaign_service import flask_app as app

APP_URL = app.config['APP_URL']
SMS_CAMPAIGN_API_URL = APP_URL + '/campaigns/'


class TestSmsCampaign:

    def test_get_with_invalid_token(self):
        response = requests.get(SMS_CAMPAIGN_API_URL,
                                headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_get_with_valid_token_and_no_user_phone(self, auth_token):
        response = requests.get(SMS_CAMPAIGN_API_URL,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 200, 'Status should be Ok (200)'
        assert 'count' in response.json()
        assert 'campaigns' in response.json()
        assert response.json()['count'] == 0
        assert response.json()['campaigns'] == []

    def test_get_with_valid_token_and_one_user_phone(self, auth_token, user_phone):
        response = requests.get(SMS_CAMPAIGN_API_URL,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 200, 'Status should be Ok (200)'
        assert 'count' in response.json()
        assert 'campaigns' in response.json()
        assert response.json()['count'] == 0
        assert response.json()['campaigns'] == []
