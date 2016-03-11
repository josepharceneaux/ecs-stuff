"""Email Templates API: Provides the endpoints to create, retrieve, update and delete
Email Templates. Also contains endpoints for creating and deleting Email Template Folders
"""
import requests

from flask import request
from flask import Blueprint

from email_campaign_service.common.models.user import (User, DomainRole)
from email_campaign_service.common.utils.handy_functions import get_valid_json_data
from email_campaign_service.common.utils.validators import validate_immutable_value
from email_campaign_service.common.utils.auth_utils import (require_oauth, require_all_roles)
from email_campaign_service.common.models.email_campaign import (UserEmailTemplate, EmailTemplateFolder)
from email_campaign_service.common.error_handling import (jsonify, InvalidUsage, ForbiddenError, NotFoundError,
                                                          ResourceNotFound, UnauthorizedError)

email_template_blueprint = Blueprint('email_template_service', __name__)
IMMUTABLE_TRUE = 1


@email_template_blueprint.route('/v1/email-templates', methods=['POST'])
@require_oauth()
def post_email_template():
    """

        POST /v1/email-templates
        Function will create an email template
        Required parameters:
        name:                     Name of email template
        body_html:                Body of email template
        email_template_folder_id: ID of email template folder
        is_immutable:             Parameter to determine is the email template is  mutable or not
    """
    user_id = request.user.id
    domain_id = request.user.domain_id

    data = get_valid_json_data(request)
    template_name = data.get('name')
    if not template_name:
        raise InvalidUsage(error_message="Template name is empty")

    email_template_html_body = data.get("body_html")
    if not email_template_html_body:
        raise InvalidUsage(error_message="Email HTML body is empty")

    # Check if the name is already exists in the domain
    existing_template_name = UserEmailTemplate.get(template_name)
    if existing_template_name:
        raise InvalidUsage(error_message="Template name with name=%s already exists" % existing_template_name)

    email_template_folder_id = data.get("email_template_folder_id")
    if email_template_folder_id and not (isinstance(email_template_folder_id, int) or
                                         email_template_folder_id.isdigit()):
        raise InvalidUsage(error_message="Invalid input: folder_id must be positive integer")

    email_template_folder = EmailTemplateFolder.get_by_id(email_template_folder_id)

    # Check if the email template folder belongs to current domain
    if email_template_folder and email_template_folder.domain_id != domain_id:
        raise ForbiddenError(error_message="Email template's folder is not in the user's domain %d" %
                                           email_template_folder.domain_id)

    # If is_immutable value is not passed, make it as 0
    is_immutable = data.get("is_immutable", 0)
    validate_immutable_value(is_immutable)

    if not require_all_roles(DomainRole.Roles.CAN_CREATE_EMAIL_TEMPLATE):
        raise UnauthorizedError(error_message="User is not authorized to create email template")
    user_email_template = UserEmailTemplate(user_id=user_id, type=0,
                                            name=template_name, body_html=email_template_html_body,
                                            body_text=data.get("email_body_text"),
                                            template_folder_id=email_template_folder_id if
                                            email_template_folder_id else None,
                                            is_immutable=is_immutable)
    UserEmailTemplate.save(user_email_template)

    user_email_template_id = user_email_template.id
    return jsonify({'template_id': [{'id': user_email_template_id}]}), requests.codes.created


@email_template_blueprint.route('/v1/email-templates/', methods=['GET'])
@email_template_blueprint.route('/v1/email-templates/<int:template_id>', methods=['GET'])
@require_oauth()
def get_email_template(template_id):
    """
        GET /v1/email-templates
        Function will return email template based on specified id
        Required parameters:
        :param template_id: ID of of email template
    """

    # Validate email template id
    if template_id == 0:
        raise InvalidUsage(error_message="ID must be greater than 0")
    if isinstance(template_id, basestring):
        template_id = int(template_id)
    domain_id = request.user.domain_id
    template = UserEmailTemplate.get_by_id(template_id)
    if not template:
        raise ResourceNotFound(error_message="Template with id %d not found" % template_id)

    # Verify owned by same domain
    template_owner_user = User.get_by_id(template.user_id)
    if template_owner_user.domain_id != domain_id:
        raise ForbiddenError(error_message="Template(id:%d) is not owned by"
                                           "domain(id:%d)" % (template_id, domain_id))

    # Verify is_immutable
    if template.is_immutable == IMMUTABLE_TRUE and not require_all_roles(DomainRole.Roles.CAN_GET_EMAIL_TEMPLATE):
        raise ForbiddenError(error_message="User %d not allowed to update the template" % template_owner_user.id)

    return jsonify({'email_template': {'body_html': template.body_html, 'id': template_id}})


@email_template_blueprint.route('/v1/email-templates/<int:template_id>', methods=['PUT'])
@require_oauth()
def update_email_template(template_id):
    """
        PUT /v1/email-templates
        Function would update existing email template
        Required parameters:
        :param template_id: ID of of email template
    """
    if template_id == 0:
        raise InvalidUsage(error_message="ID must be greater than 0")

    data = get_valid_json_data(request)

    domain_id = request.user.domain_id
    user_id = request.user.id

    template = UserEmailTemplate.get(template_id)
    if not template:
        raise ResourceNotFound(error_message="Template with id %d not found for user (id:%d)" % (template_id,
                                                                                                 user_id))

    # Verify is_immutable
    if template.is_immutable == IMMUTABLE_TRUE and not require_all_roles(DomainRole.Roles.CAN_UPDATE_EMAIL_TEMPLATE):
        raise ForbiddenError(error_message="User %d not allowed to update the template (id:%d)" % (user_id,
                                                                                                   template_id))

    body_html = data.get("body_html") or template.body_html
    email_body_text = data.get("email_body_text") or template.body_text

    # Verify owned by same domain
    template_owner_user = User.get_by_id(template.user_id)
    updated_data = {"body_html": body_html, "body_text": email_body_text}
    if template_owner_user.domain_id == domain_id:
        # Update email template
        template.update(**updated_data)
    else:
        raise ForbiddenError(error_message="Template(id:%d) is not owned by user(id:%d) &"
                                           "domain(id:%d)" % (template_id, user_id, domain_id))

    return jsonify({'email_template': {'body_html': body_html, 'id': template_id}})


@email_template_blueprint.route('/v1/email-templates/<int:template_id>', methods=['DELETE'])
@require_oauth()
def delete_email_template(template_id):
    """
        DELETE /v1/email-templates
        Function will delete email template
        Required parameters:
        :param template_id: ID of of email template
    """

    # Validate email template id
    if template_id == 0:
        raise InvalidUsage(error_message="ID must be greater than 0")
    if isinstance(template_id, basestring):
        template_id = int(template_id)

    user_id = request.user.id
    domain_id = request.user.domain_id

    template = UserEmailTemplate.get(template_id)
    if not template:
        raise NotFoundError(error_message="Template (id:%d) not found" % template_id)

    # Verify owned by same domain
    template_owner_user = User.get(template.user_id)

    if template_owner_user.domain_id != domain_id:
        raise ForbiddenError(error_message="Template (id:%d) is not owned by same domain (id:%d)" % (template_id,
                                                                                                     domain_id))

    if template.is_immutable == IMMUTABLE_TRUE and not require_all_roles(DomainRole.Roles.CAN_DELETE_EMAIL_TEMPLATE):
        raise ForbiddenError(error_message="User (id:%d) not allowed to delete the template (id:%d)" % (user_id,
                                                                                                        template.id))
    # Delete the template
    UserEmailTemplate.delete(template)
    return '', requests.codes.no_content


@require_all_roles(DomainRole.Roles.CAN_CREATE_EMAIL_TEMPLATE_FOLDER)
@email_template_blueprint.route('/v1/email-template-folders', methods=['POST'])
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
        raise InvalidUsage(error_message="Invalid input: Folder name must be a valid string.")
    domain_id = request.user.domain_id

    # Check if the name already exists under same domain
    duplicate = EmailTemplateFolder.get_by_name_and_domain_id(folder_name, domain_id)

    if duplicate:
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
    is_immutable = data.get("is_immutable", 0)
    validate_immutable_value(is_immutable)

    email_template_folder = EmailTemplateFolder(name=folder_name, domain_id=domain_id, parent_id=parent_id,
                                                is_immutable=is_immutable)
    EmailTemplateFolder.save(email_template_folder)
    email_template_folder_id = email_template_folder.id

    return jsonify({"template_folder_id": [{"id": email_template_folder_id}]}), requests.codes.created


@require_all_roles(DomainRole.Roles.CAN_DELETE_EMAIL_TEMPLATE_FOLDER)
@email_template_blueprint.route('/v1/email-template-folders/<int:folder_id>', methods=['DELETE'])
@require_oauth()
def delete_email_template_folder(folder_id):
    """
        DELETE /v1/email-template-folders
        Required parameters:
        :param folder_id: ID of of email template
    """
    domain_id = request.user.domain_id
    if folder_id == 0:
        raise InvalidUsage(error_message="ID must be greater than 0")

    template_folder = EmailTemplateFolder.get(folder_id)

    if not template_folder:
        raise NotFoundError(error_message='Template folder not found')
    # Verify owned by same domain
    if not template_folder.domain_id == domain_id:
        raise ForbiddenError(error_message="Template folder is not owned by same domain")
    else:
        EmailTemplateFolder.delete(template_folder)

    return '', requests.codes.no_content
