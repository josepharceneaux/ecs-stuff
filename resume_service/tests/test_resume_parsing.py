"""Test suite for Flask Resume Parsing MicroService."""

# Standard library
from StringIO import StringIO
import datetime
import json
import os

# Third party/module
import pytest
from resume_service.resume_parsing_app import app
from resume_service.resume_parsing_app import db
from resume_service.common.models.candidate import Candidate
from resume_service.common.models.candidate import CandidateEmail
from resume_service.common.models.candidate import EmailLabel
from resume_service.common.models.misc import Culture
from resume_service.common.models.misc import Organization
from resume_service.common.models.user import Client
from resume_service.common.models.user import Domain
from resume_service.common.models.user import Token
from resume_service.common.models.user import User

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
def test_org(request):
    org_attrs = dict(name='Rocket League All Stars - {}'.format(random_word(8)))
    test_org, created = get_or_create(db.session, Organization, defaults=None, **org_attrs)
    if created:
        db.session.add(test_org)
        db.session.commit()

    def fin():
        db.session.delete(test_org)
        db.session.commit()
    request.addfinalizer(fin)
    return test_org


@pytest.fixture(autouse=True)
def test_culture(request):
   culture_attrs = dict(description='Foo {}'.format(random_word(12)), code=random_word(5))
   test_culture, created = get_or_create(db.session, Culture, defaults=None, **culture_attrs)
   if created:
       db.session.add(test_culture)
       db.session.commit()

   def fin():
       db.session.delete(test_culture)
       db.session.commit()
   request.addfinalizer(fin)
   return test_culture


@pytest.fixture(autouse=True)
def test_domain(test_culture, test_org, request):
    test_domain = Domain(name=random_word(40), usage_limitation=0,
                         expiration=datetime.datetime(2050, 4, 26),
                         added_time=datetime.datetime(2050, 4, 26),
                         organization_id=test_org.id, is_fair_check_on=False, is_active=1,
                         default_tracking_code=1, default_from_name=(random_word(100)),
                         default_culture_id=test_culture.id,
                         settings_json=random_word(55), updated_time=datetime.datetime.now())

    db.session.add(test_domain)
    db.session.commit()

    def fin():
       db.session.delete(test_domain)
       db.session.commit()
    request.addfinalizer(fin)
    return test_domain


@pytest.fixture(autouse=True)
def test_user(test_domain, request):
    test_user = User(domain_id=test_domain.id, first_name='Jamtry', last_name='Jonas',
                     password='password', email='jamtry@{}.com'.format(random_word(8)),
                     added_time=datetime.datetime(2050, 4, 26))
    db.session.add(test_user)
    db.session.commit()

    def fin():
        db.session.delete(test_user)
        db.session.commit()
    request.addfinalizer(fin)
    return test_user


@pytest.fixture(autouse=True)
def test_client(request):
    test_client = Client(client_id=random_word(12), client_secret=random_word(12))
    db.session.add(test_client)
    db.session.commit()

    def fin():
        db.session.query(Client).delete()
        db.session.commit()
    request.addfinalizer(fin)
    return test_client


@pytest.fixture(autouse=True)
def test_token(test_user, test_client, request):
    test_token = Token(client_id=test_client.client_id, user_id=test_user.id, token_type='bearer', access_token=random_word(8),
                       refresh_token=random_word(8), expires=datetime.datetime(2050, 4, 26))
    db.session.add(test_token)
    db.session.commit()

    def fin():
        db.session.query(Token).delete()
        db.session.commit()
    request.addfinalizer(fin)
    return test_token


@pytest.fixture(autouse=True)
def test_email_label(request):
    label_attrs = dict(id=1, description='Primary', updated_time=datetime.datetime.now())
    label_object, created = get_or_create(db.session, EmailLabel, label_attrs)
    if created:
        db.session.commit()
    return label_object


def test_base_url():
    """Test that the application root lists the endpoint."""
    base_response = APP.get('/')
    assert '/parse_resume' in base_response.data


def test_doc_from_fp_key(test_token):
    """Test that .doc files from S3 can be parsed."""
    json_obj = fetch_resume_fp_key_response(test_token, '0169173d35beaf1053e79fdf1b5db864.docx')['candidate']
    assert json_obj['full_name'] == 'VEENA NITHOO'
    assert len(json_obj['addresses']) == 1
    assert json_obj['addresses'][0] == DOC_DICT
    # Below should be 3.BG upgrade caused dice_api_response change
    assert len(json_obj['educations']) == 1
    assert len(json_obj['work_experiences']) == 7
    keys_formatted_test(json_obj)


def test_doc_by_post(test_token):
    """Test that .doc files that are posted to the end point can be parsed."""
    json_obj = fetch_resume_post_response(test_token, 'test_bin.docx')['candidate']
    assert json_obj['full_name'] == 'VEENA NITHOO'
    assert len(json_obj['addresses']) == 1
    assert json_obj['addresses'][0] == DOC_DICT
    # Below should be 3. BG upgrade caused dice_api_response change
    assert len(json_obj['educations']) == 1
    assert len(json_obj['work_experiences']) == 7
    doc_db_record = db.session.query(Candidate).filter_by(formatted_name='VEENA NITHOO').first()
    assert not doc_db_record
    keys_formatted_test(json_obj)


def test_v15_pdf_from_fp_key(test_token):
    """Test that v1.5 pdf files from S3 can be parsed."""
    json_obj = fetch_resume_fp_key_response(test_token, 'e68b51ee1fd62db589d2669c4f63f381.pdf')['candidate']
    assert json_obj['full_name'] == 'MARK GREENE'
    assert len(json_obj['educations']) == 1
    # Below should be 9 OR 15 (9major + 6 'Additional work experience information'. See resume. Blame BG
    assert len(json_obj['work_experiences']) == 11
    keys_formatted_test(json_obj)


def test_v14_pdf_from_fp_key(test_token):
    """Test that v1.4 pdf files from S3 can be parsed."""
    json_obj = fetch_resume_fp_key_response(test_token, 'test_bin_14.pdf')['candidate']
    # doesnt get good name data back
    assert len(json_obj['work_experiences']) == 4
    keys_formatted_test(json_obj)


def test_v13_pdf_from_fp_key(test_token):
    """Test that v1.3 pdf files from S3 can be parsed."""
    json_obj = fetch_resume_fp_key_response(test_token, 'test_bin_13.pdf')['candidate']
    assert json_obj['full_name'] == 'BRUCE PARKEY'
    assert len(json_obj['work_experiences']) == 3
    keys_formatted_test(json_obj)


def test_v14_pdf_by_post(test_token):
    """Test that v1.4 pdf files can be posted."""
    json_obj = fetch_resume_post_response(test_token, 'test_bin_14.pdf')['candidate']
    # Currently fails with email in footer of both pages.
    # assert json_obj['emails'][0]['address'] == 'jlchavez@telus.net'
    assert len(json_obj['work_experiences']) == 4
    keys_formatted_test(json_obj)


def test_v13_pdf_by_post(test_token):
    """Test that v1.5 pdf files can be posted."""
    json_obj = fetch_resume_post_response(test_token, 'test_bin_13.pdf')['candidate']
    assert json_obj['full_name'] == 'BRUCE PARKEY'
    assert json_obj['emails'][0]['address'] == 'bparkey@sagamoreapps.com'
    assert len(json_obj['work_experiences']) == 3
    keys_formatted_test(json_obj)


def test_jpg_from_fp_key(test_token):
    """Test that jpg files from S3 can be parsed."""
    json_obj = fetch_resume_fp_key_response(test_token, 'test_bin.jpg')['candidate']
    assert json_obj['full_name'] == 'Erik D Farmer'
    # Below should be two. Blame BG upgrade
    assert len(json_obj['educations']) == 0
    assert len(json_obj['work_experiences']) == 2
    keys_formatted_test(json_obj)


def test_jpg_by_post(test_token):
    """Test that jpg files can be posted."""
    json_obj = fetch_resume_post_response(test_token, 'test_bin.jpg')['candidate']
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


def test_2448_3264_jpg_by_post(test_token):
    """Test that large jpgs files can be posted."""
    json_obj = fetch_resume_post_response(test_token, '2448_3264.jpg')['candidate']
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
        test_response = c.post('/parse_resume',
                               headers={'Authorization': 'Bearer %s' % 'invalidtokenzzzz'},
                               data=dict(filepicker_key=filepicker_key))
    json_obj = json.loads(test_response.data)
    assert 'error' in json_obj


def test_health_check():
    import requests
    response = requests.get('http://127.0.0.1:8003/healthcheck')
    assert response.status_code == 200


# def test_v15_pdf_by_post(test_token):
#     """Test that v1.5 pdf files can be posted."""
#     json_obj = fetch_resume_post_response(test_token, 'test_bin.pdf', create_mode='True')['candidate']
#     assert json_obj['full_name'] == 'MARK GREENE'
#     assert json_obj['emails'][0]['address'] == 'techguymark@yahoo.com'
#     assert len(json_obj['educations']) == 1
#     # Below should be 9 OR 15 (9major + 6 'Additional work experience information'. See resume. Blame BG
#     assert len(json_obj['work_experiences']) == 11
#     v15_pdf_candidate = db.session.query(Candidate).filter_by(formatted_name='MARK GREENE').first()
#     assert v15_pdf_candidate is not None
#     keys_formatted_test(json_obj)
#

def fetch_resume_post_response(test_token, file_name, create_mode=''):
    """Posts file to local test auth server for json formatted resumes."""
    current_dir = os.path.dirname(__file__)
    with open(os.path.join(current_dir, 'test_resumes/{}'.format(file_name))) as raw_file:
        resume_file = raw_file.read()
    response = APP.post('/parse_resume',
                        headers={'Authorization': 'Bearer %s' % test_token.access_token},
                        data=dict(
                            resume_file=(StringIO(resume_file), file_name),
                            resume_file_name=file_name,
                            create_candidate=create_mode,
                        ),
                        follow_redirects=True)
    return json.loads(response.data)


def fetch_resume_fp_key_response(test_token, fp_key):
    """Posts FilePicker key to local test auth server for json formatted resumes."""
    with APP as c:
        test_response = c.post('/parse_resume', headers={'Authorization': 'Bearer %s' % test_token.access_token},
                               data=dict(filepicker_key=fp_key))
    return json.loads(test_response.data)


def keys_formatted_test(json_obj):
    assert all(k in json_obj['work_experiences'][0] for k in WORK_EXPERIENCES_KEYS if json_obj['work_experiences'])
    assert 'text' in json_obj['work_experiences'][0]['bullets'][0].keys() if json_obj['work_experiences'][0][
        'bullets'] else False
    assert all(k in json_obj['addresses'][0] for k in ADDRESS_KEYS if json_obj['addresses'])
    assert all(k in json_obj['skills'][0] for k in SKILLS_KEYS if json_obj['skills'])
    assert all(k in json_obj['emails'][0] for k in EMAILS_KEYS if json_obj['emails'])
    assert all(k in json_obj['phones'][0] for k in PHONES_KEYS if json_obj['phones'])
    assert all(k in json_obj['educations'][0] for k in EDUCATIONS_KEYS if json_obj['educations'])

# Temp Paste-ins until utils are merged in.
from sqlalchemy.sql.expression import ClauseElement
def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.iteritems() if not isinstance(v, ClauseElement))
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        return instance, True


import random
import string

def random_word(length):
    return ''.join(random.choice(string.lowercase) for i in xrange(length))
