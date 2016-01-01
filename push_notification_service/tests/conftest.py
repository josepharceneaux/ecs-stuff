"""
Author: Zohaib Ijaz <mzohaib.qc@gmail.com>
"""
from push_notification_service.common.tests.conftest import *
from push_notification_service.common.models.smartlist import *
from push_notification_service.common.models.candidate import *

from faker import Faker
from werkzeug.security import gen_salt

fake = Faker()

# Service specific
from push_notification_service.push_campaign_app.app import app

# This is data to create/update SMS campaign
CREATE_CAMPAIGN_DATA = {"title": "TEST Push Campaign",
                        "content": "Hi all, we have few openings at http://www.abc.com",
                        "url": "http://www.google.com",
                        "smartlist_ids": [1028]
                        }
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
def campaign_data(request):
    """ TODO
    """
    return CREATE_CAMPAIGN_DATA.copy()


@pytest.fixture()
def test_smartlist(request, sample_user, test_candidate):
    """ TODO
    """
    smartlist = Smartlist(user_id=sample_user.id,
                          name=fake.word())
    return smartlist


@pytest.fixture()
def test_smartlist_candidate(request, test_candidate, test_smartlist):
    """ TODO
    """
    smartlist_candidate = SmartlistCandidate(candidate_id=test_candidate.id,
                                             smartlist_id=test_smartlist.id)
    SmartlistCandidate.save(smartlist_candidate)
    return smartlist_candidate


@pytest.fixture()
def test_candidate(request):
    """ TODO
    """
    candidate = Candidate(fisrt_name=fake.first_name(),
                          middle_name=fake.user_name(),
                          last_name=fake.last_name(),
                          status_id=1)
    Candidate.save(candidate)
    candidate_email = CandidateEmail(candidate_id=candidate.id,
                                     email_label_id=1,
                                     email=fake.email(),
                                     is_default=True)
    CandidateEmail.save(candidate_email)
    return candidate