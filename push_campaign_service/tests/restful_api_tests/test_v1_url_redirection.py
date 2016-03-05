"""
This modules contains tests for Url Redirection endpoint
If anything goes wrong, this endpoint raises InternalServerError (500)
This module contains test for API endpoint
        /v1/redirect/:id

In these tests, we will try to emulate push notification click, which will actually
hit out API endpint to update stats of that campaign

Here are scenarios:

Hit endpoint:
    - with invalid redirect url, and after that check that campaign
        stats has changed as expected
    - without signature in url
    - but campaign associated has been deleted
    - but associated candidate has been delete
    - but url conversion object has been deleted from database
"""
from push_campaign_service.tests.test_utilities import *
from push_campaign_service.common.utils.test_utils import HttpStatus, delete_candidate
from push_campaign_service.common.routes import PushCampaignApiUrl
from push_campaign_service.tests.test_utilities import get_blasts


class TestURLRedirectionApi(object):
    """
    This class contains tests for endpoint /v1/redirect/:id
    As response from Api endpoint is returned to candidate. So ,in case of any error,
    candidate should only get internal server error.
    """

    def test_for_get(self, token_first, user_first, campaign_in_db,
                     url_conversion):
        """
        GET method should give OK response. We check the "hit_count" and "clicks" before
        hitting the endpoint and after hitting the endpoint. Then we assert that both
        "hit_count" and "clicks" have been successfully updated by '1' in database.
        :return:
        """
        # stats before making HTTP GET request to source URL
        response = get_blasts(campaign_in_db['id'], token_first, expected_status=(HttpStatus.OK,))
        blasts = response['blasts']
        assert len(blasts) == 1
        blast = blasts[0]
        hit_count, clicks = url_conversion['hit_count'],  blast['clicks']
        response = send_request('get', url_conversion['source_url'], '')
        assert response.status_code == HttpStatus.OK, 'Response should be ok'

        response = send_request('get', PushCampaignApiUrl.BLASTS % campaign_in_db['id'], token_first)
        assert response.status_code == HttpStatus.OK
        blasts = response.json()['blasts']
        assert len(blasts) == 1
        blast = blasts[0]

        response = send_request('get', PushCampaignApiUrl.URL_CONVERSION % url_conversion['id'], token_first)
        assert response.status_code == HttpStatus.OK
        url_conversion = response.json()['url_conversion']

        updated_hit_counts, updated_clicks = url_conversion['hit_count'],  blast['clicks']
        assert updated_hit_counts == hit_count + 1
        assert updated_clicks == clicks + 1

    def test_get_with_no_signature(self, url_conversion):
        """
        Removing signature of signed redirect URL. It should get internal server error.
        :return:
        """
        url_without_signature = url_conversion['source_url'].split('?')[0]
        response = send_request('get', url_without_signature, '')
        assert response.status_code == HttpStatus.INTERNAL_SERVER_ERROR
# TODO: We can have test like with invalid_signature etc

    def test_get_with_deleted_campaign(self, token_first, campaign_in_db,
                                       url_conversion):
        """
        Here we first delete the campaign, and then test functionality of process_url_redirect
        by making HTTP GET call to endpoint /v1/redirect. It should give ResourceNotFound Error.
        But candidate should get Internal server error. Hence this test should get internal server
        error.
        """
        delete_campaign(campaign_in_db['id'], token_first, expected_status=(HttpStatus.OK,))
        response = send_request('get', url_conversion['source_url'], '')
        assert response.status_code == HttpStatus.INTERNAL_SERVER_ERROR

    def test_get_with_deleted_candidate(self, url_conversion, candidate_first, token_first):
        """
        Here we first delete the candidate, which internally deletes the sms_campaign_send record
        as it uses candidate as primary key. We then test functionality of process_url_redirect
        by making HTTP GET call to endpoint /v1/redirect. It should get ResourceNotFound Error.
        But candidate should only get internal server error. So this test asserts we get internal
        server error.
        """
        delete_candidate(candidate_first['id'], token_first, expected_status=(204,))
        response = send_request('get', url_conversion['source_url'], '')
        assert response.status_code == HttpStatus.INTERNAL_SERVER_ERROR

    def test_get_with_deleted_url_conversion(self, url_conversion, token_first):
        """
        Here we first delete the url_conversion object. which internally deletes the
        sms_campaign_send record as it uses url_conversion as primary key. We then test
        functionality of process_url_redirect by making HTTP GET call to endpoint /v1/redirect.
        It should get ResourceNotFound Error. But candidate should only get internal server error.
        So this test asserts we get internal server error.
        """
        source_url = url_conversion['source_url']
        response = send_request('delete', PushCampaignApiUrl.URL_CONVERSION % url_conversion['id'], token_first)
        assert response.status_code == HttpStatus.OK
        response = send_request('get', source_url, '')
        assert response.status_code == HttpStatus.INTERNAL_SERVER_ERROR
