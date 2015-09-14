"""Test suite for Flask Resume Parsing MicroService."""

import json
import os
from StringIO import StringIO
import unittest

from application import app

APP = app.test_client()


class TestSingleResumeCandidateDict(unittest.TestCase):
    """Test Cases for RP Service."""

    def setUp(self):
        self.doc_dict = dict(addressLine1=u'466 Tailor Way', addressLine2=u'', city=u'Lansdale',
                             coordinates=u'40.2414952,-75.2837862', country=None, state=u'Pennsylvania', zipCode=u'19446')

    def test_base_url(self):
        """Test that the application root lists the endpoint."""
        base_response = APP.get('/')
        assert '/parse_resume' in base_response.data

    def test_doc_from_fp_key(self):
        """Test that .doc files from S3 can be parsed."""
        json_obj = fetch_resume_fp_key_response('0169173d35beaf1053e79fdf1b5db864.docx')
        assert json_obj['full_name'] == 'VEENA NITHOO'
        assert len(json_obj['addresses']) == 1
        self.assertEqual(json_obj['addresses'][0], self.doc_dict)
        assert len(json_obj['educations']) == 3
        assert len(json_obj['work_experiences']) == 7

    def test_doc_by_post(self):
        """Test that .doc files that are posted to the end point can be parsed."""
        json_obj = json.loads(fetch_resume_post_response('test_bin.docx'))
        assert json_obj['full_name'] == 'VEENA NITHOO'
        assert len(json_obj['addresses']) == 1
        self.assertEqual(json_obj['addresses'][0], self.doc_dict)
        assert len(json_obj['educations']) == 3
        assert len(json_obj['work_experiences']) == 7

    def test_v15_pdf_from_fp_key(self):
        """Test that v1.5 pdf files from S3 can be parsed."""
        json_obj = fetch_resume_fp_key_response('e68b51ee1fd62db589d2669c4f63f381.pdf')
        self.assertEqual(json_obj['full_name'], 'MARK GREENE')
        self.assertEqual(len(json_obj['educations']), 1)
        self.assertEqual(len(json_obj['work_experiences']), 15)

    def test_v14_pdf_from_fp_key(self):
        """Test that v1.5 pdf files from S3 can be parsed."""
        json_obj = fetch_resume_fp_key_response('test_bin_14.pdf')
        #doesnt get good name data back
        self.assertEqual(len(json_obj['work_experiences']), 4)

    def test_v13_pdf_from_fp_key(self):
        """Test that v1.5 pdf files from S3 can be parsed."""
        json_obj = fetch_resume_fp_key_response('test_bin_13.pdf')
        self.assertEqual(json_obj['full_name'], 'BRUCE PARKEY')
        self.assertEqual(len(json_obj['work_experiences']), 3)

    def test_v15_pdf_by_post(self):
        """Test that v1.5 pdf files can be posted."""
        json_obj = json.loads(fetch_resume_post_response('test_bin.pdf'))
        self.assertEqual(json_obj['full_name'], 'MARK GREENE')
        self.assertEqual(len(json_obj['educations']), 1)
        self.assertEqual(len(json_obj['work_experiences']), 15)

    def test_v14_pdf_by_post(self):
        """Test that v1.5 pdf files can be posted."""
        json_obj = json.loads(fetch_resume_post_response('test_bin_14.pdf'))
        self.assertEqual(len(json_obj['work_experiences']), 4)

    def test_v13_pdf_by_post(self):
        """Test that v1.5 pdf files can be posted."""
        json_obj = json.loads(fetch_resume_post_response('test_bin_13.pdf'))
        self.assertEqual(len(json_obj['work_experiences']), 3)

    def test_jpg_from_fp_key(self):
        """Test that v1.5 pdf files from S3 can be parsed."""
        json_obj = fetch_resume_fp_key_response('test_bin.jpg')
        self.assertEqual(json_obj['full_name'], 'Erik D Farmer')
        self.assertEqual(len(json_obj['educations']), 2)
        self.assertEqual(len(json_obj['work_experiences']), 2)

    def test_jpg_by_post(self):
        """Test that img files can be posted."""
        json_obj = json.loads(fetch_resume_post_response('test_bin.jpg'))
        self.assertEqual(json_obj['full_name'], 'Erik D Farmer')
        self.assertEqual(len(json_obj['educations']), 2)
        self.assertEqual(len(json_obj['work_experiences']), 2)

    def test_no_token_fails(self):
        filepicker_key = '0169173d35beaf1053e79fdf1b5db864.docx'
        with APP as c:
            test_response = c.post('/parse_resume', data=dict(filepicker_key=filepicker_key))
        json_obj = json.loads(test_response.data)
        assert 'error' in json_obj

    def test_invalid_token_fails(self):
        filepicker_key = '0169173d35beaf1053e79fdf1b5db864.docx'
        with APP as c:
            test_response = c.post('/parse_resume', headers={'Authorization': 'Bearer bar'}, data=dict(filepicker_key=filepicker_key))
        json_obj = json.loads(test_response.data)
        assert 'error' in json_obj


def fetch_resume_post_response(file_name):
    """Posts file to local test auth server for json formatted resumes."""
    current_dir = os.path.dirname(__file__)
    with open(os.path.join(current_dir, 'test_resumes/{}'.format(file_name))) as raw_file:
        resume_file = raw_file.read()
    response = APP.post('/parse_resume', headers={'Authorization': 'Bearer foo'}, data=dict(
        resume_file=(StringIO(resume_file), file_name),
        resume_file_name=file_name
    ), follow_redirects=True)
    return response.data


def fetch_resume_fp_key_response(fp_key):
    """Posts FilePicker key to local test auth server for json formatted resumes."""
    with APP as c:
        test_response = c.post('/parse_resume', headers={'Authorization': 'Bearer foo'}, data=dict(filepicker_key=fp_key))
    return json.loads(test_response.data)
