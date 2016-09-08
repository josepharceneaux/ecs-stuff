"""
Here we have endpoint which is treated as Mock-Service for different social-networks, e.g. Meetup.
"""

# Standard Library
import types

# Third party
from flask import Blueprint, request
from flask.ext.restful import Resource

# Application Specific
from mock_service.common.constants import MEETUP
from mock_service.common.routes import MockServiceApi
from mock_service.common.utils.api_utils import ApiResponse
from mock_service.common.talent_config_manager import TalentConfigKeys, TalentEnvs
from mock_service.common.error_handling import (NotFoundError, InternalServerError,
                                                UnauthorizedError)
from mock_service.common.utils.handy_functions import (HttpMethods, JSON_CONTENT_TYPE_HEADER)
from mock_service.mock_service_app import app, logger
from mock_service.modules.mock_utils import get_mock_response
from mock_service.modules.vendors.meetup import meetup_vendor

mock_blueprint = Blueprint('mock_service', __name__)

mock_url_hub = dict()


def register_vendor(vendor_name, vendor_json_data):
    """
    Register vendor and json data so that it can be used in mock endpoint
    :param vendor_name: Meetup
    :type vendor_name: str | basestring
    :param vendor_json_data: See meetup_mock.py
    :type vendor_json_data: Callable
    """
    mock_url_hub.update({vendor_name: vendor_json_data})


# Register meetup mock data
register_vendor(MEETUP, meetup_vendor)


# TODO: Make this endpoint generic and usable for all services
@mock_blueprint.route(MockServiceApi.MOCK_SERVICE)
def mock_endpoint(url_type, social_network, path):
    """
    Mock endpoint to handle mock requests and its response.
    Note: Currently it works for only meetup vendor.
    :param url_type: auth url or api url
    :type url_type: str | basestring
    :param social_network: Name of social-network. e.g. "meetup"
    :type social_network: str | basestring
    :param path: relative part of vendor url
    :type: str | basestring
    """
    # We need to mock third party urls in case of jenkins or dev environment.
    if app.config[TalentConfigKeys.ENV_KEY] not in [TalentEnvs.DEV, TalentEnvs.JENKINS]:
        raise UnauthorizedError('This endpoint is not accessible in `%s` env.'
                                % app.config[TalentConfigKeys.ENV_KEY])

    # path will be relative url. i.e self/member
    relative_url = path

    vendor_data = mock_url_hub.get(social_network)
    if not vendor_data:
        raise NotFoundError("Vendor '{}' not found or mocked yet." % social_network)
    request_method = request.method

    # To get id from put or get url i.e event/23 or event/45. Split data and get resource id
    splitted_data = relative_url.split('/')
    if len(splitted_data) > 1 and splitted_data[1].isdigit():
        relative_url = splitted_data[0]
        resource_id = splitted_data[1]
        if request_method == HttpMethods.POST:
            request_method = HttpMethods.PUT
    else:
        resource_id = None
    try:
        if request.content_type in ['application/x-www-form-urlencoded', '']:
            data = dict()
            # In case of url encoded data or form data get all values from querystring or form data
            [data.update({k: v}) for k, v in request.values.iteritems()]
        elif request.content_type == JSON_CONTENT_TYPE_HEADER['content-type']:
            # In case of json, get json data
            data = request.json()
        else:
            data = request.data
        # get mocked json vendor based. In case of meetup, a meetup dict will be returned (response, status code.
        # see meetup_mock.py)
        mocked_json = vendor_data(url_type, resource_id)['/' + relative_url][request_method]
        response, status_code = get_mock_response(mocked_json, payload=data, headers=request.headers)
        logger.info('MOCK RESPONSE: {} Request data: {} {} {}'.format(str(response), url_type, relative_url,
                                                                      request_method))
    except KeyError:
        raise InternalServerError('No Data found. Method:%s, Url:%s.' % (request_method, relative_url))
    return ApiResponse(response=response, status=status_code)
