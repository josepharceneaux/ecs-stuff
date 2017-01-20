from flask_sqlalchemy import BaseQuery
"""
GTBOT SHARED CONSTANTS
"""
NUMBER_OF_ROWS_PER_PAGE = 10
OWNED = 1
DOMAIN_SPECIFIC = 2

"""
GTBOT COMMON METHODS
"""


def get_paginated_objects(query, page_number):
    """
    This method will return the list of objects according to the page_number
    :param flask_sqlalchemy.BaseQuery query: QueryObject
    :param long|int page_number: Page number
    :rtype: list
    """
    assert isinstance(query, BaseQuery) and isinstance(page_number, (int, long)), "Invalid parameters type"
    start = (page_number - 1) * NUMBER_OF_ROWS_PER_PAGE
    end = page_number * NUMBER_OF_ROWS_PER_PAGE
    return query[start:end]
