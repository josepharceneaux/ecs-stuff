from flask import Blueprint
from email_template_service.common.utils.auth_utils import require_oauth, require_all_roles
from email_template_service.common.models.db import db
from email_template_service.common.models.misc import UserEmailTemplate, EmailTemplateFolder
from email_template_service.common.models.user import User
from flask import request
from email_template_service.common.error_handling import *
import json


mod = Blueprint('email_template_service', __name__)


@mod.route('/v1/email-templates', methods=['POST'])
@require_oauth
def post_email_template():
    """
    POST /email_template  Create a new email_template
    input: {'name': "template_name", "email_body_html": "html_body"}
    :return:  A dictionary containing array of template id
    :rtype: dict
    """
    data = json.loads(request.data)
    user_id = request.user.id
    domain_id = request.user.domain_id
    template_name = data['name']
    if not template_name:
        raise ResourceNotFound(error_message="Template name is empty")

    email_template_html_body = data["email_body_html"]
    if not email_template_html_body:
        raise ResourceNotFound(error_message="Email HTML body is empty")

    # Check if the name is already exists in the domain
    existing_template_name = UserEmailTemplate.query.get(template_name)
    if existing_template_name:
        raise InvalidUsage(error_message="Template name with name=%s already exists" % existing_template_name)

    email_template_folder_id = data["email_template_folder_id"]
    if not RepresentsInt(email_template_folder_id):
        raise InvalidUsage(error_message="Invalid input")
    email_template_folder = db.session.query(EmailTemplateFolder).filter_by(id=email_template_folder_id).first()

    # Check if the email template folder belongs to current domain
    if email_template_folder and email_template_folder.domain_id != domain_id:
        raise ForbiddenError(error_message="Email template's folder is in the user's domain %d" % domain_id)

    # If is_immutable = 0, It can be accessed by everyone
    is_immutable_value = data["is_immutable"]
    if not RepresentsInt(is_immutable_value):
        raise InvalidUsage(error_message="Invalid input")
    if is_immutable_value == 1 and not require_all_roles('CAN_CREATE_EMAIL_TEMPLATE'):
        raise UnauthorizedError(error_message="User is not admin")
    user_email_template = UserEmailTemplate(user_id=user_id, type=0,
                                            name=template_name, email_body_html=email_template_html_body,
                                            email_body_text=data["email_body_text"] or None,
                                            email_template_folder_id=email_template_folder_id if
                                            email_template_folder_id else None,
                                            is_immutable=is_immutable_value)
    db.session.add(user_email_template)
    db.session.commit()
    user_email_template_id = user_email_template.id
    return jsonify({'template_id': [{'id': user_email_template_id}]}), 201


@mod.route('/v1/email-templates', methods=['DELETE'])
@require_oauth
def delete_email_template():
    """
    Function will delete email template from db
    input: {'id': "template_id"}
    :return: success=1 or 0
    :rtype:  dict
    """
    data = json.loads(request.data)
    email_template_id = data["id"]
    if not RepresentsInt(email_template_id):
        raise InvalidUsage(error_message="Invalid input")

    user_id = request.user.id
    domain_id = request.user.domain_id

    template = UserEmailTemplate.query.get(email_template_id)

    # Verify owned by same domain
    template_owner_user = db.session.query(User).filter(template.user_id == User.id).first()
    user_domain = template_owner_user.domain_id
    if user_domain != domain_id:
        raise ForbiddenError(error_message="Template is not owned by same domain")

    if template.is_immutable == 1 and not require_all_roles('CAN_DELETE_EMAIL_TEMPLATE'):
        raise ForbiddenError(error_message="User %d not allowed to delete the template" % user_id)

    # Delete the template
    template_to_delete = UserEmailTemplate.query.get(email_template_id)
    db.session.delete(template_to_delete)
    db.session.commit()
    return jsonify({"success": 1}), 204


@mod.route('/v1/email-templates', methods=['PUT'])
@require_oauth
def update_email_template():
    """
    Function can update email template(s).
    input: {'id': "template_id"}
    :return: success=1 or 0
    :rtype:  dict
    """
    data = json.loads(request.data)
    email_template_id = data["id"]
    if not RepresentsInt(email_template_id):
        raise InvalidUsage(error_message="Invalid input")

    domain_id = request.user.domain_id
    user_id = request.user.id

    user_email_template = UserEmailTemplate.query.get(email_template_id)

    if not user_email_template:
        raise ResourceNotFound(error_message="Template with id %d not found" % email_template_id)

    # Verify owned by same domain
    template_owner_user = db.session.query(User).filter(user_email_template.user_id == User.id).first()
    user_domain = template_owner_user.domain_id
    if user_domain != domain_id:
        raise ForbiddenError(error_message="Template is not owned by same domain")

    # Verify is_immutable
    if user_email_template.is_immutable == 1 and not require_all_roles('CAN_UPDATE_EMAIL_TEMPLATE'):
        raise ForbiddenError(error_message="User %d not allowed to update the template" % user_id)

    db.session.query(UserEmailTemplate).filter_by(id=email_template_id).update(
        {"email_body_html": data["email_body_html"] or UserEmailTemplate.email_body_html,
         "email_body_text": data["email_body_text"] or UserEmailTemplate.email_body_text})
    db.session.commit()
    email_body_html = user_email_template.email_body_html
    return jsonify({'email_template': {'email_body_html': email_body_html, 'id': email_template_id}})


@mod.route('/v1/email-templates', methods=['GET'])
@require_oauth
def get_email_template():
    """
    Function can retrieve email template(s).
    input: {'id': "template_id"}
    :return:  A dictionary containing array of template html body and template id
    :rtype: dict
    """
    data = json.loads(request.data)
    email_template_id = data["id"]
    if not RepresentsInt(email_template_id):
        raise InvalidUsage(error_message="Invalid input")

    domain_id = request.user.domain_id

    if isinstance(email_template_id, basestring):
        email_template_id = int(email_template_id)

    user_email_template = UserEmailTemplate.query.get(email_template_id)

    if not user_email_template:
        raise ResourceNotFound(error_message="Template with id %d not found" % email_template_id)

    # Verify owned by same domain
    template_owner_user = db.session.query(User).filter(user_email_template.user_id == User.id).first()
    user_domain = template_owner_user.domain_id

    if user_domain != domain_id:
        raise ForbiddenError(error_message="Template is not owned by same domain")

    # Verify is_immutable
    if user_email_template.is_immutable == 1 and not require_all_roles('CAN_GET_EMAIL_TEMPLATE'):
        raise ForbiddenError(error_message="User %d not allowed to update the template" % template_owner_user.id)

    email_body_html = user_email_template.email_body_html

    return jsonify({'email_template': {'email_body_html': email_body_html, 'id': email_template_id}})


@require_all_roles('CAN_CREATE_EMAIL_TEMPLATE_FOLDER')
@mod.route('/v1/email-template-folders', methods=['POST'])
@require_oauth
def create_email_template_folder():
    """
    This function will create email template folder
    input: {'name': "template_folder_name", 'parent_id': "parent_id", "is_immutable": 0 or 1}
    :return: Template folder id
    """
    auth_user = request.user
    requested_data = json.loads(request.data)
    folder_name = requested_data['name']
    domain_id = request.user.domain_id

    # Check if the name is already exists under same domain
    existing_row = EmailTemplateFolder.query.filter(EmailTemplateFolder.name == folder_name,
                                                    EmailTemplateFolder.domain_id == domain_id).first()

    if existing_row:
        raise InvalidUsage(error_message="Template Folder with name=%s already exists" % folder_name)

    parent_id = requested_data['parent_id'] if 'parent_id' in requested_data else None
    template_folder_parent_id = EmailTemplateFolder.query.filter_by(parent_id=parent_id, domain_id=domain_id).first()
    if parent_id and not template_folder_parent_id:
        raise ForbiddenError(error_message="parent ID %s does not belong to domain %s" % auth_user.id % domain_id)

    # If is_immutable value is not passed, make it as 0
    try:
        is_immutable = requested_data["is_immutable"]
    except:
        is_immutable = 0

    email_template_folder = EmailTemplateFolder(name=folder_name, domain_id=domain_id, parent_id=parent_id,
                                                is_immutable=is_immutable)
    db.session.add(email_template_folder)
    db.session.commit()
    email_template_folder_id = email_template_folder.id

    return jsonify({"template_folder_id": [{"id": email_template_folder_id}]}), 201


@require_all_roles('CAN_DELETE_EMAIL_TEMPLATE_FOLDER')
@mod.route('/v1/email-template-folders', methods=['DELETE'])
@require_oauth
def delete_email_template_folder():
    """
    This function will delete email template folder from the domain
    input: {'name': "template_folder_name", 'parent_id': "parent_id", "is_immutable": 0 or 1}
    :return: Template folder id
    """
    requested_data = json.loads(request.data)
    folder_id = requested_data['id']

    template_folder = EmailTemplateFolder.query.get(folder_id)

    # Verify owned by same domain
    template_folder_owner_user = db.session.query(User).filter(template_folder.domain_id == User.domain_id).first()
    if not template_folder_owner_user:
        raise ForbiddenError(error_message="Template folder is not owned by same domain")

    # Delete the template
    db.session.query(UserEmailTemplate).filter_by(id=folder_id).delete()
    db.session.commit()

    return jsonify({"success": 1}), 204


def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
