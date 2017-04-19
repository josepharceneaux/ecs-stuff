# StdLib
import json
# Third Party
import requests
# Module Specific Imports
from candidate_service.common.routes import CandidateApiUrl
from candidate_service.common.tests.conftest import access_token_first
from candidate_service.common.tests.conftest import domain_first
from candidate_service.common.tests.conftest import domain_source
from candidate_service.common.tests.conftest import first_group
from candidate_service.common.tests.conftest import sample_client
from candidate_service.common.tests.conftest import talent_pool
from candidate_service.common.tests.conftest import user_first


class TestCandidateDocument(object):
    def test_document_life_cycle(self, access_token_first, candidate_first):
        test_post_response = requests.post(
            CandidateApiUrl.DOCUMENTS % candidate_first.id,
            data=json.dumps({
                'filename': 'bar',
                'key_path': 'foo'
            }),
            headers={'Content-Type': 'application/json',
                     'Authorization': 'Bearer {}'.format(access_token_first)})
        assert test_post_response.status_code == 201
        test_get_response = requests.get(
            CandidateApiUrl.DOCUMENTS % candidate_first.id,
            headers={'Authorization': 'Bearer {}'.format(access_token_first)})
        assert test_get_response.status_code == 200
        document_id = json.loads(test_get_response.content)['documents'][0]['id']
        test_patch_response = requests.patch(
            CandidateApiUrl.DOCUMENT % (candidate_first.id, document_id),
            data=json.dumps({
                'filename': 'barz',
            }),
            headers={'Content-Type': 'application/json',
                     'Authorization': 'Bearer {}'.format(access_token_first)})
        assert test_patch_response.status_code == 204
        test_del_response = requests.delete(
            CandidateApiUrl.DOCUMENT % (candidate_first.id, document_id),
            headers={'Content-Type': 'application/json',
                     'Authorization': 'Bearer {}'.format(access_token_first)})
        assert test_del_response.status_code == 204
