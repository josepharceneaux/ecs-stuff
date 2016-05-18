"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/sms-campaigns/:id/blasts/:id of
    SMS Campaign API.
"""
# Third Party
import requests

# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from sms_campaign_service.common.models.sms_campaign import (SmsCampaign, SmsCampaignBlast)


class TestSmsCampaignBlastsWithId(object):
    """
    This class contains tests for endpoint /v1/sms-campaigns/:id/blasts/:id
    """
    URL = SmsCampaignApiUrl.BLAST
    HTTP_METHOD = 'get'
    ENTITY = 'blast'

    def test_get_with_invalid_token(self, sent_campaign_and_blast_ids):
        """
         User auth token is invalid. It should result in Unauthorized error
        """
        campaign, blast_ids = sent_campaign_and_blast_ids
        CampaignsTestsHelpers.request_with_invalid_token(
            self.HTTP_METHOD, self.URL % (campaign['id'], blast_ids[0]), None)

    def test_get_with_deleted_campaign(self, access_token_first, sent_campaign_and_blast_ids):
        """
        It first deletes a campaign from database and try to get its blasts.
        It should result in ResourceNotFound error.
        """
        campaign, blast_ids = sent_campaign_and_blast_ids
        CampaignsTestsHelpers.request_after_deleting_campaign(
            campaign, SmsCampaignApiUrl.CAMPAIGN,
            self.URL % ('%s', blast_ids[0]), self.HTTP_METHOD, access_token_first)

    def test_get_with_saved_blast(self, access_token_first, sent_campaign_and_blast_ids,
                                  create_campaign_replies):
        """
        This is the case where we assume we have blast saved with one reply and 2 sends.
        We are using fixture "create_campaign_replies" to create an entry in database table
        "sms_campaign_replies". Replies count should be 1 and sends count should be 2.
        """
        campaign, blast_ids = sent_campaign_and_blast_ids
        expected_sends = 2
        # Poll sends for blast
        CampaignsTestsHelpers.assert_blast_sends(
            campaign, expected_sends,
            blast_url=SmsCampaignApiUrl.BLAST % (campaign['id'], blast_ids[0]),
            access_token=access_token_first)

        response = requests.get(
            self.URL % (campaign['id'], blast_ids[0]),
            headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, entity=self.ENTITY,
                                                            check_count=False)
        json_resp = response.json()[self.ENTITY]
        assert json_resp['id'] == blast_ids[0]
        assert json_resp['campaign_id'] == campaign['id']
        assert json_resp['sends'] == expected_sends
        assert json_resp['replies'] == 1

    def test_get_with_not_owned_campaign(self, access_token_first, sms_campaign_in_other_domain,
                                         sent_campaign_and_blast_ids):
        """
        This is the case where we try to get blast of a campaign which was created by
        some other user. It should result in Forbidden error.
        """
        campaign, blast_ids = sent_campaign_and_blast_ids
        CampaignsTestsHelpers.request_for_forbidden_error(
            self.HTTP_METHOD, self.URL % (sms_campaign_in_other_domain['id'], blast_ids[0]),
            access_token_first)

    def test_get_with_blast_id_associated_with_not_owned_campaign(
            self, access_token_first, sms_campaign_of_current_user,
            sent_campaign_and_blast_ids_in_other_domain):
        """
        Here we assume that requested blast_id is associated with such a campaign which does not
        belong to domain of logged-in user. It should get Forbidden error.
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
