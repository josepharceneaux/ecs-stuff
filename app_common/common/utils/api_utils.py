"""
This modules contains helper methods and classes which we are using in e.g. Social Network API app.

        * ApiResponse:
            This class is used to create API response object to return json response.

"""
__author__ = 'basit'

# Standard Library
import json

# Third Part
from flask import Response

# Application Specific
from models_utils import to_json
from ..error_handling import InvalidUsage
from .handy_functions import JSON_CONTENT_TYPE_HEADER

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50


class ApiResponse(Response):
    """
    Override default_mimetype to 'application/json' to return proper json api response
    """
    def __init__(self, response, status=200, content_type=JSON_CONTENT_TYPE_HEADER['content-type'],
                 headers=None):
        if isinstance(response, dict):
            response = json.dumps(response)
        super(Response, self).__init__(response, status=status,
                                       content_type=content_type,
                                       headers=headers)


def api_route(self, *args, **kwargs):
    """
    This method helps to make api endpoints to look similar to normal flask routes.
    Simply use it as a decorator on api endpoint method.

        :Example:

            @api.route('/events/')
            class Events(Resource):

                def get(*args, **kwargs):
                    do stuff here for GET request

                def post(*args, **kwargs):
                    do stuff here for POST request

    """
    def wrapper(cls):
        self.add_resource(cls, *args, **kwargs)
        return cls
    return wrapper


def get_pagination_constraints(request):
    page = request.args.get('page', DEFAULT_PAGE)
    per_page = request.args.get('per_page', DEFAULT_PAGE_SIZE)

    if not(str(page).isdigit() and int(page) > 0):
        raise InvalidUsage('page value should a positive number. Given %s' % page)

    if not(str(per_page).isdigit() and int(per_page) <= MAX_PAGE_SIZE):
        raise InvalidUsage('per_page should be a number with maximum value %s. Given %s'
                           % (MAX_PAGE_SIZE, per_page))

    return int(page), int(per_page)


def get_paginated_response(key, query, page, per_page):
    results = query.paginate(page, per_page, error_out=False)
    items = [to_json(item) for item in results.items]
    headers = {
        'X-Total': results.total,
        'X-Per-Page': per_page,
        'X-Page': page
    }
    response = {
        key: items,
        'count': len(items)
    }
    return ApiResponse(response, headers=headers, status=200)
