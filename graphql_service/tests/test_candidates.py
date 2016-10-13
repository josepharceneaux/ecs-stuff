from graphql_service.application import app
from graphql_service.common.tests.conftest import *
from helpers import GraphQLClient

headers = {'content-type': 'application/json'}


class TestQueryCandidate(object):
    def test_get_candidate(self):
        desired_data = dict(
            primary=('first_name',),
            secondary={'emails': ('address', 'label')}
        )
        client = GraphQLClient(candidate_id=568132, desired_data=desired_data)
        response = requests.post(url=client.base_url,
                                 headers={'content-type': 'application/json'},
                                 data=client.generated_query_string)
        assert response.status_code == requests.codes.ok
        print "\ncandidate_data: {}".format(response.json())


class TestAddCandidate(object):
    def test_add_candidate(self):
        candidate_data = dict(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            emails=[dict(address=fake.safe_email())]
        )
        client = GraphQLClient(is_creating=True, **candidate_data)
        response = requests.post(url=client.base_url, headers=headers, data=json.dumps(client.generated_query_string))
        assert response.status_code == requests.codes.OK
        print '\ndata: {}'.format(response.json())
        assert response.json()['data']['create_candidate']['id'] is not None


class TestUpdateCandidate(object):
    def test_change_candidates_primary_information(self):
        # Add candidate
        candidate_data = dict(
            first_name=fake.first_name(),
            middle_name=fake.first_name(),
            last_name=fake.last_name()
        )
        client = GraphQLClient(is_creating=True, **candidate_data)
        response = requests.post(url=client.base_url, headers=headers, data=json.dumps(client.generated_query_string))
        print '\ndata: {}'.format(response.json())

        candidate_id = response.json()['data']['create_candidate']['id']

        # Change candidate's first & last names
        update_data = dict(first_name=fake.first_name(), last_name=fake.last_name())
        client = GraphQLClient()