from flask_restful import (Api, reqparse, Resource)
from auth_service.oauth import app
from common.models.user import User
from common.utils.validators import is_number
from common.utils.auth_utils import authenticate_oauth_user
from flask import request
from common.error_handling import *


api = Api(app)
parser = reqparse.RequestParser()


class UserResource(Resource):
    def get(self, **kwargs):
        """ GET /web/users/:id

        Fetch user object with user's basic info.

        Takes an integer as user_id, assigned to args[0].
        The function will only accept an integer.
        Logged in user must be an admin.

        :return: A dictionary containing user's info from the database except
                 user's password, registration_key, and reset_password_key.
                 Not Found Error if user is not found.
        """
        authenticated_user = authenticate_oauth_user(request=request)
        if authenticated_user.get('error'):
            print "auth_service/api/..."
            return {'error': {'code': 2, 'message': 'not authorized'}}, 401
            # raise ForbiddenError(error_message='not authorized', error_code=401)

        requested_user_id = kwargs.get('id')
        # id must be integer
        if not is_number(requested_user_id):
            print is_number(requested_user_id)
            return {'error': {'message': 'invalid input'}}, 400

        requested_user = User.query.get(requested_user_id)
        if not requested_user:
            print "no authenticated user"
            return {'error': {'message': 'user not found'}}, 404

        return {'user': {
            'id': requested_user_id,
            'domain_id': requested_user.domain_id,
            'email': requested_user.email,
            'first_name': requested_user.first_name,
            'last_name': requested_user.last_name,
            'phone': requested_user.phone,
            'registration_id': requested_user.registration_id,
            'dice_user_id': requested_user.dice_user_id
        }}

api.add_resource(UserResource, "/v1/users/<id>")


if __name__ == '__main__':
    app.run(debug=True)