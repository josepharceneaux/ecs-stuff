from flask import Blueprint
from flask_restful import Resource
from email_template_service.common.utils.auth_utils import require_oauth, require_all_roles
from email_template_service.common.models.db import db
from email_template_service.common.models.misc import UserEmailTemplate, EmailTemplateFolder
from email_template_service.common.models.user import User
from flask import request
from email_template_service.common.error_handling import *
from email_template_service.common.utils.validators import is_number
import json

mod = Blueprint('email_template_service', __name__)


TEMPLATE_EMAIL_MARKETING = 0
# current.TEMPLATE_EMAIL_MARKETING = TEMPLATE_EMAIL_MARKETING Todo: Change the value


class EmailTemplate(Resource):

    # Access token and role authentication decorators
    decorators = [require_oauth]

    @require_oauth
    def post(self):
        """
        POST /email_template  Create a new email_template
        input: {'users': [userDict1, userDict2, userDict3, ... ]}

        Take a JSON dictionary containing array of User dictionaries
        A single user dict must contain user's first name, last name, and email

        :return:  A dictionary containing array of user ids
        :rtype: dict
        """
        requested_data = json.loads(request.data)
        requested_user_id = request.user.id
        template_name = requested_data['name']
        domain_id = request.user.domain_id
        # Check if the name is already exists in the domain
        existing_rows = db.session.query(UserEmailTemplate).join(User).filter(UserEmailTemplate.name == template_name,
                                                                              User.domain_id == domain_id).one()
        existing_template_name = existing_rows.name
        if existing_template_name:
            raise InvalidUsage(error_message="Template name with name=%s already exists" % existing_template_name)

        email_template_folder_id = int(requested_data("email_template_folder_id") or 0)
        email_template_folder = EmailTemplateFolder.query.get(email_template_folder_id) if email_template_folder_id else None
        if email_template_folder and email_template_folder.domainId != domain_id:
            raise ForbiddenError(error_message="parent ID %s does not belong to domain %s" % requested_user_id % domain_id)

        get_immutable_value = int(requested_data("is_immutable") or 0)
        if get_immutable_value == "1" and not require_all_roles('CAN_CREATE_EMAIL_TEMPLATE'):
            raise UnauthorizedError(error_message="User is not admin")
        user_email_template = UserEmailTemplate(user_id=requested_user_id, type=TEMPLATE_EMAIL_MARKETING,
                                                name=template_name, email_body_html=requested_data["email_body_html"] or None,
                                                email_body_text=requested_data["email_body_text"] or None,
                                                emailTemplateFolderId=email_template_folder_id if
                                                email_template_folder_id else None,
                                                is_immutable=get_immutable_value)
        db.session.add(user_email_template)
        db.session.commit()
        user_email_template_id = user_email_template.id
        return {'template_id': {'id': user_email_template_id}}

    # Input: template_id
    @require_oauth
    def delete(self, **kwargs):
        """
        Function will delete email template from db
        :return: success=1 or 0
        :rtype:  dict
        """
        # Parse request body
        body_dict = request.get_json(force=True)
        if not any(body_dict):
            raise InvalidUsage(error_message="JSON body cannot be empty.")
        requested_template_id = body_dict.get("id")
        domain_id = request.user.domain_id
        template = UserEmailTemplate.query.filter_by(id=requested_template_id).first()
        if template.isImmutable == 1 and not require_all_roles('CAN_DELETE_EMAIL_TEMPLATE'):
            raise ForbiddenError(error_message="Non-admin user trying to delete immutable template")
        else:
            db.session.query(UserEmailTemplate).join(User).filter(
                UserEmailTemplate.id == requested_template_id, UserEmailTemplate.user_id.in_(
                    User.domain_id == domain_id)).first().delete()

            return dict(success=1)

    # Inputs: id, emailBodyHtml
    @require_oauth
    def patch(self, **kwargs):
        """
        PATCH /v1/emailTemplate
        Function can update email template(s).

        Takes a JSON dict containing:
            - a email_template_id as key and a template-object as value
        Function only accepts JSON dict.
        JSON dict must contain email template's ID.

        :return: {'candidates': [{'id': candidate_id}, {'id': candidate_id}, ...]}
        """
        # Parse request body
        body_dict = request.get_json(force=True)
        requested_email_template_id = body_dict.get("id")
        domain_id = request.user.domain_id
        user_email_template = UserEmailTemplate.query.get(requested_email_template_id)

        # Verify owned by same domain
        owner_user = db.session.query(UserEmailTemplate).join(User).filter_by(
            UserEmailTemplate.user_id == User.id).first()
        if owner_user.domain_id != domain_id:
            raise ForbiddenError(error_message="Template is not owned by same domain")
        # Verify isImmutable
        if user_email_template.is_immutable and not require_all_roles('CAN_UPDATE_EMAIL_TEMPLATE'):
            raise ForbiddenError(error_message="Non-admin user trying to update immutable template")

        db.session.query(UserEmailTemplate).update(
            {"email_body_html": body_dict("email_body_html") or UserEmailTemplate.email_body_html,
             "email_body_text": request.args.get("email_body_text") or UserEmailTemplate.email_body_text})
        db.session.commit()

        return dict(success=1)

    # Inputs: id
    @require_oauth
    def get(self, **kwargs):
        """
        """
        # Authenticated user
        authed_user = request.user
        domain_id = request.user.domain_id

        email_template_id = kwargs.get("id")
        if email_template_id:
            # Candidate ID must be an integer
            if not is_number(email_template_id):
                raise InvalidUsage(error_message="Template ID must be an integer")
        user_email_template_row = UserEmailTemplate.query.filter_by(id=email_template_id).first()

        # Verify domain
        owner_user = db.session.query(UserEmailTemplate).filter_by(user_id=authed_user.id).first()
        if owner_user.domain_id != domain_id:
            raise ForbiddenError(error_message="Template is not owned by same domain")

        # Verify isImmutable
        if user_email_template_row.is_immutable and not require_all_roles('CAN_GET_EMAIL_TEMPLATE'):
            raise ForbiddenError(error_message="Non-admin user trying to access immutable template")

        email_body_html = user_email_template_row.email_body_html
        return {'email_template': {'id': email_body_html}}


# Inputs: name, parentId (if any), is_immutable (only if admin)
# @require_all_roles('CAN_CREATE_EMAIL_TEMPLATE_FOLDER')
@mod.route('/emailTemplateFolder', methods=['POST'])
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
        is_immutable = 1
        raise UnauthorizedError(error_message="User is not admin")
    email_template_folder = EmailTemplateFolder(name=folder_name, domain_id=domain_id, parent_id=parent_id,
                                                is_immutable=is_immutable)
    db.session.add(email_template_folder)
    db.session.commit()
    email_template_folder_id = email_template_folder.id

    return jsonify(id=email_template_folder_id)


