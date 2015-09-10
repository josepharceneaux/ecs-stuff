__author__ = 'ufarooqi'

from oauth import app
from datetime import datetime, timedelta
from oauth.models import *
from werkzeug.security import check_password_hash
from oauth import db
from oauth import gt_oauth
from oauth import logger
from flask import request, jsonify


@gt_oauth.clientgetter
def load_client(client_id):
    return Client.query.filter_by(client_id=client_id).first()


# Format of PBKDF hashed passwords in web2py is different than that of flask
def change_hashing_format(password):
        if password is None:
            return ''
        elif password.count('$') == 2:
            (digest_alg, salt, hash) = password.split('$')
            return 'pbkdf2:sha512:1000$%s$%s' % (salt, hash)


gt_oauth.grantgetter(lambda *args, **kwargs: None)
gt_oauth.grantsetter(lambda *args, **kwargs: None)


@gt_oauth.usergetter
def get_user(username, password, *args, **kwargs):
    user = User.query.filter_by(email=username).first()
    if user:
        user_password = change_hashing_format(user.password)
        if check_password_hash(user_password, password):
            return user
    logger.warn('There is no user with username: %s and password: %s', username, password)
    return None


@gt_oauth.tokengetter
def load_token(access_token=None, refresh_token=None):
    if access_token:
        return Token.query.filter_by(access_token=access_token).first()
    elif refresh_token:
        return Token.query.filter_by(refresh_token=refresh_token).first()


@gt_oauth.tokensetter
def save_token(token, request, *args, **kwargs):
    tokens = Token.query.filter_by(
        client_id=request.client.client_id,
        user_id=request.user.id
    )
    # make sure that every client has only one token connected to a user
    for t in tokens:
        db.session.delete(t)

    expires_in = token.pop('expires_in')
    expires = datetime.utcnow() + timedelta(seconds=2*expires_in)  # 2 hours expiration time

    tok = Token(
        access_token=token['access_token'],
        refresh_token=token['refresh_token'],
        token_type=token['token_type'],
        _scopes=token['scope'],
        expires=expires,
        client_id=request.client.client_id,
        user_id=request.user.id,
    )
    db.session.add(tok)
    db.session.commit()
    logger.info('Bearer token has been created for user %s', request.user.id)
    return tok


@app.route('/oauth2/token', methods=['POST'])
@gt_oauth.token_handler
def access_token(*args, **kwargs):
    return None


@app.route('/oauth2/revoke', methods=['POST'])
@gt_oauth.revoke_handler
def revoke_token():
    pass


@app.route('/oauth2/authorize')
@gt_oauth.require_oauth()
def authorize():
    user = request.oauth.user
    logger.info('User %s has been authorized to access getTalent api', user.id)
    return jsonify(user_id=user.id)
