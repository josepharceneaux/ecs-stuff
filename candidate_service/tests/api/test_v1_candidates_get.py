"""
Test cases for CandidateResource/get()
"""
# Third party imports
from sqlalchemy import and_, or_

# Candidate Service app instance
# Conftest
from candidate_sample_data import generate_single_candidate_data
from candidate_service.common.models.email_campaign import EmailCampaignSend, EmailCampaignSendUrlConversion, \
    TRACKING_URL_TYPE, TEXT_CLICK_URL_TYPE
from candidate_service.common.models.misc import UrlConversion
from candidate_service.common.routes import EmailCampaignApiUrl
from candidate_service.common.tests.conftest import *
from candidate_service.common.utils.test_utils import send_request, response_info
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error
from candidate_service.common.campaign_services.tests.modules.email_campaign_helper_functions import \
    create_data_for_campaign_creation, assert_campaign_send


class TestGetCandidate(object):
    @staticmethod
    def create_candidate(access_token_first, talent_pool, data=None):
        if data is None:
            data = generate_single_candidate_data([talent_pool.id])
        return send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)

    def test_create_candidate_with_empty_input(self, access_token_first):
        """
        Test: Retrieve user's candidate(s) by providing empty string for data
        Expect: 400
        """
        # Create candidate
        resp = requests.post(url=CandidateApiUrl.CANDIDATES,
                             headers={'Authorization': 'Bearer {}'.format(access_token_first),
                                      'content-type': 'application/json'})
        print response_info(resp)
        assert resp.status_code == 400
        assert resp.json()['error']['code'] == custom_error.MISSING_INPUT

    def test_create_candidate_with_non_json_data(self, access_token_first, talent_pool):
        """
        Test: Send post request with non json data
        Expect: 400
        """
        # Create candidate
        resp = requests.post(
            url=CandidateApiUrl.CANDIDATES,
            headers={'Authorization': 'Bearer {}'.format(access_token_first),
                     'content-type': 'application/xml'},
            data=generate_single_candidate_data([talent_pool.id])
        )
        print response_info(resp)
        assert resp.status_code == 400
        assert resp.json()['error']['code'] == custom_error.INVALID_INPUT

    def test_get_candidate_without_authed_user(self, access_token_first, talent_pool):
        """
        Test:   Attempt to retrieve candidate with no access token
        Expect: 401
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        resp_dict = create_resp.json()
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve Candidate
        candidate_id = resp_dict['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, None)
        print response_info(get_resp)
        assert get_resp.status_code == 401
        assert get_resp.json()['error']['code'] == 11 # Bearer token not found

    def test_get_candidate_without_id_or_email(self, access_token_first, talent_pool):
        """
        Test:   Attempt to retrieve candidate without providing ID or Email
        Expect: 400
        """
        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Retrieve Candidate without providing ID or Email
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % None, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 400
        assert get_resp.json()['error']['code'] == custom_error.INVALID_EMAIL

    def test_get_candidate_from_forbidden_domain(self, access_token_first, talent_pool, access_token_second):
        """
        Test:   Attempt to retrieve a candidate outside of logged-in-user's domain
        Expect: 403 status_code
        """

        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        resp_dict = create_resp.json()
        print response_info(create_resp)

        # Retrieve candidate from a different domain
        candidate_id = resp_dict['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_second)
        print response_info(get_resp)
        assert get_resp.status_code == 403
        assert get_resp.json()['error']['code'] == custom_error.CANDIDATE_FORBIDDEN

    def test_get_candidate_via_invalid_email(self, access_token_first, user_first):
        """
        Test:   Retrieve candidate via an invalid email address
        Expect: 400
        """
        # Retrieve Candidate via candidate's email
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % 'bad_email.com', access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 400
        assert get_resp.json()['error']['code'] == custom_error.INVALID_EMAIL

    def test_get_candidate_via_id_and_email(self, access_token_first, user_first, talent_pool):
        """
        Test:   Retrieve candidate via candidate's ID and candidate's Email address
        Expect: 200 in both cases
        """
        # Create candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        resp_dict = create_resp.json()

        # Retrieve candidate
        candidate_id = resp_dict['candidates'][0]['id']
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)

        # Candidate Email
        candidate_email = get_resp.json()['candidate']['emails'][0]['address']

        # Get candidate via Candidate ID
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        resp_dict = get_resp.json()
        print response_info(get_resp)
        assert get_resp.status_code == 200
        assert isinstance(resp_dict, dict)

        # Get candidate via Candidate Email
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_email, access_token_first)
        resp_dict = get_resp.json()
        print response_info(get_resp)
        assert get_resp.status_code == 200
        assert isinstance(resp_dict, dict)

    def test_get_non_existing_candidate(self, access_token_first, talent_pool):
        """
        Test: Attempt to retrieve a candidate that doesn't exists or is web-hidden
        """
        # Retrieve non existing candidate
        last_candidate = Candidate.query.order_by(Candidate.id.desc()).first()
        non_existing_candidate_id = last_candidate.id * 100
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % str(non_existing_candidate_id), access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 404
        assert get_resp.json()['error']['code'] == custom_error.CANDIDATE_NOT_FOUND

        # Create Candidate and archive it
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        candidate_id = create_resp.json()['candidates'][0]['id']
        archive_data = {'candidates': [{'id': candidate_id, 'archive': True}]}
        send_request('patch', CandidateApiUrl.CANDIDATES, access_token_first, archive_data)

        # Retrieve archived candidate
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 404
        assert get_resp.json()['error']['code'] == custom_error.CANDIDATE_IS_ARCHIVED

    def test_get_candidate_assert_timeline(self, access_token_first, user_first,
                                    candidate_first, talent_pipeline, smartlist_first):
        """
        This test creates candidate and sends an email campaign to candidate twice. After that gets candidate 
        and asserts its contact history(timeline)
        """
        url = EmailCampaignApiUrl.SEND
        campaign_data = create_data_for_campaign_creation(access_token_first, talent_pipeline)
        campaign_data['body_html'] = "<html><body><a href=\"{}\">Email campaign test</a></body></html>".format(
            fake.url())
        response = send_request('post', EmailCampaignApiUrl.CAMPAIGNS, access_token_first, campaign_data)
        db.session.commit()
        campaign = EmailCampaign.get(response.json()['campaign']['id'])
        assert_campaign_send(response, campaign, user_first.id, 1, expected_status=codes.CREATED, email_client=True,
                             delete_url_conversion=False)
        email_campaign_send = EmailCampaignSend.filter_by_keywords(campaign_id=campaign.id)
        response = send_request('post', url % campaign.id, access_token_first)
        assert response.status_code == codes.OK, 'Expected status: {}, Found: {}'.format(codes.OK, response.status_code)
        db.session.commit()
        assert_campaign_send(response, campaign, user_first.id, blasts_count=2, total_sends=2,
                             expected_status=codes.OK, email_client=True, delete_url_conversion=False)

        email_campaign_sends = EmailCampaign.get(campaign.id).sends.all()
        for campaign_send in email_campaign_sends:
            # Getting url_conversion ids and setting hit_count = 1 to check event_type='email_open' in timeline
            url_conversion_ids = db.session.query(
                EmailCampaignSendUrlConversion.url_conversion_id).filter(
                EmailCampaignSendUrlConversion.email_campaign_send_id == campaign_send.id, (
                    or_(EmailCampaignSendUrlConversion.type == TEXT_CLICK_URL_TYPE,
                        EmailCampaignSendUrlConversion.type == TRACKING_URL_TYPE))).all()[0]
            assert len(url_conversion_ids) == 1, 'Expected length of url conversion ids: 1, Found: {}'.\
                format(len(url_conversion_ids))
            url_conversion = UrlConversion.get(url_conversion_ids[0])
            response = requests.get(url_conversion.source_url)
            assert response.status_code == codes.OK, 'Expected status: {}, Found: {}'.format(codes.OK, response.status_code)

        db.session.commit()
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % str(email_campaign_send[0].candidate_id),
                                access_token_first)
        assert get_resp.status_code == codes.OK, 'Expected status: {}, Found: {}'.format(codes.OK, response.status_code)
        assert len(get_resp.json()['candidate']['contact_history']['timeline']) == 4, 'Expected length: 4, got: {}'\
            .format(len(get_resp.json()['candidate']['contact_history']['timeline']))
