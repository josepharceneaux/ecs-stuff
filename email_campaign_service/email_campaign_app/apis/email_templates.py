"""Email Templates API: Provide the endpoints to create, retrieve, update and delete
Email Templates. Also contains endpoints for creating and deleting Email Template Folders
"""
import json

from flask import request
from flask import Blueprint

from email_campaign_service.common.models.db import db
from email_campaign_service.common.models.user import User
from email_campaign_service.common.utils.handy_functions import get_valid_json_data
from email_campaign_service.common.utils.auth_utils import (require_oauth, require_all_roles)
from email_campaign_service.common.models.misc import (UserEmailTemplate, EmailTemplateFolder)
from email_campaign_service.common.error_handling import (jsonify, InvalidUsage, ForbiddenError, NotFoundError,
                                                          ResourceNotFound, UnauthorizedError)

mod = Blueprint('email_template_service', __name__)


@mod.route('/v1/email-templates', methods=['POST'])
@require_oauth()
def post_email_template():
    """

        POST /email-templates
        Function will create an email template
        Required parameters:
        name:                     Name of email template
        email_body_html:          Body of email template
        email_template_folder_id: ID of email template folder
        is_immutable:             Parameter to determine is the email template is  mutable or not
    """
    user_id = request.user.id
    domain_id = request.user.domain_id

    #Todo: use getvalidjsondata from handy functions
    data = get_valid_json_data(request)
    if data is None:
        raise InvalidUsage(error_message="Missing parameters for creating email template.")

    template_name = data.get('name')
    if not template_name:
        raise InvalidUsage(error_message="Template name is empty")

    email_template_html_body = data.get("email_body_html")
    if not email_template_html_body:
        raise InvalidUsage(error_message="Email HTML body is empty")

    # Check if the name is already exists in the domain
    existing_template_name = UserEmailTemplate.get(template_name)
    if existing_template_name:
        raise InvalidUsage(error_message="Template name with name=%s already exists" % existing_template_name)

    email_template_folder_id = data.get("email_template_folder_id")
    if email_template_folder_id and not (isinstance(email_template_folder_id, int) or
                                         email_template_folder_id.isdigit()):
        raise InvalidUsage(error_message="Invalid input")

    email_template_folder = EmailTemplateFolder.get(email_template_folder_id)

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


@mod.route('/v1/email-templates/', methods=['GET'])
@mod.route('/v1/email-templates/<int:id>', methods=['GET'])
@require_oauth()
def get_email_template(**kwargs):
    """
        GET /email-templates
        Function will return email template based on specified id
        Required parameters:
        id:     ID of of email template
    """
    email_template_id = kwargs.get("id")

    # Validate email template id
    validate_template_id(email_template_id)
    if isinstance(email_template_id, basestring):
        email_template_id = int(email_template_id)
    domain_id = request.user.domain_id
    #todo: remove .query everywhere
    template = UserEmailTemplate.get(email_template_id)
    if not template:
        raise ResourceNotFound(error_message="Template with id %d not found" % email_template_id)

    # Verify owned by same domain
    template_owner_user = User.get(template.user_id)
    if template_owner_user.domain_id != domain_id:
        raise ForbiddenError(error_message="Template is not owned by same domain")

    # Verify is_immutable
    if template.is_immutable == 1 and not require_all_roles('CAN_GET_EMAIL_TEMPLATE'):
        raise ForbiddenError(error_message="User %d not allowed to update the template" % template_owner_user.id)

    return jsonify({'email_template': {'email_body_html': template.email_body_html, 'id': email_template_id}})


@mod.route('/v1/email-templates', methods=['PUT'])
@require_oauth()
def update_email_template():
    """
        PUT /email-templates
        Function would update existing email template
        Required parameters:
        id:     ID of email template
    """
    #todo: same as get, use template id from url
    data = json.loads(request.data)
    if data is None:
        raise InvalidUsage(error_message="Missing parameter email_template_id.")

    email_template_id = data.get("id")

    # Validate email template id
    validate_template_id(email_template_id)
    if isinstance(email_template_id, basestring):
        email_template_id = int(email_template_id)
    domain_id = request.user.domain_id
    user_id = request.user.id

    template = UserEmailTemplate.get(email_template_id)
    if not template:
        raise ResourceNotFound(error_message="Template with id %d not found" % email_template_id) #todo add user id

    # Verify is_immutable
    if template.is_immutable == 1 and not require_all_roles('CAN_UPDATE_EMAIL_TEMPLATE'):
        raise ForbiddenError(error_message="User %d not allowed to update the template" % user_id) #todo add template id

    email_body_html = data.get("email_body_html") or template.email_body_html # todo: remove prefixes from column names in model
    email_body_text = data.get("email_body_text") or template.email_body_text

    # Verify owned by same domain
    template_owner_user = User.get(template.user_id)

    if template_owner_user.domain_id != domain_id:
        raise ForbiddenError(error_message="Template is not owned by same domain") #todo add user, template and domains's id

    # Update email template
    template.update({"email_body_html": email_body_html, "email_body_text": email_body_text})

    return jsonify({'email_template': {'email_body_html': email_body_html, 'id': email_template_id}})


@mod.route('/v1/email-templates', methods=['DELETE']) #todo: get id from url
@require_oauth()
def delete_email_template():
    """
        DELETE /email-templates
        Function will delete email template
        Required parameters:
        id:     ID of email template
    """
    data = json.loads(request.data)
    if data is None:
        raise InvalidUsage(error_message="Missing parameter email_template_id.")

    email_template_id = data.get("id")

    # Validate email template id
    validate_template_id(email_template_id)
    if isinstance(email_template_id, basestring):
        email_template_id = int(email_template_id)

    user_id = request.user.id
    domain_id = request.user.domain_id

    template = UserEmailTemplate.get(email_template_id)
    if not template:
        raise NotFoundError(error_message="Template not found")

    # Verify owned by same domain
    template_owner_user = User.get(template.user_id)

    if template_owner_user.domain_id != domain_id:
        raise ForbiddenError(error_message="Template is not owned by same domain")

    #todo: remove magic constant
    if template.is_immutable == 1 and not require_all_roles('CAN_DELETE_EMAIL_TEMPLATE'):
        raise ForbiddenError(error_message="User %d not allowed to delete the template" % user_id)

    # Delete the template
    db.session.delete(template)
    db.session.commit()
    return '', 204  # todo: use requests.code


@require_all_roles('CAN_CREATE_EMAIL_TEMPLATE_FOLDER')
@mod.route('/v1/email-template-folders', methods=['POST'])
@require_oauth()
def create_email_template_folder():
    """
        POST /email-template-folders
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
        raise InvalidUsage(error_message="Invalid input")
    domain_id = request.user.domain_id

    # Check if the name is already exists under same domain
    #TODO: move to models and restructure the query using filterby
    existing_row = EmailTemplateFolder.get_by_name_and_domain_id(folder_name, domain_id)

    if existing_row:
        raise InvalidUsage(error_message="Template folder with name=%s already exists" % folder_name)

    parent_id = data.get('parent_id')
    if parent_id and not parent_id.isdigit():
        raise InvalidUsage(error_message="Invalid input: parent_id must be a valid digit")
    template_folder_parent_id = EmailTemplateFolder.filter_by(parent_id=parent_id, domain_id=domain_id).first()
    if template_folder_parent_id:
        raise ForbiddenError(error_message="Parent ID does not belong to domain %s" % domain_id)

    # If is_immutable value is not passed, make it as 0
    is_immutable = data.get("is_immutable")
    if is_immutable and not is_immutable.isdigit():  # TODO: cater all cases
        raise InvalidUsage(error_message="Invalid input")
    else:
        is_immutable = 0

    email_template_folder = EmailTemplateFolder(name=folder_name, domain_id=domain_id, parent_id=parent_id,
                                                is_immutable=is_immutable)
    db.session.add(email_template_folder)
    db.session.commit()
    email_template_folder_id = email_template_folder.id

    return jsonify({"template_folder_id": [{"id": email_template_folder_id}]}), 201


@require_all_roles('CAN_DELETE_EMAIL_TEMPLATE_FOLDER')  # TODO: use roles as used in candidate service
@mod.route('/v1/email-template-folders', methods=['DELETE'])
@require_oauth()
def delete_email_template_folder():
    """
        DELETE /email-template-folders
        Required parameters:
        id:     ID of email template
    """
    domain_id = request.user.domain_id
    data = json.loads(request.data)
    if data is None:
        raise InvalidUsage(error_message="Missing parameter email template folder id.")

    folder_id = data.get('id')
    if not folder_id:
        raise InvalidUsage("Folder ID must be provided")
    if not isinstance(folder_id, int):
        if not folder_id.isdigit():
            raise InvalidUsage(error_message="Invalid input")
    if isinstance(folder_id, basestring):
        folder_id = int(folder_id)
    template_folder = EmailTemplateFolder.get(folder_id)

    if not template_folder:
        raise NotFoundError(error_message='Template folder not found')
    # Verify owned by same domain
    if not template_folder.domain_id == domain_id:
        raise ForbiddenError(error_message="Template folder is not owned by same domain")
    else:
        EmailTemplateFolder.delete(template_folder)

    return '', 204


def validate_template_id(email_template_id):
    """
    Function will validate email template ID
    """
    if not email_template_id:
        raise InvalidUsage(error_message="Template ID must be provided")

    if not isinstance(email_template_id, int):
        if not email_template_id.isdigit():
            raise InvalidUsage(error_message="Invalid input")


def check_domain_role():
    pass
