import pytest
import json
from banner_service.common.tests.conftest import access_token_first
from banner_service.common.tests.conftest import user_first
from banner_service.common.tests.conftest import domain_first
from banner_service.common.tests.conftest import first_group
from banner_service.common.tests.conftest import sample_client
from banner_service.app import app, redis_store


class TestUserBannerApiEndpoints(object):
    def setup_method(self, method):
        with app.test_client() as tc:
            self.app = tc

    def teardown_method(self, method):
        with app.test_client() as tc:
            keys_to_delete = redis_store.keys('USER_BANNER_*')
            for k in keys_to_delete:
                redis_store.delete(k)

    def test_get_requires_auth(self, access_token_first):
        response = self.app.get('/v1/user_banner')
        assert response.status_code == 401

    def test_post_get_requires_auth(self):
        response = self.app.post('/v1/user_banner')
        assert response.status_code == 401

    def test_can_post_format(self, access_token_first):
        response = self.app.post(
            '/v1/user_banner/',
            headers={'Authorization': 'Bearer {}'.format(access_token_first)})
        assert response.status_code == 201
        response_json = json.loads(response.data)
        assert response_json.get('entry_created')

        # Second post shouldn't cause error
        response = self.app.post(
            '/v1/user_banner/',
            headers={'Authorization': 'Bearer {}'.format(access_token_first)})
        assert response.status_code == 201
        response_json = json.loads(response.data)
        assert response_json.get('entry_created')

    def test_can_get(self, access_token_first):
        post_response = self.app.post(
            '/v1/user_banner/',
            headers={'Authorization': 'Bearer {}'.format(access_token_first)})
        assert post_response.status_code == 201

        get_response = self.app.get(
            '/v1/user_banner/',
            headers={'Authorization': 'Bearer {}'.format(access_token_first)})
        assert get_response.status_code == 200
        get_json = json.loads(get_response.data)
        assert get_json.get('has_seen_banner')
