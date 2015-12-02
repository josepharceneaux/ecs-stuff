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
from sms_campaign_service.common.models.candidate import PhoneLabel
from sms_campaign_service.common.models.sms_campaign import SmsCampaign

TEST_NUMBER_1 = '+123'
TEST_NUMBER_2 = '+456'


@pytest.fixture()
def auth_token(user_auth, sample_user):
    """
    returns the access token using pytest fixture defined in common/tests/conftest.py
    :param user_auth: fixture in common/tests/conftest.py
    :param sample_user: fixture in common/tests/conftest.py
    """
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    return auth_token_row['access_token']


@pytest.fixture()
def user_phone_1(request, sample_user):
    """
    This creates a user_phone record for sample_user
    :param request:
    :param sample_user: fixture in common/tests/conftest.py
    :return:
    """
    return _create_user_twilio_phone(sample_user, TEST_NUMBER_1)


@pytest.fixture()
def user_phone_2(request, sample_user):
    """
    This creates another user_phone record for sample_user
    :param request:
    :param sample_user: fixture in common/tests/conftest.py
    :return:
    """
    return _create_user_twilio_phone(sample_user, TEST_NUMBER_2)


@pytest.fixture()
def user_phone_3(sample_user_2):
    """
    This creates user_phone record for sample_user_2
    :param sample_user_2:
    :return:
    """
    return _create_user_twilio_phone(sample_user_2, TEST_NUMBER_1)


@pytest.fixture()
def campaign_valid_data():
    """
    This returns the valid data to save an SMS campaign in database
    :return:
    """
    return {"name": "New SMS Campaign",
            "sms_body_text": "HI all, we have few openings at abc.com",
            "frequency_id": 2,
            "added_time": "2015-11-24T08:00:00",
            "send_time": "2015-11-26T08:00:00",
            "stop_time": "2015-11-30T08:00:00",
            }


@pytest.fixture()
def campaign_invalid_data():
    """
    This returns invalid data to save an SMS campaign. 'sms_body_text' required field
    name is modified to 'text' here.
    :return:
    """
    return {"name": "New SMS Campaign",
            "text": "HI all, we have few openings at abc.com",  # invalid key
            "frequency_id": 2,
            "added_time": "2015-11-24T08:00:00",
            "send_time": "2015-11-26T08:00:00",
            "stop_time": "2015-11-30T08:00:00",
            }


@pytest.fixture()
def sms_campaign_of_current_user(campaign_valid_data, user_phone_1):
    return _create_sms_campaign(campaign_valid_data, user_phone_1)


@pytest.fixture()
def sms_campaign_of_other_user(campaign_valid_data, user_phone_3):
    return _create_sms_campaign(campaign_valid_data, user_phone_3)


def _create_sms_campaign(campaign_data, user_phone):
    """
    This creates an SMS campaign in database table "sms_campaign"
    :param campaign_data: data to create campaign
    :param user_phone: user_phone row
    :return:
    """
    campaign_data['user_phone_id'] = user_phone.id
    sms_campaign = SmsCampaign(**campaign_data)
    SmsCampaign.save(sms_campaign)
    return sms_campaign


def _create_user_twilio_phone(user, phone_value):
    """
    This adds user_phone record in database table "user_phone"
    :param user: user row
    :param phone_value: value of phone number
    :return: user_phone row
    """
    phone_label_id = PhoneLabel.phone_label_id_from_phone_label(TWILIO)
    user_phone = UserPhone(user_id=user.id,
                           phone_label_id=phone_label_id,
                           value=phone_value)
    UserPhone.save(user_phone)
    return user_phone
