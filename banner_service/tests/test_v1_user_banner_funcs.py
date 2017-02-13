import pytest

from banner_service.app import app, redis_store
from banner_service.app.modules.v1_user_banner_processors import create_user_banner_entry
from banner_service.app.modules.v1_user_banner_processors import retrieve_user_banner_entry


class TestCRFunction(object):
    def setup_method(self, method):
        with app.test_client() as tc:
            self.app = tc

    def teardown_method(self, method):
        with app.test_client() as tc:
            keys_to_delete = redis_store.keys('USER_BANNER_*')
            for k in keys_to_delete:
                redis_store.delete(k)

    def test_we_can_log_users(self):
        assert create_user_banner_entry(1)

    def test_we_can_retrieve_logs(self):
        create_user_banner_entry(2)
        assert retrieve_user_banner_entry(2)
