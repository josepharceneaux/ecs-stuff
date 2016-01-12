"""Test suite for Flask Resume Parsing MicroService."""

__author__ = 'erik@getTalent.com'
# Standard library
import json
import os
import random
# Third party
import requests as r
# Module Specific.
from resume_service.common.utils.handy_functions import random_word
from resume_service.resume_parsing_app import redis_store
from resume_service.resume_parsing_app.views.batch_lib import add_fp_keys_to_queue
# Test fixtures, imports required even though not 'used'
# TODO: Look into importing these once and use via namespacing.
from resume_service.tests.test_fixtures import client_fixture
from resume_service.tests.test_fixtures import country_fixture
from resume_service.tests.test_fixtures import culture_fixture
from resume_service.tests.test_fixtures import domain_fixture
from resume_service.tests.test_fixtures import email_label_fixture
from resume_service.tests.test_fixtures import org_fixture
from resume_service.tests.test_fixtures import token_fixture
from resume_service.tests.test_fixtures import user_fixture
from resume_service.tests.test_fixtures import phone_label_fixture
from resume_service.tests.test_fixtures import product_fixture
from resume_service.common.routes import ResumeApiUrl, ResumeApi


DOC_FP_KEY = '0169173d35beaf1053e79fdf1b5db864.docx'
PDF15_FP_KEP = 'e68b51ee1fd62db589d2669c4f63f381.pdf'
REDIS_EXPIRE_TIME = 10


def test_base_url():
    """Test that the application root lists the endpoint."""
    base_response = r.get(ResumeApiUrl.API_URL % '')
    assert ResumeApi.PARSE in base_response.content


def test_doc_from_fp_key(token_fixture):
    """Test that .doc files from S3 can be parsed."""
    response = fetch_resume_fp_key_response(token_fixture, DOC_FP_KEY)
    assert_k_in_d('candidate', response, 'response')



def test_doc_by_post(token_fixture):
    """Test that .doc files that are posted to the end point can be parsed."""
    response = fetch_resume_post_response(token_fixture, 'test_bin.docx')
    assert_k_in_d('candidate', response, 'response')


def test_v15_pdf_from_fp_key(token_fixture):
    """Test that v1.5 pdf files from S3 can be parsed."""
    response = fetch_resume_fp_key_response(token_fixture, PDF15_FP_KEP)
    assert_k_in_d('candidate', response, 'response')


def test_v14_pdf_from_fp_key(token_fixture):
    """Test that v1.4 pdf files from S3 can be parsed."""
    response = fetch_resume_fp_key_response(token_fixture, 'test_bin_14.pdf')
    assert_k_in_d('candidate', response, 'response')


def test_v13_pdf_from_fp_key(token_fixture):
    """Test that v1.3 pdf files from S3 can be parsed."""
    response = fetch_resume_fp_key_response(token_fixture, 'test_bin_13.pdf')
    assert_k_in_d('candidate', response, 'response')


def test_v14_pdf_by_post(token_fixture):
    """Test that v1.4 pdf files can be posted."""
    response = fetch_resume_post_response(token_fixture, 'test_bin_14.pdf')
    assert_k_in_d('candidate', response, 'response')


def test_v13_pdf_by_post(token_fixture):
    """Test that v1.5 pdf files can be posted."""
    response = fetch_resume_post_response(token_fixture, 'test_bin_13.pdf')
    assert_k_in_d('candidate', response, 'response')


def test_jpg_from_fp_key(token_fixture):
    """Test that jpg files from S3 can be parsed."""
    response = fetch_resume_fp_key_response(token_fixture, 'test_bin.jpg')
    assert_k_in_d('candidate', response, 'response')


def test_jpg_by_post(token_fixture):
    """Test that jpg files can be posted."""
    response = fetch_resume_post_response(token_fixture, 'test_bin.jpg')
    assert_k_in_d('candidate', response, 'response')


def test_2448_3264_jpg_by_post(token_fixture):
    """Test that large jpgs files can be posted."""
    response = fetch_resume_post_response(token_fixture, '2448_3264.jpg')
    assert_k_in_d('candidate', response, 'response')


def test_no_token_fails():
    """Test that tokens are required."""
    filepicker_key = DOC_FP_KEY
    test_response = r.post(ResumeApiUrl.PARSE, data=dict(filepicker_key=filepicker_key))
    json_obj = json.loads(test_response.content)
    assert_k_in_d('error', json_obj, 'json_obj')


def test_invalid_token_fails():
    """Test that VALID tokens are required."""
    filepicker_key = DOC_FP_KEY
    test_response = r.post(ResumeApiUrl.PARSE,
                           headers={'Authorization': 'Bearer %s' % 'invalidtokenzzzz'},
                           data=dict(filepicker_key=filepicker_key))
    json_obj = json.loads(test_response.content)
    assert_k_in_d('error', json_obj, 'json_obj')


def test_v15_pdf_by_post(token_fixture):
    """Test that v1.5 pdf files can be posted."""
    response = fetch_resume_post_response(token_fixture, 'test_bin.pdf', create_mode='True')
    assert_k_in_d('candidate', response, 'response')
    assert_k_in_d('id', response['candidate'], 'candidate')


def test_batch_processing(user_fixture, token_fixture):
    # create a single file queue
    user_id = user_fixture.id
    queue_string = 'batch:{}:fp_keys'.format(user_id)
    unused_queue_status = add_fp_keys_to_queue([PDF15_FP_KEP], user_id, token_fixture.access_token)
    redis_store.expire(queue_string, REDIS_EXPIRE_TIME)
    # mock hit from scheduler service.
    response = r.get(ResumeApiUrl.BATCH_URL + '/{}'.format(user_id),
                     headers={'Authorization': 'Bearer %s' % token_fixture.access_token})
    assert_k_in_d('candidate', response, 'response')


def test_add_single_queue_item(token_fixture):
    """Test adding a single item to a users queue stored in Redis"""
    user_id = random_word(6)
    queue_string = 'batch:{}:fp_keys'.format(user_id)
    response = add_fp_keys_to_queue(['file1'], user_id, token_fixture.access_token)
    redis_store.expire(queue_string, 20)
    try:
        assert response == {'redis_key': queue_string, 'quantity': 1}
    except Exception as e:
        e.args += ('Improperly Formatted redis post response for single item',)
        raise


def test_add_multiple_queue_items(token_fixture):
    """Tests adding n+1 items to a users queue stored in Redis"""
    user_id = random_word(6)
    file_count = random.randrange(1, 100)
    filenames = ['file{}'.format(i) for i in xrange(file_count)]
    queue_string = 'batch:{}:fp_keys'.format(user_id)
    queue_status = add_fp_keys_to_queue(filenames, user_id, token_fixture.access_token)
    redis_store.expire(queue_string, REDIS_EXPIRE_TIME)
    try:
        assert queue_status == {'redis_key': queue_string, 'quantity': file_count}
    except Exception as e:
        e.args += ('Improperly Formatted redis post response for single item',)
        raise

def test_health_check():
    """HealthCheck/PingDom test endpoint."""
    response = r.get(ResumeApiUrl.HEALTH_CHECK)
    assert response.status_code == 200


def fetch_resume_post_response(token_fixture, file_name, create_mode=''):
    """Posts file to local test auth server for json formatted resumes."""
    current_dir = os.path.dirname(__file__)
    with open(os.path.join(current_dir, 'test_resumes/{}'.format(file_name)), 'rb') as resume_file:
        response = r.post(ResumeApiUrl.PARSE,
                          headers={'Authorization': 'Bearer %s' % token_fixture.access_token},
                          data=dict(
                              # files = dict(resume_file=raw_file),
                              resume_file_name=file_name,
                              create_candidate=create_mode,
                          ),
                          files=dict(resume_file=resume_file),
                         )
    return json.loads(response.content)


def fetch_resume_fp_key_response(token_fixture, fp_key):
    """Posts FilePicker key to local test auth server for json formatted resumes."""
    test_response = r.post(ResumeApiUrl.PARSE, headers={
        'Authorization': 'Bearer %s' % token_fixture.access_token},
        data=dict(filepicker_key=fp_key))
    return json.loads(test_response.content)


def assert_k_in_d(key, dict, name):
    try:
        assert key in dict
    except:
        raise KeyError("'{}' not in {}").format(key, name)