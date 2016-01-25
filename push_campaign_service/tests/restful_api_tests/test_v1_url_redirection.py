"""
This modules contains tests for Url Redirection endpoint
If anything goes wrong, this endpoint raises InternalServerError (500)
"""
from push_campaign_service.tests.test_utilities import send_request
from push_campaign_service.common.models.candidate import Candidate
from push_campaign_service.common.models.misc import Activity, UrlConversion
from push_campaign_service.common.utils.activity_utils import ActivityMessageIds
from push_campaign_service.common.models.push_campaign import PushCampaignBlast, PushCampaign


class TestURLRedirectionApi(object):
    """
    This class contains tests for endpoint /v1/redirect/:id
    As response from Api endpoint is returned to candidate. So ,in case of any error,
    candidate should only get internal server error.
    """

    def test_for_get(self, sample_user, campaign_in_db, schedule_a_campaign,
                     url_conversion):
        """
        GET method should give OK response. We check the "hit_count" and "clicks" before
        hitting the endpoint and after hitting the endpoint. Then we assert that both
        "hit_count" and "clicks" have been successfully updated by '1' in database.
        :return:
        """
        # stats before making HTTP GET request to source URL
        campaign_blast = campaign_in_db.blasts.first()
        hit_count, clicks = url_conversion.hit_count,  campaign_blast.clicks
        response = send_request('get', url_conversion.source_url, '')
        assert response.status_code == 200, 'Response should be ok'
        assert response.url == url_conversion.destination_url
        # stats after making HTTP GET request to source URL
        PushCampaignBlast.session.commit()
        updated_hit_counts, updated_clicks = url_conversion.hit_count,  campaign_blast.clicks
        assert updated_hit_counts == hit_count + 1
        assert updated_clicks == clicks + 1
        assert Activity.get_by_user_id_type_source_id(sample_user.id,
                                                      ActivityMessageIds.CAMPAIGN_PUSH_CLICK,
                                                      campaign_in_db.id)

    def test_get_with_no_sigature(self, url_conversion):
        """
        Removing signature of signed redirect URL. It should get internal server error.
        :return:
        """
        url_without_signature = url_conversion.source_url.split('?')[0]
        response = send_request('get', url_without_signature, '')
        assert response.status_code == 500

    def test_get_with_empty_destination_url(self, url_conversion):
        """
        Making destination URL an empty string here, it should get internal server error.
        :return:
        """
        # forcing destination URL to be empty
        url_conversion.update(destination_url='')
        response = send_request('get', url_conversion.source_url, '')
        assert response.status_code == 500

    def test_get_with_deleted_campaign(self, token, campaign_in_db,
                                       url_conversion):
        """
        Here we first delete the campaign, and then test functionality of process_url_redirect
        by making HTTP GET call to endpoint /v1/redirect. It should give ResourceNotFound Error.
        But candidate should get Internal server error. Hence this test should get internal server
        error.
        """
        PushCampaign.delete(campaign_in_db)
        response = send_request('get', url_conversion.source_url, '')
        assert response.status_code == 500

    def test_get_with_deleted_candidate(self, url_conversion,
                                        test_candidate):
        """
        Here we first delete the candidate, which internally deletes the sms_campaign_send record
        as it uses candidate as primary key. We then test functionality of process_url_redirect
        by making HTTP GET call to endpoint /v1/redirect. It should get ResourceNotFound Error.
        But candidate should only get internal server error. So this test asserts we get internal
        server error.
        """
        Candidate.delete(test_candidate)
        response = send_request('get', url_conversion.source_url, '')
        assert response.status_code == 500

    def test_get_with_deleted_url_conversion(self, url_conversion):
        """
        Here we first delete the url_conversion object. which internally deletes the
        sms_campaign_send record as it uses url_conversion as primary key. We then test
        functionality of process_url_redirect by making HTTP GET call to endpoint /v1/redirect.
        It should get ResourceNotFound Error. But candidate should only get internal server error.
        So this test asserts we get internal server error.
        """
        source_url = url_conversion.source_url
        UrlConversion.delete(url_conversion)
        response = send_request('get', source_url, '')
        assert response.status_code == 500
