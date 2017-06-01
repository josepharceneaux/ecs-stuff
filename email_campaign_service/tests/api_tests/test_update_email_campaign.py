"""
This module contains tests for updating an email campaign
"""
import pytest
from requests import codes
from email_campaign_service.common.models.db import db
from candidate_service.tests.unit_tests.test_utilities import fake
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.tests.modules.handy_functions import get_campaign_or_campaigns
from email_campaign_service.common.campaign_services.tests_helpers import (CampaignsTestsHelpers, send_request)


class TestCampaignUpdate(object):
    """
    Here we have tests to update an email-campaign. Currently this endpoint only marks an email-campaign
    as archived.
    """

    @pytest.mark.qa
    def test_update_email_campaign_with_allowed_parameter(self, access_token_first, email_campaign_of_user_first):
        """
         The test is to make sure that email campaign update functionality with allowed parameters/fields
         is working properly or not. Should return 200 status ok.
        """
        campaign_id = email_campaign_of_user_first.id
        for param in [True, 1, False, 0]:
            data = {'is_hidden': param}
            CampaignsTestsHelpers.request_for_ok_response('patch', EmailCampaignApiUrl.CAMPAIGN % campaign_id,
                                                          access_token_first, data)
            email_campaign = get_campaign_or_campaigns(access_token_first, campaign_id=campaign_id)
            assert email_campaign['is_hidden'] == param

    @pytest.mark.qa
    def test_update_email_campaign_with_invalid_data(self, access_token_first, email_campaign_of_user_first):
        """
         This test to make sure that update email campaign with invalid data is not
         possible, only valid data is acceptable. Should return 400 bad request on invalid data.
        """
        campaign_id = email_campaign_of_user_first.id
        update_with_invalid_data = [fake.word(), fake.random_int(2, )]
        for param in update_with_invalid_data:
            data = {'is_hidden': param}
            response = send_request('patch', EmailCampaignApiUrl.CAMPAIGN % campaign_id, access_token_first, data)
            CampaignsTestsHelpers.assert_non_ok_response(response, expected_status_code=codes.BAD_REQUEST)

    def test_archive_scheduled_campaign(self, access_token_first, email_campaign_of_user_first):
        """
        Here we archive a scheduled campaign. scheduler_task_id of campaign should be set to empty string
        after successfully archived from API.
        """
        # Assert that campaign is scheduled
        assert email_campaign_of_user_first.scheduler_task_id
        # Archive email-campaign
        data = {'is_hidden': True}
        CampaignsTestsHelpers.request_for_ok_response('patch',
                                                      EmailCampaignApiUrl.CAMPAIGN % email_campaign_of_user_first.id,
                                                      access_token_first, data)
        db.session.commit()
        assert not email_campaign_of_user_first.scheduler_task_id
