"""
Fixtures particular to ATS testing.
"""

import pytest

from ats_service.common.test_config_manager import load_test_config
from ats_service.common.tests.api_conftest import token_first
from ats_service.common.tests.conftest import *

test_config = load_test_config()


@pytest.fixture(scope="module")
def account_post_data():
    """
    Data used to create an ATS account.

    :rtype dict
    """
    return { 'ats_name' : 'Workday', 'ats_homepage' : 'https://newats.com', 'ats_login' : 'https://https://faux-workday.gettalent.com/authenticate',
             'ats_auth_type' : 'Basic', 'ats_id' : 'id on ATS', 'ats_credentials' : 'My ATS Credentials' }


@pytest.fixture(scope="module")
def candidate_post_data():
    """
    Data used to create an ATS candidate.

    :rtype dict:
    """
    return {'ats_remote_id': 'some_id', 'ats_account_id': 'another_id', 'ats_remote_id': 'yaid',
            'active': 'True', 'profile_json': '{ "some" : "json" } '}
