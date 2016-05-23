# User Service app instance
from user_service.user_app import app

# Conftest
from user_service.common.tests.conftest import *

# Helper functions
from user_service.common.routes import UserServiceApiUrl
from user_service.common.utils.test_utils import send_request, response_info


class TestCreateDomainSource(object):
    """
    Class contains test cases for POST /v1/sources
    """
    CREATED = 201
    INVALID = 400
    UNAUTHORIZED = 401
    URL = UserServiceApiUrl.DOMAIN_SOURCES

    def test_add_source_to_domain(self, access_token_first):
        """
        Test: Add a source to domain
        """
        data = dict(source=dict(description='job fair', notes='recruited initials: ahb'))
        create_resp = send_request('post', self.URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == self.CREATED
        assert 'id' in create_resp.json()['source']

    def test_add_duplicate_source_in_same_domain(self, access_token_first):
        """
        Test:  Add same source in the same domain
        """
        # Create source
        data = dict(source=dict(description='job fair', notes='recruited initials: ahb'))
        send_request('post', self.URL, access_token_first, data)

        # Create same source in same domain again
        create_resp = send_request('post', self.URL, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == self.INVALID

    def test_add_source_without_access_token(self):
        """
        Test:  Unauthenticated user accessing source endpoint
        :return:
        """
        create_resp = send_request('post', self.URL, access_token_first, {})
        print response_info(create_resp)
        assert create_resp.status_code == self.UNAUTHORIZED


class TestGetDomainSource(object):
    """
    Class contains test cases for GET /v1/sources
    """
    OK = 200
    URL = UserServiceApiUrl.DOMAIN_SOURCES
    URL_PLUS_ID = UserServiceApiUrl.DOMAIN_SOURCE

    def test_get_domain_sources(self, access_token_first):
        """
        Test: Get all domain's sources
        """
        # Create some sources
        number_of_sources_created = random.randrange(2, 8)
        for _ in range(number_of_sources_created):
            send_request(method='post', url=self.URL, access_token=access_token_first,
                         data=dict(source=dict(description=str(uuid.uuid4())[:5])))

        # Retrieve all sources in user's domain
        get_resp = send_request('get', self.URL, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == self.OK
        assert isinstance(get_resp.json()['sources'], list)
        assert len(get_resp.json()['sources']) == number_of_sources_created

    def test_get_source(self, access_token_first):
        """
        Test: Get a source from user's domain by providing source's ID
        """
        # Create source
        data = dict(source=dict(description='job fair', notes='recruited initials: ahb'))
        create_resp = send_request('post', self.URL, access_token_first, data)

        # Retrieve source
        source_id = create_resp.json()['source']['id']
        get_resp = send_request('get', self.URL_PLUS_ID % source_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == self.OK
        assert isinstance(get_resp.json()['source'], dict)
