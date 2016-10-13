from flask import request
import urllib
from graphql_service.common.routes import GTApis


class GraphQLClient(object):
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

    def __init__(self, candidate_id=None, desired_data=None, is_creating=False, **kwargs):
        """
        :type first_name: str
        :type middle_name: str
        :type last_name: str
        :type addresses: list[dict]
        :type emails: list[dict]
        :type is_creating: bool
        """
        self.candidate_id = candidate_id
        self.desired_data = desired_data
        self.candidate_data = kwargs

        # Generate url encoded string for querying candidate and its desired data
        if candidate_id and desired_data:
            assert isinstance(desired_data, dict), 'desired data must be a dict'
            assert isinstance(desired_data.get('primary', ()), tuple), 'primary data must be tuple'
            assert isinstance(desired_data.get('secondary', {}), dict), 'secondary data must be a dict'
            self.generated_query_string = self.generate_query_string_for_retrieving()

        # Generate url encoded string for creating candidate
        elif is_creating:
            self.add_text = "mutation NewCandidate {create_candidate(%s) {ok, id}}"
            self.generated_query_string = self.generate_query_string_for_mutation()
            # self.url_encoded_string = self.url_encode()

    def generate_query_string_for_retrieving(self):
        query_string = "query {candidate(id: %d) {%s}}" % (self.candidate_id, '%s')
        build = ""  # "first_name,last_name,emails{address,label,is_default,},addresses{address_line_1,},"
        for key, values in self.desired_data.iteritems():
            if key == 'primary':
                for index, value in enumerate(values, start=1):
                    if index != 1 and index == len(values):
                        build += value
                    else:
                        build += (value + ',')

            if key == 'secondary':
                i = 1
                for key_, values_ in self.desired_data[key].iteritems():
                    build += key_
                    build += '{'
                    for index, value_ in enumerate(values_, start=1):
                        if index == len(values_):
                            build += value_
                        else:
                            build += (value_ + ',')
                    build += '}'
                    if i < len(self.desired_data[key]):
                        build += ','

        query_string = query_string % build
        return '{"query": "%s"}' % query_string

    def generate_query_string_for_mutation(self):
        """
        function will create a graphql document out of class' constructor arguments
        """
        query_string = "mutation NewCandidate {create_candidate (%s) {ok, id}}"
        build = ''
        collection = {
            'areas_of_interest', 'addresses', 'custom_fields', 'educations',
            'emails', 'experiences', 'military_services', 'notes', 'phones',
            'photos', 'preferred_locations', 'references', 'skills',
            'social_networks', 'tags'
        }

        index = 1
        for key, value in self.candidate_data.iteritems():
            if key in collection:
                build += (key + ':[{')
                for dict_ in self.candidate_data[key]:
                    i = 1
                    for k, v in dict_.iteritems():
                        build += (k + ':"%s"' % v)
                        if i < len(dict_):
                            build += ','
                build += '}]'
                if index < len(self.candidate_data):
                    build += ','
                    index += 1
            else:
                build += (key + ':"%s"' % value)
                if index < len(self.candidate_data):
                    build += ','
                    index += 1

        query_string = query_string % build
        return {"query": query_string}

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

        # def url_encode(self):
        #     """
        #     Function will convert query string into utf8-encode and add the base url to the beginning of the encoded url
        #     """
        #     url_encoded = urllib.quote(self.generated_query_string.encode('utf8'))
        #     return self.base_url + '?query={}'.format(url_encoded)
