__author__ = 'ufarooqi'
from user_service.common.tests.conftest import *
from user_service.common.redis_cache import redis_store
from common_functions import *


def test_update_password(access_token_first):

    # Logged-in user updating its password but providing empty values of old and new password
    assert update_password(access_token_first, '', '') == 404

    # Logged-in user updating its password but providing wrong value of old_password
    assert update_password(access_token_first, PASSWORD + 'temp', CHANGED_PASSWORD) == 401

    # Logged-in user updating its password
    assert update_password(access_token_first, PASSWORD, CHANGED_PASSWORD) == 200

    # Logged-in user changing its own password but as its password has changed before so all of its tokens have been
    # revoked. So 401 status code should be returned
    assert update_password(access_token_first, CHANGED_PASSWORD, PASSWORD) == 401


def test_forgot_password(user_first):

    # Someone trying to reset his password without an email address
    assert forgot_password(action='POST') == 400

    # Someone trying to reset his password with invalid email address
    assert forgot_password(user_first.email + 'temp', 'POST') == 404

    # Someone trying to reset his password with valid email address
    assert forgot_password(user_first.email, 'POST') == 204

    db.session.refresh(user_first)
    db.session.commit()

    token = user_first.reset_password_key

    # Verifying an invalid alphanumeric token
    assert reset_password(token + 'temp') == 403

    # Verifying a valid alphanumeric token
    assert reset_password(token) == 204

    # Someone trying to reset his password without providing new password
    assert reset_password(token, action='POST') == 400

    # Someone trying to reset his password using alphanumeric token
    assert reset_password(token, password='temp123', action='POST') == 204

    # Someone trying to reset his password again using same alphanumeric token
    assert reset_password(token, password='temp123', action='POST') == 403

    # Someone again trying to reset his password with valid email address
    assert forgot_password(user_first.email, 'POST') == 204

    db.session.refresh(user_first)
    db.session.commit()

    token = user_first.reset_password_key

    six_digit_token = ''
    for key in redis_store.keys('[0-9]' * 6):
        if redis_store.get(key) == token:
            six_digit_token = key
            break

    # Someone trying to reset his password using six_digit_token
    assert reset_password(six_digit_token, password='temp125', action='POST') == 204

    # Someone trying to reset his password again using same six_digit_token
    assert reset_password(six_digit_token, password='temp125', action='POST') == 403

    # Someone trying to reset his password again using alphanumeric token
    assert reset_password(token, password='temp125', action='POST') == 403
