__author__ = 'ufarooqi'

import os
from . import app
from datetime import datetime
from flask import request, Blueprint
from user_service.common.models.user import User
from user_service.common.redis_cache import redis_store
from user_service_utilties import send_reset_password_email, PASSWORD_RECOVERY_JWT_SALT, \
    PASSWORD_RECOVERY_JWT_MAX_AGE_SECONDS
from user_service.common.error_handling import *
from user_service.common.routes import UserServiceApi, get_web_app_url
from user_service.common.utils.validators import is_valid_email
from user_service.common.models.user import Token, db
from werkzeug.security import check_password_hash
from user_service.common.utils.auth_utils import require_oauth, gettalent_generate_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

users_utilities_blueprint = Blueprint('users_utilities_api', __name__)


@users_utilities_blueprint.route(UserServiceApi.UPDATE_PASSWORD, methods=['PUT'])
@require_oauth()
def update_password():
    """
    This endpoint will be used to update the password of a user given old password
    :param: int user_id: Id of user whose password is going to be updated
    :return: success message if password will be updated successfully
    :rtype: dict
    """

    # Validate inputs
    posted_data = request.get_json()
    if not posted_data:
        raise InvalidUsage(error_message='No request data is found')
    old_password = posted_data.get('old_password', '')
    new_password = posted_data.get('new_password', '')
    if not old_password or not new_password:
        raise NotFoundError(error_message="Either old or new password is missing")

    old_password_hashed = request.user.password

    # If password is hashed in web2py (old framework) format, change it to werkzeug.security format
    if 'pbkdf2:sha512:1000' not in old_password_hashed and old_password_hashed.count('$') == 2:
        (digest_alg, salt, hash_key) = request.user.password.split('$')
        old_password_hashed = 'pbkdf2:sha512:1000$%s$%s' % (salt, hash_key)

    # Verify old password hash
    if not check_password_hash(old_password_hashed, old_password):
        raise InvalidUsage("Old password is not correct")

    # Change user's password & clear out all user's access tokens
    request.user.password = gettalent_generate_password_hash(new_password)
    request.user.password_reset_time = datetime.utcnow()

    db.session.commit()

    # Delete all existing tokens for logged-in user
    tokens = Token.query.filter_by(user_id=request.user.id).all()
    for token in tokens:
        token.delete()

    return jsonify(dict(success="Your password has been changed successfully"))


@users_utilities_blueprint.route(UserServiceApi.FORGOT_PASSWORD, methods=['POST'])
def forgot_password():

    posted_data = request.get_json()
    if not posted_data:
        raise InvalidUsage(error_message="No request data is found")

    email = posted_data.get('username', '')
    if not email or not is_valid_email(email):
        raise InvalidUsage("A valid username should be provided")

    user = User.query.filter_by(email=email).first()
    if not user or user.is_disabled:
        raise NotFoundError(error_message="User with username: %s does not exist or is disabled" % email)

    token = URLSafeTimedSerializer(app.config["SECRET_KEY"]).dumps(email, salt=PASSWORD_RECOVERY_JWT_SALT)

    user.reset_password_key = token
    db.session.commit()

    # Create an alphanumeric token for mobile app and store it into cache
    alphanumeric_token = os.urandom(3).encode('hex')

    redis_store.setex(alphanumeric_token, token, PASSWORD_RECOVERY_JWT_MAX_AGE_SECONDS)

    reset_password_url = get_web_app_url() + "/reset-password/'%s'" % token

    name = user.first_name or user.last_name or 'User'
    send_reset_password_email(email, name, reset_password_url, alphanumeric_token)

    return '', 204


@users_utilities_blueprint.route(UserServiceApi.RESET_PASSWORD, methods=['GET', 'POST'])
def reset_password(token):

    try:
        # Check if token is six characters long (For Mobile).  If so, it's actually the token key
        alphanumeric_token = ''
        token = token.strip("'")
        if len(token) == 6:
            alphanumeric_token = token
            token = redis_store.get(alphanumeric_token)

        email = URLSafeTimedSerializer(app.config["SECRET_KEY"]).loads(token, salt=PASSWORD_RECOVERY_JWT_SALT,
                                                                       max_age=PASSWORD_RECOVERY_JWT_MAX_AGE_SECONDS)

        user = User.query.filter_by(email=email).first()
        if user.reset_password_key != token:
            raise Exception()

    except SignatureExpired:
        raise ForbiddenError(error_message="Your encrypted token has been expired")
    except BadSignature:
        raise ForbiddenError(error_message="Your encrypted token is not valid")
    except Exception as e:
        raise InvalidUsage(error_message="Your encrypted token could not be decrypted")

    if request.method == 'GET':
        return '', 204
    else:
        posted_data = request.get_json()
        if not posted_data:
            raise InvalidUsage(error_message="No request data is found")

        password = posted_data.get('password', '')
        if not password:
            raise InvalidUsage(error_message="A valid password should be provided")

        # Remove key-value pair from redis-cache
        if alphanumeric_token:
            redis_store.delete(alphanumeric_token)

        user.reset_password_key = ''
        user.password = gettalent_generate_password_hash(password)
        user.password_reset_time = datetime.utcnow()
        user.is_disabled = 0
        db.session.commit()
        return '', 204


