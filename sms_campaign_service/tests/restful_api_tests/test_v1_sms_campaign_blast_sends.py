"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/sms-campaigns/:id/blasts/:id/sends of
    SMS Campaign API.
"""
# Third Party
import requests

# Common Utils
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from sms_campaign_service.common.models.sms_campaign import (SmsCampaign, SmsCampaignBlast)
from sms_campaign_service.tests.modules.common_functions import \
    candidate_ids_associated_with_campaign


class TestSmsCampaignBlastSends(object):
    """
    This class contains tests for endpoint /v1/sms-campaigns/:id/blasts/:id/sends
    """
    URL = SmsCampaignApiUrl.BLAST_SENDS
    HTTP_METHOD = 'get'
    ENTITY = 'sends'

    def test_get_with_invalid_token(self, sent_campaign_and_blast_ids):
        """
         User auth token is invalid. It should result in Unauthorized error.
        """
        campaign, blast_ids = sent_campaign_and_blast_ids
        CampaignsTestsHelpers.request_with_invalid_token(
            self.HTTP_METHOD,
            self.URL % (campaign['id'], blast_ids[0]),
            None)

    def test_get_with_deleted_campaign(self, access_token_first, sent_campaign_and_blast_ids):
        """
        It first deletes a campaign from database and try to get its sends for given blast_id.
        It should result in ResourceNotFound error.
        """
        campaign, blast_ids = sent_campaign_and_blast_ids
        blast_id = blast_ids[0]
        CampaignsTestsHelpers.request_after_deleting_campaign(
            campaign, SmsCampaignApiUrl.CAMPAIGN,
            self.URL % ('%s', blast_id), self.HTTP_METHOD, access_token_first)

    def test_get_with_one_campaign_send(self, access_token_first, sent_campaign_and_blast_ids):
        """
        This is the case where we assume we have sent the campaign to 2 candidates.
        So, in database table "sms_campaign_send" sends count should be 2.
        """
        campaign, blast_ids = sent_campaign_and_blast_ids
        candidate_ids = candidate_ids_associated_with_campaign(campaign, access_token_first)
        expected_count = 2
        CampaignsTestsHelpers.assert_blast_sends(campaign, 2,
                                                 blast_url=SmsCampaignApiUrl.BLAST % (campaign['id'], blast_ids[0]),
                                                 access_token=access_token_first)
        response = requests.get(
            self.URL % (campaign['id'], blast_ids[0]),
            headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=expected_count)
        json_resp = response.json()[self.ENTITY][0]
        assert json_resp['blast_id'] == blast_ids[0]
        assert str(json_resp['candidate_id']) in candidate_ids

    def test_get_with_campaign_in_other_domain(self, access_token_first,
                                               sms_campaign_in_other_domain,
                                               sent_campaign_and_blast_ids):
        """
        This is the case where we try to get sends of a campaign which was created by
        some other user. It should result in Forbidden error.
        """
        campaign, blast_ids = sent_campaign_and_blast_ids
        CampaignsTestsHelpers.request_for_forbidden_error(
            self.HTTP_METHOD,
            self.URL % (sms_campaign_in_other_domain['id'], blast_ids[0]),
            access_token_first)

    def test_get_with_blast_id_associated_with_campaign_in_other_domain(
            self, access_token_first, sms_campaign_of_current_user,
            sent_campaign_and_blast_ids_in_other_domain):
        """
        Here we assume that requested blast_id is associated with such a campaign which
        does not belong to domain of logged-in user. It should get Forbidden error.
        """
        campaign_in_other_domain, blast_ids = sent_campaign_and_blast_ids_in_other_domain
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
            SmsCampaignBlast, self.HTTP_METHOD,
            self.URL % (sms_campaign_of_current_user['id'], '%s'),
            access_token_first, None)
