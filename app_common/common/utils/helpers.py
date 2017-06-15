"""
This module contains helper methods and classes which can be used in any service.

:Authors:
    - Zohaib Ijaz    <mzohaib.qc@gmail.com>
"""


class GtDict(dict):
    """
    This class is to allow getting attribute value from dict object instead of using get item syntax.
    TODO: It does not converts lists of objects / dict inside list (nested lists).
    e.g d = {'a': [[{'b': 1}, {'c': 2}], [{'d': 3}]]}

    :Examples:

        >>> data = { 'emails': [ {'address': 'amir@gettalent.com'}, {'address': 'zohaib@gettalent.com'}  ] }
        >>> data = GtDict(data)
        >>> data.emails
        [ {'address': 'zohaib@gettalent.com'}, {'address': 'zohaib@gettalent.com'} ]
        >>> data.emails[0].address
        amir@gettalent.com
    """
    def __init__(self, data):
        super(GtDict, self).__init__(data)
        for key, val in self.items():
            if isinstance(val, dict):
                self[key] = GtDict(val)
            if isinstance(val, list):
                for index, item in enumerate(val):
                    val[index] = GtDict(item) if isinstance(item, dict) else item

    def __getattr__(self, key):
        """
        Get item value from dict object
        :param key: key name
        :return: value of object under that key
        """
        return self.get(key)

    def __setattr__(self, key, value):
        """
        Set value against a key in dict object
        :param key: key name
        :param value: value to be set against key
        :return: value of object under that key
        """
        self[key] = value
