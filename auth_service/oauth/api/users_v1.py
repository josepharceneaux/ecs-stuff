from flask_restful import Resource, Api, reqparse
from auth_service.oauth import app, db
from common.models.user import User

api = Api(app)
parser = reqparse.RequestParser()

# Post, Get, Update, Delete
class UserResource(Resource):
    def get(self, **kwargs):
        """ GET /web/api/users/:id

        Fetch user object with user's basic info.

        Takes an integer as user_id, assigned to args[0].
        The function will only accept an integer.
        Logged in user must be an admin.

        :return: A dictionary containing user's info from the database except
                 user's password, registration_key, and reset_password_key.
                 Not Found Error if user is not found.
        """
        requested_user_id = kwargs.get('id')

        requested_user = User.query.get(requested_user_id)

        return {'user': {
            'id': requested_user_id,
            'domin_id': requested_user.domain_id,
            'email': requested_user.email,
            'first_name': requested_user.first_name,
            'last_name': requested_user.last_name,
            'phone': requested_user.phone,
            'registration_id': requested_user.registration_id,
            'dice_user_id': requested_user.dice_user_id
        }}

api.add_resource(UserResource, "/api/users/<id>")


if __name__ == '__main__':
    app.run(debug=True)