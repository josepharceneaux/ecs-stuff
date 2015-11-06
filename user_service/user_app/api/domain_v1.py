__author__ = 'ufarooqi'
from flask_restful import Resource
from flask import request
from dateutil import parser
from common.models.user import User, Domain, db
from common.models.misc import Culture
from user_service.user_app.user_service_utilties import get_or_create_domain
from user_service.common.utils.auth_utils import require_oauth, require_any_role, require_all_roles
from common.error_handling import *


class DomainApi(Resource):

    # Access token and role authentication decorators
    decorators = [require_oauth]

    @require_any_role()
    def get(self, **kwargs):
        """
        GET /domains/<id> Fetch domain object with domain's basic info
        :return A dictionary containing domain info except safety critical info
        :rtype: dict
        """

        requested_domain_id = kwargs.get('id')
        if not requested_domain_id:
            raise InvalidUsage(error_message="Domain id is not provided")

        requested_domain = Domain.query.get(requested_domain_id)
        if not requested_domain:
            raise NotFoundError(error_message="Domain with domain id %s not found" % requested_domain_id)

        # Either Logged in user should be ADMIN or should belong to same domain as requested_domain
        if requested_domain_id == request.user.domain_id or request.is_admin_user:
            return {
                    'domain': {
                        'id': requested_domain.id,
                        'name': requested_domain.name,
                        'organization_id': requested_domain.organization_id,
                        'dice_company_id': requested_domain.dice_company_id
                        }
                    }
        else:
            raise UnauthorizedError(error_message="Either logged-in user belongs to different domain as requested_user "
                                                  "or it's not an ADMIN user")

    @require_all_roles('ADMIN')
    def post(self):
        """
        POST /domains  Create a new Domain
        input: {'domains': [domain1, domain2, domain3, ... ]}

        Take a JSON dictionary containing array of Domain dictionaries
        A single domain dict must contain at least domain's name.
        Logged in user must be an ADMIN or DOMAIN_ADMIN.

        :return:  A dictionary containing array of user ids
        :rtype: dict
        """

        posted_data = request.get_json(silent=True)
        if not posted_data or 'domains' not in posted_data:
            raise InvalidUsage(error_message="Request body is empty or not provided")

        # Save domain object(s)
        domains = posted_data['domains']

        # Domain object(s) must be in a list
        if not isinstance(domains, list):
            raise InvalidUsage(error_message="Request body is not properly formatted")

        for domain_dict in domains:

            name = domain_dict.get('name', '')
            default_culture_id = domain_dict.get('default_culture_id', '')
            expiration = domain_dict.get('expiration', '')

            if not name:
                raise InvalidUsage(error_message="Domain name should be provided")

            # If domain already exists then raise an exception
            if Domain.query.filter_by(name=name).first():
                raise InvalidUsage(error_message="Domain %s already exist" % name)

            # If Culture doesn't exist in database
            if default_culture_id and not Culture.query.get(default_culture_id):
                raise InvalidUsage(error_message="Culture %s doesn't exist" % default_culture_id)

            if expiration:
                try:
                    parser.parse(expiration)
                except Exception as e:
                    raise InvalidUsage(error_message="Expiration Time is not valid as: %s" % e.message)

        domain_ids = []  # Newly created user object's id(s) are appended to this list
        for domain_dict in domains:

            name = domain_dict.get('name', '')
            expiration = domain_dict.get('expiration', '')
            default_culture_id = domain_dict.get('default_culture_id', 1)
            default_tracking_code = domain_dict.get('default_tracking_code', None)
            dice_company_id = domain_dict.get('dice_company_id', None)
            expiration = parser.parse(expiration) if expiration else ""

            domain_id = get_or_create_domain(name=name, expiration=expiration, default_culture_id=default_culture_id,
                                             default_tracking_code=default_tracking_code, dice_company_id=dice_company_id)

            domain_ids.append(domain_id)

        return {'domains': domain_ids}

    @require_all_roles('ADMIN')
    def delete(self, **kwargs):
        """
        DELETE /domains/<id>

        Function will disable domain-object in db
        Only ADMIN users can disable a domain

        :return: {'deleted_domain' {'id': domain_id}}
        :rtype:  dict
        """

        domain_id_to_delete = kwargs.get('id')
        if not domain_id_to_delete:
            raise InvalidUsage(error_message="Domain id is not provided")

        # Return 404 if requested user does not exist
        domain_to_delete = Domain.query.get(domain_id_to_delete)
        if not domain_to_delete:
            raise NotFoundError(error_message="Requested domain with domain_id %s doesn't exist" % domain_id_to_delete)

        # Disable the domain by setting is_disabled field to 1
        Domain.query.filter(Domain.id == domain_id_to_delete).update({'is_disabled': '1'})

        # Disable all users of this domain as Domain has been disabled
        User.query.filter(User.domain_id == domain_id_to_delete).update({'is_disabled': '1'})
        db.session.commit()

        return {'deleted_domain': {'id': domain_id_to_delete}}

    @require_any_role('ADMIN', 'DOMAIN_ADMIN')
    def put(self, **kwargs):
        """
        PUT /domains/<id>

        Function will change credentials of one domain per request.
        Only ADMIN or DOMAIN_ADMIN user can modify a domain

        :return: {'updated_domain' {'id': domain_id}}
        :rtype:  dict
        """

        requested_domain_id = kwargs.get('id')
        requested_domain = Domain.query.get(requested_domain_id) if requested_domain_id else None
        if not requested_domain:
            raise NotFoundError(error_message="Either domain_id is not provided or domain doesn't exist")

        posted_data = request.get_json(silent=True)
        if not posted_data:
            raise InvalidUsage(error_message="Request body is empty or not provided")

        # Logged-in user should be either DOMAIN_ADMIN, ADMIN to modify a domain
        if not request.is_admin_user and requested_domain_id != request.user.domain_id:
            raise UnauthorizedError(error_message="Logged-in user should be either ADMIN or DOMAIN_ADMIN if it belongs "
                                                  "to same domain as requested domain")

        name = posted_data.get('name', '')
        expiration = posted_data.get('expiration', '')
        default_culture_id = posted_data.get('default_culture_id', '')
        default_tracking_code = posted_data.get('default_tracking_code', '')
        dice_company_id = posted_data.get('dice_company_Id', '')

        if expiration:
            try:
                expiration = parser.parse(expiration)
            except Exception as e:
                raise InvalidUsage(error_message="Expiration Time is not valid as: %s" % e.message)

        # If Culture doesn't exist in database
        if default_culture_id and not Culture.query.get(default_culture_id):
            raise InvalidUsage(error_message="Culture %s doesn't exist" % default_culture_id)

        # Update user
        update_domain_dict = {
            'name': name,
            'expiration': expiration,
            'default_culture_id': default_culture_id,
            'default_tracking_code': default_tracking_code,
            'dice_company_id': dice_company_id
        }
        update_domain_dict = dict((k, v) for k, v in update_domain_dict.iteritems() if v)
        Domain.query.filter(Domain.id == requested_domain_id).update(update_domain_dict)
        db.session.commit()

        return {'updated_domain': {'id': requested_domain_id}}
