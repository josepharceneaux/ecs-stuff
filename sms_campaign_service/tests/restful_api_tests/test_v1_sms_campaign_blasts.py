"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint /v1/sms-campaigns/:id/blasts of
    SMS Campaign API.
"""
# Third Party
import requests

# Common Utils
from sms_campaign_service.common.models.db import db
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers


class TestSmsCampaignBlasts(object):
    """
    This class contains tests for endpoint /v1/sms-campaigns/:id/blasts
    """
    URL = SmsCampaignApiUrl.BLASTS
    HTTP_METHOD = 'get'
    ENTITY = 'blasts'

    def test_get_with_invalid_token(self, sms_campaign_of_current_user):
        """
         User auth token is invalid. It should result in Unauthorized error.
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        CampaignsTestsHelpers.request_with_invalid_token(self.HTTP_METHOD, self.URL
                                                         % sms_campaign_of_current_user.id, None)

    def test_get_with_no_blasts_saved(self, access_token_first, sms_campaign_of_current_user):
        """
        Here we assume that there is no blast saved for given campaign. We should get OK
        response and count should be 0.
        :param access_token_first: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.get(self.URL % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, entity=self.ENTITY)

    def test_get_with_deleted_campaign(self, access_token_first, sms_campaign_of_current_user):
        """
        It first deletes a campaign from database and try to get its blasts.
        It should result in ResourceNotFound error.
        :param access_token_first: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        CampaignsTestsHelpers.request_after_deleting_campaign(sms_campaign_of_current_user,
                                                              SmsCampaignApiUrl.CAMPAIGN,
                                                              self.URL, self.HTTP_METHOD,
                                                              access_token_first)

    def test_get_with_saved_blasts(self, access_token_first, candidate_phone_1,
                                   sms_campaign_of_current_user,
                                   create_campaign_replies, create_campaign_sends):
        """
        This is the case where we assume we have blast saved with one reply and 2 sends.
        We are using fixtures to create campaign blast and campaign replies and sends.
        This uses fixture "sms_campaign_of_current_user" to create an SMS campaign and
        "create_campaign_replies" to create an entry in database table "sms_campaign_replies",
        and then gets the "sends" of that campaign. Replies count should be 1 and sends count
        should be 2.
        :param access_token_first: access token for sample user
        :param sms_campaign_of_current_user: fixture to create SMS campaign for current user
        :return:
        """
        response = requests.get(self.URL % sms_campaign_of_current_user.id,
                                headers=dict(Authorization='Bearer %s' % access_token_first))
        CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=1, entity=self.ENTITY)
        json_resp = response.json()[self.ENTITY][0]
        assert json_resp['id'] == sms_campaign_of_current_user.blasts[0].id
        assert json_resp['campaign_id'] == sms_campaign_of_current_user.id
        assert json_resp['sends'] == 2
        assert json_resp['replies'] == 1

    def test_get_with_not_owned_campaign(self, access_token_first, sms_campaign_in_other_domain):
        """
        This is the case where we try to get sends of a campaign which was created by
        some other user. It should result in Forbidden error.
        :return:
        """
        CampaignsTestsHelpers.request_for_forbidden_error(self.HTTP_METHOD,
                                                          self.URL % sms_campaign_in_other_domain.id,
                                                          access_token_first)

    # def test_get_blasts_with_paginated_response(self, access_token_first,
    #                                             process_send_sms_campaign,
    #                                             sms_campaign_of_current_user):
    #     """
    #     Here we test the paginated response of GET call on endpoint /v1/sms-campaigns/:id/blasts
    #     """
    #     sent_campaign = sms_campaign_of_current_user
    #     url = self.URL % sent_campaign.id
    #     response = requests.get(url + '?per_page=1',
    #                             headers=dict(Authorization='Bearer %s' % access_token_first))
    #     CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=1, entity=self.ENTITY)
    #     json_resp = response.json()[self.ENTITY]
    #     assert len(json_resp) == 1
    #     received_blast_obj = json_resp[0]
    #     assert received_blast_obj['id'] == sent_campaign.blasts[0].id
    #     assert received_blast_obj['campaign_id'] == sent_campaign.id
    #     assert received_blast_obj['sends'] == 2
    #
    #     # sending campaign 10 times to create 10 blast objects
    #     for _ in xrange(1, 10):
    #         CampaignsTestsHelpers.send_campaign(SmsCampaignApiUrl.SEND,
    #                                             sent_campaign, access_token_first)
    #     db.session.commit()
    #     #  Test GET blasts of email campaign with 4 results per_page. It should get 4 blast objects
    #     response = requests.get(url + '?per_page=4',
    #                             headers=dict(Authorization='Bearer %s' % access_token_first))
    #     CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=4, entity=self.ENTITY)
    #     json_resp = response.json()[self.ENTITY]
    #     # pick 4th blast object and assert valid response
    #     received_blast_obj = json_resp[3]
    #
    #     assert received_blast_obj['id'] == sent_campaign.blasts[3].id
    #     assert received_blast_obj['campaign_id'] == sent_campaign.id
    #     assert received_blast_obj['sends'] == 2
    #
    #     #  Test GET blasts of email campaign with 4 results per_page using page = 2
    #     response = requests.get(url + '?per_page=4&page=2',
    #                             headers=dict(Authorization='Bearer %s' % access_token_first))
    #     CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=4, entity=self.ENTITY)
    #     json_resp = response.json()[self.ENTITY]
    #     # pick second blast object and assert valid response
    #     # pick first blast object from the response. it will be 5th blast object
    #     received_blast_obj = json_resp[0]
    #     assert received_blast_obj['id'] == sent_campaign.blasts[4].id
    #     assert received_blast_obj['campaign_id'] == sent_campaign.id
    #     assert received_blast_obj['sends'] == 2
    #
    #     #  Test GET blasts of email campaign with 4 results per_page using page = 3
    #     response = requests.get(url + '?per_page=4&page=3',
    #                             headers=dict(Authorization='Bearer %s' % access_token_first))
    #     CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=2, entity=self.ENTITY)
    #     json_resp = response.json()[self.ENTITY]
    #     # pick second blast object from the response. it will be 10th blast object
    #     received_blast_obj = json_resp[1]
    #     assert received_blast_obj['id'] == sent_campaign.blasts[9].id
    #     assert received_blast_obj['campaign_id'] == sent_campaign.id
    #     assert received_blast_obj['sends'] == 2
    #
    #     # Test GET blasts of email campaign with page = 4. No blast object should be received
    #     # in response as we have sent campaign only 10 times so far and we are using
    #     # per_page=4 and page=4.
    #     response = requests.get(url + '?per_page=4&page=4',
    #                             headers=dict(Authorization='Bearer %s' % access_token_first))
    #     CampaignsTestsHelpers.assert_ok_response_and_counts(response, count=0, entity=self.ENTITY)
