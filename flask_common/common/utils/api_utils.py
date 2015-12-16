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
from .common_functions import JSON_CONTENT_TYPE_HEADER


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
