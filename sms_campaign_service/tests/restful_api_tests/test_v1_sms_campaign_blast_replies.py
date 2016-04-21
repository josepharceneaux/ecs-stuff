"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/sms-campaigns/:id/blasts/:id/replies of
    SMS Campaign API.
"""
# Third Party
import requests

# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl
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

    def test_get_with_no_replies_on_campaign(self, access_token_first, sent_campaign_and_blast_ids):
        """
        Here we are assuming that SMS campaign has been sent to candidates.
        And we didn't receive any reply from candidate. Replies count should be 0.
        """
        campaign, blasts_ids = sent_campaign_and_blast_ids
        response = requests.get(
            self.URL % (campaign['id'], blasts_ids[0]),
            headers=dict(Authorization='Bearer %s' % access_token_first))
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

    def test_get_with_one_blast_reply(self, access_token_first, candidate_and_phone_1,
                                      sent_campaign_and_blast_ids,
                                      create_campaign_replies):
        """
        This is the case where one candidate has replied to the sms-campaign.
        This uses fixture "create_campaign_replies" to create an entry in database table
        "sms_campaign_replies". Replies count should be 1.
        """
        campaign, blast_ids = sent_campaign_and_blast_ids
        response = requests.get(
            self.URL % (campaign['id'], blast_ids[0]),
            headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=1, entity=self.ENTITY)
        json_resp = response.json()[self.ENTITY][0]
        assert json_resp['blast_id'] == blast_ids[0]
        assert json_resp['candidate_phone_id'] == candidate_and_phone_1[1]['id']

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
