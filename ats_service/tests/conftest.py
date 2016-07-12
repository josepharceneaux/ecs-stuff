"""
Fixtures particular to ATS testing.
"""

import pytest

from push_campaign_service.common.test_config_manager import load_test_config
from push_campaign_service.common.tests.api_conftest import token_first
from ats_service.common.tests.conftest import *

test_config = load_test_config()


@pytest.fixture(scope="module")
def account_post_data():
    """
    Data used to create an ATS account.

    :rtype dict
    """
    return { 'ats_name' : 'A New ATS', 'ats_homepage' : 'https://newats.com', 'ats_login' : 'https://newats.com',
             'ats_auth_type' : 'Basic', 'ats_id' : 'id on ATS', 'ats_credentials' : 'My ATS Credentials' }
