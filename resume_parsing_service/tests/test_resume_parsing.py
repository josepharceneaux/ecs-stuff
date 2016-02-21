"""Test suite for Flask Resume Parsing MicroService."""
# pylint: disable=wrong-import-position
__author__ = 'erik@getTalent.com'
# Standard library
import json
import os
import random
# Third party
import requests
# Module Specific.
from resume_parsing_service.common.utils.handy_functions import random_word
from resume_parsing_service.app import redis_store
from resume_parsing_service.app.views.batch_lib import add_fp_keys_to_queue
# Test fixtures, imports required even though not 'used'
# TODO: Look into importing these once and use via namespacing.
from resume_parsing_service.tests.test_fixtures import client_fixture
from resume_parsing_service.tests.test_fixtures import country_fixture
from resume_parsing_service.tests.test_fixtures import culture_fixture
from resume_parsing_service.tests.test_fixtures import domain_fixture
from resume_parsing_service.tests.test_fixtures import email_label_fixture
from resume_parsing_service.tests.test_fixtures import org_fixture
from resume_parsing_service.tests.test_fixtures import token_fixture
from resume_parsing_service.tests.test_fixtures import user_fixture
from resume_parsing_service.tests.test_fixtures import user_group_fixture
from resume_parsing_service.tests.test_fixtures import phone_label_fixture
from resume_parsing_service.tests.test_fixtures import product_fixture
from resume_parsing_service.tests.test_fixtures import talent_pool_fixture
from resume_parsing_service.tests.test_fixtures import talent_pool_group_fixture
from resume_parsing_service.common.routes import ResumeApiUrl, ResumeApi

from resume_parsing_service.common.models.user import DomainRole
from resume_parsing_service.common.utils.handy_functions import add_role_to_test_user

DOC_FP_KEY = '0169173d35beaf1053e79fdf1b5db864.docx'
PDF15_FP_KEY = 'e68b51ee1fd62db589d2669c4f63f381.pdf'
REDIS_EXPIRE_TIME = 10


def test_base_url():
    """Test that the application root lists the endpoint."""
    base_response = requests.get(ResumeApiUrl.API_URL % '')
    assert ResumeApi.PARSE in base_response.content


# This resume was failing to parse. Keeping it here for debugging until issue resolved/error confirmed.
def test_get_890(token_fixture, user_fixture):
    add_role_to_test_user(user_fixture, [DomainRole.Roles.CAN_ADD_CANDIDATES,
                                         DomainRole.Roles.CAN_GET_TALENT_POOLS])
    content, status = fetch_resume_fp_key_response(token_fixture, "0382RHQRwSWq6jytZm1w_Patrick.David_11.doc")
    assert_non_create_content_and_status(content, status)


def test_invalid_fp_key(token_fixture, user_fixture):
    add_role_to_test_user(user_fixture, [DomainRole.Roles.CAN_ADD_CANDIDATES,
                                         DomainRole.Roles.CAN_GET_TALENT_POOLS])
    content, status = fetch_resume_fp_key_response(token_fixture, "MichaelKane/AlfredFromBatman.doc")
    assert 'error' in content
    assert status == requests.codes.bad_request


def test_doc_from_fp_key(token_fixture, user_fixture):
    """Test that .doc files from S3 can be parsed."""
    add_role_to_test_user(user_fixture, [DomainRole.Roles.CAN_ADD_CANDIDATES,
                                         DomainRole.Roles.CAN_GET_TALENT_POOLS])
    content, status = fetch_resume_fp_key_response(token_fixture, DOC_FP_KEY)
    assert_non_create_content_and_status(content, status)



def test_doc_by_post(token_fixture, user_fixture):
    """Test that .doc files that are posted to the end point can be parsed."""
    add_role_to_test_user(user_fixture, [DomainRole.Roles.CAN_ADD_CANDIDATES,
                                         DomainRole.Roles.CAN_GET_TALENT_POOLS])
    content, status = fetch_resume_post_response(token_fixture, 'test_bin.docx')
    assert_non_create_content_and_status(content, status)


def test_HTML_doc_by_post(token_fixture, user_fixture):
    """Test that .doc files that are posted to the end point can be parsed."""
    add_role_to_test_user(user_fixture, [DomainRole.Roles.CAN_ADD_CANDIDATES,
                                         DomainRole.Roles.CAN_GET_TALENT_POOLS])
    content, status = fetch_resume_post_response(token_fixture, 'Bridgeport.Ave.doc')
    # For this resume xhtml2pdf loses essentially all the content and just reports back css/font info...
    assert_non_create_content_and_status(content, status)


def test_v15_pdf_from_fp_key(token_fixture, user_fixture):
    """Test that v1.5 pdf files from S3 can be parsed."""
    add_role_to_test_user(user_fixture, [DomainRole.Roles.CAN_ADD_CANDIDATES,
                                         DomainRole.Roles.CAN_GET_TALENT_POOLS])
    content, status = fetch_resume_fp_key_response(token_fixture, PDF15_FP_KEY)
    assert_non_create_content_and_status(content, status)


def test_v14_pdf_from_fp_key(token_fixture, user_fixture):
    """Test that v1.4 pdf files from S3 can be parsed."""
    add_role_to_test_user(user_fixture, [DomainRole.Roles.CAN_ADD_CANDIDATES,
                                         DomainRole.Roles.CAN_GET_TALENT_POOLS])
    content, status = fetch_resume_fp_key_response(token_fixture, 'test_bin_14.pdf')
    assert_non_create_content_and_status(content, status)


def test_v13_pdf_from_fp_key(token_fixture, user_fixture):
    """Test that v1.3 pdf files from S3 can be parsed."""
    add_role_to_test_user(user_fixture, [DomainRole.Roles.CAN_ADD_CANDIDATES,
                                         DomainRole.Roles.CAN_GET_TALENT_POOLS])
    content, status = fetch_resume_fp_key_response(token_fixture, 'test_bin_13.pdf')
    assert_non_create_content_and_status(content, status)


def test_v14_pdf_by_post(token_fixture, user_fixture):
    """Test that v1.4 pdf files can be posted."""
    add_role_to_test_user(user_fixture, [DomainRole.Roles.CAN_ADD_CANDIDATES,
                                         DomainRole.Roles.CAN_GET_TALENT_POOLS])
    content, status = fetch_resume_post_response(token_fixture, 'test_bin_14.pdf')
    assert_non_create_content_and_status(content, status)


def test_v13_pdf_by_post(token_fixture, user_fixture):
    """Test that v1.5 pdf files can be posted."""
    add_role_to_test_user(user_fixture, [DomainRole.Roles.CAN_ADD_CANDIDATES,
                                         DomainRole.Roles.CAN_GET_TALENT_POOLS])
    content, status = fetch_resume_post_response(token_fixture, 'test_bin_13.pdf')
    assert_non_create_content_and_status(content, status)


def test_jpg_from_fp_key(token_fixture, user_fixture):
    """Test that jpg files from S3 can be parsed."""
    add_role_to_test_user(user_fixture, [DomainRole.Roles.CAN_ADD_CANDIDATES,
                                         DomainRole.Roles.CAN_GET_TALENT_POOLS])
    content, status = fetch_resume_fp_key_response(token_fixture, 'test_bin.jpg')
    assert_non_create_content_and_status(content, status)


def test_jpg_by_post(token_fixture, user_fixture):
    """Test that jpg files can be posted."""
    add_role_to_test_user(user_fixture, [DomainRole.Roles.CAN_ADD_CANDIDATES,
                                         DomainRole.Roles.CAN_GET_TALENT_POOLS])
    content, status = fetch_resume_post_response(token_fixture, 'test_bin.jpg')
    assert_non_create_content_and_status(content, status)


def test_2448_3264_jpg_by_post(token_fixture, user_fixture):
    """Test that large jpgs files can be posted."""
    add_role_to_test_user(user_fixture, [DomainRole.Roles.CAN_ADD_CANDIDATES,
                                         DomainRole.Roles.CAN_GET_TALENT_POOLS])
    content, status = fetch_resume_post_response(token_fixture, '2448_3264.jpg')
    assert_non_create_content_and_status(content, status)


def test_no_token_fails():
    """Test that tokens are required."""
    filepicker_key = DOC_FP_KEY
    test_response = requests.post(ResumeApiUrl.PARSE, data=dict(filepicker_key=filepicker_key))
    json_obj = json.loads(test_response.content)
    assert 'error' in json_obj, "There should be an error if no token is provided"
    assert test_response.status_code == requests.codes.unauthorized


def test_invalid_token_fails():
    """Test that VALID tokens are required."""
    filepicker_key = DOC_FP_KEY
    test_response = requests.post(ResumeApiUrl.PARSE,
                                  headers={'Authorization': 'Bearer %s' % 'invalidtokenzzzz'},
                                  data=dict(filepicker_key=filepicker_key))
    json_obj = json.loads(test_response.content)
    assert 'error' in json_obj, "There should be an error if a bad token is provided"
    assert test_response.status_code == requests.codes.unauthorized


def test_v15_pdf_by_post_with_create(token_fixture, user_fixture):
    """Test that v1.5 pdf files can be posted."""
    add_role_to_test_user(user_fixture, [DomainRole.Roles.CAN_ADD_CANDIDATES,
                                         DomainRole.Roles.CAN_GET_TALENT_POOLS,
                                         DomainRole.Roles.CAN_GET_CANDIDATES])
    content, status = fetch_resume_post_response(token_fixture, 'test_bin.pdf', create_mode=True)
    assert_create_or_update_content_and_status(content, status)


def test_already_exists_candidate(token_fixture, user_fixture):
    """Test that v1.5 pdf files can be posted."""
    add_role_to_test_user(user_fixture, [DomainRole.Roles.CAN_ADD_CANDIDATES,
                                         DomainRole.Roles.CAN_GET_TALENT_POOLS,
                                         DomainRole.Roles.CAN_GET_CANDIDATES,
                                         DomainRole.Roles.CAN_EDIT_CANDIDATES])
    unused_create_response = fetch_resume_post_response(token_fixture, 'test_bin.pdf', create_mode=True)
    update_content, status = fetch_resume_post_response(token_fixture, 'test_bin.pdf', create_mode=True)
    assert_create_or_update_content_and_status(update_content, status)


def test_batch_processing(user_fixture, token_fixture):
    # create a single file queue
    user_id = user_fixture.id
    add_role_to_test_user(user_fixture, [DomainRole.Roles.CAN_ADD_CANDIDATES,
                                         DomainRole.Roles.CAN_GET_TALENT_POOLS,
                                         DomainRole.Roles.CAN_GET_CANDIDATES])
    queue_string = 'batch:{}:fp_keys'.format(user_id)
    unused_queue_status = add_fp_keys_to_queue([PDF15_FP_KEY], user_id, token_fixture.access_token)
    redis_store.expire(queue_string, REDIS_EXPIRE_TIME)
    # mock hit from scheduler service.
    batch_response = requests.get('{}/{}'.format(ResumeApiUrl.BATCH_URL, user_id),
                                  headers={'Authorization': 'bearer {}'.format(
                                      token_fixture.access_token)})
    formatted_response = json.loads(batch_response.content)
    assert 'candidate' in formatted_response, "Candidate should be in response content"


# Unittest Style - located here due to conversion to flask redis which requires app context.
def test_add_single_queue_item(token_fixture):
    """Test adding a single item to a users queue stored in Redis"""
    user_id = random_word(6)
    queue_string = 'batch:{}:fp_keys'.format(user_id)
    response = add_fp_keys_to_queue(['file1'], user_id, 'bearer {}'.format(
        token_fixture.access_token))
    redis_store.expire(queue_string, 20)
    assert response == {'redis_key': queue_string, 'quantity': 1}, ('Improperly Formatted redis '
                                                                    'post response for single item')


# Integration test of the above.
def test_integration_add_single_item(user_fixture, token_fixture):
    """Test adding a single item via end point."""
    queue_string = 'batch:{}:fp_keys'.format(user_fixture.id)
    response = requests.post(ResumeApiUrl.BATCH_URL,
                             headers={'Authorization': 'bearer {}'.format(
                                 token_fixture.access_token),
                                      'Content-Type': 'application/json'},
                             data=json.dumps({'filenames': ['file1']})
                            )
    assert response.status_code == requests.codes.created
    assert json.loads(response.content) == {'redis_key': queue_string, 'quantity': 1}, (
        'Improperly Formatted redis post response for single item')


def test_add_multiple_queue_items(token_fixture):
    """Tests adding n-100 items to a users queue stored in Redis"""
    user_id = random_word(6)
    file_count = random.randrange(1, 100)
    filenames = ['file{}'.format(i) for i in xrange(file_count)]
    queue_string = 'batch:{}:fp_keys'.format(user_id)
    queue_status = add_fp_keys_to_queue(filenames, user_id,
                                        'bearer {}'.format(token_fixture.access_token))
    redis_store.expire(queue_string, REDIS_EXPIRE_TIME)
    assert queue_status == {'redis_key': queue_string, 'quantity': file_count}, (
        'Improperly Formatted redis post response for multiple items')


def test_health_check():
    """HealthCheck/PingDom test endpoint."""
    response = requests.get(ResumeApiUrl.HEALTH_CHECK)
    assert response.status_code == requests.codes.ok

    # Testing Health Check URL with trailing slash
    response = requests.get(ResumeApiUrl.HEALTH_CHECK + '/')
    assert response.status_code == requests.codes.ok


def fetch_resume_post_response(token_fixture, file_name, create_mode=False):
    """Posts file to local test auth server for json formatted resumes."""
    current_dir = os.path.dirname(__file__)
    with open(os.path.join(current_dir, 'test_resumes/{}'.format(file_name)), 'rb') as resume_file:
        response = requests.post(ResumeApiUrl.PARSE,
                                 headers={'Authorization': 'Bearer {}'.format(
                                     token_fixture.access_token)},
                                 data={
                                     'resume_file_name': file_name, 'create_candidate':create_mode},
                                 files=dict(resume_file=resume_file)
                                )
    content = json.loads(response.content)
    status_code = response.status_code
    return content, status_code


def fetch_resume_fp_key_response(token_fixture, fp_key):
    """Posts FilePicker key to local test auth server for json formatted resumes."""
    test_response = requests.post(ResumeApiUrl.PARSE,
                                  headers={
                                      'Authorization': 'Bearer {}'.format(
                                          token_fixture.access_token),
                                      'Content-Type': 'application/json'
                                  },
                                  data=json.dumps({'filepicker_key': fp_key})
                                 )
    content = json.loads(test_response.content)
    status_code = test_response.status_code
    return content, status_code


def assert_non_create_content_and_status(content, status):
    assert 'candidate' in content, "Candidate should be in response content"
    assert 'raw_response' in content and content['raw_response'] is not None, "None create response should return raw content"
    assert status == requests.codes.ok


def assert_create_or_update_content_and_status(content, status):
    assert 'candidate' in content, "Candidate should be in response content"
    assert 'id' in content['candidate'], "Candidate should contain id in response if create=True."
    assert content['candidate']['id'], "Candidate should contain non-None id to signal creation."
    assert status == requests.codes.ok