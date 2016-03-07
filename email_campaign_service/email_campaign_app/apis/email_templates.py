import types

from flask import Blueprint
from email_campaign_service.common.utils.auth_utils import require_oauth, require_all_roles
from email_campaign_service.common.models.db import db
from email_campaign_service.common.talent_api import TalentApi
from email_campaign_service.common.utils.api_utils import api_route
from email_campaign_service.common.models.misc import UserEmailTemplate, EmailTemplateFolder
from email_campaign_service.common.models.user import User, UserScopedRoles, DomainRole
from flask import request
from email_campaign_service.common.error_handling import *
import json

mod = Blueprint('email_template_service', __name__)



@mod.route('/v1/email-templates', methods=['POST'])
@require_oauth()
def post_email_template():
    """
    This function creates a new email_template
    input: {'name': "template_name", "email_body_html": "html_body"}
    :return:  A dictionary containing array of template id
    :rtype: dict
    """
    user_id = request.user.id
    # Check roles assigned to user
    # role_id = UserScopedRoles.query.filter_by(user_id=user_id)
    # # Check the user has role to create template
    # role = DomainRole.query.get(role_id)
    # domain_role_name = role.role_name
    # assert domain_role_name == "CAN_CREATE_EMAIL_TEMPLATE"
    data = json.loads(request.data)

    domain_id = request.user.domain_id
    template_name = data.get('name')
    if not template_name:
        raise InvalidUsage(error_message="Template name is empty")

    email_template_html_body = data.get("email_body_html")

    if not email_template_html_body:
        raise InvalidUsage(error_message="Email HTML body is empty")

    # Check if the name is already exists in the domain
    existing_template_name = UserEmailTemplate.query.get(template_name)
    if existing_template_name:
        raise InvalidUsage(error_message="Template name with name=%s already exists" % existing_template_name)

    email_template_folder_id = data.get("email_template_folder_id")
    if email_template_folder_id and not (isinstance(email_template_folder_id, int)
                                         or email_template_folder_id.isdigit()):
        raise InvalidUsage(error_message="Invalid input")

    email_template_folder = EmailTemplateFolder.query.get(email_template_folder_id)

    # Check if the email template folder belongs to current domain
    if email_template_folder and email_template_folder.domain_id != domain_id:
        raise ForbiddenError(error_message="Email template's folder is not in the user's domain %d" %
                                           email_template_folder.domain_id)

    # If is_immutable value is not passed, make it as 0
    is_immutable = data.get("is_immutable")
    if is_immutable and not is_immutable.isdigit():
        raise InvalidUsage(error_message="Invalid input")
    if not is_immutable:
        is_immutable = 0

    if not require_all_roles('CAN_CREATE_EMAIL_TEMPLATE'):
        raise UnauthorizedError(error_message="User is not authorized to create email template")
    user_email_template = UserEmailTemplate(user_id=user_id, type=0,
                                            name=template_name, email_body_html=email_template_html_body,
                                            email_body_text=data.get("email_body_text"),
                                            email_template_folder_id=email_template_folder_id if
                                            email_template_folder_id else None,
                                            is_immutable=is_immutable)
    db.session.add(user_email_template)
    db.session.commit()
    user_email_template_id = user_email_template.id
    return jsonify({'template_id': [{'id': user_email_template_id}]}), 201


@mod.route('/v1/email-templates', methods=['DELETE'])
@require_oauth()
def delete_email_template():
    """
    Function will delete email template from db
    input: {'id': "template_id"}
    :return: success=1 or 0
    :rtype:  dict
    """
    data = json.loads(request.data)
    if(data is None):
        raise InvalidUsage(error_message="Missing parameter email_template_id")
    email_template_id = data.get("id")
    # Validate email template id
    validate_template_id(email_template_id)
    if isinstance(email_template_id, basestring):
        email_template_id = int(email_template_id)

    user_id = request.user.id
    domain_id = request.user.domain_id

    template = UserEmailTemplate.query.get(email_template_id)
    if not template:
        raise NotFoundError(error_message="Template not found")

    # Verify owned by same domain
    template_owner_user = User.query.get(template.user_id)

    if template_owner_user.domain_id != domain_id:
        raise ForbiddenError(error_message="Template is not owned by same domain")

    if template.is_immutable == 1 and not require_all_roles('CAN_DELETE_EMAIL_TEMPLATE'):
        raise ForbiddenError(error_message="User %d not allowed to delete the template" % user_id)

    # Delete the template
    template_to_delete = UserEmailTemplate.query.get(email_template_id)
    db.session.delete(template_to_delete)
    db.session.commit()
    return '', 204


@mod.route('/v1/email-templates', methods=['PUT'])
@require_oauth()
def update_email_template():
    """
    Function can update email template(s).
    input: {'id': "template_id"}
    :return: success=1 or 0
    :rtype:  dict
    """
    data = json.loads(request.data)
    email_template_id = data.get("id")
    # Validate email template id
    validate_template_id(email_template_id)
    if isinstance(email_template_id, basestring):
        email_template_id = int(email_template_id)
    domain_id = request.user.domain_id
    user_id = request.user.id

    template = UserEmailTemplate.query.get(email_template_id)
    if not template:
        raise ResourceNotFound(error_message="Template with id %d not found" % email_template_id)

    # Verify is_immutable
    if template.is_immutable == 1 and not require_all_roles('CAN_UPDATE_EMAIL_TEMPLATE'):
        raise ForbiddenError(error_message="User %d not allowed to update the template" % user_id)

    email_body_html = data.get("email_body_html") or template.email_body_html
    email_body_text = data.get("email_body_text") or template.email_body_text

    # Verify owned by same domain
    template_owner_user = User.query.get(template.user_id)

    if template_owner_user.domain_id != domain_id:
        raise ForbiddenError(error_message="Template is not owned by same domain")

    # Update email template
    db.session.query(UserEmailTemplate).filter_by(id=email_template_id).update(
        {"email_body_html": email_body_html, "email_body_text": email_body_text})

    db.session.commit()

    return jsonify({'email_template': {'email_body_html': email_body_html, 'id': email_template_id}})


@mod.route('/v1/email-templates/', methods=['GET'])
@mod.route('/v1/email-templates/<id>', methods=['GET'])
@require_oauth()
def get_email_template(**kwargs):
    """
    Function can retrieve email template(s).
    input: {'id': "template_id"}
    :return:  A dictionary containing array of template html body and template id
    :rtype: dict
    """
    email_template_id = kwargs.get("id")
    # Validate email template id
    validate_template_id(email_template_id)
    if isinstance(email_template_id, basestring):
        email_template_id = int(email_template_id)
    domain_id = request.user.domain_id

    template = UserEmailTemplate.query.get(email_template_id)
    if not template:
        raise ResourceNotFound(error_message="Template with id %d not found" % email_template_id)

    # Verify owned by same domain
    template_owner_user = User.query.get(template.user_id)
    if template_owner_user.domain_id != domain_id:
        raise ForbiddenError(error_message="Template is not owned by same domain")

    # Verify is_immutable
    if template.is_immutable == 1 and not require_all_roles('CAN_GET_EMAIL_TEMPLATE'):
        raise ForbiddenError(error_message="User %d not allowed to update the template" % template_owner_user.id)

    return jsonify({'email_template': {'email_body_html': template.email_body_html, 'id': email_template_id}})


@require_all_roles('CAN_CREATE_EMAIL_TEMPLATE_FOLDER')
@mod.route('/v1/email-template-folders', methods=['POST'])
@require_oauth()
def create_email_template_folder():
    """
    This function will create email template folder
    input: {'name': "template_folder_name", 'parent_id': "parent_id", "is_immutable": 0 or 1}
    :return: Template folder id
    """
    data = json.loads(request.data)
    folder_name = data.get('name')
    if not folder_name:
        raise InvalidUsage(error_message="Folder name must be provided")
    if not isinstance(folder_name, basestring):
        raise InvalidUsage(error_message="Invalid input")
    domain_id = request.user.domain_id

    # Check if the name is already exists under same domain
    existing_row = EmailTemplateFolder.query.filter(EmailTemplateFolder.name == folder_name,
                                                    EmailTemplateFolder.domain_id == domain_id).first()

    if existing_row:
        raise InvalidUsage(error_message="Template folder with name=%s already exists" % folder_name)

    parent_id = data.get('parent_id')
    if parent_id and not parent_id.isdigit():
        raise InvalidUsage(error_message="Invalid input")
    template_folder_parent_id = EmailTemplateFolder.query.filter_by(parent_id=parent_id, domain_id=domain_id).first()
    if template_folder_parent_id:
        raise ForbiddenError(error_message="Parent ID does not belong to domain %s" % domain_id)

    # If is_immutable value is not passed, make it as 0
    is_immutable = data.get("is_immutable")
    if is_immutable and not is_immutable.isdigit():
        raise InvalidUsage(error_message="Invalid input")
    else:
        is_immutable = 0

    email_template_folder = EmailTemplateFolder(name=folder_name, domain_id=domain_id, parent_id=parent_id,
                                                is_immutable=is_immutable)
    db.session.add(email_template_folder)
    db.session.commit()
    email_template_folder_id = email_template_folder.id

    return jsonify({"template_folder_id": [{"id": email_template_folder_id}]}), 201


@require_all_roles('CAN_DELETE_EMAIL_TEMPLATE_FOLDER')
@mod.route('/v1/email-template-folders', methods=['DELETE'])
@require_oauth()
def delete_email_template_folder():
    """
    This function will delete email template folder from the domain
    input: {'name': "template_folder_name", 'parent_id': "parent_id", "is_immutable": 0 or 1}
    :return: Template folder id
    """
    data = json.loads(request.data)
    folder_id = data.get('id')
    if not folder_id:
        raise InvalidUsage("Folder ID must be provided")
    if not isinstance(folder_id, int):
        if not folder_id.isdigit():
            raise InvalidUsage(error_message="Invalid input")
    if isinstance(folder_id, basestring):
        folder_id = int(folder_id)
    template_folder = EmailTemplateFolder.query.get(folder_id)

    if not template_folder:
        raise NotFoundError(error_message='Template folder not found')
    # Verify owned by same domain
    template_folder_owner_user = db.session.query(User).filter(template_folder.domain_id == User.domain_id).first()
    if not template_folder_owner_user:
        raise ForbiddenError(error_message="Template folder is not owned by same domain")

    # Delete the template
    template_folder_to_delete = EmailTemplateFolder.query.get(folder_id)
    db.session.delete(template_folder_to_delete)
    db.session.commit()

    return '', 204


def validate_template_id(email_template_id):
    """
    Function will validate template ID
    :param email_template_id:
    :return:
    """
    if not email_template_id:
        raise InvalidUsage(error_message="Template ID must be provided")

    if not isinstance(email_template_id, int):
        if not email_template_id.isdigit():
            raise InvalidUsage(error_message="Invalid input")


def check_domain_role():
    pass
