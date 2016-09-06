"""
Here we have endpoint which is treated as Mock-Service for different social-networks, e.g. Meetup.
"""
# Third party
import types
from flask import Blueprint, request

# Application Specific
from flask.ext.restful import Resource

from mock_service.common.constants import MEETUP
from mock_service.common.routes import MockServiceApi
from mock_service.common.talent_api import TalentApi
from mock_service.common.utils.api_utils import api_route, ApiResponse
from mock_service.common.talent_config_manager import TalentConfigKeys, TalentEnvs
from mock_service.common.error_handling import (NotFoundError, InternalServerError,
                                                UnauthorizedError)
from mock_service.mock_service_app import app, logger
from mock_service.modules.mock_api import MockApi
from mock_service.modules.vendors.meetup_mock import meetup_vendor

mock_blueprint = Blueprint('mock_service', __name__)
api = TalentApi()
api.init_app(mock_blueprint)
api.route = types.MethodType(api_route, api)

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
@api.route(MockServiceApi.MOCK_SERVICE)
class MockServer(Resource):
    """
    Mock Server endpoint to handle mock requests and its response.

    - mock_endpoint(self, url_type, social_network):
      when a request is made then return mocked response based on vendor dict defined. (See vendors/meetup_mock.py)
    """
    def get(self, url_type, social_network):
        return self.mock_endpoint(url_type, social_network)

    def put(self, url_type, social_network):
        return self.mock_endpoint(url_type, social_network)

    def post(self, url_type, social_network):
        return self.mock_endpoint(url_type, social_network)

    def delete(self, url_type, social_network):
        return self.mock_endpoint(url_type, social_network)

    def patch(self, url_type, social_network):
        return self.mock_endpoint(url_type, social_network)

    def mock_endpoint(self, url_type, social_network):
        """
        Mock endpoint
        :param url_type: auth url or api url
        :type url_type: str | basestring
        :param string social_network: Name of social-network. e.g. "meetup"
        """
        # We need to mock third party urls in case of jenkins or dev environment.
        if not app.config[TalentConfigKeys.ENV_KEY] in [TalentEnvs.DEV, TalentEnvs.JENKINS]:
            raise UnauthorizedError('This endpoint is not accessible in `%s` env.'
                                    % app.config[TalentConfigKeys.ENV_KEY])

        relative_url = request.args.get('path')

        vendor_data = mock_url_hub.get(social_network)
        if not vendor_data:
            raise NotFoundError("Vendor '{}' not found or mocked yet." % social_network)
        request_method = request.method

        splitted_data = relative_url.split('/')
        if len(splitted_data) > 2 and splitted_data[2].isdigit():
            relative_url = '/' + splitted_data[1]
            resource_id = splitted_data[2]
            if request_method == 'POST':
                request_method = 'PUT'
        else:
            resource_id = None

        try:
            if request.content_type == 'application/x-www-form-urlencoded' or request.content_type == '':
                data = dict()
                [data.update({k: v}) for k, v in request.values.iteritems()]
            elif request.content_type == 'application/json':
                data = request.json()
            else:
                data = request.data
            mocked_json = vendor_data(url_type, resource_id)[relative_url][request_method]
            mock_api = MockApi(mocked_json, payload=data, headers=request.headers)
            response, status_code = mock_api.get_response()
            logger.info('MOCK RESPONSE: {} Request data: {} {} {}'.format(str(response), url_type, relative_url,
                                                                          request_method))
        except KeyError:
            raise InternalServerError('No Data found. Method:%s, Url:%s.' % (request_method, relative_url))
        return ApiResponse(response=response, status=status_code)
