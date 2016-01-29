"""
This module contains tests related to Push Campaign RESTful API endpoints.
"""
# Builtin imports
import time

# Application specific imports
from push_campaign_service.tests.test_utilities import *
from push_campaign_service.common.models.push_campaign import *
from push_campaign_service.common.routes import PushCampaignApiUrl
from push_campaign_service.common.campaign_services.custom_errors import CampaignException

URL = PushCampaignApiUrl.SEND


class TestSendCmapign(object):
    # Send a campaign
    # URL: /v1/campaigns/<int:campaign_id>/send [POST]
    def test_send_campaign_with_invalid_token(self, campaign_in_db):
        unauthorize_test('post', URL % campaign_in_db.id, 'invalid_token')

    def test_send_campaign_with_non_existing_campaign(self, token):
        # 404 case. Send a non existing campaign id
        invalid_id = get_non_existing_id(PushCampaign)
        response = send_request('post', URL % invalid_id, token)
        assert response.status_code == NOT_FOUND, 'Push campaign should not exists with this id'

    def test_send_a_camapign(self, token, campaign_in_db, test_smartlist):
        # 200 case: Campaign Sent successfully
        response = send_request('post', URL % campaign_in_db.id, token)
        assert response.status_code == OK, 'Push campaign has not been sent'
        response = response.json()
        assert response['message'] == 'Campaign(id:%s) is being sent to candidates' \
                                      % campaign_in_db.id

        # Wait for 20 seconds to run celery which will send campaign and creates blast
        time.sleep(2 * SLEEP_TIME)
        # Update session to get latest changes in database. Celery has added some records
        db.session.commit()
        # There should be only one blast for this campaign
        blasts = campaign_in_db.blasts.all()
        assert len(blasts) == 1
        assert blasts[0].sends == 1, 'Campaign should have been sent to one candidate'

    def test_send_campaign_without_smartlist(self, token, campaign_in_db):

        response = send_request('post', URL % campaign_in_db.id, token)
        assert response.status_code == INVALID_USAGE, 'Status code is not 500'
        error = response.json()['error']
        assert error['code'] == CampaignException.NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN

    def test_send_campaign_to_smartlist_with_no_candidates(self, token, campaign_in_db,
                                                           test_smartlist_with_no_candidates):

        response = send_request('post', URL % campaign_in_db.id, token)
        assert response.status_code == INVALID_USAGE, 'status code is not 500'
        error = response.json()['error']
        assert error['code'] == CampaignException.NO_CANDIDATE_ASSOCIATED_WITH_SMARTLIST

    def test_campaign_send_with_multiple_smartlists(
            self, token, sample_user, campaign_in_db,
            test_smartlist, test_smartlist_2, test_candidate):
        """
        - This tests the endpoint /v1/campaigns/:id/send

        User auth token is valid, campaign has one smart list associated. Smartlist has one
        candidate.
        :return:
        """
        response = send_request('post', URL % campaign_in_db.id, token)
        assert response.status_code == OK, 'Push campaign has not been sent'
        response = response.json()
        assert response['message'] == 'Campaign(id:%s) is being sent to candidates' \
                                      % campaign_in_db.id

        # Wait for 20 seconds to run celery which will send campaign and creates blast
        time.sleep(2 * SLEEP_TIME)
        # Update session to get latest changes in database. Celery has added some records
        db.session.commit()
        # There should be only one blast for this campaign
        blasts = campaign_in_db.blasts.all()
        assert len(blasts) == 1
        assert blasts[0].sends == 2, 'Campaign should have been sent to two candidate'