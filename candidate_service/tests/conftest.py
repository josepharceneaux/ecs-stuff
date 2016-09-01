"""
File contains fixtures to help candidate service's functional tests
"""
import pytest
import requests
from candidate_service.candidate_app import app
from candidate_service.candidate_app import db
from candidate_service.common.tests.conftest import candidate_first, fake, domain_aois, domain_custom_fields

from candidate_service.common.utils.test_utils import send_request, response_info
from candidate_service.common.routes import CandidateApiUrl

from api.candidate_sample_data import generate_single_candidate_data


@pytest.fixture(params=["", " ", "Test Email", None])
def client_email_campaign_subject(request):
    """
    This fixture is used to return to us the possible values that can be set as
     the email subject in the POST request.
    """
    return request.param


@pytest.fixture()
def notes_first(user_first, candidate_first, access_token_first):
    """
    Fixture will create 3 notes for candidate first
    """
    data = {'notes': [
        {'title': fake.word(), 'comment': fake.bs()},
        {'title': fake.word(), 'comment': fake.bs()}
    ]}
    create_resp = send_request('post', CandidateApiUrl.NOTES % candidate_first.id, access_token_first, data)
    print response_info(create_resp)
    return dict(user=user_first, candidate=candidate_first, data=data, notes=create_resp.json())


@pytest.fixture()
def test_candidate_1(access_token_first, talent_pool, domain_aois, domain_custom_fields, domain_source):
    """
    Fixture will create a full candidate profile in domain_first (owned by user_first)
    :rtype: dict
    """
    # Data containing candidate's full profile
    data = generate_single_candidate_data(talent_pool_ids=[talent_pool.id],
                                          areas_of_interest=domain_aois,
                                          custom_fields=domain_custom_fields,
                                          source_id=domain_source['source']['id'])

    # Create candidate via the API
    create_response = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
    assert create_response.status_code == requests.codes.CREATED

    # Retrieve candidate
    candidate_id = create_response.json()['candidates'][0]['id']
    get_response = send_request('get', CandidateApiUrl.CANDIDATE % str(candidate_id), access_token_first)
    assert get_response.status_code == requests.codes.OK

    return get_response.json()
