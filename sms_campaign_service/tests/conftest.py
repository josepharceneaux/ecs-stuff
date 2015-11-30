# Third Party
import pytest

# App Settings
from sms_campaign_service import init_app
app = init_app()


# Application Specific
# Common conftest
from sms_campaign_service.common.tests.conftest import *

# App specific
from sms_campaign_service.config import TWILIO
from sms_campaign_service.common.models.user import UserPhone
from sms_campaign_service.sms_campaign_base import SmsCampaignBase
from sms_campaign_service.common.models.candidate import PhoneLabel


TEST_NUMBER = '123456789'


@pytest.fixture()
def auth_token(user_auth, sample_user):
    """
    returns the access token using pytest fixture defined in common/tests/conftest.py
    """
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    return auth_token_row['access_token']


@pytest.fixture()
def user_phone(request, sample_user):
    """
    This creates a user_phone record for sample_user
    :param request:
    :param sample_user:
    :return:
    """
    phone_label_id = PhoneLabel.phone_label_id_from_phone_label(TWILIO)
    user_phone_row = SmsCampaignBase.create_or_update_user_phone(sample_user.id,
                                                                 TEST_NUMBER,
                                                                 phone_label_id=phone_label_id)
    return user_phone_row
