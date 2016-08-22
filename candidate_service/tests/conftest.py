import pytest
from candidate_service.candidate_app import app
from candidate_service.candidate_app import db
from candidate_service.common.tests.conftest import candidate_first, fake
from candidate_service.common.tests.api_conftest import token_first, candidate_device_first

from candidate_service.common.utils.test_utils import send_request, response_info
from candidate_service.common.routes import CandidateApiUrl

from candidate_service.common.models.candidate import CandidateDevice



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
