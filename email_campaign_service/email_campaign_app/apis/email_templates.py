"""Email Templates API: Provides the endpoints to create, retrieve, update and delete
Email Templates. Also contains endpoints for creating and deleting Email Template Folders
"""
import requests

from flask import request
from flask import Blueprint

from email_campaign_service.common.models.db import db
from email_campaign_service.common.models.user import (User, DomainRole)
from email_campaign_service.common.utils.handy_functions import get_valid_json_data
from email_campaign_service.common.utils.auth_utils import (require_oauth, require_all_roles)
from email_campaign_service.common.models.misc import (UserEmailTemplate, EmailTemplateFolder)
from email_campaign_service.common.error_handling import (jsonify, InvalidUsage, ForbiddenError,
                                                          NotFoundError, ResourceNotFound,
                                                          UnauthorizedError)
# TODO --basit: rename `mod` to readable name
mod = Blueprint('email_template_service', __name__)
IMMUTABLE_TRUE = 1


@mod.route('/v1/email-templates', methods=['POST'])
@require_oauth()
def post_email_template():
    """

        POST /v1/email-templates
        Function will create an email template
        Required parameters:
        name:                     Name of email template
        email_body_html:          Body of email template
        email_template_folder_id: ID of email template folder
        is_immutable:             Parameter to determine is the email template is  mutable or not
    """
    user_id = request.user.id
    domain_id = request.user.domain_id

    data = get_valid_json_data(request)
    template_name = data.get('name')
    if not template_name:
        raise InvalidUsage(error_message="Template name is empty")
    # TODO --basit: rename field
    email_template_html_body = data.get("email_body_html")
    if not email_template_html_body:
        raise InvalidUsage(error_message="Email HTML body is empty")

    # Check if the name is already exists in the domain
    existing_template_name = UserEmailTemplate.get(template_name)
    if existing_template_name:
        raise InvalidUsage(error_message="Template name with name=%s already exists" % existing_template_name)
    # TODO --basit: rename field
    email_template_folder_id = data.get("email_template_folder_id")
    if email_template_folder_id and not (isinstance(email_template_folder_id, int) or
                                         email_template_folder_id.isdigit()):
        raise InvalidUsage(error_message="Invalid input")
    # TODO --basit: IMO get -> get_by_id will be more readable
    email_template_folder = EmailTemplateFolder.get(email_template_folder_id)

    # Check if the email template folder belongs to current domain
    if email_template_folder and email_template_folder.domain_id != domain_id:
        raise ForbiddenError(error_message="Email template's folder is not in the user's domain %d" %
                                           email_template_folder.domain_id)

    # If is_immutable value is not passed, make it as 0
    is_immutable = data.get("is_immutable")
    if not is_immutable:
        is_immutable = 0
    elif int(is_immutable) not in (0, 1):
            raise InvalidUsage(error_message="Invalid input: should be integer with value 0 or 1")

    if not require_all_roles(DomainRole.Roles.CAN_CREATE_EMAIL_TEMPLATE):
        raise UnauthorizedError(error_message="User is not authorized to create email template")
    user_email_template = UserEmailTemplate(user_id=user_id, type=0,
                                            name=template_name, body_html=email_template_html_body,
                                            body_text=data.get("email_body_text"),
                                            template_folder_id=email_template_folder_id if
                                            email_template_folder_id else None,
                                            is_immutable=is_immutable)
    # TODO --basit: as zohaib suggested
    db.session.add(user_email_template)
    db.session.commit()
    user_email_template_id = user_email_template.id
    return jsonify({'template_id': [{'id': user_email_template_id}]}), requests.codes.created


# TODO --basit: As discussed earlier, can these 2 be in one line?
@mod.route('/v1/email-templates/', methods=['GET'])
@mod.route('/v1/email-templates/<int:id>', methods=['GET'])
@require_oauth()
def get_email_template(**kwargs):
    """
        GET /v1/email-templates
        Function will return email template based on specified id
        Required parameters:
        id:     ID of of email template
    """
    email_template_id = kwargs.get("id")

    # Validate email template id
    validate_id(email_template_id)
    if isinstance(email_template_id, basestring):
        email_template_id = int(email_template_id)
    domain_id = request.user.domain_id
    # TODO --basit: get_by_id
    template = UserEmailTemplate.get(email_template_id)
    if not template:
        raise ResourceNotFound(error_message="Template with id %d not found" % email_template_id)

    # Verify owned by same domain
    template_owner_user = User.get(template.user_id)
    if template_owner_user.domain_id != domain_id:
        raise ForbiddenError(error_message="Template(id:%d) is not owned by"
                                           "domain(id:%d)" % (email_template_id, domain_id))

    # Verify is_immutable
    if template.is_immutable == IMMUTABLE_TRUE and not require_all_roles(DomainRole.Roles.CAN_GET_EMAIL_TEMPLATE):
        raise ForbiddenError(error_message="User %d not allowed to update the template" % template_owner_user.id)

    return jsonify({'email_template': {'email_body_html': template.body_html, 'id': email_template_id}})


@mod.route('/v1/email-templates/<int:id>', methods=['PUT'])
@require_oauth()
def update_email_template(**kwargs):
    """
        PUT /v1/email-templates
        Function would update existing email template
        Required parameters:
        id:     ID of email template
    """
    email_template_id = kwargs.get("id")
    validate_id(email_template_id)

    data = get_valid_json_data(request)

    domain_id = request.user.domain_id
    user_id = request.user.id

    template = UserEmailTemplate.get(email_template_id)
    if not template:
        raise ResourceNotFound(error_message="Template with id %d not found for user (id:%d)" % (email_template_id,
                                                                                                 user_id))

    # Verify is_immutable
    if template.is_immutable == IMMUTABLE_TRUE and not require_all_roles(DomainRole.Roles.CAN_UPDATE_EMAIL_TEMPLATE):
        raise ForbiddenError(error_message="User %d not allowed to update the template (id:%d)" % (user_id,
                                                                                                   email_template_id))
    # TODO --basit: rename fields
    email_body_html = data.get("email_body_html") or template.body_html
    email_body_text = data.get("email_body_text") or template.body_text

    # Verify owned by same domain
    # TODO --basit: get_by_id
    template_owner_user = User.get(template.user_id)
    updated_data = {"body_html": email_body_html, "body_text": email_body_text}
    if template_owner_user.domain_id == domain_id:
        # Update email template
        template.update(**updated_data)
    else:
        raise ForbiddenError(error_message="Template(id:%d) is not owned by user(id:%d) &"
                                           "domain(id:%d)" % (email_template_id, user_id, domain_id))

    return jsonify({'email_template': {'email_body_html': email_body_html, 'id': email_template_id}})


@mod.route('/v1/email-templates/<int:id>', methods=['DELETE'])
@require_oauth()
def delete_email_template(**kwargs):
    """
        DELETE /v1/email-templates
        Function will delete email template
        Required parameters:
        id:     ID of email template
    """
    email_template_id = kwargs.get("id")

    # Validate email template id
    validate_id(email_template_id)
    if isinstance(email_template_id, basestring):
        email_template_id = int(email_template_id)

    user_id = request.user.id
    domain_id = request.user.domain_id

    template = UserEmailTemplate.get(email_template_id)
    if not template:
        # TODO --basit: add id of template as well in message
        raise NotFoundError(error_message="Template not found")

    # Verify owned by same domain
    template_owner_user = User.get(template.user_id)

    if template_owner_user.domain_id != domain_id:
        # TODO --basit: Update message as was discussed
        raise ForbiddenError(error_message="Template is not owned by same domain")

    if template.is_immutable == IMMUTABLE_TRUE and not require_all_roles(DomainRole.Roles.CAN_DELETE_EMAIL_TEMPLATE):
        # TODO --basit: Update message as was discussed
        raise ForbiddenError(error_message="User %d not allowed to delete the template" % user_id)
    # TODO --basit: as Zohaib suggested
    # Delete the template
    db.session.delete(template)
    db.session.commit()
    return '', requests.codes.no_content


@require_all_roles(DomainRole.Roles.CAN_CREATE_EMAIL_TEMPLATE_FOLDER)
@mod.route('/v1/email-template-folders', methods=['POST'])
@require_oauth()
def create_email_template_folder():
    """
        POST /v1/email-template-folders
        Create email template folder
        Required parameters:
        name:          Name of email template folder
        parent_id:     Parent ID of email template folder
        is_immutable:  Parameter to determine is the email template folder is mutable or not
        :return:       Template folder id
    """

    data = get_valid_json_data(request)
    folder_name = data.get('name')
    if not folder_name:
        raise InvalidUsage(error_message="Folder name must be provided.")
    if not isinstance(folder_name, basestring):
        # TODO --basit: Message should be more meaningful
        raise InvalidUsage(error_message="Invalid input")
    domain_id = request.user.domain_id

    # Check if the name is already exists under same domain
    existing_row = EmailTemplateFolder.get_by_name_and_domain_id(folder_name, domain_id)

    if existing_row:
        raise InvalidUsage(error_message="Template folder with name=%s already exists" % folder_name)

    parent_id = data.get('parent_id')
    if parent_id and not parent_id.isdigit():
        raise InvalidUsage(error_message="Invalid input: parent_id must be a valid digit")
    if parent_id and domain_id:
        template_folder_parent = EmailTemplateFolder.get(parent_id)
        if not template_folder_parent:
            raise ForbiddenError(error_message="Email Template Folder with (id:%d) does not exist" % parent_id)
        elif not template_folder_parent.domain_id == domain_id:
            raise ForbiddenError(error_message="Email Template Folder with (id:%d) does not belong to domain (id:%d)"
                                               % (parent_id, domain_id))

    # If is_immutable value is not passed, make it as 0
    is_immutable = data.get("is_immutable")
    if not is_immutable:
        is_immutable = 0
    elif int(is_immutable) not in (0, 1):
            raise InvalidUsage(error_message="Invalid input: should be integer with value 0 or 1")

    email_template_folder = EmailTemplateFolder(name=folder_name, domain_id=domain_id, parent_id=parent_id,
                                                is_immutable=is_immutable)
    db.session.add(email_template_folder)
    db.session.commit()
    email_template_folder_id = email_template_folder.id

    return jsonify({"template_folder_id": [{"id": email_template_folder_id}]}), requests.codes.created


@require_all_roles(DomainRole.Roles.CAN_DELETE_EMAIL_TEMPLATE_FOLDER)
@mod.route('/v1/email-template-folders/<int:id>', methods=['DELETE'])
@require_oauth()
def delete_email_template_folder(**kwargs):
    """
        DELETE /email-template-folders
        Required parameters:
        id:     ID of email template
    """
    domain_id = request.user.domain_id

    folder_id = kwargs.get('id')
    validate_id(folder_id)

    template_folder = EmailTemplateFolder.get(folder_id)

    if not template_folder:
        raise NotFoundError(error_message='Template folder not found')
    # Verify owned by same domain
    if not template_folder.domain_id == domain_id:
        raise ForbiddenError(error_message="Template folder is not owned by same domain")
    else:
        EmailTemplateFolder.delete(template_folder)

    return '', requests.codes.no_content


# TODO --basit: Move these to validations.py
def validate_id(id):
    """
    Function will validate email template ID
    """
    if not id:
        raise InvalidUsage(error_message="ID must be provided")

    if id <= 0:
        raise InvalidUsage(error_message="ID must be greater than 0")


# TODO --basit: Is it being used?
def check_domain_role():
    pass
