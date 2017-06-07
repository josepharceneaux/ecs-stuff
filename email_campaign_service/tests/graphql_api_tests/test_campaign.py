"""
Here we have tests for getting single campaigns in user's domain
"""
# Third Party
import requests

# Application Specific
from ..conftest import GRAPHQL_BASE_URL
from email_campaign_service.common.utils.handy_functions import send_request
from email_campaign_service.common.models.email_campaign import EmailCampaign
from email_campaign_service.common.tests.fake_testing_data_generator import fake
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers

__author__ = 'basit'


class TestCampaignGet(object):
    """
    This contains tests to get single email-campaigns
    """
    expected_fields_list = EmailCampaign.get_fields()
    query_string = "query{email_campaign_query{campaign(id:%s){%s}}}" % ('%d', ' '.join(expected_fields_list))

    def test_get_campaign_without_auth_header(self):
        """
        Test to get campaign without auth header. It should get 'error' in JSON response.
        """
        query = {'query': self.query_string % fake.random_int()}
        response = requests.get(GRAPHQL_BASE_URL, data=query)
        assert response.status_code == requests.codes.ok, response.text
        assert response.json()['errors']

    def test_get_campaign_with_auth_header(self, access_token_first, email_campaign_user1_domain1_in_db):
        """
        Test to get campaign created by logged-in user with auth header. It should not get any error.
        """
        query = {'query': self.query_string % email_campaign_user1_domain1_in_db.id}
        response = send_request('get', GRAPHQL_BASE_URL, access_token_first, data=query)
        assert response.status_code == requests.codes.ok, response.text
        assert 'errors' not in response.json()
        campaign = response.json()['data']['email_campaign_query']['campaign']
        for expected_field in self.expected_fields_list:
            assert expected_field in campaign, '%s not present in response' % expected_field

    def test_get_campaign_in_same_domain(self, access_token_first, email_campaign_user2_domain1_in_db):
        """
        Test to get campaign created by some other user of same domain. It should not get any error.
        """
        query = {'query': self.query_string % email_campaign_user2_domain1_in_db.id}
        response = send_request('get', GRAPHQL_BASE_URL, access_token_first, data=query)
        assert response.status_code == requests.codes.ok
        assert 'errors' not in response.json()
        campaign = response.json()['data']['email_campaign_query']['campaign']
        for expected_field in self.expected_fields_list:
            assert expected_field in campaign, '%s not present in response' % expected_field

    def test_get_campaign_from_other_domain(self, access_token_other, email_campaign_user1_domain1_in_db):
        """
        Test to get campaign by user of some other domain. It should not get any campaign.
        """
        query = {'query': self.query_string % email_campaign_user1_domain1_in_db.id}
        response = send_request('get', GRAPHQL_BASE_URL, access_token_other, data=query)
        assert response.status_code == requests.codes.ok
        assert 'errors' in response.json()
        assert response.json()['data']['email_campaign_query']['campaign'] is None

    def test_get_non_existing_campaign(self, access_token_first):
        """
        Test to get non-existing email-campaign. It should not get any campaign.
        """
        query = {'query': self.query_string % CampaignsTestsHelpers.get_non_existing_id(EmailCampaign)}
        response = send_request('get', GRAPHQL_BASE_URL, access_token_first, data=query)
        assert response.status_code == requests.codes.ok
        assert 'errors' in response.json()
        assert response.json()['data']['email_campaign_query']['campaign'] is None
