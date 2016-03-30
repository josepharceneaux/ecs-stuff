"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/sms-campaigns/:campaign_id/sends of
    SMS Campaign API.
"""
# Third Party
import requests

# Common Utils
from sms_campaign_service.common.models.db import db
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.models.sms_campaign import SmsCampaign
from sms_campaign_service.common.error_handling import UnauthorizedError
from sms_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers


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
        :param access_token_first: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.get(self.URL % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s invalid_token'))
        assert response.status_code == UnauthorizedError.http_status_code(), \
            'It should not be authorized (401)'

    def test_get_with_no_campaign_sent(self, access_token_first, sms_campaign_of_current_user):
        """
        Here we are assuming that SMS campaign has not been sent to any of candidates,
        So no blast should be saved for the campaign. Sends count should be 0.
        :param access_token_first: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.get(self.URL % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response)

    def test_get_with_no_candidate_associated_to_campaign(self, access_token_first,
                                                          sms_campaign_of_current_user,
                                                          create_sms_campaign_blast):
        """
        Here we are assuming that SMS campaign has been sent but no candidate was associated with
        the associated smartlists. So, sends count should be 0.

        This uses fixture "sms_campaign_of_current_user" to create an SMS campaign and
        "create_sms_campaign_blast" to create an entry in database table "sms_campaign_blast",
        and then gets the "sends" of that campaign.
        :param access_token_first: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :param create_sms_campaign_blast: fixture to create entry in "sms_campaign_blast" db table.
        :return:
        """
        response = requests.get(self.URL % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response)

    def test_get_with_deleted_campaign(self, access_token_first, sms_campaign_of_current_user):
        """
        It first deletes a campaign from database and try to get its sends.
        It should result in ResourceNotFound error.
        :param access_token_first: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        CampaignsTestsHelpers.request_after_deleting_campaign(sms_campaign_of_current_user,
                                                              SmsCampaignApiUrl.CAMPAIGN,
                                                              self.URL, self.HTTP_METHOD,
                                                              access_token_first)

    def test_get_with_valid_token_and_two_sends(self, access_token_first, candidate_first,
                                                sms_campaign_of_current_user,
                                                create_campaign_sends):
        """
        This is the case where we assume we have sent the campaign to 2 candidates. We are
        using fixtures to create campaign blast and campaign sends.
        This uses fixture "sms_campaign_of_current_user" to create an SMS campaign and
        "create_sms_campaign_sends" to create an entry in database table "sms_campaign_sends",
        and then gets the "sends" of that campaign. Sends count should be 2.
        :param access_token_first: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.get(self.URL % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=2)
        json_resp = response.json()[self.ENTITY][0]
        assert json_resp['blast_id'] == sms_campaign_of_current_user.blasts[0].id
        assert json_resp['candidate_id'] == candidate_first.id

    def test_get_with_not_owned_campaign(self, access_token_first, sms_campaign_in_other_domain):
        """
        This is the case where we try to get sends of a campaign which was created by
        some other user. It should result in Forbidden error.
        :return:
        """
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD,
                                                          self.URL % sms_campaign_in_other_domain.id,
                                                          access_token_first)

    def test_get_with_invalid_campaign_id(self, access_token_first):
        """
        This is a test to get campaign sends of a campaign which does not exist in database.
        :param access_token_first:
        :return:
        """
        CampaignsTestsHelpers.request_with_invalid_resource_id(SmsCampaign,
                                                               self.HTTP_METHOD,
                                                               self.URL,
                                                               access_token_first,
                                                               None)

    def test_get_sends_with_paginated_response(self, access_token_first, sent_campaign_bulk):
        """
        Here we test the paginated response of GET call on endpoint /v1/sms-campaigns/:campaign_id/sends
        """
        # GET blasts of campaign
        sent_campaign = sent_campaign_bulk[0]
        candidate_ids = sent_campaign_bulk[1]
        response_blasts = requests.get(SmsCampaignApiUrl.BLASTS % sent_campaign.id,
                                       headers={'Authorization': 'Bearer %s' % access_token_first})
        CampaignsTestsHelpers.assert_ok_response_and_counts(response_blasts,
                                                            count=1, entity='blasts')
        json_resp = response_blasts.json()['blasts'][0]
        assert json_resp['campaign_id'] == sent_campaign.id
        assert json_resp['sends'] == 10
        blast_id = json_resp['id']
        # URL to GET sends
        url = self.URL % sent_campaign.id
        #  Test GET sends of SMS campaign with 4 results per_page. It should get 4 blast objects
        response = requests.get(url + '?per_page=4',
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=4, entity=self.ENTITY)
        json_resp = response.json()[self.ENTITY]
        # Pick first send object
        received_send_obj = json_resp[0]
        assert received_send_obj['blast_id'] == blast_id
        assert received_send_obj['candidate_id'] in candidate_ids

        #  Test GET sends of SMS campaign with 4 results per_page using page = 2
        response = requests.get(url + '?per_page=4&page=2',
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=4, entity=self.ENTITY)
        json_resp = response.json()[self.ENTITY]
        # pick second blast object from the response. it will be 6th blast object
        received_send_obj = json_resp[1]
        assert received_send_obj['blast_id'] == blast_id
        assert received_send_obj['candidate_id'] in candidate_ids

        response = requests.get(url + '?per_page=4&page=3',
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=2, entity=self.ENTITY)
        json_resp = response.json()[self.ENTITY]
        # pick second send object from the response. it will be 10th send object
        received_send_obj = json_resp[1]
        assert received_send_obj['blast_id'] == blast_id
        assert received_send_obj['candidate_id'] in candidate_ids

        # Test GET blasts of SMS campaign with page = 2. No blast object should be received
        # in response as we have sent campaign only two times so far and default per_page is 10.
        response = requests.get(url + '?per_page=4&page=4',
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=0, entity=self.ENTITY)
