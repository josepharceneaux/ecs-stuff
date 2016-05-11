"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/sms-campaigns/:id/blasts/:id/replies of
    SMS Campaign API.
"""
# Third Party
import requests

# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.tests.modules.common_functions import assert_valid_reply_object, \
    assert_valid_blast_object
from sms_campaign_service.common.models.sms_campaign import (SmsCampaign, SmsCampaignBlast)
from sms_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers


class TestSmsCampaignBlastReplies(object):
    """
    This class contains tests for endpoint /v1/sms-campaigns/:id/blasts/:id/replies
    """
    URL = SmsCampaignApiUrl.BLAST_REPLIES
    HTTP_METHOD = 'get'
    ENTITY = 'replies'

    def test_get_with_invalid_token(self, sent_campaign_and_blast_ids):
        """
         User auth token is invalid. It should result in Unauthorized error.
        """
        campaign, blasts_ids = sent_campaign_and_blast_ids
        CampaignsTestsHelpers.request_with_invalid_token(
            self.HTTP_METHOD, self.URL % (campaign['id'], blasts_ids[0]),
            None)

    def test_get_with_no_replies_on_campaign(self, headers, sent_campaign_and_blast_ids):
        """
        Here we are assuming that SMS campaign has been sent to candidates.
        And we didn't receive any reply from candidate. Replies count should be 0.
        """
        campaign, blasts_ids = sent_campaign_and_blast_ids
        response = requests.get(self.URL % (campaign['id'], blasts_ids[0]), headers=headers)
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, entity=self.ENTITY)

    def test_get_with_deleted_campaign(self, access_token_first, sent_campaign_and_blast_ids):
        """
        It first deletes a campaign from database and try to get its replies for given blast_id.
        It should result in ResourceNotFound error.
        """
        campaign, blast_ids = sent_campaign_and_blast_ids
        blast_id = blast_ids[0]
        CampaignsTestsHelpers.request_after_deleting_campaign(
            campaign, SmsCampaignApiUrl.CAMPAIGN, self.URL % ('%s', blast_id),
            self.HTTP_METHOD, access_token_first)

    def test_get_with_one_blast_reply(self, headers_for_different_users_of_same_domain,
                                      candidate_and_phone_1,
                                      sent_campaign_and_blast_ids,
                                      create_campaign_replies):
        """
        This is the case where one candidate has replied to the sms-campaign.
        This uses fixture "create_campaign_replies" to create an entry in database table
        "sms_campaign_replies". Replies count should be 1.
        This runs for both users
        1) Who created the campaign and 2) Some other user of same domain
        """
        campaign, blast_ids = sent_campaign_and_blast_ids
        response = requests.get(self.URL % (campaign['id'], blast_ids[0]),
                                headers=headers_for_different_users_of_same_domain)
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=1, entity=self.ENTITY)
        received_reply_objects = response.json()[self.ENTITY]
        # Assert all reply objects have valid fields
        for received_reply_object in received_reply_objects:
            assert_valid_reply_object(received_reply_object, blast_ids[0], [candidate_and_phone_1[1]['id']])

    def test_get_with_not_owned_campaign(self, access_token_first, sms_campaign_in_other_domain,
                                         sent_campaign_and_blast_ids):
        """
        This is the case where we try to get blast of a campaign which was created by
        some other user. It should result in Forbidden error.
        """
        _, blast_ids = sent_campaign_and_blast_ids
        CampaignsTestsHelpers.request_for_forbidden_error(
            self.HTTP_METHOD,
            self.URL % (sms_campaign_in_other_domain['id'], blast_ids[0]),
            access_token_first)

    def test_get_with_blast_id_associated_with_not_owned_campaign(
            self, access_token_first, sms_campaign_of_current_user,
            sent_campaign_and_blast_ids_in_other_domain):
        """
        Here we assume that requested blast_id is associated with such a campaign which does not
        belong to domain of logged-in user. It should result in Forbidden error.
        """
        _, blast_ids = sent_campaign_and_blast_ids_in_other_domain
        CampaignsTestsHelpers.request_for_forbidden_error(
            self.HTTP_METHOD,
            self.URL % (sms_campaign_of_current_user['id'], blast_ids[0]),
            access_token_first)

    def test_get_with_invalid_campaign_id(self, access_token_first, sent_campaign_and_blast_ids):
        """
        This is a test to get blasts of a campaign which does not exist in database.
        """
        _, blast_ids = sent_campaign_and_blast_ids
        CampaignsTestsHelpers.request_with_invalid_resource_id(
            SmsCampaign, self.HTTP_METHOD, self.URL % ('%s', blast_ids[0]),
            access_token_first,
            None)

    def test_get_with_invalid_blast_id(self, access_token_first, sms_campaign_of_current_user):
        """
        This is a test to get blasts of a campaign using non-existing blast_id
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(
            SmsCampaignBlast, self.HTTP_METHOD, self.URL % (sms_campaign_of_current_user['id'], '%s'),
            access_token_first, None)

    def test_get_blast_replies_with_paginated_response(self,
                                                 sent_campaign_and_blast_ids,
                                                 create_bulk_replies, headers,
                                                 candidate_and_phone_1, candidate_and_phone_2):
        """
        Here we test the paginated response of GET call on endpoint
        /v1/sms-campaigns/:campaign_id/replies
        """
        # GET blasts of campaign
        sent_campaign, blast_ids = sent_campaign_and_blast_ids
        expected_blast_id = blast_ids[0]
        candidate_phone_ids = [candidate_phone_tuple[1]['id'] for candidate_phone_tuple
                               in [candidate_and_phone_1, candidate_and_phone_2]]

        # GET blasts of campaign, replies should be 10
        response_blasts = requests.get(SmsCampaignApiUrl.BLASTS % sent_campaign['id'],
                                       headers=headers)
        CampaignsTestsHelpers.assert_ok_response_and_counts(response_blasts,
                                                            count=1, entity='blasts')
        json_resp = response_blasts.json()['blasts'][0]
        assert_valid_blast_object(json_resp, expected_blast_id, sent_campaign['id'], expected_sends=2, expected_replies=10)

        # URL to GET replies
        url = self.URL % (sent_campaign['id'], expected_blast_id)

        # GET all replies objects and assert there are 10 replies objects
        response = requests.get(url, headers=headers)
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=10, entity=self.ENTITY)

        # Moving to first page
        # Test GET replies of SMS campaign with 4 results per_page. It should get 4 replies objects
        response = requests.get(url + '?per_page=4', headers=headers)
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=4, entity=self.ENTITY)
        received_reply_objects = response.json()[self.ENTITY]
        # Assert all reply objects have valid fields
        for received_reply_object in received_reply_objects:
            assert_valid_reply_object(received_reply_object, expected_blast_id, candidate_phone_ids)

        # Moving to next page which is second page
        # Test GET replies of SMS campaign with 4 results per_page using page=2. It should get 4
        # records
        response = requests.get(url + '?per_page=4&page=2', headers=headers)
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=4, entity=self.ENTITY)
        received_reply_objects = response.json()[self.ENTITY]
        # Assert all reply objects have valid fields
        for received_reply_object in received_reply_objects:
            assert_valid_reply_object(received_reply_object, expected_blast_id, candidate_phone_ids)

        # Moving to next page which is third page, it should get 2 records
        response = requests.get(url + '?per_page=4&page=3', headers=headers)
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=2, entity=self.ENTITY)
        received_reply_objects = response.json()[self.ENTITY]
        # Assert all reply objects have valid fields
        for received_reply_object in received_reply_objects:
            assert_valid_reply_object(received_reply_object, expected_blast_id, candidate_phone_ids)

        # Test GET replies of SMS campaign with per_page=4 and page=4.
        # No reply object should be received in response as we only have 10 replies created so far
        response = requests.get(url + '?per_page=4&page=4', headers=headers)
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=0, entity=self.ENTITY)
