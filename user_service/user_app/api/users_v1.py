import pytz
from datetime import datetime
from dateutil import parser
from babel import Locale
from werkzeug.security import gen_salt
from flask_restful import Resource
from flask import request, Blueprint
from user_service.common.routes import UserServiceApi
from user_service.common.error_handling import *
from user_service.common.talent_api import TalentApi
from user_service.common.models.user import User, db, Permission, Token, Domain
from user_service.common.utils.validators import is_valid_email, is_number
from user_service.common.utils.auth_utils import gettalent_generate_password_hash
from user_service.common.utils.auth_utils import require_oauth, require_all_permissions
from user_service.user_app.user_service_utilties import (check_if_user_exists, create_user_for_company,
                                                         send_new_account_email, validate_role)


class UserInviteApi(Resource):

    # Access token and role authentication decorators
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_ADD_USERS)
    def post(self, **kwargs):
        """
        POST /users/<id>/invite This endpoint will send invitation email to an already existing user
        :param kwargs:
        :return: None
        """

        requested_user_id = kwargs.get('id')
        requested_user = User.get(requested_user_id)
        if not requested_user:
            raise NotFoundError("User with user id %s is not found" % requested_user_id)

        if requested_user.is_disabled == 0:
            raise InvalidUsage("User %s is already active" % requested_user_id)

        temp_password = gen_salt(8)
        requested_user.password = gettalent_generate_password_hash(temp_password)
        requested_user.password_reset_time = datetime.utcnow()
        requested_user.is_disabled = 0
        db.session.commit()

        send_new_account_email(requested_user.email, temp_password, requested_user.email)

        return '', 201


class UserApi(Resource):

    # Access token and role authentication decorators
    decorators = [require_oauth()]

    # 'SELF' is for readability. It means this endpoint will be accessible to any user
    @require_all_permissions(Permission.PermissionNames.CAN_GET_USERS)
    def get(self, **kwargs):
        """
        GET /users/<id>             Fetch user object with user's basic info
        GET /users?domain_id=1      Fetch all user ids of a given domain

        :return A dictionary containing user basic info except safety critical info or a dictionary containing
                all user_ids of a domain
        :rtype: dict
        """

        requested_user_id = kwargs.get('id')
        if requested_user_id:
            requested_user = User.query.get(requested_user_id)
            if not requested_user:
                raise NotFoundError("User with user id %s not found" % requested_user_id)

            if request.user.role.name != 'TALENT_ADMIN' and requested_user.domain_id != request.user.domain_id:
                raise UnauthorizedError("User %s doesn't have appropriate permission to get user %s" % (
                    request.user.id, requested_user_id))

            return {
                'user': requested_user.to_dict()
            }

        # User id is not provided so logged-in user wants to get all users of its domain
        else:
            domain_id = request.user.domain_id

            # Get all users of any domain if user is `TALENT_ADMIN`
            if request.user.role.name == 'TALENT_ADMIN' and request.args.get('domain_id'):
                domain_id = request.args.get('domain_id')
                if not is_number(domain_id) or not Domain.query.get(int(domain_id)):
                    raise InvalidUsage("Invalid Domain Id is provided")

            return {'users': [user.to_dict() for user in User.all_users_of_domain(int(domain_id))]}

    @require_all_permissions(Permission.PermissionNames.CAN_ADD_USERS)
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
            raise InvalidUsage("Request body is empty or not provided")

        # Save user object(s)
        users = posted_data['users']

        # User object(s) must be in a list
        if not isinstance(users, list):
            raise InvalidUsage("Request body is not properly formatted")

        for user_dict in users:

            first_name = user_dict.get('first_name', "").strip()
            last_name = user_dict.get('last_name', "").strip()
            email = user_dict.get('email', "").strip()

            if not first_name or not last_name or not email:
                raise InvalidUsage("first name, last name or email is missing in request body")

            if not is_valid_email(email=email):
                raise InvalidUsage("Email Address %s is not properly formatted" % email)

            # Check if user already exist
            already_existing_user = check_if_user_exists(email)
            if already_existing_user:
                if already_existing_user.is_disabled:
                    raise InvalidUsage("User with email=%s already exists in Database but is disabled" % email)
                else:
                    raise InvalidUsage("User with email=%s already exists in Database" % email)

            if request.user.role.name == 'TALENT_ADMIN':
                domain_id = user_dict.get('domain_id', request.user.domain_id)
            else:
                domain_id = request.user.domain_id
            user_dict['domain_id'] = domain_id

            role = user_dict.get('role', '')
            user_dict['role_id'] = validate_role(role, domain_id, request.user) if role else ''

        user_ids = []  # Newly created user object's id(s) are appended to this list
        for user_dict in users:
            first_name = user_dict.get('first_name', "").strip()
            last_name = user_dict.get('last_name', "").strip()
            email = user_dict.get('email', "").strip()
            phone = user_dict.get('phone', "").strip()
            dice_user_id = user_dict.get('dice_user_id')
            thumbnail_url = user_dict.get('thumbnail_url', '').strip()
            user_group_id = user_dict.get('user_group_id')
            locale = user_dict.get('locale', 'en-US')
            domain_id = user_dict.get('domain_id')
            role_id = user_dict.get('role_id', '')

            try:
                Locale.parse(locale, sep='-')
            except:
                raise InvalidUsage('A valid Locale value should be provided')

            user_id = create_user_for_company(first_name=first_name, last_name=last_name, email=email, phone=phone,
                                              domain_id=domain_id, dice_user_id=dice_user_id, thumbnail_url=thumbnail_url,
                                              user_group_id=user_group_id, locale=locale, role_id=role_id)
            user_ids.append(user_id)

        return {'users': user_ids}

    # 'SELF' is for readability. It means this endpoint will be accessible to any user
    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_USERS)
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
            raise NotFoundError("Either user_id is not provided or user doesn't exist")

        posted_data = request.get_json(silent=True)
        if not posted_data:
            raise InvalidUsage("Request body is empty or not provided")

        if request.user.role.name != 'TALENT_ADMIN' and requested_user.domain_id != request.user.domain_id:
            raise UnauthorizedError("Logged-in user doesn't have appropriate permissions to edit a user")

        if request.user.role.name == 'USER' and requested_user_id != request.user.id:
            raise UnauthorizedError("Logged-in user doesn't have appropriate permissions to edit a user")

        first_name = posted_data.get('first_name', '').strip()
        last_name = posted_data.get('last_name', '').strip()
        email = posted_data.get('email', '').strip()
        phone = posted_data.get('phone', '').strip()
        thumbnail_url = posted_data.get('thumbnail_url', '').strip()
        last_read_datetime = posted_data.get('last_read_datetime', '').strip()
        is_disabled = posted_data.get('is_disabled', 0)
        locale = posted_data.get('locale', '')

        try:
            last_read_datetime = parser.parse(last_read_datetime)
        except Exception as e:
            raise InvalidUsage("Last read datetime %s is invalid because: %s" % (last_read_datetime, e.message))

        if email and not is_valid_email(email=email):
            raise InvalidUsage("Email Address %s is not properly formatted" % email)

        if email and check_if_user_exists(email) and requested_user.email != email:
            raise InvalidUsage("Email Address %s already exists" % email)

        if not is_number(is_disabled) or (int(is_disabled) != 0 and int(is_disabled) != 1):
            raise InvalidUsage("Possible vaues of `is_disabled` are 0 and 1")

        is_disabled = int(is_disabled)

        if locale:
            try:
                Locale.parse(locale, sep='-')
            except:
                raise InvalidUsage('A valid Locale value should be provided')
        
        # Update user
        update_user_dict = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
            'thumbnail_url': thumbnail_url,
            'last_read_datetime': last_read_datetime,
            'is_disabled': is_disabled,
            'locale': locale
        }
        update_user_dict = dict((k, v) for k, v in update_user_dict.iteritems() if v)
        User.query.filter(User.id == requested_user_id).update(update_user_dict)
        db.session.commit()

        if is_disabled:
            # Delete all tokens of deleted user
            request.user.password_reset_time = datetime.utcnow()
            tokens = Token.query.filter_by(user_id=requested_user_id).all()
            for token in tokens:
                token.delete()

        return {'updated_user': {'id': requested_user_id}}


users_blueprint = Blueprint('users_api', __name__)
api = TalentApi(users_blueprint)
api.add_resource(UserApi, UserServiceApi.USERS, UserServiceApi.USER)
api.add_resource(UserInviteApi, UserServiceApi.USER_INVITE)