"""
This module contains utility functions to handle GraphQL data and queries.

:Authors:
    - Zohaib Ijaz    <mzohaib.qc@gmail.com>
"""
from contracts import contract

from ..error_handling import InvalidUsage


@contract
def get_query(key, fields, args=None, return_str=False):
    """
    This function takes response key, list of expected response fields and optional args and returns
    GraphQL compatible query.
    To create nested queries from list of fields, add a nested list of fields of that object.
    Look at the examples below.
    We can get any level of nested query unless the nested query needs args, e.g. if you want only first page of events
    you can not create below query from list of fields.

    :param string key: response key
    :param list | tuple fields: list of fields to be retrieved
    :param dict | None args: optional args
    :param bool return_str: True if you want just string query
    :return: query dict
    :rtype: dict | string

        ..Examples:

            >>> key = 'events'
            >>> fields = ['id', 'title', 'cost', 'description']
            >>> get_query(key, fields)
                {
                    "query" : "{ events { id title cost description } }"
                }

            >>> get_query(key, fields, args=dict(page=1, per_page=10))
                {
                    "query" : "{ events (page: 1, per_page=10) { id title cost description } }"
                }

            >>> key = "event"
            >>> get_query(key, fields, args=dict(id=123))
                {
                    "query" : "{ event (id: 123) { id title cost description } }"
                }

            >>> key = 'me'
            >>> fields = ['id', 'last_name', 'events', ['id', 'title']]
            >>> get_query(key, fields)
                {
                    "query": "{ me { id last_name events { id title } } }"
                }

    """
    query = '{ %s %s { %s } }'
    args_list = []
    if args:
        for k, v in args.iteritems():
            args_list.append('%s : %s' % (k, str(v) if str(v).isdigit() else '\"%s\"' % v))
    fields = map(lambda field: '{ %s }' % ' '.join(field) if isinstance(field, list) else field,
                 enumerate(fields))
    query = query % (
        key,
        '( %s )' % ', '.join(args_list) if args_list else '',
        ' '.join(fields)
    )
    return query if return_str else {'query': query}


@contract
def validate_graphql_response(key, response, fields, is_array=False):
    """
    This functions is doing a simple task. It checks required keys in response data.
    If response contains a list of objects, is_array must be True.
    :param string key: root key in response
    :param dict response: response object
    :param list | tuple fields: list of fields to validate
    :param bool is_array: True for array type data and False for single object/dict

    ..Example:
        >>> key = 'events'
        >>> response = {
        >>>     "events" : [
        >>>             {
        >>>                 "id": "1",
        >>>                 "title": "Test Event",
        >>>                 "cost": "10",
        >>>                 "description": "Some description"
        >>>             }
        >>>         ]
        >>> }
        >>> fields = ['id', 'title', 'cost', 'description']
        >>> validate_graphql_response(key, response, fields, is_array=True)
    """
    print('validate_graphql_response. Response: %s' % response)
    try:
        data = response[key]
    except KeyError:
        raise InvalidUsage("response must be a dict with given key. Given key: %s\nResponse: %s" % (key, response))
    if is_array:
        # validate every item in collection
        for obj in data:
            assert_keys(obj, fields)
    else:
        assert_keys(data, fields)


def assert_keys(response, keys):
    """
    This function asserts that all given keys are present in given response.
    :param dict response: dictionary data
    :param list keys: list of keys
    """
    if response is None:
        return
    assert isinstance(response, dict), 'response must be a dict. Given: %s' % response
    assert isinstance(keys, list), 'keys must be a list. Given: %s' % keys
    for index, key in enumerate(keys):
        if isinstance(key, (list, tuple)):
            fields = key
            key = keys[index - 1]
            data = response[key]
            is_array = isinstance(data, (list, tuple))
            data = {key: data}
            validate_graphql_response(key, data, fields, is_array=is_array)
        else:
            assert key in response, 'key: %s, response: %s' % (key, response)
