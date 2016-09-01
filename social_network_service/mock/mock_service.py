"""
Here we have endpoint which is treated as Mock-Service for different social-networks, e.g. Meetup.
"""
# Third party
from flask import Blueprint, request, jsonify

# Application Specific
from social_network_service.mock.mock_api import MockApi
from social_network_service.social_network_app import app, logger
from social_network_service.modules.constants import MEETUP
from social_network_service.modules.urls import SocialNetworkUrls
from social_network_service.common.routes import SocialNetworkApi
from social_network_service.mock.vendors.meetup_mock import meetup_vendor
from social_network_service.common.talent_config_manager import TalentConfigKeys
from social_network_service.common.error_handling import (NotFoundError, InternalServerError,
                                                          UnauthorizedError)

mock_blueprint = Blueprint('mock_service', __name__)

vendor_hub = dict()


def register_vendor(vendor_name, vendor_json_data):
    """
    Register vendor and json data so that it can be used in mock endpoint
    :param vendor_name: Meetup
    :type vendor_name: str | basestring
    :param vendor_json_data: See meetup.py
    :type vendor_json_data: Callable function
    """
    vendor_hub.update({vendor_name: vendor_json_data})


# Register meetup mock data
register_vendor(MEETUP, meetup_vendor)


@mock_blueprint.route(SocialNetworkApi.MOCK_SERVICE, methods=['PUT', 'PATCH', 'GET', 'POST', 'DELETE'])
def mock_endpoint(url_type, social_network):
    """
    Mock endpoint
    :param url_type: auth url or api url
    :type url_type: str | basestring
    :param string social_network: Name of social-network. e.g. "meetup"
    """
    # We need to mock third party vendors in case of jenkins or dev environment.
    if not SocialNetworkUrls.IS_DEV:
        raise UnauthorizedError('This endpoint is not accessible in `%s` env.'
                                % app.config[TalentConfigKeys.ENV_KEY])

    relative_url = request.args.get('path')

    vendor_data = vendor_hub.get(social_network)
    if not vendor_data:
        raise NotFoundError("Vendor '{}' not found or mocked yet." % social_network)
    request_method = request.method

    logger.info('CODE008:Testing %s - %s - %s' % (url_type, social_network, relative_url))

    splitted_data = relative_url.split('/')
    if len(splitted_data) > 1 and splitted_data[1].isdigit():
        relative_url = splitted_data[0]
        resource_id = splitted_data[1]
        if request_method == 'POST':
            request_method = 'PUT'
    else:
        resource_id = None

    try:
        if request.content_type == 'application/x-www-form-urlencoded':
            data = dict()
            [data.update({k: v}) for k, v in request.values.iteritems()]
        elif request.content_type == 'application/json':
            data = request.json()
        else:
            data = request.data
        logger.info('CODE008:Testing 01 %s - %s - %s' % (url_type, social_network, relative_url))
        mocked_json = vendor_data(url_type, resource_id)[relative_url][request_method]
        mock_api = MockApi(mocked_json, payload=data, headers=request.headers)
        logger.info('CODE008:Testing 02 %s - %s - %s' % (url_type, social_network, relative_url))
        response, status_code = mock_api.get_response()
        logger.info('CODE008:Testing 03 %s - %s' % (url_type, response))
    except KeyError:
        raise InternalServerError('No Data found. Method:%s, Url:%s.' % (request_method, relative_url))
    return jsonify(response), status_code
