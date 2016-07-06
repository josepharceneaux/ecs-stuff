"""
"""

import pytest

from push_campaign_service.common.test_config_manager import load_test_config
from push_campaign_service.common.tests.api_conftest import token_first
                                                             
test_config = load_test_config()


@pytest.fixture(scope="module")
def account_post_data():
    return { 'ats_name' : 'data', 'ats_homepage' : 'data', 'ats_login' : 'data',
             'ats_auth_type' : 'data', 'ats_id' : 'data', 'ats_credentials' : 'data' }
