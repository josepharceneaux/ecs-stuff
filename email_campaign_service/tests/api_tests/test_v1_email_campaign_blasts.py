"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/email-campaigns/:id/blasts of
    email campaign API.
"""
# Third Party
import requests

# Common Utils
from email_campaign_service.common.models.db import db
from email_campaign_service.common.routes import EmailCampaignUrl
from email_campaign_service.common.models.email_campaign import EmailCampaign
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.tests.modules.handy_functions import send_campaign, assert_blast_sends


class TestEmailCampaignBlasts(object):
    """
    This class contains tests for endpoint /v1/email-campaigns/:id/blasts
    """
    # URL of this endpoint
    URL = EmailCampaignUrl.BLASTS
    # HTTP Method for this endpoint
    HTTP_METHOD = 'get'
    # Resource for this endpoint
    ENTITY = 'blasts'

    def test_get_with_invalid_token(self, campaign_with_valid_candidate):
        """
         User auth token is invalid. It should get Unauthorized error.
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL
                                                         % campaign_with_valid_candidate.id, None)

    def test_get_with_no_campaign_sent(self, access_token_first, campaign_with_valid_candidate):
        """
        Here we assume that there is no blast saved for given campaign. We should get OK
        response and count should be 0.
        """
        response = requests.get(self.URL % campaign_with_valid_candidate.id,
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, entity=self.ENTITY)

    def test_get_by_sending_campaign(self, access_token_first, sent_campaign):
        """
        Here we first send the campaign to 2 candidates (with and without email-client-id).
        We then assert that blast has been created by making HTTP
        GET call on endpoint /v1/email-campaigns/:id/blasts
        """
        expected_count = 2
        assert_blast_sends(sent_campaign, expected_count, abort_time_for_sends=100)
        response = requests.get(self.URL % sent_campaign.id,
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=1, entity=self.ENTITY)
        json_resp = response.json()[self.ENTITY][0]
        db.session.commit()
        assert json_resp['id'] == sent_campaign.blasts[0].id
        assert json_resp['campaign_id'] == sent_campaign.id
        assert json_resp['sends'] == expected_count

    def test_get_blasts_for_primary_candidate_emails(self, access_token_first,
                                                     sent_campaign_multiple_email):
        """
        The test sends email to two candidates each having two emails.
        But email-campaign should be sent to only primary-email-addresses of candidates.
        If primary email is not found then email-campaign will be sent to latest emails added for candidates.
        """
        expected_count = 2
        assert_blast_sends(sent_campaign_multiple_email, expected_count, abort_time_for_sends=100)
        response = requests.get(
            self.URL % sent_campaign_multiple_email.id,
            headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, entity=self.ENTITY,
                                                            check_count=False)
        json_resp = response.json()[self.ENTITY]
        assert json_resp[0]['campaign_id'] == int(sent_campaign_multiple_email.id)
        assert json_resp[0]['sends'] == expected_count

    def test_get_blasts_with_paginated_response(self, access_token_first, sent_campaign):
        """
        Here we test the paginated response of GET call on endpoint /v1/email-campaigns/:id/blasts
        """
        # Test GET blasts of email campaign with 1 result per_page
        expected_sends_count = 2
        assert_blast_sends(sent_campaign, expected_sends_count, abort_time_for_sends=100)
        url = self.URL % sent_campaign.id
        response = requests.get(url + '?per_page=1',
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=1, entity=self.ENTITY)
        json_resp = response.json()[self.ENTITY]
        assert len(json_resp) == 1
        received_blast_obj = json_resp[0]
        db.session.commit()
        assert received_blast_obj['id'] == sent_campaign.blasts[0].id
        assert received_blast_obj['campaign_id'] == sent_campaign.id
        assert received_blast_obj['sends'] == expected_sends_count

        # sending campaign 10 times to create 10 blast objects
        for index in xrange(1, 10):
            send_campaign(sent_campaign, access_token_first, index+1)

        assert_blast_sends(sent_campaign, expected_sends_count, blast_index=3, abort_time_for_sends=100)
        #  Test GET blasts of email campaign with 4 results per_page. It should get 4 blast objects
        response = requests.get(url + '?per_page=4',
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=4, entity=self.ENTITY)
        json_resp = response.json()[self.ENTITY]
        # pick 4th blast object and assert valid response
        received_blast_obj = json_resp[3]
        db.session.commit()
        assert received_blast_obj['id'] == sent_campaign.blasts[3].id
        assert received_blast_obj['campaign_id'] == sent_campaign.id
        assert received_blast_obj['sends'] == expected_sends_count

        assert_blast_sends(sent_campaign, expected_sends_count, blast_index=4, abort_time_for_sends=300)
        #  Test GET blasts of email campaign with 4 results per_page using page = 2
        response = requests.get(url + '?per_page=4&page=2',
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=4, entity=self.ENTITY)
        json_resp = response.json()[self.ENTITY]
        # pick second blast object and assert valid response
        # pick first blast object from the response. it will be 5th blast object
        received_blast_obj = json_resp[0]
        db.session.commit()
        assert received_blast_obj['id'] == sent_campaign.blasts[4].id
        assert received_blast_obj['campaign_id'] == sent_campaign.id
        assert received_blast_obj['sends'] == expected_sends_count

        assert_blast_sends(sent_campaign, expected_sends_count, blast_index=9, abort_time_for_sends=100)
        #  Test GET blasts of email campaign with 4 results per_page using page = 3
        response = requests.get(url + '?per_page=4&page=3',
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=2, entity=self.ENTITY)
        json_resp = response.json()[self.ENTITY]
        # pick second blast object from the response. it will be 10th blast object
        received_blast_obj = json_resp[1]
        db.session.commit()
        assert received_blast_obj['id'] == sent_campaign.blasts[9].id
        assert received_blast_obj['campaign_id'] == sent_campaign.id
        assert received_blast_obj['sends'] == expected_sends_count

        # Test GET blasts of email campaign with page = 4. No blast object should be received
        # in response as we have sent campaign only 10 times so far and we are using
        # per_page=4 and page=4.
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
        This is a test to get the blasts of a campaign which does not exist in database.
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(EmailCampaign,
                                                               self.HTTP_METHOD,
                                                               self.URL,
                                                               access_token_first,
                                                               None)
