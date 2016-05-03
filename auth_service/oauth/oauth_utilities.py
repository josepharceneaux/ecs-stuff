__author__ = 'ufarooqi'
from werkzeug.security import check_password_hash
from auth_service.common.models.user import *
from auth_service.oauth import logger, app
from datetime import datetime, timedelta


# TODO Once our flask services would be up we'll migrate all existing passwords to flask PBKDF format
def change_hashing_format(password):
    """
    This method compensates for difference between formats of PBKDF hashed password in web2py and flask
    :param str password: password of a user
    :rtype: str
    """
    if password is None:
        return ''
    elif password.count('$') == 2:
        (digest_alg, salt, hash) = password.split('$')
        return 'pbkdf2:sha512:1000$%s$%s' % (salt, hash)


def authenticate_user(username, password):
    """
    It's user getter method i.e it'll retrieve a User object from database given valid username/password
    :param str username: username of a user
    :param str password:  password of a user
    :rtype: User
    """
    assert isinstance(username, basestring)
    assert isinstance(password, basestring)
    user = User.query.filter_by(email=username).first()
    if user and not user.is_disabled:
        user_password = change_hashing_format(user.password)
        if check_password_hash(user_password, password):
            return user
    logger.warn('There is no user with username: %s and password: %s', username, password)
    return None


def save_token(user):
    """
    This method will create a new bearer token from authenticated user
    :param User user: Authenticated user object
    :rtype: dict
    """
    assert isinstance(user, User)
    current_date_time = datetime.utcnow()
    expires = current_date_time + timedelta(seconds=app.config['JWT_OAUTH_EXPIRATION'])
    expires_at = expires.strftime("%d/%m/%Y %H:%M:%S")

    secret_key_id = str(uuid.uuid4())[0:10]
    secret_key = os.urandom(24)
    redis_store.setex(secret_key_id, secret_key, app.config['JWT_OAUTH_EXPIRATION'])
    s = Serializer(secret_key, expires_in=app.config['JWT_OAUTH_EXPIRATION'])

    payload = dict(
        user_id=user.id,
        expires_at=expires_at
    )
    return jsonify(dict(
        user_id=user.id,
        access_token=s.dumps(payload),
        expires_in=app.config['JWT_OAUTH_EXPIRATION'],
        expires_at=expires_at,
        token_type="Bearer",
        secret_key_id=secret_key_id
    ))


def verify_jw_token(secret_key_id, token):
    """
    This method will authenticate/verify a json web token
    :param secret_key_id: Redis key of SECRET_KEY
    :param token: JSON Web Token (JWT)
    :return:
    """
    s = Serializer(redis_store.get(secret_key_id) or '')
    try:
        data = s.loads(token)
    except SignatureExpired:
        raise UnauthorizedError(error_message="Your Token has been expired", error_code=12)
    except BadSignature:
        raise UnauthorizedError(error_message="Your Token is not found", error_code=11)
    except Exception:
        raise UnauthorizedError(error_message="Your Token is not found", error_code=11)

    if data['user_id']:
        user = User.query.get(data['user_id'])
        if user:
            return user

    raise UnauthorizedError(error_message="Your Token is invalid", error_code=13)
