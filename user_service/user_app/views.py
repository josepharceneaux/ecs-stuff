__author__ = 'ufarooqi'

from . import app
from user_service.common.models.user import Domain, DomainRole, Token, db
from flask import request
from user_service.common.error_handling import *
from user_service.common.utils.auth_utils import require_oauth, require_all_roles
from werkzeug.security import generate_password_hash, check_password_hash


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