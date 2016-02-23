from dateutil import parser
from flask_restful import Resource
from flask import request, Blueprint
from user_service.common.routes import UserServiceApi
from user_service.common.error_handling import *
from user_service.common.talent_api import TalentApi
from user_service.common.models.user import User, db, DomainRole, Token
from user_service.common.utils.validators import is_valid_email, is_number
from user_service.common.utils.auth_utils import require_oauth, require_any_role, require_all_roles
from user_service.user_app.user_service_utilties import check_if_user_exists, create_user_for_company


class UserApi(Resource):

    # Access token and role authentication decorators
    decorators = [require_oauth()]

    # 'SELF' is for readability. It means this endpoint will be accessible to any user
    @require_any_role('SELF', DomainRole.Roles.CAN_GET_USERS)
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
            if not requested_user or requested_user.is_disabled == 1:
                raise NotFoundError(error_message="User with user id %s not found" % requested_user_id)

            if requested_user.domain_id != request.user.domain_id and not request.user_can_edit_other_domains:
                raise UnauthorizedError(error_message="User %s doesn't have appropriate permission to get user %s" %
                                                      (request.user.id, requested_user_id))

            if requested_user_id == request.user.id or 'CAN_GET_USERS' in request.valid_domain_roles or request.user_can_edit_other_domains:

                return {'user': {
                        'id': requested_user.id,
                        'domain_id': requested_user.domain_id,
                        'email': requested_user.email,
                        'first_name': requested_user.first_name,
                        'last_name': requested_user.last_name,
                        'phone': requested_user.phone,
                        'registration_id': requested_user.registration_id,
                        'dice_user_id': requested_user.dice_user_id,
                        'last_read_datetime': requested_user.last_read_datetime.isoformat() if requested_user.last_read_datetime else None,
                        'thumbnail_url': requested_user.thumbnail_url
                        }}

        # User id is not provided so logged-in user wants to get all users of its domain
        elif 'CAN_GET_USERS' in request.valid_domain_roles or request.user_can_edit_other_domains:
                return {'users': [user.id for user in User.all_users_of_domain(request.user.domain_id) if not
                user.is_disabled]}

        # If nothing is returned above then simply raise the custom exception
        raise UnauthorizedError(error_message="Logged-in user doesn't have appropriate permissions to get user's info.")

    @require_any_role(DomainRole.Roles.CAN_ADD_USERS, DomainRole.Roles.CAN_EDIT_OTHER_DOMAIN_INFO)
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
            already_existing_user = check_if_user_exists(email)
            if already_existing_user:
                if already_existing_user.is_disabled:
                    raise InvalidUsage(error_message="User with email=%s already exists in Database but is disabled" % email)
                else:
                    raise InvalidUsage(error_message="User with email=%s already exists in Database" % email)

        user_ids = []  # Newly created user object's id(s) are appended to this list
        for user_dict in users:
            first_name = user_dict.get('first_name', "").strip()
            last_name = user_dict.get('last_name', "").strip()
            email = user_dict.get('email', "").strip()
            phone = user_dict.get('phone', "").strip()
            dice_user_id = user_dict.get('dice_user_id')
            thumbnail_url = user_dict.get('thumbnail_url', '').strip()
            user_group_id = user_dict.get('user_group_id')
            if request.user_can_edit_other_domains:
                domain_id = user_dict.get('domain_id', request.user.domain_id)
            else:
                domain_id = request.user.domain_id

            user_id = create_user_for_company(first_name=first_name, last_name=last_name, email=email, phone=phone,
                                              domain_id=domain_id, dice_user_id=dice_user_id, thumbnail_url=thumbnail_url,
                                              user_group_id=user_group_id)
            user_ids.append(user_id)

        return {'users': user_ids}

    # 'SELF' is for readability. It means this endpoint will be accessible to any user
    @require_any_role('SELF', DomainRole.Roles.CAN_EDIT_USERS)
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

        if not request.user_can_edit_other_domains:
            if requested_user.domain_id != request.user.domain_id:
                raise UnauthorizedError("User to be edited belongs to different domain than logged-in user")

            if requested_user_id != request.user.id and 'CAN_EDIT_USERS' not in request.valid_domain_roles:
                raise UnauthorizedError(error_message="Logged-in user doesn't have appropriate permissions to edit a user")

        first_name = posted_data.get('first_name', '').strip()
        last_name = posted_data.get('last_name', '').strip()
        email = posted_data.get('email', '').strip()
        phone = posted_data.get('phone', '').strip()
        thumbnail_url = posted_data.get('thumbnail_url', '').strip()
        last_read_datetime = posted_data.get('last_read_datetime', '').strip()
        is_disabled = posted_data.get('is_disabled', 0)

        try:
            last_read_datetime = parser.parse(last_read_datetime)
        except Exception as e:
            raise InvalidUsage("Last read datetime %s is invalid because: %s" % (last_read_datetime, e.message))

        if email and not is_valid_email(email=email):
            raise InvalidUsage(error_message="Email Address %s is not properly formatted" % email)

        if check_if_user_exists(email):
            raise InvalidUsage(error_message="Email Address %s already exists" % email)

        if not is_number(is_disabled) or (int(is_disabled) != 0 and int(is_disabled) != 1):
            raise InvalidUsage("Possible vaues of `is_disabled` are 0 and 1")

        is_disabled = int(is_disabled)
        
        # Update user
        update_user_dict = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
            'thumbnail_url': thumbnail_url,
            'last_read_datetime': last_read_datetime,
            'is_disabled': is_disabled
        }
        update_user_dict = dict((k, v) for k, v in update_user_dict.iteritems() if v)
        User.query.filter(User.id == requested_user_id).update(update_user_dict)
        db.session.commit()

        if is_disabled:
            # Delete all tokens of deleted user
            tokens = Token.query.filter_by(user_id=requested_user_id).all()
            for token in tokens:
                token.delete()

        return {'updated_user': {'id': requested_user_id}}


users_blueprint = Blueprint('users_api', __name__)
api = TalentApi(users_blueprint)
api.add_resource(UserApi, UserServiceApi.USERS, UserServiceApi.USER)
