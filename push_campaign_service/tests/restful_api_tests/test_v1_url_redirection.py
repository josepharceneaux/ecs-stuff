"""
This modules contains tests for Url Redirection endpoint
If anything goes wrong, this endpoint raises InternalServerError (500)
"""
from push_campaign_service.common.routes import PushCampaignApiUrl, CandidateApiUrl
from push_campaign_service.tests.test_utilities import send_request
from push_campaign_service.common.utils.activity_utils import ActivityMessageIds


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
        response = send_request('get', PushCampaignApiUrl.BLASTS % campaign_in_db['id'], token_first)
        assert response.status_code == 200
        blasts = response.json()['blasts']
        assert len(blasts) == 1
        blast = blasts[0]
        hit_count, clicks = url_conversion['hit_count'],  blast['clicks']
        response = send_request('get', url_conversion['source_url'], '')
        assert response.status_code == 200, 'Response should be ok'
        assert response.url == url_conversion['destination_url']

        response = send_request('get', PushCampaignApiUrl.BLASTS % campaign_in_db['id'], token_first)
        assert response.status_code == 200
        blasts = response.json()['blasts']
        assert len(blasts) == 1
        blast = blasts[0]

        response = send_request('get', PushCampaignApiUrl.URL_CONVERSION % url_conversion['id'], token_first)
        assert response.status_code == 200
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
        assert response.status_code == 500

    def test_get_with_deleted_campaign(self, token_first, campaign_in_db,
                                       url_conversion):
        """
        Here we first delete the campaign, and then test functionality of process_url_redirect
        by making HTTP GET call to endpoint /v1/redirect. It should give ResourceNotFound Error.
        But candidate should get Internal server error. Hence this test should get internal server
        error.
        """
        response = send_request('delete', PushCampaignApiUrl.CAMPAIGN % campaign_in_db['id'], token_first)
        assert response.status_code == 200
        response = send_request('get', url_conversion['source_url'], '')
        assert response.status_code == 500

    def test_get_with_deleted_candidate(self, url_conversion, candidate_first, token_first):
        """
        Here we first delete the candidate, which internally deletes the sms_campaign_send record
        as it uses candidate as primary key. We then test functionality of process_url_redirect
        by making HTTP GET call to endpoint /v1/redirect. It should get ResourceNotFound Error.
        But candidate should only get internal server error. So this test asserts we get internal
        server error.
        """
        response = send_request('delete', CandidateApiUrl.CANDIDATE % candidate_first['id'], token_first)
        assert response.status_code == 204

        response = send_request('get', url_conversion['source_url'], '')
        assert response.status_code == 500

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
        assert response.status_code == 200
        response = send_request('get', source_url, '')
        assert response.status_code == 500
