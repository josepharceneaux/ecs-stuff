from flask import Blueprint
from flask_restful import Resource
from email_template_service.common.utils.auth_utils import require_oauth, require_all_roles
from email_template_service.common.models.db import db
from email_template_service.common.models.misc import UserEmailTemplate, EmailTemplateFolder
from email_template_service.common.models.user import User
from flask import request
from email_template_service.common.error_handling import *
import json

mod = Blueprint('email_template_service', __name__)


class EmailTemplate(Resource):

    # Access token and role authentication decorators
    decorators = [require_oauth]

    @require_oauth
    def post(self):
        """
        POST /email_template  Create a new email_template
        input: {'name': "template_name", "email_body_html": "html_body"}
        :return:  A dictionary containing array of template id
        :rtype: dict
        """
        # check email body
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
        existing_template_name = db.session.query(UserEmailTemplate).join(User).filter(
            UserEmailTemplate.name == template_name, User.domain_id == domain_id).first()
        if existing_template_name:
            raise InvalidUsage(error_message="Template name with name=%s already exists" % existing_template_name)

        email_template_folder_id = int(data("email_template_folder_id") or 0)

        email_template_folder = EmailTemplateFolder.query.get(email_template_folder_id) if \
            email_template_folder_id else None

        # Check if the email template folder belongs to current domain
        if email_template_folder and email_template_folder.domainId != domain_id:
            raise ForbiddenError(error_message="Email template's folder %d is in the user's domain %d" %
                                 email_template_folder_id % domain_id)

        # If is_immutable = 0, It can be accessed by everyone
        is_immutable_value = int(data("is_immutable") or 0)
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
        return {'template_id': {'id': user_email_template_id}}

    @require_oauth
    def delete(self, **kwargs):
        """
        Function will delete email template from db
        input: {'id': "template_id"}
        :return: success=1 or 0
        :rtype:  dict
        """
        data = json.loads(request.data)
        email_template_id = data["id"]
        user_id = request.user.id
        domain_id = request.user.domain_id

        template = UserEmailTemplate.query.filter_by(id=email_template_id).first()

        # Verify owned by same domain
        template_owner_user = db.session.query(UserEmailTemplate).join(User).filter_by(
            UserEmailTemplate.user_id == User.id).first()

        if template_owner_user.domain_id != domain_id:
            raise ForbiddenError(error_message="Template is not owned by same domain")

        if template.is_immutable == 1 and not require_all_roles('CAN_DELETE_EMAIL_TEMPLATE'):
            raise ForbiddenError(error_message="User %d not allowed to delete the template" % user_id)
        else:
            # Delete the template
            db.session.query(UserEmailTemplate).filter_by(id=email_template_id).delete()

            return dict(success=1)

    @require_oauth
    def patch(self, **kwargs):
        """
        Function can update email template(s).
        input: {'id': "template_id"}
        :return: success=1 or 0
        :rtype:  dict
        """
        data = json.loads(request.data)
        email_template_id = data["id"]
        domain_id = request.user.domain_id
        user_id = request.user.id

        user_email_template = UserEmailTemplate.query.get(email_template_id)

        if not user_email_template:
            raise ResourceNotFound(error_message="Template with id %d not found" % email_template_id)

        # Verify owned by same domain
        template_owner_user = db.session.query(UserEmailTemplate).join(User).filter_by(
            UserEmailTemplate.user_id == User.id).first()
        if template_owner_user.domain_id != domain_id:
            raise ForbiddenError(error_message="Template is not owned by same domain")

        # Verify is_immutable
        if user_email_template.is_immutable == 1 and not require_all_roles('CAN_UPDATE_EMAIL_TEMPLATE'):
            raise ForbiddenError(error_message="User %d not allowed to update the template" % user_id)

        db.session.query(UserEmailTemplate).update(
            {"email_body_html": data("email_body_html") or UserEmailTemplate.email_body_html,
             "email_body_text": request.args.get("email_body_text") or UserEmailTemplate.email_body_text})
        db.session.commit()

        return dict(success=1)

    @require_oauth
    def get(self, **kwargs):
        """
        Function can retrieve email template(s).
        input: {'id': "template_id"}
        :return:  A dictionary containing array of template html body and template id
        :rtype: dict
        """
        domain_id = request.user.domain_id

        email_template_id = kwargs.get("id")
        if isinstance(email_template_id, basestring):
            email_template_id = int(email_template_id)

        user_email_template = UserEmailTemplate.query.get(email_template_id)

        if not user_email_template:
            raise ResourceNotFound(error_message="Template with id %d not found" % email_template_id)

        # Verify owned by same domain
        template_owner_user = db.session.query(UserEmailTemplate).join(User).filter_by(
            UserEmailTemplate.user_id == User.id).first()

        if template_owner_user.domain_id != domain_id:
            raise ForbiddenError(error_message="Template is not owned by same domain")

        email_body_html = user_email_template.email_body_html

        return {'email_template': {'email_body_html': email_body_html, 'id': email_template_id}}


# Inputs: name, parentId (if any), is_immutable (only if admin)
# @require_all_roles('CAN_CREATE_EMAIL_TEMPLATE_FOLDER')
# @mod.route('/emailTemplateFolder', methods=['POST'])
@require_oauth
def create_email_template_folder():
    """
    This function will create email template folder
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
    is_immutable = 0
    get_immutable_value = request.args.get("is_immutable")
    if get_immutable_value == "1" and not require_all_roles('CAN_CREATE_EMAIL_TEMPLATE_FOLDER'):
        raise UnauthorizedError(error_message="User is not admin")
    email_template_folder = EmailTemplateFolder(name=folder_name, domain_id=domain_id, parent_id=parent_id,
                                                is_immutable=is_immutable)
    db.session.add(email_template_folder)
    db.session.commit()
    email_template_folder_id = email_template_folder.id

    return jsonify(id=email_template_folder_id)


