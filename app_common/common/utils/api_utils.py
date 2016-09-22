"""
This module contains helper methods and classes which we are using in e.g. Social Network API app.

        * ApiResponse:
            This class is used to create API response object to return JSON response.

Here we also have functions which are useful for APIs to implement pagination.

:Authors:
    - Muhammad Basit <basit.getTalent@gmail.com>
    - Zohaib Ijaz    <mzohaib.qc@gmail.com>
"""

# Standard Library
import json

# Third Part
from requests import codes
from flask import Response
from contracts import contract

# Application Specific
from sqlalchemy.orm import Query
from models_utils import to_json
from ..error_handling import InvalidUsage
from .handy_functions import JSON_CONTENT_TYPE_HEADER
from ..custom_contracts import define_custom_contracts
from ..utils.validators import raise_if_not_instance_of

define_custom_contracts()

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


def get_pagination_params(request, default_page=DEFAULT_PAGE, default_per_page=DEFAULT_PAGE_SIZE,
                          max_per_page=MAX_PAGE_SIZE):
    """
    This function helps to extract pagination query parameters "page" and "per_page" values.
    It validates the values for these params and raises InvalidUsage if given values or not
     valid number or returns default values (page=1, per_page=10) if no values are given.
    :param request: request object to get query params
    :param default_page: If given, then function will use this parameter instead of DEFAULT_PAGE
    :param default_per_page: If given, then function will use this parameter instead of DEFAULT_PER_PAGE
    :param max_per_page: If given, then function will use this parameter instead of MAX_PER_PAGE
    :return: page, per_page
    :rtype: tuple
    """
    page = request.args.get('page', default_page)
    per_page = request.args.get('per_page', default_per_page)
    try:
        page = int(page)
        assert page > 0
    except:
        raise InvalidUsage('page value should a positive number. Given %s' % page)
    try:
        per_page = int(per_page)
        assert 0 < per_page <= max_per_page, 'Give per_page value %s' % per_page
    except:
        raise InvalidUsage('per_page should be a number with maximum value %s. Given %s'
                           % (max_per_page, per_page))

    return page, per_page


def get_paginated_response(key, query, page=DEFAULT_PAGE, per_page=DEFAULT_PAGE_SIZE,
                           parser=to_json, include_fields=None):
    """
    This function takes query object and then returns ApiResponse object containing
    JSON serializable list of objects by applying pagination on query using given
    constraints (page, per_page) as response body.
    Response object has extra pagination headers like
        X-Total: Total number of results.
        X-Per-Page: Number of results per page.
        X-Page: Current page number.

    List of object is packed in a dictionary where key is specified by user/developer.
    :param key: final dictionary will contain this key where value will be list if items.
    :param query: A query object on which pagination will be applied.
    :param page: page number
    :param per_page: page size
    :param parser: Parser to be applied on object. e.g. email_campaign_obj.to_dict().
                          Default value is to_json()
    :param include_fields: List of fields we want to be returned from to_json()
    :return: api response object containing list of items
    :rtype ApiResponse

    :Example:
        >>> from app_common.common.models.push_campaign import PushCampaign
        >>> query = PushCampaign.query
        >>> page, per_page = 1, 10
        >>> response = get_paginated_response('campaigns', query, 1, 10)
        >>> response
        {
            "campaigns": [
                {
                    "name": "getTalent",
                    "body_text": "Abc.....xyz",
                    "url": "https://www.google.com"
                },
                .....
                .....
                .....
                {
                    "name": "Hiring New Talent",
                    "body_text": "Abc.....xyz",
                    "url": "https://www.gettalent.com/career"
                }
            ]
        }
    """
    raise_if_not_instance_of(key, basestring)
    raise_if_not_instance_of(query, Query)
    # error_out=false, do nor raise error if these is no object to return but return an empty list
    results = query.paginate(page, per_page, error_out=False)
    # convert model objects to serializable dictionaries
    items = [parser(item, include_fields) for item in results.items]
    headers = generate_pagination_headers(results.total, per_page, page)
    response = {
        key: items
    }
    return ApiResponse(response, headers=headers, status= codes.OK)


@contract
def generate_pagination_headers(results_count, results_per_page, current_page):
    """
    This function generates pagination response headers containing following parameters.
    :param (int|long) results_count: Total number of results
    :param int results_per_page: Number of results per page
    :param (int|long) current_page: Current page number
    :rtype: dict
    """
    return {
        'X-Total': results_count,
        'X-Per-Page': results_per_page,
        'X-Page': current_page,
        'Access-Control-Expose-Headers': 'X-Total, X-Per-Page, X-Page'
    }
