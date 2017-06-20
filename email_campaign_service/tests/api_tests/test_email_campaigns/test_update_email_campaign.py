"""
This module contains tests for updating an email campaign
"""
import pytest
from email_campaign_service.common.models.db import db
from candidate_service.tests.unit_tests.test_utilities import fake
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.models.email_campaign import EmailCampaign
from email_campaign_service.common.custom_errors.campaign import (EMAIL_CAMPAIGN_FORBIDDEN,
                                                                  EMAIL_CAMPAIGN_NOT_FOUND, INVALID_REQUEST_BODY,
                                                                  INVALID_INPUT)
from email_campaign_service.tests.modules.handy_functions import get_campaign_or_campaigns
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers


class TestCampaignUpdate(object):
    """
    Here we have tests to update an email-campaign. Currently this endpoint only marks an email-campaign
    as archived.
    """
    HTTP_METHOD = 'patch'
    URL = EmailCampaignApiUrl.CAMPAIGN

    def test_with_invalid_token(self):
        """
        Here we try to update an email campaign with invalid access token.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL % fake.random_int(2, ))

    def test_campaign_creation_with_invalid_data(self, access_token_first):
        """
        Trying to update a campaign with 1) no data and 2) Non-JSON data. It should result in invalid usage error.
        """
        for data in ({}, None):
            CampaignsTestsHelpers.request_with_invalid_input(self.HTTP_METHOD, self.URL % fake.random_int(2, ),
                                                             access_token_first, data=data, is_json=False,
                                                             expected_error_code=INVALID_REQUEST_BODY[1])

    def test_update_email_campaign_with_allowed_parameter(self, access_token_first, email_campaign_user1_domain1_in_db):
        """
         The test is to make sure that email campaign update functionality with allowed parameters/fields
         is working properly or not. Should return 200 status ok.
        """
        campaign_id = email_campaign_user1_domain1_in_db.id
        for param in [True, 1, False, 0]:
            data = {'is_hidden': param}
            CampaignsTestsHelpers.request_for_ok_response(self.HTTP_METHOD, self.URL % campaign_id,
                                                          access_token_first, data)
            email_campaign = get_campaign_or_campaigns(access_token_first, campaign_id=campaign_id)
            assert email_campaign['is_hidden'] == param

    def test_update_email_campaign_with_invalid_data(self, access_token_first, email_campaign_user1_domain1_in_db):
        """
         This test to make sure that update email campaign with invalid data is not
         possible, only valid data is acceptable. Should return 400 bad request on invalid data.
        """
        campaign_id = email_campaign_user1_domain1_in_db.id
        update_with_invalid_data = [fake.word(), fake.random_int(2, )]
        for param in update_with_invalid_data:
            data = {'is_hidden': param}
            CampaignsTestsHelpers.request_with_invalid_input(self.HTTP_METHOD, self.URL % campaign_id,
                                                             access_token_first, data,
                                                             expected_error_code=INVALID_INPUT[1])

    def test_archive_scheduled_campaign(self, access_token_first, email_campaign_of_user_first):
        """
        Here we archive a scheduled campaign. scheduler_task_id of campaign should be set to empty string
        after successfully archived from API.
        """
        # Assert that campaign is scheduled
        assert email_campaign_of_user_first.scheduler_task_id
        # Archive email-campaign
        data = {'is_hidden': True}
        CampaignsTestsHelpers.request_for_ok_response(self.HTTP_METHOD,
                                                      self.URL % email_campaign_of_user_first.id,
                                                      access_token_first, data)
        db.session.commit()
        assert not email_campaign_of_user_first.scheduler_task_id

    def test_archive_not_owned_campaign(self, access_token_other, email_campaign_user1_domain1_in_db):
        """
        Here we try to archive a campaign with such a campaign id that does not belong to user's domain.
        It then asserts that we get expected error code in the response.
        """
        # Archive email-campaign
        data = {'is_hidden': True}
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD,
                                                          self.URL % email_campaign_user1_domain1_in_db.id,
                                                          access_token_other, data,
                                                          expected_error_code=EMAIL_CAMPAIGN_FORBIDDEN[1])

    def test_archive_campaign_with_invalid_id(self, access_token_first):
        """
        Here we try to archive a campaign with invalid id and assert we get expected error code in the response.
        """
        # Archive email-campaign
        data = {'is_hidden': True}
        CampaignsTestsHelpers.request_with_invalid_resource_id(EmailCampaign, self.HTTP_METHOD, self.URL,
                                                               access_token_first, data=data,
                                                               expected_error_code=EMAIL_CAMPAIGN_NOT_FOUND[1])
