"""
This module contains API endpoint to create test data like test users, domain, tokens, client.
In this we will be able to run tests on jenkins and setting any environment `qa` or `prod`, we can test APIs on those
environments. So instead of testing manually, jenkins will do the task up to some extent.
"""
import types
from flask_restful import Resource
from flask import Blueprint, request

from user_service.common.error_handling import ForbiddenError
from user_service.common.routes import UserServiceApi
from user_service.common.talent_api import TalentApi
from user_service.common.utils.api_utils import api_route
from user_service.modules.init_test_data import create_test_data
from user_service.common.talent_config_manager import TalentConfigKeys, TalentEnvs

# creating blueprint
from user_service.user_app import app, logger

test_setup_blueprint = Blueprint('test_setup', __name__)
api = TalentApi()
api.init_app(test_setup_blueprint)
api.route = types.MethodType(api_route, api)


@api.route(UserServiceApi.TEST_SETUP)
class TestSetupApi(Resource):

    def post(self):
        """
        POST /test-setup/
        This endpoint will create test data required to run tests.

        Users created by this endpoint have ability to Create, Read and Update (CRU). (Not delete)
        Users are assigned `TEST_ADMIN` role.
        """
        origin = request.remote_addr
        localhost = '127.0.0.1'
        environment = app.config[TalentConfigKeys.ENV_KEY]
        jenkins_ip = app.config[TalentConfigKeys.JENKINS_HOST_IP]
        is_gettalent = origin.count('gettalent.com') == 1 or origin == jenkins_ip
        is_dev = origin == localhost and app.config[TalentConfigKeys.ENV_KEY] in [TalentEnvs.DEV, TalentEnvs.JENKINS]
        is_alloed = is_gettalent or is_dev
        message = """is_gettalent: %s,
                       id_dev: %s,
                       origin: %s,
                       environment: %s,
                       is_allowed: %s
                    """ % (is_gettalent, is_dev, origin, environment, is_alloed)
        if not is_alloed:
            logger.warn(message)
            raise ForbiddenError('Invalid request origin : %s' % origin)

        logger.info(message)
        return create_test_data()
