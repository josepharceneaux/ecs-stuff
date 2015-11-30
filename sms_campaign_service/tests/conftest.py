# Third Party
import pytest

# App Settings
from sms_campaign_service import init_app
app = init_app()


# Application Specific
from sms_campaign_service.common.tests.conftest import *


@pytest.fixture()
def auth_token(user_auth, sample_user):
    """
    returns the access token using pytest fixture defined in common/tests/conftest.py
    """
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    return auth_token_row['access_token']
