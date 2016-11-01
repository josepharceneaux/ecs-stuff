"""
Here we have tests for API /v1/base-campaigns
"""
import json
import requests
from requests import codes

from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers

__author__ = 'basit'


class TestCreateBaseCampaigns(object):
    """
    Here are the tests of /v1/base-campaigns
    """
    URL = EmailCampaignApiUrl.BASE_CAMPAIGNS

    def test_with_invalid_token(self):
        """
         User auth token is invalid. It should get Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token('post', self.URL)

    def test_with_valid_data(self, headers):
        """
        Data is valid. Base campaign should be created
        """
        data = CampaignsTestsHelpers.base_campaign_data()
        response = requests.post(self.URL, headers=headers, data=json.dumps(data))
        assert response.status_code == codes.CREATED
        assert response.json()['id']

    def test_with_missing_required_fields(self, headers):
        """
        Data does not contain some required fields. It should result in bad request error.
        """
        for key in ('name', 'description'):
            data = CampaignsTestsHelpers.base_campaign_data()
            del data[key]
            response = requests.post(self.URL, headers=headers, data=json.dumps(data))
            assert response.status_code == codes.BAD

    def test_with_empty_required_fields(self, headers):
        """
        Data does not contain valid values for some required fields. It should result in bad request error.
        """
        for key in ('name', 'description'):
            data = CampaignsTestsHelpers.base_campaign_data()
            data[key] = ''
            response = requests.post(self.URL, headers=headers, data=json.dumps(data))
            assert response.status_code == codes.BAD

    def test_with_same_name(self, headers):
        """
        Tries to create base-campaign with existing name. It should result in bad request error.
        """
        data = CampaignsTestsHelpers.base_campaign_data()
        # Create campaign first time
        response = requests.post(self.URL, headers=headers, data=json.dumps(data))
        assert response.status_code == codes.CREATED
        # Create campaign second time
        response = requests.post(self.URL, headers=headers, data=json.dumps(data))
        assert response.status_code == codes.BAD

    def test_with_same_name_in_other_domain(self, headers, headers_other):
        """
        Tries to create base-campaign in other doamin with existing name. It should allow creation.
        """
        data = CampaignsTestsHelpers.base_campaign_data()
        # Create campaign first time
        response = requests.post(self.URL, headers=headers, data=json.dumps(data))
        assert response.status_code == codes.CREATED
        # Create campaign second time
        response = requests.post(self.URL, headers=headers_other, data=json.dumps(data))
        assert response.status_code == codes.CREATED
