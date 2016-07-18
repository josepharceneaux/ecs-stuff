"""Test suite for Flask Resume Parsing MicroService."""
# pylint: disable=wrong-import-position
__author__ = 'erik@getTalent.com'
# Standard library
import json
import os
# Third party
import requests
# Module Specific.
# Test fixtures, imports required even though not 'used'
# TODO: Look into importing these once and use via namespacing.
from resume_parsing_service.common.routes import ResumeApiUrl
from resume_parsing_service.tests.test_fixtures import client_fixture
from resume_parsing_service.tests.test_fixtures import country_fixture
from resume_parsing_service.tests.test_fixtures import culture_fixture
from resume_parsing_service.tests.test_fixtures import domain_fixture
from resume_parsing_service.tests.test_fixtures import email_label_fixture
from resume_parsing_service.tests.test_fixtures import org_fixture
from resume_parsing_service.tests.test_fixtures import phone_label_fixture
from resume_parsing_service.tests.test_fixtures import product_fixture
from resume_parsing_service.tests.test_fixtures import talent_pool_fixture
from resume_parsing_service.tests.test_fixtures import talent_pool_group_fixture
from resume_parsing_service.tests.test_fixtures import token_fixture
from resume_parsing_service.tests.test_fixtures import user_fixture
from resume_parsing_service.tests.test_fixtures import user_group_fixture

DOC_FP_KEY = '0169173d35beaf1053e79fdf1b5db864.docx'
PDF15_FP_KEY = 'e68b51ee1fd62db589d2669c4f63f381.pdf'
DOC_890 = "0382RHQRwSWq6jytZm1w_Patrick.David_11.doc"
REDIS_EXPIRE_TIME = 10


####################################################################################################
# Static URL tests
####################################################################################################
def test_health_check():
    """HealthCheck/PingDom test endpoint."""
    response = requests.get(ResumeApiUrl.HEALTH_CHECK)
    assert response.status_code == requests.codes.ok

    # Testing Health Check URL with trailing slash
    response = requests.get(ResumeApiUrl.HEALTH_CHECK + '/')
    assert response.status_code == requests.codes.ok


####################################################################################################
# Test Invalid Inputs
####################################################################################################
def test_invalid_fp_key(token_fixture, user_fixture):
    content, status = fetch_resume_fp_key_response(token_fixture, "MichaelKane/AlfredFromBatman.doc")
    assert 'error' in content
    assert status == requests.codes.bad_request


def test_none_fp_key(token_fixture, user_fixture):
    content, status = fetch_resume_fp_key_response(token_fixture, None)
    assert 'error' in content
    assert status == requests.codes.bad_request


def test_posting_no_file(token_fixture, user_fixture):
    invalid_post = requests.post(ResumeApiUrl.PARSE,
                                 headers={
                                     'Authorization': 'Bearer {}'.format(
                                         token_fixture.access_token),
                                     'Content-Type': 'application/json'
                                 },
                                 data=json.dumps({'resume_file_name': 'foobarbaz',
                                                  'create_candidate': True})
                                )
    content = json.loads(invalid_post.content)
    assert 'error' in content
    assert invalid_post.status_code == requests.codes.bad_request


def test_posting_None_file(token_fixture, user_fixture):
    invalid_post = requests.post(ResumeApiUrl.PARSE,
                                 headers={
                                     'Authorization': 'Bearer {}'.format(
                                         token_fixture.access_token),
                                     'Content-Type': 'application/json'
                                 },
                                 data=json.dumps({'resume_file': None,
                                                  'create_candidate': True})
                                )
    content = json.loads(invalid_post.content)
    assert 'error' in content
    assert invalid_post.status_code == requests.codes.bad_request


def test_talent_pool_error(token_fixture):
    invalid_post = requests.post(ResumeApiUrl.PARSE,
                                 headers={
                                     'Authorization': 'Bearer {}'.format(token_fixture.access_token),
                                     'Content-Type': 'application/json'
                                 },
                                 data=json.dumps({'resume_file_name': 'foobarbaz',
                                                  'create_candidate': True})
                                )
    content = json.loads(invalid_post.content)
    assert 'error' in content
    assert invalid_post.status_code == requests.codes.bad_request

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


def test_bad_header(token_fixture, user_fixture):
    invalid_post = requests.post(ResumeApiUrl.PARSE,
                                 headers={
                                     'Authorization': 'Bearer {}'.format(token_fixture.access_token),
                                     'Content-Type': 'text/csv'
                                 },
                                 data=json.dumps({'resume_file_name': 'foobarbaz',
                                                  'create_candidate': True})
                                )
    content = json.loads(invalid_post.content)
    assert 'error' in content
    assert invalid_post.status_code == requests.codes.bad_request


def test_blank_file(token_fixture, user_fixture):
    content, status = fetch_resume_fp_key_response(token_fixture, 'blank.txt')
    assert 'error' in content, "There should be an error if no text can be extracted."


def test_picture_not_resume(token_fixture, user_fixture):
    content, status = fetch_resume_post_response(token_fixture, 'notResume.jpg')
    assert 'error' in content, "There should be an error Because it's a picture of a backyard."

    content, status = fetch_resume_post_response(token_fixture, 'notResume2.jpg')
    assert 'error' in content, "There should be an error Because it's a picture of food."


def test_bad_create_candidate_inputs(token_fixture):
    error_message = 'There has been a critical error parsing this resume, the development team has been notified'
    for invalid_type in [1, 'string', {}, []]:
        test_response = requests.post(
            ResumeApiUrl.PARSE,
            headers={
                'Authorization': 'Bearer {}'.format(token_fixture.access_token),
                'Content-Type': 'application/json'
            },
            data=json.dumps({
                'filepicker_key': 'hey',
                'create_candidate': invalid_type
            })
        )
        content = json.loads(test_response.content)
        status_code = test_response.status_code

        assert 'error' in content
        assert content.get('error', {}).get('message') == error_message
        assert status_code == requests.codes.bad

def test_bad_filename_inputs(token_fixture):
    error_message = 'There has been a critical error parsing this resume, the development team has been notified'
    for invalid_type in [1, True, {}, []]:
        test_response = requests.post(
            ResumeApiUrl.PARSE,
            headers={
                'Authorization': 'Bearer {}'.format(token_fixture.access_token),
                'Content-Type': 'application/json'
            },
            data=json.dumps({
                'filepicker_key': 'hey',
                'filename': invalid_type
            })
        )
        content = json.loads(test_response.content)
        status_code = test_response.status_code

        assert 'error' in content
        assert content.get('error', {}).get('message') == error_message
        assert status_code == requests.codes.bad

def test_bad_fpkey_inputs(token_fixture):
    error_message = 'There has been a critical error parsing this resume, the development team has been notified'
    for invalid_type in [1, True, {}, [], None]:
        test_response = requests.post(
            ResumeApiUrl.PARSE,
            headers={
                'Authorization': 'Bearer {}'.format(token_fixture.access_token),
                'Content-Type': 'application/json'
            },
            data=json.dumps({
                'filepicker_key': invalid_type
            })
        )
        content = json.loads(test_response.content)
        status_code = test_response.status_code

        assert 'error' in content
        assert content.get('error', {}).get('message') == error_message
        assert status_code == requests.codes.bad


def test_bad_tpool_inputs(token_fixture):
    error_message = 'There has been a critical error parsing this resume, the development team has been notified'
    for invalid_type in [1, True, {}, 'string']:
        test_response = requests.post(
            ResumeApiUrl.PARSE,
            headers={
                'Authorization': 'Bearer {}'.format(token_fixture.access_token),
                'Content-Type': 'application/json'
            },
            data=json.dumps({
                'filepicker_key': 'unused_key',
                'talent_pools': invalid_type
            })
        )
        content = json.loads(test_response.content)
        status_code = test_response.status_code

        assert 'error' in content
        assert content.get('error', {}).get('message') == error_message
        assert status_code == requests.codes.bad


####################################################################################################
# Test FilePicker Key Parsing without create option
####################################################################################################
def test_doc_from_fp_key(token_fixture, user_fixture):
    """Test that .doc files from S3 can be parsed."""
    content, status = fetch_resume_fp_key_response(token_fixture, DOC_FP_KEY)
    assert_non_create_content_and_status(content, status)


def test_v15_pdf_from_fp_key(token_fixture, user_fixture):
    """Test that v1.5 pdf files from S3 can be parsed."""
    content, status = fetch_resume_fp_key_response(token_fixture, PDF15_FP_KEY)
    assert_non_create_content_and_status(content, status)


def test_v14_pdf_from_fp_key(token_fixture, user_fixture):
    """Test that v1.4 pdf files from S3 can be parsed."""
    content, status = fetch_resume_fp_key_response(token_fixture, 'test_bin_14.pdf')
    assert_non_create_content_and_status(content, status)


def test_v13_pdf_from_fp_key(token_fixture, user_fixture):
    """Test that v1.3 pdf files from S3 can be parsed."""
    content, status = fetch_resume_fp_key_response(token_fixture, 'test_bin_13.pdf')
    assert_non_create_content_and_status(content, status)


def test_jpg_from_fp_key(token_fixture, user_fixture):
    """Test that jpg files from S3 can be parsed."""
    content, status = fetch_resume_fp_key_response(token_fixture, 'test_bin.jpg')
    assert_non_create_content_and_status(content, status)


def test_doc_with_texthtml_mime(token_fixture, user_fixture):
    """Test that jpg files from S3 can be parsed."""
    content, status = fetch_resume_fp_key_response(token_fixture, 'Breland.Bobby.doc')
    assert_non_create_content_and_status(content, status)


####################################################################################################
# Test JSON POST Parsing without create option
####################################################################################################


def test_doc_by_post(token_fixture, user_fixture):
    """Test that .doc files that are posted to the end point can be parsed."""
    content, status = fetch_resume_post_response(token_fixture, 'test_bin.docx')
    assert_non_create_content_and_status(content, status)


def test_HTML_doc_by_post(token_fixture, user_fixture):
    """Test that .doc files that are posted to the end point can be parsed."""
    content, status = fetch_resume_post_response(token_fixture, 'Bridgeport.Ave.doc')
    assert_non_create_content_and_status(content, status)


def test_v14_pdf_by_post(token_fixture, user_fixture):
    """Test that v1.4 pdf files can be posted."""
    content, status = fetch_resume_post_response(token_fixture, 'test_bin_14.pdf')
    assert_non_create_content_and_status(content, status)


def test_v13_pdf_by_post(token_fixture, user_fixture):
    """Test that v1.5 pdf files can be posted."""
    content, status = fetch_resume_post_response(token_fixture, 'test_bin_13.pdf')
    assert_non_create_content_and_status(content, status)


def test_jpg_by_post(token_fixture, user_fixture):
    """Test that jpg files can be posted."""
    content, status = fetch_resume_post_response(token_fixture, 'test_bin.jpg')
    assert_non_create_content_and_status(content, status)


def test_2448_3264_jpg_by_post(token_fixture, user_fixture):
    """Test that large jpgs files can be posted."""
    content, status = fetch_resume_post_response(token_fixture, '2448_3264.jpg')
    assert_non_create_content_and_status(content, status)


def test_jpg_in_pdf(token_fixture, user_fixture):
    content, status = fetch_resume_post_response(token_fixture, 'jpg_in_pdf.pdf')
    """Test that large jpgs files can be posted."""
    assert_non_create_content_and_status(content, status)


def test_txt_with_jpg_in_encrypted_pdf(token_fixture, user_fixture):
    content, status = fetch_resume_post_response(token_fixture, 'pic_in_encrypted.pdf')
    assert_non_create_content_and_status(content, status)


def test_no_multiple_skills(token_fixture, user_fixture):
    """
    Test for GET-1301 where multiple skills are being parsed out for a single new candidate.
    """
    content, status = fetch_resume_post_response(token_fixture, 'GET_1301.doc')
    assert_non_create_content_and_status(content, status)
    skills = content['candidate']['skills']
    skills_set = set()
    for skill in skills:
        skills_set.add(skill['name'])
    assert len(skills) == len(skills_set)


def test_encrypted_resume(token_fixture, user_fixture):
    """Test that encrypted pdf files that are posted to the end point can be parsed."""
    content, status = fetch_resume_post_response(token_fixture, 'jDiMaria.pdf')
    assert_non_create_content_and_status(content, status)

####################################################################################################
# Test Candidate Creation
####################################################################################################
def test_v15_pdf_by_post_with_create(token_fixture, user_fixture):
    """Test that v1.5 pdf files can be posted."""

    content, status = fetch_resume_post_response(token_fixture, 'test_bin.pdf', create_mode=True)
    assert_create_or_update_content_and_status(content, status)


def test_doc_FP_with_create(token_fixture, user_fixture):

    content, status = fetch_resume_fp_key_response(token_fixture, DOC_890, create_mode=True)
    assert_create_or_update_content_and_status(content, status)


def test_985_from_fp_key(token_fixture, user_fixture):
    """Test that .doc files from S3 can be parsed."""

    content, status = fetch_resume_fp_key_response(token_fixture, "Bruncak.Daren.doc", create_mode=True)
    assert_create_or_update_content_and_status(content, status)


def test_create_candidate_from_resume_without_name(token_fixture, user_fixture):

    content, status = fetch_resume_post_response(token_fixture, 'Adams.John.doc', create_mode=True)
    assert_create_or_update_content_and_status(content, status)


def test_create_candidate_from_resume_ben_fred(token_fixture, user_fixture):

    content, status = fetch_resume_post_response(token_fixture, 'ben.fred.doc', create_mode=True)
    assert_create_or_update_content_and_status(content, status)


def test_create_candidate_from_no_email_resume(token_fixture, user_fixture):

    content, status = fetch_resume_post_response(token_fixture, 'no_email_resume.doc', create_mode=True)
    assert_create_or_update_content_and_status(content, status)


def test_create_candidate_from_no_address_resume(token_fixture, user_fixture):

    content, status = fetch_resume_post_response(token_fixture, 'no_address.doc', create_mode=True)
    assert_create_or_update_content_and_status(content, status)


def test_create_with_references(token_fixture, user_fixture):
    content, status = fetch_resume_post_response(token_fixture, 'GET_1210.doc', create_mode=True)
    assert_create_or_update_content_and_status(content, status)


def test_create_with_long_punc_name(token_fixture, user_fixture):
    content, status = fetch_resume_post_response(token_fixture, 'GET-1319.pdf', create_mode=True)
    assert_create_or_update_content_and_status(content, status)
    assert content['candidate']['last_name'] == u'Weston'


def test_create_from_image(token_fixture, user_fixture):
    """
    Test for GET-1351. POST'd JSON.
    """
    content, status = fetch_resume_post_response(token_fixture, 'test_bin.jpg', create_mode=True)
    assert_create_or_update_content_and_status(content, status)


def test_create_from_jpgTxtPdf(token_fixture, user_fixture):
    """
    Test for GET-1463. POST'd JSON.
    """
    content, status = fetch_resume_post_response(token_fixture, 'pic_in_encrypted.pdf', create_mode=True)
    assert_create_or_update_content_and_status(content, status)


####################################################################################################
# Test Candidate Updating
####################################################################################################
def test_already_exists_candidate(token_fixture, user_fixture):
    """Test that v1.5 pdf files can be posted."""
    unused_create_response = fetch_resume_post_response(token_fixture, 'test_bin.pdf', create_mode=True)
    print "\nunused_create_response: {}".format(unused_create_response)
    update_content, status = fetch_resume_post_response(token_fixture, 'test_bin.pdf', create_mode=True)
    assert_create_or_update_content_and_status(update_content, status)


####################################################################################################
# Test Helper/Utility Functions
####################################################################################################
def fetch_resume_post_response(token_fixture, file_name, create_mode=False):
    """Posts file to local test auth server for json formatted resumes."""
    current_dir = os.path.dirname(__file__)
    with open(os.path.join(current_dir, 'test_resumes/{}'.format(file_name)), 'rb') as resume_file:
        response = requests.post(ResumeApiUrl.PARSE,
                                 headers={'Authorization': 'Bearer {}'.format(
                                     token_fixture.access_token)},
                                 data={
                                     # 'Local Test Upload' prefix.
                                     'resume_file_name': 'LTU_{}'.format(file_name),
                                     'create_candidate':create_mode},
                                 files=dict(resume_file=resume_file)
                                )
    content = json.loads(response.content)
    status_code = response.status_code
    return content, status_code


def fetch_resume_fp_key_response(token_fixture, fp_key, create_mode=False):
    """Posts FilePicker key to local test auth server for json formatted resumes."""
    test_response = requests.post(ResumeApiUrl.PARSE,
                                  headers={
                                      'Authorization': 'Bearer {}'.format(
                                          token_fixture.access_token),
                                      'Content-Type': 'application/json'
                                  },
                                  data=json.dumps({'filepicker_key': fp_key,
                                                   # 'Local Test Upload' prefix.
                                                   'resume_file_name': 'LTU_{}'.format(fp_key),
                                                   'create_candidate': create_mode})
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
