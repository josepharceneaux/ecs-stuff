"""
A test for the v1/candidates/client_email_campaign endpoint
"""

from candidate_service.common.routes import CandidateApiUrl

# Candidate Service app instance
from candidate_service.candidate_app import app

# Conftest
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import (
    request_to_candidates_resource,
    request_to_candidate_resource, AddUserRoles
)
from candidate_service.tests.api.candidate_sample_data import generate_single_candidate_data


class TestClientEmailCampaign(object):

    def test_client_email_campaign(self, access_token_first, user_first, talent_pool):

        # give the test user roles to perform all needed actions
        AddUserRoles.all_roles(user=user_first)

        # Create a Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_candidate_response = request_to_candidates_resource(access_token_first, 'post', data)

        # Get Candidate via ID
        candidate_id = create_candidate_response.json()['candidates'][0]['id']
        get_candidate_response = request_to_candidate_resource(access_token_first, 'get', candidate_id)

        # create POST request body
        candidate = json.loads(get_candidate_response.content)['candidate']
        body = {
            'candidates': [candidate],
            'email_subject': 'Email Subject',
            'email_from': 'Samuel L. Jackson',
            'email_reply_to': 'amir@gettalent.com',
            'email_body_html': '<html><body>Email Body</body></html>',
            'email_body_text': 'Plaintext part of email goes here, if any',
            'email_client_id': 101
         }

        # send the post request to /v1/candidates/client-email-campaign
        email_campaign = requests.post(
            url=CandidateApiUrl.CANDIDATE_CLIENT_CAMPAIGN,
            data=json.dumps(body),
            headers={'Authorization': 'Bearer %s' % access_token_first,
                     'content-type': 'application/json'}
        )
        # assert it is created and contains email campaign sends objects
        assert email_campaign.status_code == 201
        email_campaign_sends = json.loads(email_campaign.content)['email_campaign_sends']

        # assert each email campaign send has an ID, an email address to send to and new_html to send to the user
        for email_campaign_send in email_campaign_sends:
            assert email_campaign_send['email_campaign_id']
            assert email_campaign_send['candidate_email_address']
            assert email_campaign_send['new_html']
            assert email_campaign_send['new_text']
