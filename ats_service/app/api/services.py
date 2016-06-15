from flask import request
from flask_restful import Resource

# Decorators
from user_service.common.utils.auth_utils import require_oauth

class ServicesList(Resource):
    decorators = [require_oauth()]

    def get(self, **kwargs):
        """
        """
        
        # Authenticated user
        authenticated_user = request.user

        return {'supported-ats-list': ['ats1', 'ats2', 'ats3']}
