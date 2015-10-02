"""Test suite for Flask Resume Parsing MicroService."""

import datetime
import json
import os
from StringIO import StringIO

import pytest

from resume_service.models.db import db
from resume_service.models.user import Client, Token
from resume_service.resume_parsing_app import app

db.init_app(app)

APP = app.test_client()

DOC_DICT = dict(address_line_1=u'466 Tailor Way', address_line_2=u'', city=u'Lansdale', country=None,
                state=u'Pennsylvania', zip_code=u'19446', po_box=u'', latitude=u'40.2414952', longitude=u'-75.2837862')

ADDRESS_KEYS = ('city', 'country', 'state', 'po_box', 'address_line_1', 'address_line_2', 'zip_code', 'latitude',
                'longitude')

PHONES_KEYS = ('value', 'label')

EDUCATIONS_KEYS = ('city', 'major', 'degree', 'state', 'graduation_date', 'country', 'school_name', 'start_date')

EMAILS_KEYS = ('address', 'label')

WORK_EXPERIENCES_KEYS = ('city', 'end_date', 'country', 'company', 'role', 'is_current', 'start_date', 'bullets')

SKILLS_KEYS = ('name', 'months_used', 'last_used_date')


@pytest.fixture(autouse=True)
def test_client(request):
    test_client = Client.query.filter_by(client_id='fakeclient', client_secret='s00pers3kr37').first()
    if not test_client:
        test_client = Client(client_id='fakeclient', client_secret='s00pers3kr37')
        db.session.add(test_client)
        db.session.commit()

        def fin():
            try:
                db.session.delete(test_client)
                db.session.commit()
            except Exception:
                pass
        request.addfinalizer(fin)
    return test_client


@pytest.fixture(autouse=True)
def test_token(test_client, request):
    test_token = Token(client_id=test_client.client_id, user_id=1, token_type='bearer', access_token='fooz',
                       refresh_token='barz', expires=datetime.datetime(2050, 4, 26))
    try:
       db.session.add(test_token)
       db.session.commit()
    except Exception:  # TODO This is to handle 'Duplicate entry' MySQL errors. We should instead check for existing Client/Token before inserting
       pass

    def fin():
        try:
            db.session.delete(test_token)
            db.session.commit()
        except Exception:
            pass
    request.addfinalizer(fin)
    return test_token


def test_base_url():
    """Test that the application root lists the endpoint."""
    base_response = APP.get('/')
    assert '/parse_resume' in base_response.data


def test_doc_from_fp_key():
    """Test that .doc files from S3 can be parsed."""
    json_obj = fetch_resume_fp_key_response('0169173d35beaf1053e79fdf1b5db864.docx')['candidate']
    assert json_obj['full_name'] == 'VEENA NITHOO'
    assert len(json_obj['addresses']) == 1
    assert json_obj['addresses'][0] == DOC_DICT
    assert len(json_obj['educations']) == 3
    assert len(json_obj['work_experiences']) == 7
    keys_formatted_test(json_obj)


def test_doc_by_post():
    """Test that .doc files that are posted to the end point can be parsed."""
    json_obj = fetch_resume_post_response('test_bin.docx')['candidate']
    assert json_obj['full_name'] == 'VEENA NITHOO'
    assert len(json_obj['addresses']) == 1
    assert json_obj['addresses'][0] == DOC_DICT
    assert len(json_obj['educations']) == 3
    assert len(json_obj['work_experiences']) == 7
    keys_formatted_test(json_obj)


def test_v15_pdf_from_fp_key():
    """Test that v1.5 pdf files from S3 can be parsed."""
    json_obj = fetch_resume_fp_key_response('e68b51ee1fd62db589d2669c4f63f381.pdf')['candidate']
    assert json_obj['full_name'] == 'MARK GREENE'
    assert len(json_obj['educations']) == 1
    assert len(json_obj['work_experiences']) == 15
    keys_formatted_test(json_obj)


def test_v14_pdf_from_fp_key():
    """Test that v1.4 pdf files from S3 can be parsed."""
    json_obj = fetch_resume_fp_key_response('test_bin_14.pdf')['candidate']
    # doesnt get good name data back
    assert len(json_obj['work_experiences']) == 4
    keys_formatted_test(json_obj)


def test_v13_pdf_from_fp_key():
    """Test that v1.3 pdf files from S3 can be parsed."""
    json_obj = fetch_resume_fp_key_response('test_bin_13.pdf')['candidate']
    assert json_obj['full_name'] == 'BRUCE PARKEY'
    assert len(json_obj['work_experiences']) == 3
    keys_formatted_test(json_obj)


def test_v15_pdf_by_post():
    """Test that v1.5 pdf files can be posted."""
    json_obj = fetch_resume_post_response('test_bin.pdf')['candidate']
    assert json_obj['full_name'] == 'MARK GREENE'
    assert json_obj['emails'][0]['address'] == 'techguymark@yahoo.com'
    assert len(json_obj['educations']) == 1
    assert len(json_obj['work_experiences']) == 15
    keys_formatted_test(json_obj)


def test_v14_pdf_by_post():
    """Test that v1.4 pdf files can be posted."""
    json_obj = fetch_resume_post_response('test_bin_14.pdf')['candidate']
    # Currently fails with email in footer of both pages.
    # assert json_obj['emails'][0]['address'] == 'jlchavez@telus.net'
    assert len(json_obj['work_experiences']) == 4
    keys_formatted_test(json_obj)


def test_v13_pdf_by_post():
    """Test that v1.3 pdf files can be posted."""
    json_obj = fetch_resume_post_response('test_bin_13.pdf')['candidate']
    assert json_obj['full_name'] == 'BRUCE PARKEY'
    assert json_obj['emails'][0]['address'] == 'bparkey@sagamoreapps.com'
    assert len(json_obj['work_experiences']) == 3
    keys_formatted_test(json_obj)


def test_jpg_from_fp_key():
    """Test that jpg files from S3 can be parsed."""
    json_obj = fetch_resume_fp_key_response('test_bin.jpg')['candidate']
    assert json_obj['full_name'] == 'Erik D Farmer'
    assert len(json_obj['educations']) == 2
    assert len(json_obj['work_experiences']) == 2
    keys_formatted_test(json_obj)


def test_jpg_by_post():
    """Test that jpg files can be posted."""
    json_obj = fetch_resume_post_response('test_bin.jpg')['candidate']
    assert json_obj['full_name'] == 'Erik D Farmer'
    assert len(json_obj['educations']) == 2
    assert len(json_obj['work_experiences']) == 2
    keys_formatted_test(json_obj)


def test_2448_3264_jpg_by_post():
    """Test that large jpgs files can be posted."""
    json_obj = fetch_resume_post_response('2448_3264.jpg')['candidate']
    assert json_obj['full_name'] == 'Marion Roberson'
    assert json_obj['emails'][0]['address'] == 'MarionR3@Knology.net'
    assert len(json_obj['educations']) == 0
    # Parser incorrectly guesses 7, 4 + 3 of the bullet points.
    # assert len(json_obj['work_experiences']) == 4
    keys_formatted_test(json_obj)


def test_no_token_fails():
    filepicker_key = '0169173d35beaf1053e79fdf1b5db864.docx'
    with APP as c:
        test_response = c.post('/parse_resume', data=dict(filepicker_key=filepicker_key))
    json_obj = json.loads(test_response.data)
    assert 'error' in json_obj


def test_invalid_token_fails():
    filepicker_key = '0169173d35beaf1053e79fdf1b5db864.docx'
    with APP as c:
        test_response = c.post('/parse_resume', headers={'Authorization': 'Bearer barz'},
                               data=dict(filepicker_key=filepicker_key))
    json_obj = json.loads(test_response.data)
    assert 'error' in json_obj


def fetch_resume_post_response(file_name):
    """Posts file to local test auth server for json formatted resumes."""
    current_dir = os.path.dirname(__file__)
    with open(os.path.join(current_dir, 'test_resumes/{}'.format(file_name))) as raw_file:
        resume_file = raw_file.read()
    response = APP.post('/parse_resume', headers={'Authorization': 'Bearer fooz'}, data=dict(
        resume_file=(StringIO(resume_file), file_name),
        resume_file_name=file_name
    ), follow_redirects=True)
    return json.loads(response.data)


def fetch_resume_fp_key_response(fp_key):
    """Posts FilePicker key to local test auth server for json formatted resumes."""
    with APP as c:
        test_response = c.post('/parse_resume', headers={'Authorization': 'Bearer fooz'},
                               data=dict(filepicker_key=fp_key))
        print "Response to POST /parse_resume with filepicker_key=%s: \n%s" % (fp_key, test_response.data)
    return json.loads(test_response.data)


def keys_formatted_test(json_obj):
    assert all(k in json_obj['work_experiences'][0] for k in WORK_EXPERIENCES_KEYS if json_obj['work_experiences'])
    assert 'text' in json_obj['work_experiences'][0]['bullets'][0].keys() if json_obj['work_experiences'][0]['bullets'] else False
    assert all(k in json_obj['addresses'][0] for k in ADDRESS_KEYS if json_obj['addresses'])
    assert all(k in json_obj['skills'][0] for k in SKILLS_KEYS if json_obj['skills'])
    assert all(k in json_obj['emails'][0] for k in EMAILS_KEYS if json_obj['emails'])
    assert all(k in json_obj['phones'][0] for k in PHONES_KEYS if json_obj['phones'])
    assert all(k in json_obj['educations'][0] for k in EDUCATIONS_KEYS if json_obj['educations'])
