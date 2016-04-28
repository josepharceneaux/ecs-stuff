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

from redo import retry
from requests import codes as HttpStatus

from ..test_config_manager import load_test_config
from ..utils.test_utils import get_user, add_roles, \
    create_candidate, get_candidate, delete_candidate, create_smartlist, delete_smartlist, \
    delete_talent_pool, create_talent_pools, get_talent_pool, get_talent_pipeline, delete_talent_pipeline, \
    create_talent_pipelines, get_smartlist_candidates

ROLES = ['CAN_ADD_USERS', 'CAN_GET_USERS', 'CAN_DELETE_USERS', 'CAN_ADD_TALENT_POOLS',
         'CAN_GET_TALENT_POOLS', 'CAN_DELETE_TALENT_POOLS', 'CAN_ADD_TALENT_POOLS_TO_GROUP',
         'CAN_ADD_CANDIDATES', 'CAN_GET_CANDIDATES', 'CAN_DELETE_CANDIDATES',
         'CAN_ADD_TALENT_PIPELINE_SMART_LISTS', 'CAN_DELETE_TALENT_PIPELINE_SMART_LISTS',
         'CAN_ADD_TALENT_PIPELINES']

test_config = load_test_config()


@pytest.fixture(scope='session')
def token_first():
    """
    Au Authentication token for user_first.
    """
    return test_config['USER_FIRST']['token']


@pytest.fixture(scope='session')
def token_same_domain(request):
    """
    Authentication token for user that belongs to same domain as user_first.
    """
    return test_config['USER_SAME_DOMAIN']['token']


@pytest.fixture(scope='session')
def token_second(request):
    """
     Authentication token for user_second.
    """
    return test_config['USER_SECOND']['token']


@pytest.fixture(scope='session')
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
    return user


@pytest.fixture(scope='session')
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
    return user


@pytest.fixture(scope='session')
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
    return user


@pytest.fixture(scope='function')
def candidate_first(request, talent_pool, token_first, user_first):
    """
    This fixture created a test candidate in domain first and it will be deleted
    after test has run.
    :param request: request object
    :param talent_pool: talent pool dict object associated to user_first
    """
    response = create_candidate(talent_pool['id'], token_first)
    candidate_id = response['candidates'][0]['id']
    response = retry(get_candidate, max_sleeptime=60, sleeptime=3, attempts=20, sleepscale=1,
                     retry_exceptions=(AssertionError,), args=(candidate_id, token_first))
    candidate = response['candidate']

    def tear_down():
        delete_candidate(candidate_id, token_first,
                         expected_status=(HttpStatus.NO_CONTENT, HttpStatus.NOT_FOUND))

    request.addfinalizer(tear_down)
    return candidate


@pytest.fixture(scope='function')
def candidate_same_domain(request, user_same_domain, talent_pool, token_same_domain):
    """
    This fixture created a candidate in domain first  and it will be deleted
    after test has run.
    :param request: request object
    :param talent_pool: talent pool dict object
    :param token_same_domain: authentication token
    """
    response = create_candidate(talent_pool['id'], token_same_domain)
    candidate_id = response['candidates'][0]['id']
    response = retry(get_candidate, max_sleeptime=60, sleeptime=3, attempts=20, sleepscale=1,
                     retry_exceptions=(AssertionError,), args=(candidate_id, token_same_domain))
    candidate = response['candidate']

    def tear_down():
        delete_candidate(candidate_id, token_same_domain,
                         expected_status=(HttpStatus.NO_CONTENT, HttpStatus.NOT_FOUND))

    request.addfinalizer(tear_down)
    return candidate


@pytest.fixture(scope='function')
def candidate_second(request, token_second, talent_pool_second, user_second):
    """
    This fixture created a test candidate using for domain second and it will be deleted
    after test has run.
    :param request: request object
    :param token_second: authentication token for user_second
    :param talent_pool_second: talent pool dict object from domain second
    """
    response = create_candidate(talent_pool_second['id'], token_second)
    candidate_id = response['candidates'][0]['id']
    response = retry(get_candidate, max_sleeptime=60, sleeptime=3, attempts=20, sleepscale=1,
                     retry_exceptions=(AssertionError,), args=(candidate_id, token_second))
    candidate = response['candidate']

    def tear_down():
        delete_candidate(candidate_id, token_second,
                         expected_status=(HttpStatus.NO_CONTENT, HttpStatus.NOT_FOUND))

    request.addfinalizer(tear_down)
    return candidate


@pytest.fixture()
def talent_pipeline(request, token_first, user_first):
    """
    This fixture created a talent pipeline that is associated to user_first
    :param request: request object
    :param token_first: authentication token for user_first
    """
    talent_pipelines = create_talent_pipelines(token_first, talent_pool['id'])
    talent_pipeline_id = talent_pipelines['talent_pipelines'][0]
    talent_pipeline_obj = get_talent_pipeline(talent_pipeline_id, token_first)['talent_pipeline']

    def tear_down():
        delete_talent_pipeline(talent_pipeline_id, token_first,
                               expected_status=(HttpStatus.OK, HttpStatus.NOT_FOUND))

    request.addfinalizer(tear_down)
    return talent_pipeline_obj


@pytest.fixture(scope='function')
def smartlist_first(request, token_first, user_first, candidate_first, talent_pool):
    """
    This fixture creates a smartlist that contains a candidate from domain_first.
    :param request: request objecttalent_pipelines = create_talent_pipelines(token_first, talent_pool['id'])
    talent_pipeline_id = talent_pipelines['talent_pipelines'][0]
    talent_pipeline_obj = get_talent_pipeline(talent_pipeline_id, token_first)['talent_pipeline']
    :param candidate_first: candidate object
    :param token_first: access token for user_first
    :return: smartlist objects (dict)
    """
    talent_pipelines = create_talent_pipelines(token_first, talent_pool['id'])
    talent_pipeline_id = talent_pipelines['talent_pipelines'][0]
    candidate_ids = [candidate_first['id']]
    smartlist = create_smartlist(candidate_ids, talent_pipeline_id, token_first)['smartlist']
    smartlist_id = smartlist['id']
    retry(get_smartlist_candidates, attempts=20, sleeptime=3, max_sleeptime=60,
          sleepscale=1, retry_exceptions=(AssertionError,), args=(smartlist_id, token_first),
          kwargs={'candidates_count': 1})

    def tear_down():
        delete_smartlist(smartlist_id, token_first,
                         expected_status=(HttpStatus.OK, HttpStatus.NOT_FOUND))

    request.addfinalizer(tear_down)
    return smartlist


@pytest.fixture(scope='function')
def smartlist_second(request, token_second, user_second, candidate_second, talent_pool_second):
    """
    This fixture creates a smartlist that is associated contains a candidate from domain_second.
    :param request: request object
    :param token_second: access token for user_second
    :param candidate_second: candidate object
    :return: smartlist object
    """
    talent_pipelines = create_talent_pipelines(token_second, talent_pool_second['id'])
    talent_pipeline_id = talent_pipelines['talent_pipelines'][0]
    candidate_ids = [candidate_second['id']]
    smartlist = create_smartlist(candidate_ids, talent_pipeline_id, token_second)['smartlist']
    smartlist_id = smartlist['id']
    retry(get_smartlist_candidates, attempts=20, sleeptime=3, max_sleeptime=60,
          sleepscale=1, retry_exceptions=(AssertionError,), args=(smartlist_id, token_second),
          kwargs={'candidates_count': 1})

    def tear_down():
        delete_smartlist(smartlist_id, token_second,
                         expected_status=(HttpStatus.OK, HttpStatus.NOT_FOUND))
    request.addfinalizer(tear_down)
    return smartlist


@pytest.fixture(scope='function')
def smartlist_same_domain(request, token_same_domain, user_same_domain, candidate_same_domain, talent_pool):
    """
    This fixture creates a smartlist that belongs to "user_same_domain"
    :param request:
     same domain functionality
    :param token_same_domain: auth token for user_same_domain
    :param candidate_same_domain: candidate from domain as of user_same_domain
    :return: smartlist object
    """
    talent_pipelines = create_talent_pipelines(token_same_domain, talent_pool['id'])
    talent_pipeline_id = talent_pipelines['talent_pipelines'][0]
    candidate_ids = [candidate_same_domain['id']]
    smartlist = create_smartlist(candidate_ids, talent_pipeline_id, token_same_domain)['smartlist']
    smartlist_id = smartlist['id']
    retry(get_smartlist_candidates, attempts=20, sleeptime=3, max_sleeptime=60,
          sleepscale=1, retry_exceptions=(AssertionError,), args=(smartlist_id, token_same_domain),
          kwargs={'candidates_count': 1})

    def tear_down():
        delete_smartlist(smartlist_id, token_same_domain,
                         expected_status=(HttpStatus.OK, HttpStatus.NOT_FOUND))

    request.addfinalizer(tear_down)
    return smartlist


@pytest.fixture(scope='function')
def talent_pool(request, token_first, user_first):
    """
    This fixture created a talent pool that is associated to user_first
    :param request: request object
    :param token_first: authentication token for user_first
    """
    talent_pools = create_talent_pools(token_first)
    talent_pool_id = talent_pools['talent_pools'][0]
    talent_pool_obj = get_talent_pool(talent_pool_id, token_first)['talent_pool']

    def tear_down():
        delete_talent_pool(talent_pool_id, token_first,
                           expected_status=(HttpStatus.OK, HttpStatus.NOT_FOUND))

    request.addfinalizer(tear_down)
    return talent_pool_obj


@pytest.fixture(scope='function')
def talent_pool_second(request, token_second, user_second):
    """
    This fixture created a talent pool that is associated to user_second of domain_second
    :param token_second: authentication token for user_second
    """
    talent_pools = create_talent_pools(token_second)
    talent_pool_id = talent_pools['talent_pools'][0]
    talent_pool_obj = get_talent_pool(talent_pool_id, token_second)['talent_pool']

    def tear_down():
        delete_talent_pool(talent_pool_id, token_second,
                           expected_status=(HttpStatus.OK, HttpStatus.NOT_FOUND))

    request.addfinalizer(tear_down)
    return talent_pool_obj

