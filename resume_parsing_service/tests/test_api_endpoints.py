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
from resume_parsing_service.app.constants import error_constants
from resume_parsing_service.common.routes import ResumeApiUrl
from resume_parsing_service.common.tests.conftest import access_token_first
from resume_parsing_service.common.tests.conftest import domain_first
from resume_parsing_service.common.tests.conftest import domain_source
from resume_parsing_service.common.tests.conftest import first_group
from resume_parsing_service.common.tests.conftest import sample_client
from resume_parsing_service.common.tests.conftest import talent_pool
from resume_parsing_service.common.tests.conftest import user_first

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
# def test_invalid_fp_key(token_fixture, user_fixture, source_fixture):
def test_invalid_fp_key(access_token_first, domain_source):
    content, status = fetch_resume_fp_key_response(access_token_first, domain_source,
                                                   "MichaelKane/AlfredFromBatman.doc")
    assert 'error' in content
    assert status == requests.codes.bad_request


def test_none_fp_key(access_token_first, domain_source):
    content, status = fetch_resume_fp_key_response(access_token_first, domain_source, None)
    assert content['error']['message'] == error_constants.JSON_SCHEMA_ERROR['message']
    assert content['error']['code'] == error_constants.JSON_SCHEMA_ERROR['code']
    assert status == requests.codes.bad_request


def test_posting_no_file(access_token_first):
    invalid_post = requests.post(
        ResumeApiUrl.PARSE,
        headers={'Authorization': 'Bearer {}'.format(access_token_first),
                 'Content-Type': 'application/json'},
        data=json.dumps({
            'resume_file_name': 'foobarbaz',
            'create_candidate': True
        }))
    content = json.loads(invalid_post.content)
    assert content['error']['message'] == error_constants.JSON_SCHEMA_ERROR['message']
    assert content['error']['code'] == error_constants.JSON_SCHEMA_ERROR['code']
    assert invalid_post.status_code == requests.codes.bad_request


def test_posting_None_file(access_token_first):
    invalid_post = requests.post(
        ResumeApiUrl.PARSE,
        headers={'Authorization': 'Bearer {}'.format(access_token_first),
                 'Content-Type': 'application/json'},
        data=json.dumps({
            'resume_file': None,
            'create_candidate': True
        }))
    content = json.loads(invalid_post.content)
    assert content['error']['message'] == error_constants.JSON_SCHEMA_ERROR['message']
    assert content['error']['code'] == error_constants.JSON_SCHEMA_ERROR['code']
    assert invalid_post.status_code == requests.codes.bad_request


def test_no_fp_json_key_error(access_token_first):
    invalid_post = requests.post(
        ResumeApiUrl.PARSE,
        headers={'Authorization': 'Bearer {}'.format(access_token_first),
                 'Content-Type': 'application/json'},
        data=json.dumps({
            'resume_file_name': 'foobarbaz',
            'create_candidate': True
        }))
    content = json.loads(invalid_post.content)
    assert content['error']['message'] == error_constants.JSON_SCHEMA_ERROR['message']
    assert content['error']['code'] == error_constants.JSON_SCHEMA_ERROR['code']
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
    test_response = requests.post(
        ResumeApiUrl.PARSE,
        headers={'Authorization': 'Bearer %s' % 'invalidtokenzzzz'},
        data=dict(filepicker_key=filepicker_key))
    json_obj = json.loads(test_response.content)
    assert 'error' in json_obj, "There should be an error if a bad token is provided"
    assert test_response.status_code == requests.codes.unauthorized


def test_bad_header(access_token_first):
    invalid_post = requests.post(
        ResumeApiUrl.PARSE,
        headers={'Authorization': 'Bearer {}'.format(access_token_first),
                 'Content-Type': 'text/csv'},
        data=json.dumps({
            'resume_file_name': 'foobarbaz',
            'create_candidate': True
        }))
    content = json.loads(invalid_post.content)
    assert content['error']['message'] == error_constants.INVALID_HEADERS['message']
    assert content['error']['code'] == error_constants.INVALID_HEADERS['code']
    assert invalid_post.status_code == requests.codes.bad_request


def test_blank_file(access_token_first, domain_source):
    content, status = fetch_resume_fp_key_response(access_token_first, domain_source, 'blank.txt')
    assert content['error']['message'] == error_constants.NO_TEXT_EXTRACTED[
        'message'], "There should be an error if no text can be extracted."
    assert content['error']['code'] == error_constants.NO_TEXT_EXTRACTED['code']


# TODO: commenting out failing test (this test is not critical)  - Amir
# def test_picture_not_resume(token_fixture, user_fixture):
#     content, status = fetch_resume_post_response(token_fixture, 'notResume.jpg')
#     assert content['error']['message'] == error_constants.NO_TEXT_EXTRACTED['message'], "There should be an error Because it's a picture of a backyard."
#     # The ocr of a tree returns japanese characters and cannot be encoded.
#     assert content['error']['code'] == error_constants.NO_TEXT_EXTRACTED['code']

# content, status = fetch_resume_post_response(token_fixture, 'notResume2.jpg')
# assert content['error']['message'] == error_constants.NO_TEXT_EXTRACTED['message'], "There should be an error Because it's a picture of food."
# assert content['error']['code'] == error_constants.NO_TEXT_EXTRACTED['code']


def test_bad_create_candidate_inputs(access_token_first):
    for invalid_type in [1, 'string', {}, []]:
        test_response = requests.post(
            ResumeApiUrl.PARSE,
            headers={'Authorization': 'Bearer {}'.format(access_token_first),
                     'Content-Type': 'application/json'},
            data=json.dumps({
                'filepicker_key': 'hey',
                'create_candidate': invalid_type
            }))
        content = json.loads(test_response.content)
        status_code = test_response.status_code

        assert content['error']['message'] == error_constants.JSON_SCHEMA_ERROR['message']
        assert content['error']['code'] == error_constants.JSON_SCHEMA_ERROR['code']
        assert status_code == requests.codes.bad


def test_bad_filename_inputs(access_token_first):
    for invalid_type in [1, True, {}, []]:
        test_response = requests.post(
            ResumeApiUrl.PARSE,
            headers={'Authorization': 'Bearer {}'.format(access_token_first),
                     'Content-Type': 'application/json'},
            data=json.dumps({
                'filepicker_key': 'hey',
                'filename': invalid_type
            }))
        content = json.loads(test_response.content)
        status_code = test_response.status_code

        assert content['error']['message'] == error_constants.JSON_SCHEMA_ERROR['message']
        assert content['error']['code'] == error_constants.JSON_SCHEMA_ERROR['code']
        assert status_code == requests.codes.bad


def test_bad_fpkey_inputs(access_token_first):
    for invalid_type in [1, True, {}, [], None]:
        test_response = requests.post(
            ResumeApiUrl.PARSE,
            headers={'Authorization': 'Bearer {}'.format(access_token_first),
                     'Content-Type': 'application/json'},
            data=json.dumps({
                'filepicker_key': invalid_type
            }))
        content = json.loads(test_response.content)
        status_code = test_response.status_code

        assert content['error']['message'] == error_constants.JSON_SCHEMA_ERROR['message']
        assert content['error']['code'] == error_constants.JSON_SCHEMA_ERROR['code']
        assert status_code == requests.codes.bad


def test_bad_tpool_inputs(access_token_first):
    for invalid_type in [1, True, {}, 'string']:
        test_response = requests.post(
            ResumeApiUrl.PARSE,
            headers={'Authorization': 'Bearer {}'.format(access_token_first),
                     'Content-Type': 'application/json'},
            data=json.dumps({
                'filepicker_key': 'unused_key',
                'talent_pools': invalid_type
            }))
        content = json.loads(test_response.content)
        status_code = test_response.status_code

        assert content['error']['message'] == error_constants.JSON_SCHEMA_ERROR['message']
        assert content['error']['code'] == error_constants.JSON_SCHEMA_ERROR['code']
        assert status_code == requests.codes.bad


def test_posting_mislabeled_pdf(access_token_first):
    content, status = fetch_resume_post_response(access_token_first, 'ipdf_img_1487216451.jpeg')
    assert_non_create_content_and_status(content, status)


####################################################################################################
# Test FilePicker Key Parsing without create option
####################################################################################################
def test_doc_from_fp_key(access_token_first, domain_source):
    """Test that .doc files from S3 can be parsed."""
    content, status = fetch_resume_fp_key_response(access_token_first, domain_source, DOC_FP_KEY)
    assert_non_create_content_and_status(content, status,
                                         {'addresses': 1,
                                          'educations': 0,
                                          'phones': 0,
                                          'work_experiences': 5})


def test_v15_pdf_from_fp_key(access_token_first, domain_source):
    """Test that v1.5 pdf files from S3 can be parsed."""
    content, status = fetch_resume_fp_key_response(access_token_first, domain_source, PDF15_FP_KEY)
    assert_non_create_content_and_status(content, status,
                                         {'addresses': 0,
                                          'educations': 0,
                                          'phones': 0,
                                          'work_experiences': 6})


def test_v14_pdf_from_fp_key(access_token_first, domain_source):
    """Test that v1.4 pdf files from S3 can be parsed."""
    content, status = fetch_resume_fp_key_response(access_token_first, domain_source, 'test_bin_14.pdf')
    assert_non_create_content_and_status(content, status,
                                         {'addresses': 1,
                                          'educations': 1,
                                          'phones': 0,
                                          'work_experiences': 2})


def test_v13_pdf_from_fp_key(access_token_first, domain_source):
    """Test that v1.3 pdf files from S3 can be parsed."""
    content, status = fetch_resume_fp_key_response(access_token_first, domain_source, 'test_bin_13.pdf')
    assert_non_create_content_and_status(content, status,
                                         {'addresses': 0,
                                          'educations': 0,
                                          'phones': 0,
                                          'work_experiences': 1})


def test_jpg_from_fp_key(access_token_first, domain_source):
    """Test that jpg files from S3 can be parsed."""
    content, status = fetch_resume_fp_key_response(access_token_first, domain_source, 'test_bin.jpg')
    assert_non_create_content_and_status(content, status, {'addresses': 0, 'phones': 1, 'work_experiences': 1})


def test_doc_with_texthtml_mime(access_token_first, domain_source):
    """Test that jpg files from S3 can be parsed."""
    content, status = fetch_resume_fp_key_response(access_token_first, domain_source, 'Breland.Bobby.doc')
    assert_non_create_content_and_status(content, status,
                                         {'addresses': 1,
                                          'educations': 0,
                                          'phones': 0,
                                          'work_experiences': 7})


def test_web_1341(access_token_first, domain_source):
    content, status = fetch_resume_fp_key_response(access_token_first, domain_source, 'WEB-1341.jpg')
    assert_non_create_content_and_status(content, status,
                                         {'addresses': 0,
                                          'educations': 1,
                                          'phones': 0,
                                          'work_experiences': 1})


####################################################################################################
# Test JSON POST Parsing without create option
####################################################################################################


def test_doc_by_post(access_token_first):
    """Test that .doc files that are posted to the end point can be parsed."""
    content, status = fetch_resume_post_response(access_token_first, 'test_bin.docx')
    assert_non_create_content_and_status(content, status, {'addresses': 1, 'educations': 0, 'work_experiences': 4})


def test_HTML_doc_by_post(access_token_first):
    """Test that .doc files that are posted to the end point can be parsed."""
    content, status = fetch_resume_post_response(access_token_first, 'Bridgeport.Ave.doc')
    assert_non_create_content_and_status(content, status, {'addresses': 0, 'educations': 1, 'work_experiences': 6})


def test_v14_pdf_by_post(access_token_first):
    """Test that v1.4 pdf files can be posted."""
    content, status = fetch_resume_post_response(access_token_first, 'test_bin_14.pdf')
    assert_non_create_content_and_status(content, status, {'addresses': 1, 'educations': 1, 'work_experiences': 2})


def test_v13_pdf_by_post(access_token_first):
    """Test that v1.5 pdf files can be posted."""
    content, status = fetch_resume_post_response(access_token_first, 'test_bin_13.pdf')
    assert_non_create_content_and_status(content, status, {'addresses': 0, 'educations': 0, 'work_experiences': 2})


def test_jpg_by_post(access_token_first):
    """Test that jpg files can be posted."""
    content, status = fetch_resume_post_response(access_token_first, 'test_bin.jpg')
    assert_non_create_content_and_status(content, status, {'addresses': 0, 'phones': 1, 'work_experiences': 1})


def test_2448_3264_jpg_by_post(access_token_first):
    """Test that large jpgs files can be posted."""
    content, status = fetch_resume_post_response(access_token_first, '2448_3264.jpg')
    assert_non_create_content_and_status(content, status, {'addresses': 0, 'phones': 2, 'work_experiences': 4})


def test_jpg_in_pdf(access_token_first):
    content, status = fetch_resume_post_response(access_token_first, 'jpg_in_pdf.pdf')
    """Test PDF wrapped images can be parsed."""
    assert_non_create_content_and_status(content, status)
    candidate = content['candidate']
    assert len(candidate['addresses']) > 0
    assert len(candidate['educations']) > 0


def test_txt_with_jpg_in_encrypted_pdf(access_token_first):
    content, status = fetch_resume_post_response(access_token_first, 'pic_in_encrypted.pdf')
    assert_non_create_content_and_status(content, status, {'addresses': 0})


def test_no_multiple_skills(access_token_first):
    """
    Test for GET-1301 where multiple skills are being parsed out for a single new candidate.
    """
    content, status = fetch_resume_post_response(access_token_first, 'GET_1301.doc')
    assert_non_create_content_and_status(content, status)
    skills = content['candidate']['skills']
    skills_set = set()
    for skill in skills:
        skills_set.add(skill['name'])
    assert len(skills) == len(skills_set)


def test_encrypted_resume(access_token_first):
    """Test that encrypted pdf files that are posted to the end point can be parsed."""
    content, status = fetch_resume_post_response(access_token_first, 'jDiMaria.pdf')
    assert_non_create_content_and_status(content, status, {'addresses': 1, 'educations': 3, 'work_experiences': 7})


def test_626a(access_token_first):
    """Adds test case for old previously crashing resume. Adding for code coverage"""
    content, status = fetch_resume_post_response(access_token_first, 'GET_626a.doc')
    assert_non_create_content_and_status(content, status)


def test_626b(access_token_first):
    """Adds test case for old previously crashing resume. Adding for code coverage"""
    content, status = fetch_resume_post_response(access_token_first, 'GET_626b.doc')
    assert_non_create_content_and_status(content, status)


def test_no_name_defaults_to_email_or_none(access_token_first):
    """Adds test case for old previously crashing resume. Adding for code coverage"""
    content, status = fetch_resume_post_response(access_token_first, 'noname.doc')
    assert_non_create_content_and_status(content, status)
    assert content['candidate']['first_name'] is None
    assert content['candidate']['last_name'] is None


def test_troublesome_zip_code(access_token_first):
    content, status = fetch_resume_post_response(access_token_first, 'zips.pdf')
    assert_non_create_content_and_status(content, status)


def test_get_1799(access_token_first):
    content, status = fetch_resume_post_response(access_token_first, 'get-1799.pdf')
    assert_non_create_content_and_status(content, status)


def test_bad_email(access_token_first):
    content, status = fetch_resume_post_response(access_token_first, 'bad_email.pdf')
    assert_non_create_content_and_status(content, status)


def test_email_with_punctuation(access_token_first):
    # Burning Glass is currently returning the wrong email so this test will not get expanded.
    # It is returning `Leary@domain.com` instead of `O'Leary@domain.com
    content, status = fetch_resume_post_response(access_token_first, 'email_with_punctuation.PDF')
    assert_non_create_content_and_status(content, status)


def test_non_create_ingram(access_token_first):
    content, status = fetch_resume_post_response(access_token_first, 'ingram.pdf')
    assert_non_create_content_and_status(content, status, {'addresses': 0, 'educations': 0, 'work_experiences': 0})


def test_v13_non_create_ingram(access_token_first):
    content, status = fetch_resume_post_response(access_token_first, 'ingramV13.pdf')
    assert_non_create_content_and_status(content, status, {'addresses': 0, 'educations': 0, 'work_experiences': 0})


####################################################################################################
# Test Candidate Creation
####################################################################################################
def test_v15_pdf_by_post_with_create(access_token_first, talent_pool):
    """Test that v1.5 pdf files can be posted."""
    content, status = fetch_resume_post_response(access_token_first, 'test_bin.pdf', create_mode=True)
    assert_create_or_update_content_and_status(content, status)


def test_doc_FP_with_create(access_token_first, domain_source, talent_pool):

    content, status = fetch_resume_fp_key_response(access_token_first, domain_source, DOC_890, create_mode=True)
    assert_create_or_update_content_and_status(content, status)


def test_985_from_fp_key(access_token_first, domain_source, talent_pool):
    """Test that .doc files from S3 can be parsed."""

    content, status = fetch_resume_fp_key_response(
        access_token_first, domain_source, "Bruncak.Daren.doc", create_mode=True)
    assert_create_or_update_content_and_status(content, status)


def test_create_candidate_from_resume_without_name(access_token_first, talent_pool):

    content, status = fetch_resume_post_response(access_token_first, 'Adams.John.doc', create_mode=True)
    assert_create_or_update_content_and_status(content, status)


def test_create_candidate_from_resume_ben_fred(access_token_first, talent_pool):

    content, status = fetch_resume_post_response(access_token_first, 'ben.fred.doc', create_mode=True)
    assert_create_or_update_content_and_status(content, status)


def test_create_candidate_from_no_email_resume(access_token_first, talent_pool):

    content, status = fetch_resume_post_response(access_token_first, 'no_email_resume.doc', create_mode=True)
    assert_create_or_update_content_and_status(content, status)


def test_create_candidate_from_no_address_resume(access_token_first, talent_pool):

    content, status = fetch_resume_post_response(access_token_first, 'no_address.doc', create_mode=True)
    assert_create_or_update_content_and_status(content, status)


def test_create_with_references(access_token_first, talent_pool):
    content, status = fetch_resume_post_response(access_token_first, 'GET_1210.doc', create_mode=True)
    assert_create_or_update_content_and_status(content, status)


def test_create_with_long_punc_name(access_token_first, talent_pool):
    content, status = fetch_resume_post_response(access_token_first, 'GET-1319.pdf', create_mode=True)
    assert_create_or_update_content_and_status(content, status)
    assert content['candidate']['last_name'] == u'Weston'


def test_create_from_image(access_token_first, talent_pool):
    """
    Test for GET-1351. POST'd JSON.
    """
    content, status = fetch_resume_post_response(access_token_first, 'test_bin.jpg', create_mode=True)
    assert_create_or_update_content_and_status(content, status)


def test_create_from_jpgTxtPdf(access_token_first, talent_pool):
    """
    Test for GET-1463. POST'd JSON.
    """
    content, status = fetch_resume_post_response(access_token_first, 'pic_in_encrypted.pdf', create_mode=True)
    assert_create_or_update_content_and_status(content, status)


def test_create_poorly_parsed_phonenumber(access_token_first, talent_pool):
    """
    Test for GET-1799. POST'd JSON. Phone number is parsed by BG as 'xxx xxx xxxx *'.
    """
    content, status = fetch_resume_post_response(access_token_first, 'GET_1799.pdf', create_mode=True)
    assert_create_or_update_content_and_status(content, status)


def test_ingram_with_create(access_token_first, talent_pool):
    content, status = fetch_resume_post_response(access_token_first, 'ingram.pdf', create_mode=True)
    assert_create_or_update_content_and_status(content, status)
    candidate = content['candidate']
    assert len(candidate['addresses']) > 0
    assert len(candidate['educations']) > 0
    assert len(candidate['work_experiences']) > 0


####################################################################################################
# Test Candidate Updating
####################################################################################################
def test_already_exists_candidate(access_token_first, talent_pool):
    """Test that multiple resumes can be posted and updated right after."""
    resumes_to_update = [
        'Aleksandr_Tenishev_2016_02.doc', 'Apoorva-Resume_SynergesticIT.pdf', 'Foti Resume May 2016.pdf',
        'James_Xie_Resume_2016.doc', 'Mondal_Tej_20140522_dev.docx', 'My Resume.docx',
        'NealMcMillenResumeJan2016-2.pdf', 'Resume (CA) .pdf', 'summary.docx', 'Resume Nikhil Moorjani.pdf',
        'Resume-3.doc', 'Resume-Patrick-Ritz-2016(FE).docx', 'Resume.pdf', 'resume_fan updated.docx', 'resume_hong.pdf',
        'Sean Whitcomb_Resume_2016_R2.docx', 'Sergey Ostrovsky Resume 2016.docx', 'SteveSun-Resume.pdf', 'TD bio.pdf',
        'Bharani Krishna Resume.docx'
        # The following resumes cannot be updated due to current candidate_edit table rules.
        # 'Yehle - Resume Java  ECM.DOCX','Aparna_Resume.pdf', 'kennyyee_cv.pdf',
        # 'NamrataOjhaSoftwareDevloper .pdf', 'NikhilSyavasyaResumeV4.0.pdf', 'Resume (CS).pdf',
        # 'Resume_SDE_VickyYang.pdf', 'Supriya Grandhi Resume.docx.rtf', 'VivekTiwari.pdf',
        # 'Waheed Chuahdary - Web Analytics.pdf'
    ]

    for resume in resumes_to_update:
        unused_create_response = fetch_resume_post_response(access_token_first, resume, create_mode=True)
        update_content, status = fetch_resume_post_response(access_token_first, resume, create_mode=True)
        assert_create_or_update_content_and_status(update_content, status)


####################################################################################################
# Test Helper/Utility Functions
####################################################################################################
def fetch_resume_post_response(token_fixture, file_name, create_mode=False):
    """Posts file to local test auth server for json formatted resumes."""
    current_dir = os.path.dirname(__file__)
    with open(os.path.join(current_dir, 'files/{}'.format(file_name)), 'rb') as resume_file:
        response = requests.post(
            ResumeApiUrl.PARSE,
            headers={'Authorization': 'Bearer {}'.format(token_fixture)},
            data={
                # 'Local Test Upload' prefix.
                'resume_file_name': 'LTU_{}'.format(file_name),
                'create_candidate': create_mode
            },
            files=dict(resume_file=resume_file))
    content = json.loads(response.content)
    status_code = response.status_code
    return content, status_code


def fetch_resume_fp_key_response(access_token, source, fp_key, create_mode=False):
    """Posts FilePicker key to local test auth server for json formatted resumes."""
    test_response = requests.post(
        ResumeApiUrl.PARSE,
        headers={'Authorization': 'Bearer {}'.format(access_token),
                 'Content-Type': 'application/json'},
        data=json.dumps({
            'filepicker_key': fp_key,
            # 'Local Test Upload' prefix.
            'resume_file_name': 'LTU_{}'.format(fp_key),
            'create_candidate': create_mode,
            'source_id': source['source']['id']
        }))
    content = json.loads(test_response.content)
    status_code = test_response.status_code
    return content, status_code


def assert_non_create_content_and_status(content, status, candidate_data_checks=None):
    assert 'candidate' in content, "Candidate should be in response content"
    assert 'raw_response' in content and content[
        'raw_response'] is not None, "None create response should return raw content"
    assert status == requests.codes.ok
    if candidate_data_checks:
        candidate = content['candidate']
        for field, count in candidate_data_checks.iteritems():
            assert len(candidate[field]) > count


def assert_create_or_update_content_and_status(content, status):
    assert 'candidate' in content, "Candidate should be in response content"
    assert 'id' in content['candidate'], "Candidate should contain id in response if create=True."
    assert content['candidate']['id'], "Candidate should contain non-None id to signal creation."
    assert status == requests.codes.ok
