"""
A test for the v1/candidates/client_email_campaign endpoint
"""
import datetime
from flask import json
import requests
# Candidate Service app instance
from candidate_service.candidate_app import app
from candidate_service.common.routes import CandidateApiUrl
from candidate_service.common.tests.sample_data import generate_single_candidate_data
from candidate_service.tests.api.helpers import AddUserRoles
from candidate_service.common.tests.conftest import *
from helpers import (
    response_info, AddUserRoles, request_to_candidate_resource, request_to_candidates_resource
)
# Candidate Service app instance
from candidate_service.candidate_app import app

# Models
from candidate_service.common.models.user import User
from candidate_service.common.models.candidate import CandidateCustomField, CandidateEmail

# Conftest
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import (
    response_info, request_to_candidates_resource,
    request_to_candidate_resource, request_to_candidate_address_resource,
    request_to_candidate_aoi_resource, request_to_candidate_education_resource,
    request_to_candidate_education_degree_resource, request_to_candidate_education_degree_bullet_resource,
    request_to_candidate_custom_field_resource, AddUserRoles
)
from candidate_service.tests.api.candidate_sample_data import generate_single_candidate_data
# Custom errors
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error


class TestClientEmailCampaign(object):

    def test_client_email_campaign(self, access_token_first, user_first, talent_pool):

        AddUserRoles.all_roles(user=user_first)

        # Create Candidate
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = request_to_candidates_resource(access_token_first, 'post', data)

        candidate_id = create_resp.json()['candidates'][0]['id']
        get_resp = request_to_candidate_resource(access_token_first, 'get', candidate_id)

        candidate = json.loads(get_resp.content)['candidate']
        body = {
            'candidates': [candidate],
            'email_subject': 'Email Subject',
            'email_from': 'Samuel L. Jackson',
            'email_reply_to': 'amir@gettalent.com',
            'email_body_html': '<html><body>Email Body</body></html>',
            'email_body_text': 'Plaintext part of email goes here, if any',
            'email_client_id': 101
         }

        email_campaign = requests.post(
            url=CandidateApiUrl.CANDIDATE_CLIENT_CAMPAIGN,
            data=json.dumps(body),
            headers={'Authorization': 'Bearer %s' % access_token_first,
                     'content-type': 'application/json'}
        )
        assert email_campaign.status_code == 201
        email_campaign_sends = json.loads(email_campaign.content)['email_campaign_sends']

        for email_campaign_send in email_campaign_sends:
            assert email_campaign_send['email_campaign_id']
            assert email_campaign_send['candidate_email_address']
            assert email_campaign_send['new_html']
            assert email_campaign_send['new_text']
