"""
File contains unittests for testing functions used by the candidate-service
"""
import random
from faker import Faker
from candidate_service.common.utils.candidate_utils import replace_tabs_with_spaces
from candidate_service.modules.talent_candidates import CandidateTitle, get_fullname_from_name_fields

fake = Faker()


class TestMostRecentPosition(object):
    """
    Class contains test functions for testing CandidateTitle
    """

    def test_with_no_experience(self):
        experiences = []
        t = CandidateTitle(experiences)
        print "CandidateTitle: {}".format(t.title)
        assert t.title is None

    def test_with_is_current(self):
        experiences = [
            {'position': fake.job()},
            {'position': fake.job()},
            {'position': fake.job()}
        ]
        # Randomly set one of the experience's is_current value to true
        random.choice(experiences)['is_current'] = True
        t = CandidateTitle(experiences)
        print "CandidateTitle: {}".format(t.title)
        assert t.title == [exp['position'] for exp in experiences if exp.get('is_current')].pop()

    def test_with_dates(self):
        experiences = [
            {
                'position': fake.job(),
                'start_year': 2000,
                'start_month': 1,
                'end_year': 2002,
                'end_month': 2
            },
            {
                'position': fake.job(),
                'start_year': 2005,
                'start_month': 3,
                'end_year': 2008,
                'end_month': 11
            },
            {
                'position': fake.job(),
                'start_year': 2015,
                'end_year': 2017
            }
        ]
        t = CandidateTitle(experiences)
        print "CandidateTitle: {}".format(t.title)
        assert t.title == experiences[-1]['position']

    def test_with_same_year_diff_months(self):
        experiences = [
            {
                'position': fake.job(),
                'start_year': 2016,
                'start_month': 3,
                'end_year': 2017,
                'end_month': 4
            },
            {
                'position': fake.job(),
                'start_year': 2016,
                'start_month': 1,
                'end_year': 2017,
                'end_month': 2
            }
        ]
        t = CandidateTitle(experiences)
        print "CandidateTitle: {}".format(t.title)
        assert t.title == experiences[0]['position']


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


def test_candidate_name():
    assert get_fullname_from_name_fields('First', 'Middle', 'Last') == 'First Middle Last'
    assert get_fullname_from_name_fields('First', 'Middle', None) == 'First Middle'
    assert get_fullname_from_name_fields('First', '', 'Last') == 'First Last'
    assert get_fullname_from_name_fields('First', None, 'Last') == 'First Last'
    assert get_fullname_from_name_fields('First', None, None) == 'First'
    assert get_fullname_from_name_fields('First', '', '') == 'First'
    assert get_fullname_from_name_fields('First', 'Middle', '') == 'First Middle'
    assert get_fullname_from_name_fields(None, None, None) == ''
