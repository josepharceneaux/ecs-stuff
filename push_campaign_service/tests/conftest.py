"""
Author: Zohaib Ijaz <mzohaib.qc@gmail.com>
"""
from datetime import datetime

from push_campaign_service.common.tests.conftest import (user_auth, sample_user,
                                                         test_domain, test_org, test_culture)
from push_campaign_service.common.routes import PushCampaignApiUrl, SchedulerApiUrl
from push_campaign_service.common.models.db import db
from push_campaign_service.common.models.smartlist import Smartlist, SmartlistCandidate
from push_campaign_service.common.models.candidate import (Candidate,
                                                           CandidateDevice,
                                                           CandidateEmail)


from push_campaign_service.common.models.push_campaign import (PushCampaign,
                                                               PushCampaignSmartlist)
from push_campaign_service.common.utils.handy_functions import create_test_user

from faker import Faker
import pytest

from push_campaign_service.modules.constants import TEST_DEVICE_ID
from push_campaign_service.tests.test_utilities import (generate_campaign_data, send_request,
                                                        generate_campaign_schedule_data)

fake = Faker()
# Service specific
from push_campaign_service.push_campaign_app.app import app

# This is data to create/update SMS campaign
# This is data to schedule an SMS campaign
CAMPAIGN_SCHEDULE_DATA = {"frequency_id": 2,
                          "start_datetime": "2015-11-26T08:00:00Z",
                          "end_datetime": "2015-11-30T08:00:00Z"}


@pytest.fixture(params=['valid_token', 'invalid_token'])
def auth_data(request, user_auth, sample_user):
    """
    returns the access token using pytest fixture defined in common/tests/conftest.py
    :param user_auth: fixture in common/tests/conftest.py
    :param sample_user: fixture in common/tests/conftest.py
    :return token, is_valid (a tuple)
    """
    if request.param == 'valid_token':
        auth_token_obj = user_auth.get_auth_token(sample_user, get_bearer_token=True)
        return auth_token_obj['access_token'], True
    else:
        return 'invalid_token', False


@pytest.fixture()
def token(request, user_auth, sample_user):
    """
    returns the access token for a different user so that we can test forbidden error etc.
    :param user_auth: fixture in common/tests/conftest.py
    :param sample_user: fixture in common/tests/conftest.py
    :return token
    """
    auth_token_obj = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    return auth_token_obj['access_token']


@pytest.fixture()
def campaign_in_db(request, sample_user, campaign_data):
    campaign_data['user_id'] = sample_user.id
    campaign = PushCampaign(**campaign_data)
    PushCampaign.save(campaign)

    def tear_down():
        PushCampaign.delete(campaign)
    request.addfinalizer(tear_down)
    return campaign


@pytest.fixture(scope='function')
def campaign_data(request):
    """ Generate random data for a push campaign
    """
    data = generate_campaign_data()

    def tear_down():
        if 'id' in data:
            PushCampaign.session.commit()
            PushCampaign.delete(data['id'])
    request.addfinalizer(tear_down)
    return data


@pytest.fixture(scope='function')
def test_smartlist(request, sample_user, test_candidate, test_candidate_device, campaign_in_db):
    """ TODO
    """
    smartlist = Smartlist(user_id=sample_user.id,
                          name=fake.word())
    Smartlist.save(smartlist)

    smartlist_candidate = SmartlistCandidate(candidate_id=test_candidate.id,
                                             smartlist_id=smartlist.id)
    SmartlistCandidate.save(smartlist_candidate)

    push_smartlist = PushCampaignSmartlist(smartlist_id=smartlist.id,
                                           campaign_id=campaign_in_db.id)
    PushCampaignSmartlist.save(push_smartlist)

    def tear_down():
            Smartlist.delete(smartlist)
    request.addfinalizer(tear_down)
    return smartlist


@pytest.fixture(scope='function')
def test_smartlist_with_no_candidates(request, sample_user, campaign_in_db):
    """ TODO
    """
    smartlist = Smartlist(user_id=sample_user.id,
                          name=fake.word())
    Smartlist.save(smartlist)

    push_smartlist = PushCampaignSmartlist(smartlist_id=smartlist.id,
                                           campaign_id=campaign_in_db.id)
    PushCampaignSmartlist.save(push_smartlist)

    def tear_down():
            Smartlist.delete(smartlist)
    request.addfinalizer(tear_down)
    return smartlist


@pytest.fixture()
def campaign_blasts_count(request, test_smartlist, campaign_in_db, token):
    """ TODO
    """

    blasts_counts = 3
    # campaign_obj = PushCampaignBase(user_id=sample_user.id)
    for num in range(blasts_counts):
        response = send_request('post', PushCampaignApiUrl.SEND % campaign_in_db.id, token)
        # campaign_obj.process_send(campaign_in_db)
        assert response.status_code == 200
    return blasts_counts


@pytest.fixture()
def schedule_a_campaign(request, test_smartlist, campaign_in_db, token):
    """ TODO
    """
    task_id = None
    data = generate_campaign_schedule_data()
    response = send_request('post', PushCampaignApiUrl.SCHEDULE % campaign_in_db.id, token, data)
    assert response.status_code == 200
    response = response.json()
    task_id = response['task_id']

    def fin():
        send_request('delete', SchedulerApiUrl.TASK % task_id, token)

    request.addfinalizer(fin)
    return data


@pytest.fixture(scope='function')
def test_candidate(request):
    """ TODO
    """
    candidate = Candidate(first_name=fake.first_name(),
                          middle_name=fake.user_name(),
                          last_name=fake.last_name(),
                          candidate_status_id=1)
    Candidate.save(candidate)
    candidate_email = CandidateEmail(candidate_id=candidate.id,
                                     email_label_id=1,
                                     address=fake.email(),
                                     is_default=True)
    CandidateEmail.save(candidate_email)

    def tear_down():
        Candidate.delete(candidate)
    request.addfinalizer(tear_down)
    return candidate


@pytest.fixture(scope='function')
def test_candidate_device(request, test_candidate):
    """ TODO
    """
    device = CandidateDevice(candidate_id=test_candidate.id,
                             one_signal_device_id=TEST_DEVICE_ID,
                             registered_at=datetime.utcnow())
    CandidateDevice.save(device)

    return device



