from flask_restful import Resource
from flask import request, Blueprint
from flask.ext.common.common.routes import UserServiceApi
from user_service.common.error_handling import *
from user_service.common.talent_api import TalentApi
from user_service.common.models.user import User, db
from user_service.common.utils.validators import is_valid_email
from user_service.common.utils.auth_utils import require_oauth, require_any_role, require_all_roles
from user_service.user_app.user_service_utilties import check_if_user_exists, create_user_for_company


class UserApi(Resource):

    # Access token and role authentication decorators
    decorators = [require_oauth()]

    # 'SELF' is for readability. It means this endpoint will be accessible to any user
    @require_any_role('SELF', 'CAN_GET_USERS')
    def get(self, **kwargs):
        """
        GET /users/<id> Fetch user object with user's basic info
        GET /users      Fetch all user ids of a given domain

        :return A dictionary containing user basic info except safety critical info or a dictionary containing
                all user_ids of a domain
        :rtype: dict
        """

        requested_user_id = kwargs.get('id')
        if requested_user_id:
            requested_user = User.query.get(requested_user_id)
            if not requested_user:
                raise NotFoundError(error_message="User with user id %s not found" % requested_user_id)

            if requested_user.domain_id != request.user.domain_id:
                raise UnauthorizedError(error_message="User %s doesn't have appropriate permission to get user %s" %
                                                      (request.user.id, requested_user_id))

            if requested_user_id == request.user.id or 'CAN_GET_USERS' in request.valid_domain_roles:

                return {'user': {
                        'id': requested_user.id,
                        'domain_id': requested_user.domain_id,
                        'email': requested_user.email,
                        'first_name': requested_user.first_name,
                        'last_name': requested_user.last_name,
                        'phone': requested_user.phone,
                        'registration_id': requested_user.registration_id,
                        'dice_user_id': requested_user.dice_user_id
                        }}

        # User id is not provided so logged-in user wants to get all users of its domain
        elif 'CAN_GET_USERS' in request.valid_domain_roles:
                return {'users': [user.id for user in User.all_users_of_domain(request.user.domain_id)]}

        # If nothing is returned above then simply raise the custom exception
        raise UnauthorizedError(error_message="Logged-in user doesn't have appropriate permissions to get user's info.")

    @require_all_roles('CAN_ADD_USERS')
    def post(self):
        """
        POST /users  Create a new user
        input: {'users': [userDict1, userDict2, userDict3, ... ]}

        Take a JSON dictionary containing array of User dictionaries
        A single user dict must contain user's first name, last name, and email

        :return:  A dictionary containing array of user ids
        :rtype: dict
        """

        posted_data = request.get_json(silent=True)
        if not posted_data or 'users' not in posted_data:
            raise InvalidUsage(error_message="Request body is empty or not provided")

        # Save user object(s)
        users = posted_data['users']

        # User object(s) must be in a list
        if not isinstance(users, list):
            raise InvalidUsage(error_message="Request body is not properly formatted")

        for user_dict in users:

            first_name = user_dict.get('first_name', "").strip()
            last_name = user_dict.get('last_name', "").strip()
            email = user_dict.get('email', "").strip()

            if not first_name or not last_name or not email:
                raise InvalidUsage(error_message="first name, last name or email is missing in request body")

            if not is_valid_email(email=email):
                raise InvalidUsage(error_message="Email Address %s is not properly formatted" % email)

            # Check if user already exist
            if check_if_user_exists(email):
                raise InvalidUsage(error_message="User with email=%s already exists in Database" % email)

        user_ids = []  # Newly created user object's id(s) are appended to this list
        for user_dict in users:
            first_name = user_dict.get('first_name', "").strip()
            last_name = user_dict.get('last_name', "").strip()
            email = user_dict.get('email', "").strip()
            # TODO: Phone numbers formatting should be done on client side using country information for user
            phone = user_dict.get('phone', "").strip()
            dice_user_id = user_dict.get('dice_user_id')
            domain_id = request.user.domain_id

            user_id = create_user_for_company(first_name=first_name, last_name=last_name, email=email, phone=phone,
                                              domain_id=domain_id, dice_user_id=dice_user_id)
            user_ids.append(user_id)

        return {'users': user_ids}

    @require_all_roles('CAN_DELETE_USERS')
    def delete(self, **kwargs):
        """
        DELETE /users/<id>

        Function will disable user-object in db
        User will be prevented from deleting itself
        Last user in domain cannot be disabled

        :return: {'deleted_user' {'id': user_id}}
        :rtype:  dict
        """

        user_id_to_delete = kwargs.get('id')

        # Return 404 if requested user does not exist
        if user_id_to_delete:
            user_to_delete = User.query.filter(User.id == user_id_to_delete).first()
            if not user_to_delete:
                raise NotFoundError(error_message="Requested user with user id %s not found" % user_id_to_delete)

        if user_to_delete.domain_id != request.user.domain_id:
            raise UnauthorizedError("User to be deleted belongs to different domain than logged-in user")

        # Prevent logged-in user from deleting itself
        if user_id_to_delete == request.user.id:
            raise UnauthorizedError("Logged-in user cannot delete itself")

        # Prevent user from deleting the last user in the domain
        all_users_of_domain_of_user_to_delete = User.query.filter_by(domain_id=user_to_delete.domain_id).all()
        if len(all_users_of_domain_of_user_to_delete) < 3:
            raise InvalidUsage(error_message="Last user in domain %s cannot be deleted" % user_to_delete.domain_id)

        # Disable the user by setting is_disabled field to 1
        User.query.filter(User.id == user_id_to_delete).update({'is_disabled': '1'})
        db.session.commit()

        return {'deleted_user': {'id': user_id_to_delete}}

    # 'SELF' is for readability. It means this endpoint will be accessible to any user
    @require_any_role('SELF', 'CAN_EDIT_USERS')
    def put(self, **kwargs):
        """
        PUT /users/<id>

        Function will change credentials of one user per request.
        User will be allowed to modify itself

        :return: {'updated_user' {'id': user_id}}
        :rtype:  dict
        """

        requested_user_id = kwargs.get('id')
        requested_user = User.query.get(requested_user_id) if requested_user_id else None
        if not requested_user:
            raise NotFoundError(error_message="Either user_id is not provided or user doesn't exist")

        posted_data = request.get_json(silent=True)
        if not posted_data:
            raise InvalidUsage(error_message="Request body is empty or not provided")

        if requested_user.domain_id != request.user.domain_id:
            raise UnauthorizedError("User to be edited belongs to different domain than logged-in user")

        a = request
        if requested_user_id != request.user.id and 'CAN_EDIT_USERS' not in request.valid_domain_roles:
            raise UnauthorizedError(error_message="Logged-in user doesn't have appropriate permissions to edit a user")

        first_name = posted_data.get('first_name', '').strip()
        last_name = posted_data.get('last_name', '').strip()
        email = posted_data.get('email', '').strip()
        # TODO: Phone numbers formatting should be done on client side using country information for user
        phone = posted_data.get('phone', '').strip()

        if email and not is_valid_email(email=email):
            raise InvalidUsage(error_message="Email Address %s is not properly formatted" % email)

        if check_if_user_exists(email):
            raise InvalidUsage(error_message="Email Address %s already exists" % email)

        # Update user
        update_user_dict = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone
        }
        update_user_dict = dict((k, v) for k, v in update_user_dict.iteritems() if v)
        User.query.filter(User.id == requested_user_id).update(update_user_dict)
        db.session.commit()

        return {'updated_user': {'id': requested_user_id}}


users_blueprint = Blueprint('users_api', __name__)
api = TalentApi(users_blueprint)
api.add_resource(UserApi, UserServiceApi.USERS, UserServiceApi.USER)