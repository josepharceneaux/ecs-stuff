"""
Here we have tests for getting blasts of an email-campaign
"""
# Third Party
import requests

# Application Specific
from ..conftest import GRAPHQL_BASE_URL
from email_campaign_service.common.utils.handy_functions import send_request
from email_campaign_service.common.tests.fake_testing_data_generator import fake
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.common.models.email_campaign import EmailCampaignBlast, EmailCampaign

__author__ = 'basit'


class TestCampaignBlasts(object):
    """
    This contains tests to get blasts of an email-campaign
    """
    expected_fields_list = EmailCampaignBlast.get_fields()
    query_string = "query{email_campaign_query{blasts(campaign_id:%s){edges{node{%s}}}}}" \
                   % ('%d', ' '.join(expected_fields_list))

    def test_get_blasts_without_auth_header(self):
        """
        Test to get campaign blasts without auth header. It should get 'error' in JSON response.
        """
        query = {'query': self.query_string % fake.random_int()}
        response = requests.get(GRAPHQL_BASE_URL, data=query)
        assert response.status_code == requests.codes.ok
        assert response.json()['errors']

    def test_get_blasts_with_auth_header(self, access_token_first, sent_campaign):
        """
        Test to get blasts of an email-campaign created by logged-in user with auth header. It should not get any
        error.
        """
        expected_blasts = 1
        query = {'query': self.query_string % sent_campaign.id}
        response = send_request('get', GRAPHQL_BASE_URL, access_token_first, data=query)
        assert response.status_code == requests.codes.ok
        assert 'errors' not in response.json()
        blasts_edges = response.json()['data']['email_campaign_query']['blasts']['edges']
        assert len(response.json()['data']['email_campaign_query']['blasts']['edges']) == expected_blasts
        for blast_edge in blasts_edges:
            for expected_field in self.expected_fields_list:
                assert expected_field in blast_edge['node'], '%s not present in response' % expected_field

    def test_get_blasts_in_same_domain(self, access_token_same, sent_campaign):
        """
        Test to get blasts of a campaign created by some other user of same domain. It should not get any error.
        """
        expected_blasts = 1
        query = {'query': self.query_string % sent_campaign.id}
        response = send_request('get', GRAPHQL_BASE_URL, access_token_same, data=query)
        assert response.status_code == requests.codes.ok
        assert 'errors' not in response.json()
        blasts_edges = response.json()['data']['email_campaign_query']['blasts']['edges']
        assert len(response.json()['data']['email_campaign_query']['blasts']['edges']) == expected_blasts
        for blast_edge in blasts_edges:
            for expected_field in self.expected_fields_list:
                assert expected_field in blast_edge['node'], '%s not present in response' % expected_field

    def test_get_blasts_from_other_domain(self, access_token_other, email_campaign_of_user_first):
        """
        Test to get campaign by user of some other domain. It should not get any blasts.
        """
        query = {'query': self.query_string % email_campaign_of_user_first.id}
        response = send_request('get', GRAPHQL_BASE_URL, access_token_other, data=query)
        assert response.status_code == requests.codes.ok
        assert 'errors' in response.json()
        assert response.json()['data']['email_campaign_query']['blasts'] is None

    def test_get_non_existing_campaign(self, access_token_first):
        """
        Test to get blasts of non-existing email-campaign. It should not get any campaign.
        """
        query = {'query': self.query_string % CampaignsTestsHelpers.get_non_existing_id(EmailCampaign)}
        response = send_request('get', GRAPHQL_BASE_URL, access_token_first, data=query)
        assert response.status_code == requests.codes.ok
        assert 'errors' in response.json()
        assert response.json()['data']['email_campaign_query']['blasts'] is None
