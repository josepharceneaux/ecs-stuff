from graphql_service.common.tests.conftest import *
from graphql_service.modules.schema import schema
from gql import gql, Client

client = Client(schema=schema)


class TestQueryCandidate(object):
    def test_get_candidate(self):
        query = gql("""{candidate(id:"567518"){first_name}}""")
        response = client.execute(document=query)
        candidate = response.get('candidate')
        assert candidate
        assert candidate.get('first_name') == 'frank'


class TestAddCandidate(object):
    def test_add_candidate(self):
        query = gql(
            """
            {

            }
            """
        )