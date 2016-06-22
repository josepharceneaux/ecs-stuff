"""
Classes implementing the ATS services endpoints.
"""

from flask import request
from flask_restful import Resource

# Decorators
from ats_service.common.utils.auth_utils import require_oauth

# Modules
import ats_service.app
# Why doesn't this work?
# from ats_service.app import logger

# Database
from ats_service.common.models.ats import ATS


class ServicesList(Resource):
    """
    Controller for /v1/ats-list. Return a list of ATS we have integrated with.
    """

    decorators = [require_oauth()]

    def get(self, **kwargs):
        """
        GET /v1/ats-list
        """

        # Authenticated user
        authenticated_user = request.user

        ats_service.app.logger.info("ATS {} {} ({})".format(request.method, request.path, request.user.email))
        return ATS.get_all_as_json()
