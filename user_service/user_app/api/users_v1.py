from flask_restful import Resource
from flask import request
from user_service.common.models.user import User, Domain, db
from user_service.user_app.user_service_utilties import check_if_user_exists, create_user_for_company
from user_service.common.utils.validators import is_number, is_valid_email
from user_service.common.utils.auth_utils import require_oauth, require_any_role
from user_service.common.error_handling import *


class UserApi(Resource):

    # Access token and role authentication decorators
    decorators = [require_oauth, require_any_role('ADMIN', 'DOMAIN_ADMIN')]

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
            # Either Logged in user should be ADMIN or if logged-in user has DOMAIN_ADMIN role then it should belong
            # to same domain as requested_user
            elif requested_user_id == request.user.id or request.is_admin_user or (
                            'DOMAIN_ADMIN' in request.valid_domain_roles and requested_user.domain_id == request.user.domain_id):

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
        # But for this logged in user should be ADMIN or DOMAIN_ADMIN
        elif request.is_admin_user or 'DOMAIN_ADMIN' in request.valid_domain_roles:
                return {'users': [user.id for user in User.all_user_of_domain(request.user.domain_id)]}

        # If nothing is returned above then simply raise the custom exception
        raise UnauthorizedError(error_message="Either logged-in user belongs to different domain as requested_user\
                                                  or it's no an ADMIN or DOMAIN_ADMIN user")

    def post(self):
        """
        POST /users  Create a new user
        input: {'users': [userDict1, userDict2, userDict3, ... ]}

        Take a JSON dictionary containing array of User dictionaries
        A single user dict must contain user's first name, last name, and email.
        Logged in user must be an ADMIN or DOMAIN_ADMIN.

        :return:  A dictionary containing array of user ids
        :rtype: dict
        """

        posted_data = request.get_json(silent=True)
        if not posted_data:
            raise InvalidUsage(error_message="Request body is empty or not provided")

        # Logged in user must be an ADMIN or DOMAIN_ADMIN
        if not request.is_admin_user and 'DOMAIN_ADMIN' not in request.valid_domain_roles:
            raise UnauthorizedError(error_message="Logged-in user should be either DOMAIN_ADMIN or\
                                                    ADMIN to add a new user")

        # Save user object(s)
        users = posted_data['users']

        # User object(s) must be in a list
        if not isinstance(users, list):
            raise InvalidUsage(error_message="Request body is not properly formatted")

        for user_dict in users:

            first_name = user_dict.get('first_name', "").strip()
            last_name = user_dict.get('last_name', "").strip()
            email = user_dict.get('email', "").strip()

            # If logged-in user is an Admin then he can provide a domain_id or domain_name(existing)
            if request.is_admin_user:
                domain = user_dict.get('domain', "").strip() or request.user.domain_id
            # If logged-in user is DOMAIN_ADMIN then domain_id of logged-in user will be used for this new user
            else:
                domain = request.user.domain_id

            if not first_name or not last_name or not email:
                raise InvalidUsage(error_message="first name, last name or email is missing in request body")

            if not is_valid_email(email=email):
                raise InvalidUsage(error_message="Email Address %s is not properly formatted" % email)

            # If logged-in user is an ADMIN then he can create new domain
            if is_number(domain):
                domain_id = int(domain)
                # If domain doesn't exist then raise NotFound exception
                if not domain_id or not Domain.query.get(domain_id):
                    raise NotFoundError(error_message="Domain with domain_id %s not found in Database" % domain_id)
            else:
                domain = Domain.query.filter_by(name=domain).first()
                domain_id = domain.id if domain else None
                if not domain_id:
                    raise NotFoundError(error_message="Domain with name %s doesn't exits in Database" % domain)

            user_dict['domain_id'] = domain_id

            # Check if user already exist
            if check_if_user_exists(email, domain_id):
                raise InvalidUsage(error_message="User with email=%s already exists in Database" % email)

        user_ids = []  # Newly created user object's id(s) are appended to this list
        for user_dict in users:
            first_name = user_dict.get('first_name', "").strip()
            last_name = user_dict.get('last_name', "").strip()
            email = user_dict.get('email', "").strip()
            # TODO: Phone numbers formatting should be done on client side using country information for user
            phone = user_dict.get('phone', "").strip()
            is_admin = True if user_dict.get('is_admin') == '1' else False
            is_domain_admin = True if user_dict.get('is_domain_admin') == '1' else False
            dice_user_id = user_dict.get('dice_user_id')
            domain_id = user_dict.get('domain_id')

            user_id = create_user_for_company(first_name=first_name, last_name=last_name, email=email, phone=phone,
                                              domain_id=domain_id, is_admin=is_admin, is_domain_admin=is_domain_admin,
                                              dice_user_id=dice_user_id)
            user_ids.append(user_id)

        return {'users': user_ids}

    def delete(self, **kwargs):
        """
        DELETE /users/<id>

        Function can delete one user per request.
        Function will remove user-object from db

        Only ADMIN or DOMAIN_ADMIN users can delete users
        User will be prevented from deleting itself
        Last user in domain cannot be deleted
        All of user's data will be transferred to the DOMAIN_ADMIN

        :return: {'user' {'id': user_id}}
        :rtype:  dict
        """

        # Logged in user must be an ADMIN or DOMAIN_ADMIN
        if not request.is_admin_user and 'DOMAIN_ADMIN' not in request.valid_domain_roles:
            raise UnauthorizedError(error_message="Logged-in user should be either DOMAIN_ADMIN or\
                                                    ADMIN to add a new user")

        user_id_to_delete = kwargs.get('id')

        # Return 404 if requested user does not exist
        user_to_delete = User.query.get(user_id_to_delete)
        if not user_to_delete:
            raise NotFoundError(error_message="Requested user with user_id %s doesn't exist" % user_id_to_delete)

        # If logged-in user is a DOMAIN_ADMIN then user_to_delete should belong to same domain as logged-in user
        if not request.is_admin_user and user_to_delete.domain_id != request.user.domain_id:
            raise UnauthorizedError("User to be deleted belongs to different domain than logged-in user")

        # Prevent logged-in user from deleting itself
        if user_id_to_delete == request.user.id:
            raise UnauthorizedError("Logged-in user cannot delete itself")

        # Prevent user from deleting the last user in the domain
        # count < 3 accounts for: logged_in_user and at least one user in the logged_in_user's domain
        all_users_of_domain_of_user_to_delete = User.query.filter_by(domain_id=user_to_delete.domain_id).all
        if (user_to_delete.domain_id == request.user.domain_id and len(all_users_of_domain_of_user_to_delete) < 3)\
                or len(all_users_of_domain_of_user_to_delete) < 2:
            raise InvalidUsage(error_message="Last user in domain %s cannot be deleted" % user_to_delete.domain_id)

        # Disable the user by setting is_disabled field to 1
        User.query.get(user_id_to_delete).update({'is_disabled': '1'})
        db.session.commit()

        return {'user': {'id': user_id_to_delete}}

    def put(self, **kwargs):
        """
        PUT /users/<id>

        Function will change credentials of one user per request.

        Only ADMIN DOMAIN_ADMIN users can modify other users
        User will be allowed to modify itself

        :return: {'user' {'id': user_id}}
        :rtype:  dict
        """

        requested_user_id = kwargs.get('id')
        requested_user = User.query.get(requested_user_id) if requested_user_id else None
        if not requested_user:
            raise NotFoundError(error_message="Either user_id is not provided or user doesn't exist")

        posted_data = request.get_json(silent=True)
        if not posted_data:
            raise InvalidUsage(error_message="Request body is empty or not provided")

        # Logged-in user should be either DOMAIN_ADMIN, ADMIN to modify a user or it can modify itself
        if requested_user_id != request.user.id and not request.is_admin_user and ('DOMAIN_ADMIN' not in request.
                valid_domain_roles or requested_user.domain_id != request.user.domain_id):
            raise UnauthorizedError(error_message="Logged-in user should be either DOMAIN_ADMIN,\
                                                                    ADMIN to modify a user or it can modify itself")

        first_name = posted_data.get('first_name')
        last_name = posted_data.get('last_name')
        email = posted_data.get('email')
        # TODO: Phone numbers formatting should be done on client side using country information for user
        phone = posted_data.get('phone')

        if email and not is_valid_email(email=email):
            raise InvalidUsage(error_message="Email Address %s is not properly formatted" % email)

        # Update user
        update_user_dict = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone
        }
        update_user_dict = dict((k, v) for k, v in update_user_dict.iteritems() if v)
        User.query.get(requested_user_id).update(update_user_dict)
        db.session.commit()

        return {'user': {'id': requested_user_id}}