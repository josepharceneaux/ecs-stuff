"""
Here we have endpoint which is treated as Mock-Service for different social-networks, e.g. Meetup.
"""
# Third party
from flask import Blueprint, request, jsonify

# App specific import
from requests import codes

# Application Specific
from social_network_service.social_network_app import app
from social_network_service.modules.constants import MEETUP
from social_network_service.modules.urls import SocialNetworkUrls
from social_network_service.common.routes import SocialNetworkApi
from social_network_service.mock.vendors.meetup import meetup_vendor
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
    :type vendor_json_data: dict
    """
    vendor_hub.update({vendor_name: vendor_json_data})


# Register meetup mock data
register_vendor(MEETUP, meetup_vendor)


@mock_blueprint.route(SocialNetworkApi.MOCK_SERVICE, methods=['PUT', 'PATCH', 'GET', 'POST', 'DELETE'])
def mock_endpoint(social_network, relative_url):
    """
    Mock endpoint
    :param social_network:
    :type social_network:
    """
    # We need to mock third party vendors in case of jenkins or dev environment.
    if not SocialNetworkUrls.IS_DEV:
        raise UnauthorizedError('This endpoint is not accessible in `%s` env.'
                                % app.config[TalentConfigKeys.ENV_KEY])

    vendor_dict = vendor_hub.get(social_network)
    if not vendor_dict:
        raise NotFoundError("Vendor '{}' not found or mocked yet." % social_network)

    request_method = request.method
    try:
        data = vendor_dict['/' + relative_url][request_method.upper()][codes.ok]
        status_code = data['status_code']
    except KeyError:
        raise InternalServerError('No Data found. Method:%s, Url:%s ' % request_method, relative_url)
    return jsonify(data), status_code
