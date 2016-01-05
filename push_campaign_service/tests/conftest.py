"""
Author: Zohaib Ijaz <mzohaib.qc@gmail.com>
"""
from push_campaign_service.common.tests.conftest import *
from push_campaign_service.common.models.smartlist import *
from push_campaign_service.common.models.candidate import *
from push_campaign_service.common.models.push_notification import *

from faker import Faker

from werkzeug.security import gen_salt

from push_campaign_service.tests.helper_methods import generate_campaign_data

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
def test_campaign(request, sample_user, campaign_data):
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
            db.session.commit()
            PushCampaign.delete(data['id'])
    request.addfinalizer(tear_down)
    return data


@pytest.fixture(scope='function')
def test_smartlist(request, sample_user, test_candidate, test_campaign):
    """ TODO
    """
    smartlist = Smartlist(user_id=sample_user.id,
                          name=fake.word())
    Smartlist.save(smartlist)

    smartlist_candidate = SmartlistCandidate(candidate_id=test_candidate.id,
                                             smartlist_id=smartlist.id)
    SmartlistCandidate.save(smartlist_candidate)

    push_smartlist = PushCampaignSmartlist(smartlist_id=smartlist.id,
                                           campaign_id=test_campaign.id)
    PushCampaignSmartlist.save(push_smartlist)

    def tear_down():
            Smartlist.delete(smartlist)
    request.addfinalizer(tear_down)
    return smartlist


# @pytest.fixture()
# def test_push_campaign_smartlist(request, test_smartlist, test_campaign):
#     """ TODO
#     """
#     push_smartlist = PushCampaignSmartlist(smartlist_id=test_smartlist.id,
#                                            campaign_id=test_campaign.id)
#     PushCampaignSmartlist.save(push_smartlist)
#
#     def tear_down():
#             PushCampaignSmartlist.delete(push_smartlist)
#     request.addfinalizer(tear_down)
#     return push_smartlist


# @pytest.fixture()
# def test_candidate_device(request, test_candidate):
#     """ TODO
#     """
#     device = CandidateDevice(candidate_id=test_candidate.id,
#                              one_signal_device_id='56c1d574-237e-4a41-992e-c0094b6f2ded',
#                              registered_at=datetime.datetime.utcnow())
#     CandidateDevice.save(device)
#     return device


# @pytest.fixture()
# def test_smartlist_candidate(request, test_candidate, test_smartlist):
#     """ TODO
#     """
#     smartlist_candidate = SmartlistCandidate(candidate_id=test_candidate.id,
#                                              smartlist_id=test_smartlist.id)
#     SmartlistCandidate.save(smartlist_candidate)
#
#     def tear_down():
#         SmartlistCandidate.delete(smartlist_candidate)
#     request.addfinalizer(tear_down)
#     return smartlist_candidate


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

    device = CandidateDevice(candidate_id=candidate.id,
                             one_signal_device_id='56c1d574-237e-4a41-992e-c0094b6f2ded',
                             registered_at=datetime.datetime.utcnow())
    CandidateDevice.save(device)

    def tear_down():
        Candidate.delete(candidate)
    request.addfinalizer(tear_down)
    return candidate

