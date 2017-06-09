"""
Here we have tests for getting multiple campaigns in user's domain
"""
# Third Party
import pytest
import requests

# Application Specific
from ..conftest import GRAPHQL_BASE_URL
from email_campaign_service.common.utils.handy_functions import send_request
from email_campaign_service.common.models.email_campaign import EmailCampaign

__author__ = 'basit'


@pytest.mark.skipif(True, reason='graphQL has low priority for now')
class TestCampaignsGet(object):
    """
    This contains tests to get multiple email-campaigns
    """
    expected_fields_list = EmailCampaign.get_fields()
    query_string = "query{email_campaign_query{campaigns{edges{node{%s}}}}}" % ' '.join(expected_fields_list)
    query = {"query": query_string}

    def test_get_campaigns_without_auth_header(self):
        """
        Test to get campaigns without auth header. It should get 'error' in JSON response.
        """
        response = requests.get(GRAPHQL_BASE_URL, data=self.query)
        assert response.status_code == requests.codes.ok
        assert response.json()['errors']

    def test_get_campaigns_with_auth_header(self, access_token_first):
        """
        Test to get campaigns with auth header. It should not get any error. Total number of campaigns should be 0.
        """
        expected_campaigns = 0
        response = send_request('get', GRAPHQL_BASE_URL, access_token_first, data=self.query)
        assert response.status_code == requests.codes.ok
        assert 'errors' not in response.json()
        assert len(response.json()['data']['email_campaign_query']['campaigns']['edges']) == expected_campaigns

    def test_get_campaigns_in_same_domain(self, access_token_first, email_campaign_user1_domain1_in_db,
                                          email_campaign_user2_domain1_in_db):
        """
        Test to get campaigns created by different users of same domain. It should not get any error.
        Total number of campaigns should be 2.
        """
        expected_campaigns = 2
        response = send_request('get', GRAPHQL_BASE_URL, access_token_first, data=self.query)
        assert response.status_code == requests.codes.ok
        assert 'errors' not in response.json()
        campaigns = response.json()['data']['email_campaign_query']['campaigns']['edges']
        assert len(campaigns) == expected_campaigns
        for campaign in campaigns:
            for expected_field in self.expected_fields_list:
                assert expected_field in campaign['node'], '%s not present in response' % expected_field

    def test_get_campaigns_from_other_domain(self, access_token_other):
        """
        Test to get campaigns with user of some other domain. It should not get 'error' in JSON response.
        Total number of campaigns should be 0.
        """
        expected_campaigns = 0
        response = send_request('get', GRAPHQL_BASE_URL, access_token_other, data=self.query)
        assert response.status_code == requests.codes.ok
        assert 'errors' not in response.json()
        campaigns = response.json()['data']['email_campaign_query']['campaigns']['edges']
        assert len(campaigns) == expected_campaigns
