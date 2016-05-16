"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/sms-campaigns/:campaign_id/sends of
    SMS Campaign API.
"""
# Third Party
import requests

# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.models.sms_campaign import SmsCampaign
from sms_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from sms_campaign_service.tests.modules.common_functions import \
    candidate_ids_associated_with_campaign, assert_valid_send_object, assert_valid_blast_object


class TestSmsCampaignSends(object):
    """
    This class contains tests for endpoint /campaigns/:campaign_id/sends
    """
    URL = SmsCampaignApiUrl.SENDS
    HTTP_METHOD = 'get'
    ENTITY = 'sends'

    def test_get_with_invalid_token(self, sms_campaign_of_current_user):
        """
         User auth token is invalid. It should result in Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD,
                                                         self.URL % sms_campaign_of_current_user['id'])

    def test_get_with_no_campaign_sent(self, access_token_first, sms_campaign_of_current_user):
        """
        Here we are assuming that SMS campaign has not been sent to any of candidates,
        So no blast should be saved for the campaign. Sends count should be 0.
        """
        response = requests.get(self.URL % sms_campaign_of_current_user['id'],
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response)

    def test_get_with_no_candidate_associated_to_campaign(self, access_token_first,
                                                          sms_campaign_with_no_candidate):
        """
        Here we are assuming that SMS campaign has been sent but no candidate was associated with
        the associated smartlists. So, sends count should be 0.

        This uses fixture "sms_campaign_of_current_user" to create an SMS campaign and
        "create_sms_campaign_blast" to create an entry in database table "sms_campaign_blast",
        and then gets the "sends" of that campaign.
        """
        response = requests.get(self.URL % sms_campaign_with_no_candidate['id'],
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response)

    def test_get_with_deleted_campaign(self, access_token_first, sms_campaign_of_current_user):
        """
        It first deletes a campaign from database and try to get its sends.
        It should result in ResourceNotFound error.
        """
        CampaignsTestsHelpers.request_after_deleting_campaign(sms_campaign_of_current_user,
                                                              SmsCampaignApiUrl.CAMPAIGN,
                                                              self.URL, self.HTTP_METHOD,
                                                              access_token_first)

    def test_get_with_valid_token_and_two_sends(self,
                                                access_tokens_for_different_users_of_same_domain,
                                                sent_campaign_and_blast_ids):
        """
        This is the case where we assume we have sent the campaign to 2 candidates. We are
        using fixtures to create campaign blast and campaign sends.
        This uses fixture "sms_campaign_of_current_user" to create an SMS campaign and
        "create_sms_campaign_sends" to create an entry in database table "sms_campaign_sends",
        and then gets the "sends" of that campaign. Sends count should be 2.

        This runs for both users
        1) Who created the campaign and 2) Some other user of same domain
        """
        access_token = access_tokens_for_different_users_of_same_domain
        campaign, blast_ids = sent_campaign_and_blast_ids
        candidate_ids = candidate_ids_associated_with_campaign(campaign, access_token)
        CampaignsTestsHelpers.assert_blast_sends(campaign, 2,
                                                 blast_url=SmsCampaignApiUrl.BLAST % (campaign['id'],
                                                                                      blast_ids[0]),
                                                 access_token=access_token)
        response = requests.get(self.URL % campaign['id'],
                                headers=dict(Authorization='Bearer %s' % access_token))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=2)
        received_send_obj = response.json()[self.ENTITY]
        for send_obj in received_send_obj:
            assert_valid_send_object(send_obj, blast_ids[0], candidate_ids)

    def test_get_with_not_owned_campaign(self, access_token_first, sms_campaign_in_other_domain):
        """
        This is the case where we try to get sends of a campaign which was created by
        some other user. It should result in Forbidden error.
        """
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD,
                                                          self.URL % sms_campaign_in_other_domain['id'],
                                                          access_token_first)

    def test_get_with_invalid_campaign_id(self, access_token_first):
        """
        This is a test to get campaign sends of a campaign which does not exist in database.
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(SmsCampaign,
                                                               self.HTTP_METHOD,
                                                               self.URL,
                                                               access_token_first,
                                                               None)

    def test_get_sends_with_paginated_response(self, access_token_first, headers,
                                               sent_campaign_bulk_and_blast_ids):
        """
        Here we test the paginated response of GET call on endpoint
        /v1/sms-campaigns/:campaign_id/sends
        """
        # GET blasts of campaign
        sent_campaign = sent_campaign_bulk_and_blast_ids[0][0]
        candidate_ids = sent_campaign_bulk_and_blast_ids[0][1]
        blast_ids = sent_campaign_bulk_and_blast_ids[1]
        expected_sends = 10
        CampaignsTestsHelpers.assert_blast_sends(sent_campaign, expected_sends,
                                                 blast_url=SmsCampaignApiUrl.BLAST
                                                           % (sent_campaign['id'], blast_ids[0]),
                                                 access_token=access_token_first,
                                                 abort_time_for_sends=60)
        # GET blasts of campaign, sends should be 10
        response_blasts = requests.get(SmsCampaignApiUrl.BLASTS % sent_campaign['id'], headers=headers)
        CampaignsTestsHelpers.assert_ok_response_and_counts(response_blasts,
                                                            count=1, entity='blasts')
        CampaignsTestsHelpers.assert_ok_response_and_counts(response_blasts, count=1, entity='blasts')
        received_blast_obj = response_blasts.json()['blasts'][0]
        assert_valid_blast_object(received_blast_obj, blast_ids[0], sent_campaign['id'], expected_sends)

        blast_id = received_blast_obj['id']

        # URL to GET sends
        url = self.URL % sent_campaign['id']

        # GET all send objects without pagination params. Total count should be 10
        response = requests.get(self.URL % sent_campaign['id'], headers=headers)
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=10, entity=self.ENTITY)

        # Test GET sends of SMS campaign with 4 results per_page. It should get 4 send objects
        response = requests.get(url + '?per_page=4', headers=headers)
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=4, entity=self.ENTITY)
        received_send_objects = response.json()[self.ENTITY]

        # Assert fields of all received send objects
        for send_obj in received_send_objects:
            assert_valid_send_object(send_obj, blast_id, candidate_ids)

        # Test GET sends of SMS campaign with 4 results per_page using page = 2.
        # It should get 4 send objects
        response = requests.get(url + '?per_page=4&page=2', headers=headers)
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=4, entity=self.ENTITY)
        received_send_objects = response.json()[self.ENTITY]

        # Assert fields of all received send objects
        for send_obj in received_send_objects:
            assert_valid_send_object(send_obj, blast_id, candidate_ids)

        # Moving to next page which is third page, it should get 2 records.
        response = requests.get(url + '?per_page=4&page=3', headers=headers)
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=2, entity=self.ENTITY)
        received_send_objects = response.json()[self.ENTITY]

        # Assert fields of all received send objects
        for send_obj in received_send_objects:
            assert_valid_send_object(send_obj, blast_id, candidate_ids)

        # Test GET blasts of SMS campaign with page = 2. No send object should be received
        # in response as we have sent campaign only to ten candidates so far.
        response = requests.get(url + '?per_page=4&page=4', headers=headers)
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=0, entity=self.ENTITY)
