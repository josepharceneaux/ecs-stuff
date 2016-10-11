import urllib
from graphql_service.common.tests.conftest import *
from graphql_service.modules.schema import schema
from graphql_service.common.routes import GTApis

# TODO: remove gql library usage and use Client instead
class TestQueryCandidate(object):
    def test_get_candidate(self):
        query = gql(
            """
            {
                candidate(id:567518) {
                    first_name
                }
            }
            """
        )
        response = client.execute(document=query)
        candidate = response.get('candidate')
        assert candidate
        assert candidate.get('first_name') == 'frank'


# TODO: Use Client for simpler & more pythonic test cases
class TestAddCandidate(object):
    def test_add_candidate(self):
        query = """
        mutation NewCandidate
        {
            create_candidate(
                first_name: "%s",
                last_name: "%s",
                emails: [
                    {
                        address: "%s",
                        label: "%s",
                        is_default: %s
                    }
                ],
                addresses: [
                    {
                        address_line_1: "%s",
                        city: "%s"
                    }
                ]
            )
            {
                ok,
                id
            }
        }"""
        formatted_query = query % (fake.first_name(), fake.last_name(),
                                   fake.safe_email(), 'Primary', fake.boolean(),
                                   fake.city(), fake.street_address())

        response = requests.post(url=Client(formatted_query))
        assert response.status_code == requests.codes.OK
        print response.json()


class Client(object):
    """
    This 'client' will help make graphql requests for simpler functional testing.
    Client will convert candidate's data passed to the constructor's arguments into
    graphql document.

    'url_encoded_string' may be used to make requests.
    Example:
        c = Client(first_name='joe', emails=[{'address': 'joe@example.com'}], is_creating=True)
        response = requests.post(url=c.url_encoded_string)
        assert response.status_code == 200
    """
    base_url = 'http://localhost:{}/graphql'.format(GTApis.GRAPHQL_SERVICE_PORT)

    def __init__(self, first_name=None, middle_name=None, last_name=None,
                 addresses=None, emails=None, is_creating=False):
        """
        :type first_name: str
        :type middle_name: str
        :type last_name: str
        :type addresses: list[dict]
        :type emails: list[dict]
        :type is_creating: bool
        """
        self.first_name = first_name
        self.middle_name = middle_name
        self.last_name = last_name
        self.addresses = addresses
        self.emails = emails

        if is_creating:
            self.add_text = "mutation NewCandidate {create_candidate(%s) {ok, id}}"

        self.generated_query_string = self.generate_query_string()
        self.url_encoded_string = self.url_encode()

    def generate_query_string(self):
        """
        function will create a graphql document out of class' constructor arguments
        """
        query_string = """
        first_name: "{first_name}",
        middle_name: "{middle_name}",
        last_name: "{last_name}",
        addresses: {addresses},
        emails: {emails}
        """.format(
            first_name=self.first_name, middle_name=self.middle_name, last_name=self.last_name,
            addresses=self._formatted_collection(self.addresses),
            emails=self._formatted_collection(self.emails)
        )

        # The query string should contain javascript recognized objects
        query_string = query_string.replace("\n", "")
        query_string = query_string.replace("\'", "")
        query_string = query_string.replace("True", "true")
        query_string = query_string.replace("False", "false")

        return self.add_text % query_string

    @staticmethod
    def _formatted_collection(collection):
        """
        Function will convert a list of dict data into a compatible graphql document
        E.g. [{'address': 'you@example.com'}] => [{address: "you@example.com"}]
        """
        res = ""
        for dict_obj in collection:
            for k, v in dict_obj.iteritems():
                res += '{%s: "%s"}' % (k, v)
                res += ','

        return "[" + res[:len(res) - 1] + "]"

    def url_encode(self):
        """
        Function will convert query string into utf8-encode and add the base url to the beginning of the encoded url
        """
        url_encoded = urllib.quote(self.generated_query_string.encode('utf8'))
        return self.base_url + '?query={}'.format(url_encoded)
