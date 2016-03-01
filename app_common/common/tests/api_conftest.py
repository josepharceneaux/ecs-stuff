"""
Author: Zohaib Ijaz <mzohaib.qc@gmail.com>

This module contains fixtures to be used in tests.

Some fixtures are created twice. First one with 'user_first' as owner and those that
are postfix with  '_second' are owned by 'user_second'. 'user_first' belongs to domain 1 and
'user_second' belongs to another domain say domain 2.

A user can update or delete objects that are owned by a user that is from same domain. so there
are some fixture that are postfixed with '_same_domain', actually belong to domain 1
but user is different.

"""
import pytest

from ..test_config_manager import load_test_config
from ..utils.test_utils import get_token, get_user, add_roles, remove_roles

ROLES = ['CAN_ADD_USERS', 'CAN_GET_USERS', 'CAN_DELETE_USERS', 'CAN_ADD_TALENT_POOLS',
         'CAN_GET_TALENT_POOLS', 'CAN_DELETE_TALENT_POOLS', 'CAN_ADD_TALENT_POOLS_TO_GROUP',
         'CAN_ADD_CANDIDATES', 'CAN_GET_CANDIDATES', 'CAN_DELETE_CANDIDATES',
         'CAN_ADD_TALENT_PIPELINE_SMART_LISTS', 'CAN_DELETE_TALENT_PIPELINE_SMART_LISTS']

test_config = load_test_config()


@pytest.fixture()
def token_first():
    """
    Au Authentication token for user_first.
    :return:
    """
    info = test_config['USER_FIRST']
    return get_token(info)


@pytest.fixture()
def token_same_domain(request):
    """
    Authentication token for user that belongs to same domain as user_first.
    :param request:
    :return:
    """
    info = test_config['USER_SAME_DOMAIN']
    return get_token(info)


@pytest.fixture()
def token_second(request):
    """
     Authentication token for user_second.
    :param request:
    :return:
    """
    info = test_config['USER_SECOND']
    return get_token(info)


@pytest.fixture()
def user_first(request, token_first):
    """
    This fixture will be used to get user from UserService using id from config.
    :param request: request object
    :param token_first: auth token for first user
    :return: user dictionary object
    """
    user_id = test_config['USER_FIRST']['user_id']
    user = get_user(user_id, token_first)
    add_roles(user_id, ROLES, token_first)

    def tear_down():
        remove_roles(user_id, ROLES, token_first)
    request.addfinalizer(tear_down)
    return user


@pytest.fixture()
def user_second(request, token_second):
    """
    This fixture will be used to get user from UserService using id from config.
    :param request: request object
    :param token_second: auth token for first user
    :return: user dictionary object
    """
    user_id = test_config['USER_SECOND']['user_id']
    user = get_user(user_id, token_second)
    add_roles(user_id, ROLES, token_second)

    def tear_down():
        remove_roles(user_id, ROLES, token_second)

    request.addfinalizer(tear_down)
    return user


@pytest.fixture()
def user_same_domain(request, token_same_domain):
    """
    This fixture will be used to get user from UserService using id from config.
    :param request: request object
    :param token_same_domain: auth token for a user from same domain as of user first
    :return: user dictionary object
    """
    user_id = test_config['USER_SAME_DOMAIN']['user_id']
    user = get_user(user_id, token_same_domain)
    add_roles(user_id, ROLES, token_same_domain)

    def tear_down():
        remove_roles(user_id, ROLES, token_same_domain)

    request.addfinalizer(tear_down)
    return user

