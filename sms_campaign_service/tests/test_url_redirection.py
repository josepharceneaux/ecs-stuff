"""
Author: Hafiz Muhammad Basit, QC-Technologies,
        Lahore, Punjab, Pakistan <basit.gettalent@gmail.com>

    This module contains pyTests for endpoint

                /campaigns/:id/url_redirection/:id/candidate_id=id

    of SMS Campaign APP.
"""

# Third Party Imports
import requests

# Application Specific
from sms_campaign_service import db
from sms_campaign_service.custom_exceptions import SmsCampaignApiException
from sms_campaign_service.sms_campaign_app.app import sms_campaign_url_redirection
from sms_campaign_service.sms_campaign_base import SmsCampaignBase
from sms_campaign_service.tests.conftest import assert_for_activity
from sms_campaign_service.common.models.sms_campaign import SmsCampaignBlast
from sms_campaign_service.common.utils.activity_utils import CAMPAIGN_SMS_CLICK
from sms_campaign_service.common.utils.app_rest_urls import SmsCampaignApiUrl
from sms_campaign_service.common.error_handling import (ResourceNotFound,
                                                        InternalServerError,
                                                        MethodNotAllowed)


class TestSmsCampaignURLRedirection:
    """
    This class contains tests for endpoint /campaigns/:id/url_redirection/:id/candidate_id=id.
    """

    def test_for_post(self, url_conversion_by_send_test_sms_campaign):
        """
        POST method should not be allowed at this endpoint.
        :return:
        """
        response_post = requests.post(url_conversion_by_send_test_sms_campaign.source_url)
        # TODO: remove this when app is up
        if response_post.status_code == ResourceNotFound.http_status_code():
            localhost_url = _replace_ngrok_link_with_localhost(
                url_conversion_by_send_test_sms_campaign.source_url)
            response_post = requests.post(localhost_url)
        assert response_post.status_code == MethodNotAllowed.http_status_code(), \
            'POST Method should not be allowed'

    def test_for_delete(self, url_conversion_by_send_test_sms_campaign):
        """
        DELETE method should not be allowed at this endpoint.
        :return:
        """
        response_post = requests.delete(url_conversion_by_send_test_sms_campaign.source_url)
        # TODO: remove this when app is up
        if response_post.status_code == ResourceNotFound.http_status_code():
            localhost_url = _replace_ngrok_link_with_localhost(
                url_conversion_by_send_test_sms_campaign.source_url)
            response_post = requests.delete(localhost_url)

        assert response_post.status_code == MethodNotAllowed.http_status_code(), \
            'DELETE Method should not be allowed'

    def test_for_get(self, sample_user,
                     url_conversion_by_send_test_sms_campaign,
                     sms_campaign_of_current_user):
        """
        GET method should give ok response
        :return:
        """
        # stats before making request
        hit_count, clicks = _get_hit_count_and_clicks(url_conversion_by_send_test_sms_campaign,
                                                      sms_campaign_of_current_user)
        response_get = requests.get(url_conversion_by_send_test_sms_campaign.source_url)
        # TODO: remove this when app is up
        if response_get.status_code == ResourceNotFound.http_status_code():
            localhost_url = _replace_ngrok_link_with_localhost(
                url_conversion_by_send_test_sms_campaign.source_url)
            response_get = requests.get(localhost_url)

        assert response_get.status_code == 200, 'Response should be ok'
        # stats after making request
        hit_count_after, clicks_after = _get_hit_count_and_clicks(
            url_conversion_by_send_test_sms_campaign,
            sms_campaign_of_current_user)
        assert hit_count_after == hit_count + 1
        assert clicks_after == clicks + 1
        assert_for_activity(sample_user.id, CAMPAIGN_SMS_CLICK, sms_campaign_of_current_user.id)

    def test_for_get_with_no_candidate_id(self, url_conversion_by_send_test_sms_campaign):
        """
        Removing candidate id from destination URL. It should get internal server error.
        :return:
        """
        url_excluding_candidate_id = \
            url_conversion_by_send_test_sms_campaign.source_url.split('?')[0]
        response_get = requests.get(url_excluding_candidate_id)
        # TODO: remove this when app is up
        if response_get.status_code == ResourceNotFound.http_status_code():
            localhost_url = _replace_ngrok_link_with_localhost(url_excluding_candidate_id)
            response_get = requests.get(localhost_url)

        assert response_get.status_code == InternalServerError.http_status_code(), \
            'It should get internal server error'

    def test_for_get_with_empty_destination_url(self, url_conversion_by_send_test_sms_campaign):
        """
        Making destination URL an empty string here, it should get internal server error.
        :return:
        """
        # forcing destination URL to be empty
        url_conversion_by_send_test_sms_campaign.update(destination_url='')
        response_get = requests.get(url_conversion_by_send_test_sms_campaign.source_url)
        # TODO: remove this when app is up
        if response_get.status_code == ResourceNotFound.http_status_code():
            localhost_url = _replace_ngrok_link_with_localhost(
                url_conversion_by_send_test_sms_campaign.source_url)
            response_get = requests.get(localhost_url)

        assert response_get.status_code == InternalServerError.http_status_code(), \
            'It should get internal server error'

    # def test_pre_process_url_redirect_with_None_data(self):
    #     try:
    #         SmsCampaignBase.pre_process_url_redirect(None, None, None)
    #     except Exception as error:
    #         assert error.error_code == SmsCampaignApiException.MISSING_REQUIRED_FIELD
    #         assert 'candidate_id' in error.message
    #         assert 'campaign_id' in error.message
    #         assert 'url_conversion_id' in error.message
    #
    # def test_pre_process_url_redirect_with_valid_data(self,
    #                                                   sms_campaign_of_current_user,
    #                                                   url_conversion_by_send_test_sms_campaign,
    #                                                   candidate_first):
    #     candidate = None
    #     campaign = None
    #     try:
    #         campaign, candidate = SmsCampaignBase.pre_process_url_redirect(sms_campaign_of_current_user.id,
    #                                                             url_conversion_by_send_test_sms_campaign.id,
    #                                                             candidate_first.id)
    #
    #     except:
    #         pass
    #     assert candidate
    #     assert campaign

    # def test_pre_process_url_redirect_with_deleted_campaign(self, valid_header,
    #                                                   sms_campaign_of_current_user,
    #                                                   url_conversion_by_send_test_sms_campaign,
    #                                                   candidate_first):
    #     """
    #     Here we first delete the campaign, and then test functionality of pre_process_url_redirect
    #     class method of SmsCampaignBase. It should give ResourceNotFound Error.
    #     """
    #     response = requests.delete(SmsCampaignApiUrl.CAMPAIGN % sms_campaign_of_current_user.id,
    #                                headers=valid_header)
    #     assert response.status_code == 200, 'should get ok response (200)'
    #     try:
    #         SmsCampaignBase.pre_process_url_redirect(sms_campaign_of_current_user.id,
    #                                                  url_conversion_by_send_test_sms_campaign.id,
    #                                                  candidate_first.id)
    #
    #     except Exception as error:
    #         assert error.error_code == ResourceNotFound.http_status_code()


def _get_hit_count_and_clicks(url_conversion, campaign):
    """
    This returns the hit counts of URL conversion record and clicks of SMS campaign blast
    from database table 'sms_campaign_blast'
    :param url_conversion: URL conversion row
    :param campaign: SMS campaign row
    :return:
    """
    db.session.commit()
    sms_campaign_blasts = SmsCampaignBlast.get_by_campaign_id(campaign.id)
    return url_conversion.hit_count, sms_campaign_blasts.clicks


# TODO: remove this when app is up
def _replace_ngrok_link_with_localhost(temp_ngrok_link):
    """
    We have exposed our endpoint via ngrok. We need to expose endpoint as Google's shorten URL API
    looks for valid URL to convert into shorter version. While making HTTP request to this endpoint,
    if ngrok is not running somehow, we replace that link with localhost to hit that endpoint. i.e.

        https://9a99a454.ngrok.io/campaigns/1298/url_redirection/294/?candidate_id=544
    will become
        https://127.0.0.1:8008/campaigns/1298/url_redirection/294/?candidate_id=544

    In final version of app, this won't be necessary as we'll have valid URL for app.
    :param temp_ngrok_link:
    :return:
    """
    relative_url = temp_ngrok_link.split('ngrok.io')[1]
    return SmsCampaignApiUrl.API_URL + relative_url
