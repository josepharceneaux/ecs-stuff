"""
This module contains utility functions to handle GraphQL data and queries.
"""
from sqlalchemy.orm.attributes import InstrumentedAttribute
from ..utils.handy_functions import snake_case_to_camel_case

__author__ = 'mzohaibqc'


def get_fields(model, include=None, exclude=None, snake_case=False):
    """
    This functions receives db Model and return columns/fields name list. One can get specific fields
    by using `include` kwarg or he can exclude specific field using `exclude` kwarg.
    :param db.Model model: SqlAlchemy model class, e.g. Event, User
    :param list | tuple | None include: while fields to include, None for all
    :param list | tuple | None exclude: which fields to exclude, None for no exclusion
    :param bool snake_case: pass True to get snake_case field name like social_network_id otherwise it will be
    like socialNetworkId etc.
    :return: list of fields
    :rtype: list
    """
    keys = []
    for key in dir(model):
        if (not include or key in include) and (not exclude or key not in exclude):
            column = getattr(model, key)
            relations = model.__mapper__.relationships._data._list
            # Only column fields. Skip relationships
            if isinstance(column, InstrumentedAttribute) and key not in relations:
                if not snake_case:
                    keys.append(snake_case_to_camel_case(key))
                else:
                    keys.append(key)
    return keys


def get_query(key, fields, args=None):
    """
    This function takes response key, list of expected response fields and optional args and returns
    GraphQL compatible query. Fields name should be camel case like socialNetworkId.
    :param string key: response key
    :param list | tuple fields: list of fields to be retrieved
    :param dict | None args: optional args
    :return: query dict
    :rtype: dict

        ..Examples:

            >>> key = 'events'
            >>> fields = ['id', 'title', 'cost', 'description']
            >>> get_query(key, fields)
                {
                    "query" : "{ events { id title cost description } }"
                }

            >>> get_query(key, fields, args=dict(page=1, perPage=10))
                {
                    "query" : "{ events (page: 1, perPage=10) { id title cost description } }"
                }

            >>> key = "event"
            >>> get_query(key, fields, args=dict(id=123))
                {
                    "query" : "{ event (id: 123) { id title cost description } }"
                }

    """
    query = '{ %s %s {%s} }'
    args_str = ''
    if args:
        for k, v in args.iteritems():
            args_str += '%s : %s' % (k, str(v) if str(v).isdigit() else '\"%s\"' % v)

    query = query % (
        key,
        '( %s )' % args_str if args_str else '',
        ' '.join(fields)
    )
    return {'query': query}


def validate_graphql_response(key, response, fields, is_array=False):
    """
    This functions is doing a simple task. It checks required keys in response data.
    :param key:
    :param response:
    :param fields:
    :param is_array:

    ..Example:
        >>> key = 'events'
        >>> response = {
        >>>     "data" : {
        >>>         "events" : [
        >>>             {
        >>>                 "id": "1",
        >>>                 "title": "Test Event",
        >>>                 "cost": "10",
        >>>                 "description": "Some description"
        >>>             }
        >>>         ]
        >>>     }
        >>> }
        >>> fields = ['id', 'title', 'cost', 'description']
        >>> validate_graphql_response(key, response, fields, is_array=True)
    """
    print('validate_graphql_response. Response: %s' % response)
    data = response['data'][key]
    if is_array:
        # validate every item in collection
        for obj in data:
            for field in fields:
                assert field in obj, 'field: %s, data: %s' % (field, obj)
    else:
        for field in fields:
            assert field in data, 'field: %s, data: %s' % (field, data)