
__author__ = 'ufarooqi'
from dateutil import parser
from flask_restful import Resource
from flask import request, Blueprint
from user_service.common.error_handling import *
from user_service.common.models.misc import Culture
from user_service.common.talent_api import TalentApi
from user_service.common.routes import UserServiceApi
from user_service.common.models.user import User, Domain, db, Permission
from user_service.user_app.user_service_utilties import get_or_create_domain
from user_service.common.utils.auth_utils import require_oauth, require_all_permissions, is_number


class DomainApi(Resource):

    # Access token and role authentication decorators
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_DOMAINS)
    def get(self, **kwargs):
        """
        GET /domains/<id> Fetch domain object with domain's basic info
        GET /domains Fetch all domain objects with domain's basic info
        :return A dictionary containing domain info except safety critical info
        :rtype: dict
        """

        requested_domain_id = kwargs.get('id')
        if requested_domain_id:
            requested_domain = Domain.query.get(requested_domain_id)
            if not requested_domain:
                raise NotFoundError("Domain with domain id %s not found" % requested_domain_id)

            if requested_domain_id == request.user.domain_id or request.user.role.name == 'TALENT_ADMIN':
                return {
                    'domain': requested_domain.to_dict()
                }
        elif request.user.role.name == 'TALENT_ADMIN':

            is_disabled = request.args.get('is_disabled', 0)
            if not is_number(is_disabled) or int(is_disabled) not in (0, 1):
                raise InvalidUsage('`is_hidden` can be either 0 or 1')

            domains = Domain.query.filter(Domain.is_disabled == is_disabled).all()

            return {
                'domains': [domain.to_dict() for domain in domains]
            }

        raise UnauthorizedError("Either logged-in user belongs to different domain as requested_domain or it doesn't "
                                "have appropriate permissions")

    @require_all_permissions(Permission.PermissionNames.CAN_ADD_DOMAINS)
    def post(self):
        """
        POST /domains  Create a new Domain
        input: {'domains': [domain1, domain2, domain3, ... ]}

        Take a JSON dictionary containing array of Domain dictionaries
        A single domain dict must contain at least domain's name

        :return:  A dictionary containing array of user ids
        :rtype: dict
        """

        posted_data = request.get_json(silent=True)
        if not posted_data or 'domains' not in posted_data:
            raise InvalidUsage("Request body is empty or not provided")

        # Save domain object(s)
        domains = posted_data['domains']

        # Domain object(s) must be in a list
        if not isinstance(domains, list):
            raise InvalidUsage("Request body is not properly formatted")

        for index, domain_dict in enumerate(domains):

            name = domain_dict.get('name', '')
            default_culture_id = domain_dict.get('default_culture_id', '')
            expiration = domain_dict.get('expiration', '')

            if not name:
                raise InvalidUsage("Domain name should be provided")

            domain = Domain.query.filter_by(name=name).first()

            # If domain already exists then raise an exception
            if domain:
                if not domain.is_disabled:
                    raise InvalidUsage("Domain %s already exist" % name)
                else:
                    domain.is_disabled = 0
                    db.session.commit()
                    domains.pop(index)
                    continue

            # If Culture doesn't exist in database
            if default_culture_id and not Culture.query.get(default_culture_id):
                raise InvalidUsage("Culture %s doesn't exist" % default_culture_id)

            if expiration:
                try:
                    parser.parse(expiration)
                except Exception as e:
                    raise InvalidUsage("Expiration Time is not valid as: %s" % e.message)

        domain_ids = []  # Newly created user object's id(s) are appended to this list
        for domain_dict in domains:

            name = domain_dict.get('name', '')
            expiration = domain_dict.get('expiration', '')
            default_culture_id = domain_dict.get('default_culture_id', 1)
            default_tracking_code = domain_dict.get('default_tracking_code', None)
            dice_company_id = domain_dict.get('dice_company_id', None)
            expiration = parser.parse(expiration) if expiration else ""

            domain_id = get_or_create_domain(logged_in_user_id=request.user.id, name=name, expiration=expiration,
                                             default_culture_id=default_culture_id, default_tracking_code=
                                             default_tracking_code, dice_company_id=dice_company_id)

            domain_ids.append(domain_id)

        return {'domains': domain_ids}

    @require_all_permissions(Permission.PermissionNames.CAN_DELETE_DOMAINS)
    def delete(self, **kwargs):
        """
        DELETE /domains/<id>

        Function will disable domain-object in db

        :return: {'deleted_domain' {'id': domain_id}}
        :rtype:  dict
        """

        domain_id_to_delete = kwargs.get('id')
        if not domain_id_to_delete:
            raise InvalidUsage("Domain id is not provided")

        # Return 404 if requested user does not exist
        domain_to_delete = Domain.query.get(domain_id_to_delete)
        if not domain_to_delete:
            raise NotFoundError("Requested domain with domain_id %s doesn't exist" % domain_id_to_delete)

        # Disable the domain by setting is_disabled field to 1
        Domain.query.filter(Domain.id == domain_id_to_delete).update({'is_disabled': 1})

        # Disable all users of this domain as Domain has been disabled
        User.query.filter(User.domain_id == domain_id_to_delete).update({'is_disabled': 1})
        db.session.commit()

        return {'deleted_domain': {'id': domain_id_to_delete}}

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_DOMAINS)
    def put(self, **kwargs):
        """
        PUT /domains/<id>

        Function will change credentials of one domain per request.

        :return: {'updated_domain' {'id': domain_id}}
        :rtype:  dict
        """

        requested_domain_id = kwargs.get('id')
        requested_domain = Domain.query.get(requested_domain_id) if requested_domain_id else None
        if not requested_domain:
            raise NotFoundError("Either domain_id is not provided or domain doesn't exist")

        posted_data = request.get_json(silent=True)
        if not posted_data:
            raise InvalidUsage("Request body is empty or not provided")

        if request.user.role.name != 'TALENT_ADMIN' and requested_domain_id != request.user.domain_id:
            raise UnauthorizedError("Logged-in user doesn't have appropriate permissions for this operation")

        name = posted_data.get('name', '')
        expiration = posted_data.get('expiration', '')
        default_culture_id = posted_data.get('default_culture_id', '')
        default_tracking_code = posted_data.get('default_tracking_code', '')
        dice_company_id = posted_data.get('dice_company_Id', '')
        is_disabled = posted_data.get('is_disabled', 0)

        if expiration:
            try:
                expiration = parser.parse(expiration)
            except Exception as e:
                raise InvalidUsage("Expiration Time is not valid as: %s" % e.message)

        if name and Domain.query.filter_by(name=name).first():
            raise InvalidUsage('Domain %s already exists in database' % name)

        # If Culture doesn't exist in database
        if default_culture_id and not Culture.query.get(default_culture_id):
            raise InvalidUsage("Culture %s doesn't exist" % default_culture_id)

        is_disabled = request.args.get('is_disabled', 0)
        if not is_number(is_disabled) or int(is_disabled) not in (0, 1):
            raise InvalidUsage('`is_disabled` can be either 0 or 1')

        # Update user
        update_domain_dict = {
            'name': name,
            'expiration': expiration,
            'default_culture_id': default_culture_id,
            'default_tracking_code': default_tracking_code,
            'dice_company_id': dice_company_id,
            'is_disabled': is_disabled,
        }
        update_domain_dict = dict((k, v) for k, v in update_domain_dict.iteritems() if v)
        Domain.query.filter(Domain.id == requested_domain_id).update(update_domain_dict)
        db.session.commit()

        return {'updated_domain': {'id': requested_domain_id}}

domain_blueprint = Blueprint('domain_api', __name__)
api = TalentApi(domain_blueprint)
api.add_resource(DomainApi, UserServiceApi.DOMAINS, UserServiceApi.DOMAIN)