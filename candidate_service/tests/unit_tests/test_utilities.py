"""
File contains unittests for testing functions used by the candidate-service
"""
from candidate_service.common.utils.candidate_utils import replace_tabs_with_spaces


class TestRemoveTabs(object):
    """
    Class contains unittests testing remove_tabs function
    """

    def test_dict(self):
        """
        Test: feed dict object containing values with\t(tabs)
        """
        data = {"key": "this\tstring contains\ttabs"}
        r = replace_tabs_with_spaces(data)
        assert r['key'] == r['key'].replace("\t", " ")

    def test_list(self):
        """
        Test: feed a list of dicts that have values containing \t
        """
        data = {"data": [
            {
                "key1": "this\tstring contains\ttabs \t",
                "key2": "this\tstring contains\ttabs \t"
            },
            {
                "key1": "this\tstring contains\ttabs \t",
                "key2": "this\tstring contains\ttabs \t"
            }
        ]}

        r = replace_tabs_with_spaces(data)
        for obj in r['data']:
            assert obj['key1'] == obj['key1'].replace("\t", " ")
            assert obj['key2'] == obj['key2'].replace("\t", " ")

    def test_recursively(self):
        """
        Test: Recursively replace all\twith spaces in data
        """
        data = {
            "educations": [
                {
                    "school_name": "san\tjose\tstate\tuniversity",
                    "degrees": [
                        {
                            "title": "bachelor\tof science",
                            "bullets": [
                                {
                                    "description": "school\tneeds\tmore\tmoney"
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        r = replace_tabs_with_spaces(data)

        expected = {
            'educations': [
                {
                    'school_name': 'san jose state university',
                    'degrees': [
                        {
                            'title': 'bachelor of science',
                            'bullets': [
                                {
                                    'description': 'school needs more money'
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        assert expected == r

    def test_with_non_string_values(self):
        """
        Test: feed some data that include numbers, null values, etc.
        """
        data = {
            "number": 45,
            "null": None,
            "string": "this\ttab\tis\tunnecessary",
            "float": 35.6
        }

        r = replace_tabs_with_spaces(data)

        # Only the string values should be affected
        expected = {
            "number": 45,
            "null": None,
            "string": "this tab is unnecessary",
            "float": 35.6
        }

        assert expected == r


