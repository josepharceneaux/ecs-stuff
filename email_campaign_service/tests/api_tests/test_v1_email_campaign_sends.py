"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/email-campaigns/:id/sends of email-campaign API.
"""
# Third Party
import requests
from polling import poll

# Common Utils
from email_campaign_service.common.routes import EmailCampaignUrl
from email_campaign_service.common.models.email_campaign import EmailCampaign
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers


class TestEmailCampaignSends(object):
    """
    This class contains tests for endpoint /v1/email-campaigns/:id/sends/:id/sends
    """
    URL = EmailCampaignUrl.SENDS
    HTTP_METHOD = 'get'
    ENTITY = 'sends'

    def test_get_with_invalid_token(self, campaign_with_valid_candidate):
        """
         User auth token is invalid. It should result in Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token(
            self.HTTP_METHOD, self.URL % campaign_with_valid_candidate.id, None)

    def test_get_with_no_campaign_sent(self, access_token_first, campaign_with_valid_candidate):
        """
        Here we are assuming that email campaign has not been sent to any candidate. Sends count
        should be 0.
        """
        response = requests.get(
            self.URL % campaign_with_valid_candidate.id,
            headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, entity=self.ENTITY)

    def test_get_by_sending_campaign(self, access_token_first, sent_campaign):
        """

        Here we first send the campaign to 2 candidates (with and without email-client-id).
        We then assert that sends has been created by making HTTP GET call on
        endpoint /v1/email-campaigns/:id/sends
        """
        CampaignsTestsHelpers.assert_blast_sends(sent_campaign, 2, abort_time_for_sends=100)
        response = requests.get(self.URL % sent_campaign.id,
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=2, entity=self.ENTITY)
        json_resp = response.json()[self.ENTITY][0]
        assert json_resp['campaign_id'] == sent_campaign.id
        assert json_resp['candidate_id'] == sent_campaign.sends[0].candidate_id

    def test_get_sends_with_paginated_response(self, access_token_first, sent_campaign_to_ten_candidates):
        """
        Here we test the paginated response of GET call on endpoint /v1/email-campaigns/:id/sends
        """
        poll(CampaignsTestsHelpers.verify_blasts, args=(sent_campaign_to_ten_candidates, access_token_first, None, 1),
             step=3, timeout=100)
        CampaignsTestsHelpers.assert_blast_sends(sent_campaign_to_ten_candidates, 10, abort_time_for_sends=300)
        #  Test GET sends of email campaign with 4 results per_page. It should get 4 blast objects
        url = self.URL % sent_campaign_to_ten_candidates.id
        response = requests.get(url + '?per_page=4',
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=4, entity=self.ENTITY)
        json_resp = response.json()[self.ENTITY]
        received_send_obj = json_resp[0]
        assert received_send_obj['campaign_id'] == sent_campaign_to_ten_candidates.id
        assert received_send_obj['candidate_id'] == sent_campaign_to_ten_candidates.sends[0].candidate_id

        #  Test GET sends of email campaign with 4 results per_page using page = 2
        response = requests.get(url + '?per_page=4&page=2',
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=4, entity=self.ENTITY)
        json_resp = response.json()[self.ENTITY]
        # pick second blast object from the response. it will be 6th send object
        received_send_obj = json_resp[1]
        assert received_send_obj['campaign_id'] == sent_campaign_to_ten_candidates.id
        assert received_send_obj['candidate_id'] == sent_campaign_to_ten_candidates.sends[5].candidate_id

        response = requests.get(url + '?per_page=4&page=3',
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=2, entity=self.ENTITY)
        json_resp = response.json()[self.ENTITY]
        # pick second send object from the response. it will be 10th send object
        received_send_obj = json_resp[1]
        assert received_send_obj['campaign_id'] == sent_campaign_to_ten_candidates.id
        assert received_send_obj['candidate_id'] == sent_campaign_to_ten_candidates.sends[9].candidate_id

        # Test GET blasts of email campaign with page = 2. No blast object should be received
        # in response as we have sent campaign only two times so far and default per_page is 10.
        response = requests.get(url + '?per_page=4&page=4',
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=0, entity=self.ENTITY)

    def test_get_not_owned_campaign(self, access_token_first, email_campaign_in_other_domain):
        """
        This is the case where we try to get sends of a campaign which was created by
        some other user. It should result in 'forbidden' error.
        """
        CampaignsTestsHelpers.request_for_forbidden_error(
            self.HTTP_METHOD, self.URL % email_campaign_in_other_domain.id, access_token_first)

    def test_with_invalid_campaign_id(self, access_token_first):
        """
        This is a test to get the sends of a campaign which does not exist in database.
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(EmailCampaign,
                                                               self.HTTP_METHOD,
                                                               self.URL,
                                                               access_token_first,
                                                               None)
