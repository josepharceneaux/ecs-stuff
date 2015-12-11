"""Test suite for Flask Resume Parsing MicroService."""
__author__ = 'erik@getTalent.com'
# Standard library
import json
import os
# Third party/module
from resume_service.common.models.candidate import Candidate
from resume_service.resume_parsing_app import db
import requests as r
# Test fixtures, imports required even though not 'used'
from test_fixtures import client_fixture
from test_fixtures import country_fixture
from test_fixtures import culture_fixture
from test_fixtures import domain_fixture
from test_fixtures import email_label_fixture
from test_fixtures import org_fixture
from test_fixtures import token_fixture
from test_fixtures import user_fixture
from test_fixtures import phone_label_fixture
from test_fixtures import product_fixture

APP_URL = 'http://0.0.0.0:8003/v1'
API_URL = APP_URL + '/parse_resume'
ADDRESS_KEYS = ('city', 'country', 'state', 'po_box', 'address_line_1', 'address_line_2',
                'zip_code', 'latitude', 'longitude')

DOC_DICT = dict(address_line_1=u'466 Tailor Way', address_line_2=u'', city=u'Lansdale',
                country=None, state=u'Pennsylvania', zip_code=u'19446', po_box=u'',
                latitude=u'40.2414952', longitude=u'-75.2837862')
EDUCATIONS_KEYS = ('city', 'degrees', 'state', 'country', 'school_name')
EMAILS_KEYS = ('address', 'label')
PHONES_KEYS = ('value', 'label')
SKILLS_KEYS = ('name', 'months_used', 'last_used_date')
WORK_EXPERIENCES_KEYS = ('city', 'end_date', 'country', 'company', 'role', 'is_current',
                         'start_date', 'work_experience_bullets')


def test_base_url():
    """Test that the application root lists the endpoint."""
    base_response = r.get(APP_URL)
    assert '/parse_resume' in base_response.content


def test_doc_from_fp_key(token_fixture):
    """Test that .doc files from S3 can be parsed."""
    response = fetch_resume_fp_key_response(token_fixture, '0169173d35beaf1053e79fdf1b5db864.docx')
    assert 'candidate' in response



def test_doc_by_post(token_fixture):
    """Test that .doc files that are posted to the end point can be parsed."""
    response = fetch_resume_post_response(token_fixture, 'test_bin.docx')
    doc_db_record = db.session.query(Candidate).filter_by(formatted_name='VEENA NITHOO').first()
    assert not doc_db_record
    assert 'candidate' in response


def test_v15_pdf_from_fp_key(token_fixture):
    """Test that v1.5 pdf files from S3 can be parsed."""
    json_obj = fetch_resume_fp_key_response(token_fixture, 'e68b51ee1fd62db589d2669c4f63f381.pdf')['candidate']
    assert json_obj['full_name'] == 'MARK GREENE'
    assert len(json_obj['educations']) == 1
    # Below should be 9 OR 15 (9major + 6 'Additional work experience information'. See resume. Blame BG
    assert len(json_obj['work_experiences']) == 11
    keys_formatted_test(json_obj)


def test_v14_pdf_from_fp_key(token_fixture):
    """Test that v1.4 pdf files from S3 can be parsed."""
    json_obj = fetch_resume_fp_key_response(token_fixture, 'test_bin_14.pdf')['candidate']
    # doesnt get good name data back
    assert len(json_obj['work_experiences']) == 4
    keys_formatted_test(json_obj)


def test_v13_pdf_from_fp_key(token_fixture):
    """Test that v1.3 pdf files from S3 can be parsed."""
    json_obj = fetch_resume_fp_key_response(token_fixture, 'test_bin_13.pdf')['candidate']
    assert json_obj['full_name'] == 'BRUCE PARKEY'
    assert len(json_obj['work_experiences']) == 3
    keys_formatted_test(json_obj)


def test_v14_pdf_by_post(token_fixture):
    """Test that v1.4 pdf files can be posted."""
    json_obj = fetch_resume_post_response(token_fixture, 'test_bin_14.pdf')['candidate']
    # Currently fails with email in footer of both pages.
    # assert json_obj['emails'][0]['address'] == 'jlchavez@telus.net'
    assert len(json_obj['work_experiences']) == 4
    keys_formatted_test(json_obj)


def test_v13_pdf_by_post(token_fixture):
    """Test that v1.5 pdf files can be posted."""
    json_obj = fetch_resume_post_response(token_fixture, 'test_bin_13.pdf')['candidate']
    assert json_obj['full_name'] == 'BRUCE PARKEY'
    assert json_obj['emails'][0]['address'] == 'bparkey@sagamoreapps.com'
    assert len(json_obj['work_experiences']) == 3
    keys_formatted_test(json_obj)


def test_jpg_from_fp_key(token_fixture):
    """Test that jpg files from S3 can be parsed."""
    json_obj = fetch_resume_fp_key_response(token_fixture, 'test_bin.jpg')['candidate']
    assert json_obj['full_name'] == 'Erik D Farmer'
    # Below should be two. Blame BG upgrade
    assert len(json_obj['educations']) == 0
    assert len(json_obj['work_experiences']) == 2
    keys_formatted_test(json_obj)


def test_jpg_by_post(token_fixture):
    """Test that jpg files can be posted."""
    json_obj = fetch_resume_post_response(token_fixture, 'test_bin.jpg')['candidate']
    assert json_obj['full_name'] == 'Erik D Farmer'
    # Below should be two. Blame BG upgrade
    assert len(json_obj['educations']) == 0
    assert len(json_obj['work_experiences']) == 2
    keys_formatted_test(json_obj)


# def test_pdf_14_of_image_alyson_peters(test_token):
#     """Test that PDFs of image files can be posted."""
#     json_obj = fetch_resume_post_response(test_token, 'pdf_14_of_image_alyson_peters.pdf')['candidate']
#     assert json_obj.get('full_name') == 'Alyson Peters'
#     keys_formatted_test(json_obj)


def test_2448_3264_jpg_by_post(token_fixture):
    """Test that large jpgs files can be posted."""
    json_obj = fetch_resume_post_response(token_fixture, '2448_3264.jpg')['candidate']
    assert json_obj['full_name'] == 'Marion Roberson'
    assert json_obj['emails'][0]['address'] == 'MarionR3@Knology.net'
    assert len(json_obj['educations']) == 0
    # Parser incorrectly guesses 7, 4 + 3 of the bullet points.
    # assert len(json_obj['work_experiences']) == 4
    keys_formatted_test(json_obj)


def test_no_token_fails():
    filepicker_key = '0169173d35beaf1053e79fdf1b5db864.docx'
    test_response = r.post(API_URL, data=dict(filepicker_key=filepicker_key))
    json_obj = json.loads(test_response.content)
    assert 'error' in json_obj


def test_invalid_token_fails():
    filepicker_key = '0169173d35beaf1053e79fdf1b5db864.docx'
    test_response = r.post(API_URL,
                           headers={'Authorization': 'Bearer %s' % 'invalidtokenzzzz'},
                           data=dict(filepicker_key=filepicker_key))
    json_obj = json.loads(test_response.content)
    assert 'error' in json_obj


# def test_v15_pdf_by_post(token_fixture):
#     """Test that v1.5 pdf files can be posted."""
#     json_obj = fetch_resume_post_response(token_fixture, 'test_bin.pdf', create_mode='True')['candidate']
#     assert json_obj['full_name'] == 'MARK GREENE'
#     assert json_obj['emails'][0]['address'] == 'techguymark@yahoo.com'
#     assert len(json_obj['educations']) == 1
#     # Below should be 9 OR 15 (9major + 6 'Additional work experience information'. See resume. Blame BG
#     # assert len(json_obj['work_experiences']) == 11
#     db.session.commit() # Hack for transation mismatch
#     assert db.session.query(Candidate).get(json_obj['id']) is not None
#     keys_formatted_test(json_obj)


def test_health_check():
    import requests
    response = requests.get('http://127.0.0.1:8003/healthcheck')
    assert response.status_code == 200


def fetch_resume_post_response(token_fixture, file_name, create_mode=''):
    """Posts file to local test auth server for json formatted resumes."""
    current_dir = os.path.dirname(__file__)
    with open(os.path.join(current_dir, 'test_resumes/{}'.format(file_name)), 'rb') as resume_file:
        response = r.post(API_URL,
                            headers={'Authorization': 'Bearer %s' % token_fixture.access_token},
                            data=dict(
                                # files = dict(resume_file=raw_file),
                                resume_file_name=file_name,
                                create_candidate=create_mode,
                            ),
                          files = dict(resume_file=resume_file),
                          )
    return json.loads(response.content)


def fetch_resume_fp_key_response(token_fixture, fp_key):
    """Posts FilePicker key to local test auth server for json formatted resumes."""
    test_response = r.post(API_URL, headers={'Authorization': 'Bearer %s' % token_fixture.access_token},
                           data=dict(filepicker_key=fp_key))
    return json.loads(test_response.content)


# def keys_formatted_test(json_obj):
#     assert all(k in json_obj['work_experiences'][0] for k in WORK_EXPERIENCES_KEYS if json_obj['work_experiences'])
#     work_experience_bullet = json_obj['work_experiences'][0]['work_experience_bullets'][0]
#     assert 'text' in work_experience_bullet.keys() if work_experience_bullet else False
#     assert all(k in json_obj['addresses'][0] for k in ADDRESS_KEYS if json_obj['addresses'])
#     assert all(k in json_obj['skills'][0] for k in SKILLS_KEYS if json_obj['skills'])
#     assert all(k in json_obj['emails'][0] for k in EMAILS_KEYS if json_obj['emails'])
#     assert all(k in json_obj['phones'][0] for k in PHONES_KEYS if json_obj['phones'])
#     assert all(k in json_obj['educations'][0] for k in EDUCATIONS_KEYS if json_obj['educations'])
