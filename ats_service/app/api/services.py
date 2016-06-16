from flask import request
from flask_restful import Resource

# Decorators
from ats_service.common.utils.auth_utils import require_oauth

import ats_service.app

# Why doesn't this work?
# from ats_service.app import logger

class ServicesList(Resource):
    decorators = [require_oauth()]

    def get(self, **kwargs):
        """
        """
        
        # Authenticated user
        authenticated_user = request.user

        # logger.info("ATS {} {} ({})".format(request.method, request.path, request.user.email))
        ats_service.app.logger.info("ATS {} {} ({})".format(request.method, request.path, request.user.email))

        return {'supported-ats-list': ['ats1', 'ats2', 'ats3']}
