"""
Here we have tests for getting sends of an email-campaign
"""
# Third Party
import pytest
import requests

# Application Specific
from ..conftest import GRAPHQL_BASE_URL
from email_campaign_service.common.utils.handy_functions import send_request
from email_campaign_service.common.tests.fake_testing_data_generator import fake
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.common.models.email_campaign import EmailCampaign, EmailCampaignSend

__author__ = 'basit'


@pytest.mark.skipif(True, reason='graphQL has low priority for now')
class TestCampaignSends(object):
    """
    This contains tests to get sends of an email-campaign
    """
    expected_campaign_sends = 2
    expected_fields_list = EmailCampaignSend.get_fields()
    query_string = "query{email_campaign_query{sends(campaign_id:%s){edges{node{%s}}}}}" \
                   % ('%d', ' '.join(expected_fields_list))

    def test_get_sends_without_auth_header(self):
        """
        Test to get campaign sends without auth header. It should get 'error' in JSON response.
        """
        query = {'query': self.query_string % fake.random_int()}
        response = requests.get(GRAPHQL_BASE_URL, data=query)
        assert response.status_code == requests.codes.ok
        assert response.json()['errors']

    def test_get_with_no_campaign_sent(self, access_token_first, email_campaign_user1_domain1_in_db):
        """
        Here we are assuming that email campaign has not been sent to any candidate. Sends count should be 0.
        """
        expected_sends = 0
        query = {'query': self.query_string % email_campaign_user1_domain1_in_db.id}
        response = send_request('get', GRAPHQL_BASE_URL, access_token_first, data=query)
        assert response.status_code == requests.codes.ok
        assert 'errors' not in response.json()
        sends_edges = response.json()['data']['email_campaign_query']['sends']['edges']
        assert len(sends_edges) == expected_sends

    def test_get_sends_with_valid_data(self, access_token_first, access_token_same, sent_campaign):
        """
        Test to get sends of an email-campaign created by logged-in user with auth header. It should not get any
        error. It also gets sends by some other user of same domain. Total number of sends should be 2.
        """
        CampaignsTestsHelpers.assert_blast_sends(sent_campaign, self.expected_campaign_sends)
        query = {'query': self.query_string % sent_campaign.id}
        for access_token in (access_token_first, access_token_same):
            response = send_request('get', GRAPHQL_BASE_URL, access_token, data=query)
            assert response.status_code == requests.codes.ok
            assert 'errors' not in response.json()
            sends_edges = response.json()['data']['email_campaign_query']['sends']['edges']
            assert len(sends_edges) == self.expected_campaign_sends
            for blast_edge in sends_edges:
                for expected_field in self.expected_fields_list:
                    assert expected_field in blast_edge['node'], '%s not present in response' % expected_field
                assert blast_edge['node']['campaign_id'] == sent_campaign.id

    def test_get_sends_from_other_domain(self, access_token_other, sent_campaign):
        """
        Test to get sends by user of some other domain. It should not get any sends.
        """
        CampaignsTestsHelpers.assert_blast_sends(sent_campaign, self.expected_campaign_sends)
        query = {'query': self.query_string % sent_campaign.id}
        response = send_request('get', GRAPHQL_BASE_URL, access_token_other, data=query)
        assert response.status_code == requests.codes.ok
        assert 'errors' in response.json()
        assert response.json()['data']['email_campaign_query']['sends'] is None

    def test_get_sends_with_not_owned_campaign(self, access_token_other, email_campaign_user1_domain1_in_db):
        """
        Test to get sends of a campaign which does not exists in user's domain. It should not get any sends.
        """
        query = {'query': self.query_string % email_campaign_user1_domain1_in_db.id}
        response = send_request('get', GRAPHQL_BASE_URL, access_token_other, data=query)
        assert response.status_code == requests.codes.ok
        assert 'errors' in response.json()
        assert response.json()['data']['email_campaign_query']['sends'] is None

    def test_get_non_existing_campaign(self, access_token_first):
        """
        Test to get sends of non-existing email-campaign. It should not get any campaign.
        """
        query = {'query': self.query_string % CampaignsTestsHelpers.get_non_existing_id(EmailCampaign)}
        response = send_request('get', GRAPHQL_BASE_URL, access_token_first, data=query)
        assert response.status_code == requests.codes.ok
        assert 'errors' in response.json()
        assert response.json()['data']['email_campaign_query']['sends'] is None
