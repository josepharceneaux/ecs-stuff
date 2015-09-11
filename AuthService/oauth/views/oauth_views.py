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

    expires_in = token.get('expires_in')
    expires = datetime.utcnow() + timedelta(seconds=expires_in)
    token['expires_at'] = expires.strftime("%d/%m/%Y %H:%M:%S")
    token['user_id'] = request.user.id

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


@app.route('/roles/verify')
def verify_roles():
    user_id = request.args.get('user_id')
    role_name = request.args.get('role')
    if role_name and user_id:
        domain_role = DomainRole.get_by_name(role_name)
        user = User.query.get(user_id)
        if domain_role and user:
            role_id = domain_role.id
            all_roles_of_user = UserScopedRoles.get_all_roles_of_user(user.id)['roles']
            # User is not an admin(role_id = 1) nor it contains input role
            if DomainRole.all() == all_roles_of_user or role_id in all_roles_of_user:
                return jsonify(success=True)
    return jsonify(success=False)


@app.route('/users/<int:user_id>/roles', methods=['POST', 'GET', 'DELETE'])
@gt_oauth.require_oauth()
def user_scoped_roles(user_id):
    if request.method == 'GET':
        return UserScopedRoles.get_all_roles_of_user(user_id)
    else:
        posted_data = request.get_json(silent=True)
        if posted_data:
            try:
                if request.method == 'POST':
                    UserScopedRoles.add_role(user_id, posted_data.get('roles'))
                else:
                    UserScopedRoles.delete_roles(user_id, posted_data.get('roles'))
            except Exception as e:
                return jsonify(error_message=e.message), 404
        else:
            return jsonify(error_message='Request data is corrupt'), 400
