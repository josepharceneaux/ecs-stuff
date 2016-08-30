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

from candidate_service.common.models.candidate import CandidateDevice
from candidate_service.common.test_config_manager import load_test_config

from api.candidate_sample_data import generate_single_candidate_data


test_config = load_test_config()
PUSH_DEVICE_ID = test_config['PUSH_CONFIG']['device_id_1']


@pytest.fixture()
def associate_device(request, candidate_first):
    """
    This fixture is being used to associate a device with candidate.
    :param request:
    :return:
    """
    device = CandidateDevice(one_signal_device_id=PUSH_DEVICE_ID,
                             candidate_id=candidate_first.id)
    db.session.add(device)
    db.session.commit()

    def tear_down():
        CandidateDevice.query.filter_by(candidate_id=candidate_first.id,
                                        one_signal_device_id=PUSH_DEVICE_ID).delete()

    request.addfinalizer(tear_down)
    return device


@pytest.fixture()
def delete_device(request):
    """
    This fixture is being used to delete device association with candidate at the end of a test.
    It is because, if a one_signal_device_id is already associated to a candidate in same domain
    then it can not be assigned to another candidate. So we are deleting this entry before next test.
    :param request:
    :return:
    """
    # this data dict will be modified at the end of test.
    data = {}

    def tear_down():
        if 'device_id' in data and 'candidate_id' in data:
            device_id = data['device_id']
            candidate_id = data['candidate_id']
            CandidateDevice.query.filter_by(one_signal_device_id=device_id,
                                            candidate_id=candidate_id).delete()

    request.addfinalizer(tear_down)
    return data


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
