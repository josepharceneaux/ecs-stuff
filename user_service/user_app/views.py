__author__ = 'ufarooqi'

import random
import string
from . import app
from flask import request, url_for
from user_service.common.models.user import User
from user_service.common.redis_cache import redis_store
from user_service_utilties import send_reset_password_email
from user_service.common.error_handling import *
from user_service.common.utils.validators import is_valid_email
from user_service.common.models.user import Domain, DomainRole, Token, db
from werkzeug.security import generate_password_hash, check_password_hash
from user_service.common.utils.auth_utils import require_oauth, require_all_roles
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired



@app.route('/domain/<int:domain_id>/roles', methods=['GET'])
@require_oauth
@require_all_roles('CAN_GET_DOMAIN_ROLES')
def get_all_roles_of_domain(domain_id):
    # if logged-in user should belong to same domain as input domain_id
    if Domain.query.get(domain_id) and (request.user.domain_id == domain_id):
        all_roles_of_domain = DomainRole.all_roles_of_domain(domain_id)
        return jsonify(dict(roles=[{'id': domain_role.id, 'name': domain_role.role_name} for
                                   domain_role in all_roles_of_domain]))
    else:
        raise InvalidUsage(error_message='Either domain_id is invalid or it is different than that of logged-in user')


@app.route('/users/update_password', methods=['PUT'])
@require_oauth
def update_password():
    """
    This endpoint will be used to update the password of a user given old password
    :param: int user_id: Id of user whose password is going to be updated
    :return: success message if password will be updated successfully
    :rtype: dict
    """

    posted_data = request.get_json()
    if posted_data:
        old_password = posted_data.get('old_password', '')
        new_password = posted_data.get('new_password', '')
        if not old_password or not new_password:
            raise NotFoundError(error_message="Either old or new password is missing")
        old_password_hashed = request.user.password
        # If password is hashed in web2py app
        if 'pbkdf2:sha512:1000' not in old_password_hashed and old_password_hashed.count('$') == 2:
            (digest_alg, salt, hash_key) = request.user.password.split('$')
            old_password_hashed = 'pbkdf2:sha512:1000$%s$%s' % (salt, hash_key)
        if check_password_hash(old_password_hashed, old_password):
            # Change user's password
            request.user.password = generate_password_hash(new_password, method='pbkdf2:sha512')
            # Delete any tokens associated with him as password is changed now
            Token.query.filter_by(user_id=request.user.id).delete()
            db.session.commit()
            return jsonify(dict(success="Your password has been changed successfully"))
        else:
            raise UnauthorizedError(error_message="Old password is not correct")
    else:
        raise InvalidUsage(error_message='No request data is found')


@app.route('/users/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        # TODO: Redirect to UI view which is yet to be created
        pass
    else:
        email = request.form.get('username')
        if not email or not is_valid_email(email):
            raise InvalidUsage("A valid username should be provided")

        user = User.query.filter_by(email=email).first()
        if not user:
            raise NotFoundError(error_message="User with username: %s doesn't exist" % email)

        token = URLSafeTimedSerializer(app.config["SECRET_KEY"]).dumps(email, salt='recover-key')

        user.reset_password_key = token
        db.session.commit()

        # Create 6-digit numeric token for mobile app and store it into cache
        six_digit_token = ''.join(random.choice(string.digits) for _ in range(6))

        redis_store.setex(six_digit_token, token, 46400)  # Key-value pair will be removed after 12 hours
        reset_password_url = url_for('reset_password', token=token, _external=True)

        name = user.first_name or user.last_name or 'User'
        send_reset_password_email(email, name, reset_password_url, six_digit_token)

        return '', 204


@app.route('/users/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):

    try:
        # Check if token is six digit long (For Mobile)
        six_digit_token = ''
        if len(token) == 6:
            six_digit_token = token
            token = redis_store.get(six_digit_token)

        email = URLSafeTimedSerializer(app.config["SECRET_KEY"]).loads(token, salt='recover-key', max_age=46400)

        user = User.query.filter_by(email=email).first()
        if user.reset_password_key != token:
            raise Exception()

    except SignatureExpired:
        raise ForbiddenError(error_message="Your encrypted token has been expired")
    except BadSignature:
        raise ForbiddenError(error_message="Your encrypted token is not valid")
    except:
        raise ForbiddenError(error_message="Your encrypted token is not valid")

    if request.method == 'GET':
        # TODO: Redirect to UI view which is yet to be created
        return '', 204
    else:
        if not request.form.get('password'):
            raise InvalidUsage(error_message="A valid password should be provided")

        # Remove key-value pair from redis-cache
        if six_digit_token:
            redis_store.delete(six_digit_token)

        user.reset_password_key = ''
        user.password = generate_password_hash(request.form.get('password'), method='pbkdf2:sha512')
        db.session.commit()
        return '', 204


