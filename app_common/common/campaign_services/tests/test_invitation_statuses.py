"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

Here we have tests for API
    - /v1/email-campaigns/:email-campaign_id/:candidate_id
"""
# Service Specific
from ...models.misc import Activity
from ...constants import HttpMethods
from ...tests.sample_data import fake
from ..campaign_base import CampaignBase
from ...routes import EmailCampaignApiUrl
from ..campaign_utils import INVITATION_STATUSES
from modules.helper_functions import create_an_rsvp_in_database
from ..tests_helpers import (CampaignsTestsHelpers, send_request)
from ...models.email_campaign import EmailCampaignSend, EmailCampaign
from ...custom_errors.campaign import EMAIL_CAMPAIGN_FORBIDDEN, EMAIL_CAMPAIGN_NOT_FOUND

__author__ = 'basit'


class TestGetInvitationStatus(object):
    """
    Here are the tests of /v1/email-campaigns/:email-campaign_id/:candidate_id
    """
    URL = EmailCampaignApiUrl.INVITATION_STATUS
    HTTP_METHOD = HttpMethods.GET

    def test_with_invalid_token(self):
        """
        User auth token is invalid. It should get Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL % (fake.random_int(),
                                                                                       fake.random_int()))

    def test_for_status_delivered(self, email_campaign_with_base_id, candidate_first, token_first):
        """
        Here we are expecting from API to return status 'Delivered'.
        """
        response = send_request(self.HTTP_METHOD, self.URL % (email_campaign_with_base_id['id'], candidate_first['id']),
                                token_first)
        assert response.ok, response.text
        assert response.json()['invitation_status'] == INVITATION_STATUSES['Delivered']

    def test_for_status_not_delivered(self, email_campaign_with_base_id, token_first):
        """
        Here we are expecting from API to return status 'Not-Delivered'.
        """
        response = send_request(self.HTTP_METHOD, self.URL % (email_campaign_with_base_id['id'], fake.random_int()),
                                token_first)
        assert response.ok, response.text
        assert response.json()['invitation_status'] == INVITATION_STATUSES['Not-Delivered']

    def test_for_status_opened(self, email_campaign_with_base_id, candidate_first, token_first, user_first):
        """
        Here we are expecting from API to return status 'Opened'.
        """
        email_campaign_send = EmailCampaignSend.filter_by_keywords(campaign_id=email_campaign_with_base_id['id'])
        # Add activity
        for activity in (Activity.MessageIds.CAMPAIGN_EMAIL_OPEN, Activity.MessageIds.CAMPAIGN_EMAIL_CLICK):
            CampaignBase.create_activity(user_first['id'], activity, email_campaign_send[0],
                                         dict(candidateId=candidate_first['id']))
            response = send_request(self.HTTP_METHOD, self.URL % (email_campaign_with_base_id['id'],
                                                                  candidate_first['id']),
                                    token_first)
            assert response.ok, response.text
            assert response.json()['invitation_status'] == INVITATION_STATUSES['Opened']

    def test_for_status_accepted(self, email_campaign_with_base_id, candidate_first, token_first, event_in_db,
                                 base_campaign_event):
        """
        Here we are expecting from API to return status 'Accepted'. It assumes that base campaign has an associated
        event.
        """
        create_an_rsvp_in_database(candidate_first['id'], event_in_db['id'], token_first)
        response = send_request(self.HTTP_METHOD, self.URL % (email_campaign_with_base_id['id'], candidate_first['id']),
                                token_first)
        assert response.ok, response.text
        assert response.json()['invitation_status'] == INVITATION_STATUSES['Accepted']

    def test_for_status_rejected(self, email_campaign_with_base_id, candidate_first, token_first, event_in_db,
                                 base_campaign_event):
        """
        Here we are expecting from API to return status 'Rejected'.
        """
        create_an_rsvp_in_database(candidate_first['id'], event_in_db['id'], token_first, expected_status='no')
        response = send_request(self.HTTP_METHOD, self.URL % (email_campaign_with_base_id['id'], candidate_first['id']),
                                token_first)
        assert response.ok, response.text
        assert response.json()['invitation_status'] == INVITATION_STATUSES['Rejected']

    def test_get_with_non_existing_email_campaign(self, token_first):
        """
        This hits the API with non-existing email_campaign_id. This should result in ResourceNotFound
        error.
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(EmailCampaign, self.HTTP_METHOD,
                                                               self.URL % ('%s', fake.random_int(2,)),
                                                               token_first,
                                                               expected_error_code=EMAIL_CAMPAIGN_NOT_FOUND[1])

    def test_get_with_not_owned_email_campaign(self, email_campaign_with_base_id, token_second):
        """
        This hits the API with not-owned email_campaign_id. This should result in Forbidden error.
        """
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD,
                                                          self.URL % (
                                                              email_campaign_with_base_id['id'], fake.random_int()),
                                                          token_second,
                                                          expected_error_code=EMAIL_CAMPAIGN_FORBIDDEN[1])
