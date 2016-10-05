"""
This module contains utility functions to handle GraphQL data and queries.
"""
from sqlalchemy import inspect
from sqlalchemy.orm.attributes import InstrumentedAttribute
from ..utils.handy_functions import snake_case_to_camel_case

__author__ = 'mzohaibqc'


def get_fields(model, include=None, exclude=None, relationships=None):
    """
    This functions receives db Model and return columns/fields name list. One can get specific fields
    by using `include` kwarg or he can exclude specific field using `exclude` kwarg.
    :param db.Model model: SqlAlchemy model class, e.g. Event, User
    :param list | tuple | None include: while fields to include, None for all
    :param list | tuple | None exclude: which fields to exclude, None for no exclusion
    :param list | tuple | None relationships: list of relationships that you want to add in fields like
    eventOrganizer for Event fields.
    :return: list of fields
    :rtype: list

        ..Example:
            >>> from app_common.common.models.event import Event
            >>> model = Event
            >>> get_fields(Event)
                ['title', 'currency', 'description', 'endDatetime', 'groupUrlName', 'id', 'maxAttendees', 'organizerId',
                'registrationInstruction', 'socialNetworkEventId', 'socialNetworkGroupId', 'socialNetworkId',
                'startDatetime', 'ticketsId', 'timezone', 'title', 'url', 'userId', 'venueId']
            >>> get_fields(Event, include=('title', 'cost'))
                ['title, 'cost']
            >>> get_fields(Event, exclude=('title', 'cost'))
                ['currency', 'description', 'endDatetime', 'groupUrlName', 'id', 'maxAttendees', 'organizerId',
                'registrationInstruction', 'socialNetworkEventId', 'socialNetworkGroupId', 'socialNetworkId',
                'startDatetime', 'ticketsId', 'timezone', 'url', 'userId', 'venueId']
            >>> get_fields(Event, relationships=('eventOrganizer',))
                ['cost', 'currency', 'description', 'endDatetime', 'eventOrganizer',
                ['about', 'email', 'event', 'id', 'name', 'socialNetworkId', 'socialNetworkOrganizerId', 'user',
                'userId'], 'groupUrlName', 'id', 'maxAttendees', 'organizerId', 'registrationInstruction',
                'socialNetwork', 'socialNetworkEventId', 'socialNetworkGroupId', 'socialNetworkId', 'startDatetime',
                'ticketsId', 'timezone', 'title', 'url', 'user', 'userId', 'venue', 'venueId']
    """
    fields = []
    column_keys = inspect(model).mapper.column_attrs._data._list
    relationship_keys = inspect(model).mapper.relationships._data._list
    column_keys = map(snake_case_to_camel_case, column_keys)
    for key in column_keys:
        if (not include or key in include) and (not exclude or key not in exclude):
            fields.append(key)
    for key in relationship_keys:
        if relationships and snake_case_to_camel_case(key) in relationships:
            fields.append(snake_case_to_camel_case(key))
            relationship_class = getattr(model, key).mapper.class_
            fields.append(get_fields(relationship_class))
    return fields


def get_query(key, fields, args=None, return_str=False):
    """
    This function takes response key, list of expected response fields and optional args and returns
    GraphQL compatible query. Fields name should be camel case like socialNetworkId.
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
    query = '{ %s %s { %s } }'
    args_list = []
    if args:
        for k, v in args.iteritems():
            args_list.append('%s : %s' % (k, str(v) if str(v).isdigit() else '\"%s\"' % v))
    fields = map(lambda (index, field): '{ %s }' % ' '.join(field) if isinstance(field, list) else field,
                 enumerate(fields))
    query = query % (
        key,
        '( %s )' % ', '.join(args_list) if args_list else '',
        ' '.join(fields)
    )
    return query if return_str else {'query': query}


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
            for field in filter(lambda item: isinstance(item, basestring), fields):
                assert field in obj, 'field: %s, data: %s' % (field, obj)
    else:
        for field in fields:
            assert field in data, 'field: %s, data: %s' % (field, data)