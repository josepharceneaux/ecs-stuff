"""
File contains unittests for testing functions used by the graphql-service
"""
import random
import string
from decimal import Decimal

from graphql_service.candidate_application.dynamodb import replace_decimal, set_empty_strings_to_null


class TestReplaceDecimal(object):
    """
    Class contains unittests testing replace_decimal function
    Note: replace_decimal will only convert Decimal objects to int or float,
            all other objects will not be converted
    """

    def test_integer(self):
        """
        Test: Integers must remain unchanged
        """
        random_int = random.randint(0, 100)
        assert isinstance(replace_decimal(random_int), int)

    def test_float(self):
        """
        Test: Floats must remain unchanged
        """
        random_float = random.uniform(0, 100)
        assert isinstance(replace_decimal(random_float), float)

    def test_string(self):
        """
        Test: String objects must remain unchanged
        """
        random_string = ''.join(random.choice(string.lowercase) for _ in range(5))
        assert isinstance(replace_decimal(random_string), basestring)

    def test_decimal(self):
        """
        Test: Decimal must be converted to a float if it has a mantissa,
               otherwise it will be converted to an integer
        """
        # Random decimal number with mantissa
        random_decimal_with_precision = Decimal(random.randrange(random.randint(0, 1000000))) / 1000
        assert isinstance(replace_decimal(random_decimal_with_precision), float)

        # Random decimal number without mantissa
        random_decimal_without_precision = Decimal(random.randrange(random.randint(0, 1000000)))
        assert isinstance(replace_decimal(random_decimal_without_precision), int)

    def test_dict_data(self):
        """
        Test: All decimal objects in dict data must be converted to ints or floats,
               all other objects must remain unchanged
        """
        data = dict(
            random_int=random.randint(0, 100),
            random_decimal=Decimal(random.randrange(random.randint(0, 1000000))) / 1000
        )

        result = replace_decimal(data)
        assert isinstance(result['random_int'], int)
        assert isinstance(result['random_decimal'], float)

    def test_list_data(self):
        """
        Test: The function must recursively look for Decimal objects and convert them to ints or floats
        """
        list_data = [
            dict(random_decimal=Decimal(random.randrange(random.randint(0, 1000000))) / 1000),
            dict(random_decimal=Decimal(random.randrange(random.randint(0, 1000000))) / 1000)
        ]

        result = replace_decimal(list_data)
        for data in result:
            assert isinstance(data['random_decimal'], float)


class TestSetEmptyStringsToNull(object):
    """
    Class contains unittest testing set_empty_strings_to_null function
    Note:  set_empty_strings_to_null function must convert all empty strings to None objects
    """

    def test_empty_string(self):
        """
        Test: Empty string must be converted to None object
        """
        assert set_empty_strings_to_null('') is None

    def test_dict_data(self):
        """
        Test: All empty strings inside of a dictionary data must be converted to None object
        """
        dict_data = dict(empty_string_1='', empty_string_2='', empty_string_3='')
        result = set_empty_strings_to_null(dict_data)
        for value in result.itervalues():
            assert value is None

    def test_list_data(self):
        """
        Test: Function must recursively convert all empty strings into None objects
        """
        list_data = ['', '', '', dict(empty_string='')]
        result = set_empty_strings_to_null(list_data)
        for data in result:
            if isinstance(data, dict):
                for value in data.itervalues():
                    assert value is None
            else:
                assert data is None
