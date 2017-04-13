import os
import json

import requests

from resume_parsing_service.common.routes import ResumeApiUrl
from resume_parsing_service.common.tests.conftest import access_token_first
from resume_parsing_service.common.tests.conftest import domain_first
from resume_parsing_service.common.tests.conftest import domain_source
from resume_parsing_service.common.tests.conftest import first_group
from resume_parsing_service.common.tests.conftest import sample_client
from resume_parsing_service.common.tests.conftest import talent_pool
from resume_parsing_service.common.tests.conftest import user_first


def test_doc_by_post(access_token_first):
    """Test that .doc files that are posted to the end point can be parsed."""
    content, status = fetch_resume_post_response(access_token_first, 'test_bin.docx')
    print content
    assert status == requests.codes.ok


def fetch_resume_post_response(token_fixture, file_name):
    """Posts file to local test auth server for json formatted resumes."""
    current_dir = os.path.dirname(__file__)
    with open(os.path.join(current_dir, 'files/{}'.format(file_name)), 'rb') as resume_file:
        response = requests.post(
            ResumeApiUrl.HOST_NAME % '/v1/contact_only',
            headers={'Authorization': 'Bearer {}'.format(token_fixture)},
            data={
                # 'Local Test Upload' prefix.
                'resume_file_name': 'LTU_{}'.format(file_name),
            },
            files=dict(resume_file=resume_file))
    content = json.loads(response.content)
    status_code = response.status_code
    return content, status_code
