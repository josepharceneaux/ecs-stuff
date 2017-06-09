"""
Here we have tests for getting particular send of an email-campaign
"""
# Third Party
import pytest
import requests

# Application Specific
from ..conftest import GRAPHQL_BASE_URL
from email_campaign_service.common.utils.handy_functions import send_request
from email_campaign_service.common.tests.fake_testing_data_generator import fake
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.common.models.email_campaign import (EmailCampaignSend, EmailCampaign)

__author__ = 'basit'


@pytest.mark.skipif(True, reason='graphQL has low priority for now')
class TestCampaignSend(object):
    """
    This contains tests to get particular send of an email-campaign
    """
    expected_fields_list = EmailCampaignSend.get_fields()
    query_string = "query{email_campaign_query{send(campaign_id:%s id:%s){%s}}}" \
                   % ('%d', '%d', ' '.join(expected_fields_list))

    def test_get_send_without_auth_header(self):
        """
        Test to get campaign send without auth header. It should get 'error' in JSON response.
        """
        query = {'query': self.query_string % (fake.random_int(), fake.random_int())}
        response = requests.get(GRAPHQL_BASE_URL, data=query)
        assert response.status_code == requests.codes.ok
        assert response.json()['errors']

    def test_get_send_with_valid_data(self, access_token_first, access_token_same, sent_campaign):
        """
        Test to get send of an email-campaign created by logged-in user with auth header. It should not get any
        error. It also get sends for other user of same domain.
        """
        for campaign_send in sent_campaign.sends:
            for access_token in (access_token_first, access_token_same):
                query = {'query': self.query_string % (sent_campaign.id, campaign_send.id)}
                response = send_request('get', GRAPHQL_BASE_URL, access_token, data=query)
                assert response.status_code == requests.codes.ok
                assert 'errors' not in response.json()
                send = response.json()['data']['email_campaign_query']['send']
                for expected_field in self.expected_fields_list:
                    assert expected_field in send, '%s not present in response' % expected_field
                    assert send['campaign_id'] == sent_campaign.id

    def test_get_send_from_other_domain(self, access_token_other, sent_campaign):
        """
        Test to get campaign by user of some other domain. It should not get any send.
        """
        for send in sent_campaign.sends:
            query = {'query': self.query_string % (sent_campaign.id, send.id)}
            response = send_request('get', GRAPHQL_BASE_URL, access_token_other, data=query)
            assert response.status_code == requests.codes.ok
            assert 'errors' in response.json()
            assert response.json()['data']['email_campaign_query']['send'] is None

    def test_get_send_of_non_existing_campaign(self, access_token_first):
        """
        Test to get send of non-existing email-campaign. It should not get any send object.
        """
        query = {'query': self.query_string % (CampaignsTestsHelpers.get_non_existing_id(EmailCampaign),
                                               fake.random_int())}
        response = send_request('get', GRAPHQL_BASE_URL, access_token_first, data=query)
        assert response.status_code == requests.codes.ok
        assert 'errors' in response.json()
        assert response.json()['data']['email_campaign_query']['send'] is None

    def test_get_non_existing_send(self, access_token_first, email_campaign_user1_domain1_in_db):
        """
        Test to get send of non-existing send. It should not get any send.
        """
        query = {'query': self.query_string % (email_campaign_user1_domain1_in_db.id,
                                               CampaignsTestsHelpers.get_non_existing_id(EmailCampaignSend),
                                               )}
        response = send_request('get', GRAPHQL_BASE_URL, access_token_first, data=query)
        assert response.status_code == requests.codes.ok
        assert 'errors' in response.json()
        assert response.json()['data']['email_campaign_query']['send'] is None
