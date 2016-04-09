"""Email Templates API: Provides the endpoints to create, retrieve, update and delete
Email Templates. Also contains endpoints for creating and deleting Email Template Folders
"""
import requests

from flask import request
from flask import Blueprint

from email_campaign_service.common.routes import EmailCampaignEndpoints
from email_campaign_service.common.models.user import (User, DomainRole)
from email_campaign_service.common.utils.handy_functions import get_valid_json_data
from email_campaign_service.common.utils.validators import validate_and_return_immutable_value
from email_campaign_service.common.utils.auth_utils import (require_oauth, require_all_roles)
from email_campaign_service.common.models.email_campaign import (UserEmailTemplate, EmailTemplateFolder)
from email_campaign_service.common.error_handling import (jsonify, InvalidUsage, ForbiddenError, ResourceNotFound)

template_blueprint = Blueprint('email_template_service', __name__)


@template_blueprint.route('/' + EmailCampaignEndpoints.VERSION + '/email-templates', methods=['POST'])
@require_oauth()
@require_all_roles(DomainRole.Roles.CAN_CREATE_EMAIL_TEMPLATE)
def post_email_template():
    """
    Function will create an email template based on the values provided by user in post data.
    Values required from data are template name, html body of template, template folder id and
    either a 0 or 1 as is_immutable value for the template.

    :return: ID of the created template.
    """
    user_id = request.user.id
    domain_id = request.user.domain_id

    data = get_valid_json_data(request)
    template_name = data.get('name')
    if not template_name:
        raise InvalidUsage(error_message='Template name is empty')

    template_html_body = data.get('body_html')
    if not template_html_body:
        raise InvalidUsage(error_message='Email HTML body is empty')

    # Check if the name is already exists in the domain
    existing_template = UserEmailTemplate.get_by_name(template_name)
    if existing_template:
        raise InvalidUsage(error_message='Template name with name=%s already exists' % existing_template)

    template_folder_id = data.get('template_folder_id')
    if template_folder_id and not (isinstance(template_folder_id, int) or template_folder_id.isdigit()):
        raise InvalidUsage(error_message='Invalid input: folder_id must be positive integer')

    template_folder = EmailTemplateFolder.get_by_id(template_folder_id)

    # Check if the email template folder belongs to current domain
    if template_folder and template_folder.domain_id != domain_id:
        raise ForbiddenError(error_message="Email template's folder (id:%d) is not in the user's domain (id:%d)" % (
            template_folder.id, template_folder.domain_id))

    # If is_immutable value is not passed, make it as 0
    is_immutable = data.get('is_immutable', 0)
    is_immutable = validate_and_return_immutable_value(is_immutable)

    template = UserEmailTemplate(user_id=user_id, type=0,
                                 name=template_name, body_html=template_html_body,
                                 body_text=data.get('body_text'),
                                 template_folder_id=template_folder_id if
                                 template_folder_id else None,
                                 is_immutable=is_immutable)
    UserEmailTemplate.save(template)

    template_id = template.id
    return jsonify({'template_id': [{'id': template_id}]}), requests.codes.CREATED


@template_blueprint.route('/' + EmailCampaignEndpoints.VERSION + '/email-templates', methods=['GET'])
@template_blueprint.route('/' + EmailCampaignEndpoints.VERSION + '/email-templates/<int:template_id>', methods=['GET'])
@require_oauth()
@require_all_roles(DomainRole.Roles.CAN_GET_EMAIL_TEMPLATE)
def get_email_template(template_id):
    """
        GET /v1/email-templates
        Function will return email template based on specified id
        :param template_id: ID of of email template
        :return: Email Template with specified id
    """

    # Validate email template id
    if template_id == 0:
        raise InvalidUsage(error_message='template_id must be greater than 0')

    domain_id = request.user.domain_id
    template = UserEmailTemplate.get_by_id(template_id)
    if not template:
        raise ResourceNotFound(error_message='Template with id %d not found' % template_id)

    # Verify owned by same domain
    template_owner_user = User.get_by_id(template.user_id)
    if template_owner_user.domain_id != domain_id:
        raise ForbiddenError(error_message='Template(id:%d) is not owned by'
                                           'domain(id:%d)' % (template_id, domain_id))

    return jsonify({'template': {'body_html': template.body_html, 'id': template_id}})


@template_blueprint.route('/' + EmailCampaignEndpoints.VERSION + '/email-templates/<int:template_id>',
                          methods=['PATCH'])
@require_oauth()
@require_all_roles(DomainRole.Roles.CAN_UPDATE_EMAIL_TEMPLATE)
def update_email_template(template_id):
    """
        PUT /v1/email-templates
        Function would update existing email template
        Required parameters:
        :param template_id: ID of of email template
        :return: Updated email template
    """
    if template_id == 0:
        raise InvalidUsage(error_message='template_id must be greater than 0')

    data = get_valid_json_data(request)

    domain_id = request.user.domain_id
    user_id = request.user.id

    template = UserEmailTemplate.get_by_id(template_id)
    if not template:
        raise ResourceNotFound(error_message='Template with id %d not found for user (id:%d)' % (template_id,
                                                                                                 user_id))

    body_html = data.get('body_html') or template.body_html
    body_text = data.get('body_text') or template.body_text

    # Verify owned by same domain
    template_owner_user = User.get_by_id(template.user_id)
    updated_data = {'body_html': body_html, 'body_text': body_text}
    if template_owner_user.domain_id == domain_id:
        # Update email template
        template.update(**updated_data)
    else:
        raise ForbiddenError(error_message='Template(id:%d) is not owned by user(id:%d) &'
                                           'domain(id:%d)' % (template_id, user_id, domain_id))

    return jsonify({'template': {'body_html': body_html, 'id': template_id}})


@template_blueprint.route('/' + EmailCampaignEndpoints.VERSION + '/email-templates/<int:template_id>',
                          methods=['DELETE'])
@require_oauth()
@require_all_roles(DomainRole.Roles.CAN_DELETE_EMAIL_TEMPLATE)
def delete_email_template(template_id):

    # Validate email template id
    if template_id == 0:
        raise InvalidUsage(error_message='template_id must be greater than 0')

    user_id = request.user.id
    domain_id = request.user.domain_id

    template = UserEmailTemplate.get_by_id(template_id)
    if not template:
        raise ResourceNotFound(error_message='Template (id:%d) not found' % template_id)

    # Verify owned by same domain
    template_owner_user = User.get_by_id(template.user_id)

    if template_owner_user.domain_id != domain_id:
        raise ForbiddenError(error_message="Template (id:%d) does not belong to user(id:%d)`s domain(id:%d)" %
                                           (template_id, user_id, domain_id))

    # Delete the template
    UserEmailTemplate.delete(template)
    return '', requests.codes.NO_CONTENT


@template_blueprint.route('/' + EmailCampaignEndpoints.VERSION + '/email-template-folders', methods=['POST'])
@require_oauth()
@require_all_roles(DomainRole.Roles.CAN_CREATE_EMAIL_TEMPLATE_FOLDER)
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
        raise InvalidUsage(error_message='Folder name must be provided.')
    if not isinstance(folder_name, basestring):
        raise InvalidUsage(error_message='Invalid input: Folder name must be a valid string.')
    domain_id = request.user.domain_id

    # Check if the name already exists under same domain
    duplicate = EmailTemplateFolder.get_by_name_and_domain_id(folder_name, domain_id)

    if duplicate:
        raise InvalidUsage(error_message='Template folder with name=%s already exists' % folder_name)

    parent_id = data.get('parent_id')
    if parent_id and not (isinstance(parent_id, int) or parent_id.isdigit()):
        raise InvalidUsage(error_message='Invalid input: parent_id must be a valid digit')
    if parent_id and domain_id:
        template_folder_parent = EmailTemplateFolder.get_by_id(parent_id)
        if not template_folder_parent:
            raise ForbiddenError(error_message='Email Template Folder with (id:%d) does not exist' % parent_id)
        elif not template_folder_parent.domain_id == domain_id:
            raise ForbiddenError(error_message='Email Template Folder with (id:%d) does not belong to domain (id:%d)'
                                               % (parent_id, domain_id))

    # If is_immutable value is not passed, make it as 0
    is_immutable = data.get('is_immutable', 0)
    is_immutable = validate_and_return_immutable_value(is_immutable)

    template_folder = EmailTemplateFolder(name=folder_name, domain_id=domain_id, parent_id=parent_id,
                                          is_immutable=is_immutable)
    EmailTemplateFolder.save(template_folder)
    template_folder_id = template_folder.id

    return jsonify({'template_folder_id': [{'id': template_folder_id}]}), requests.codes.CREATED


@template_blueprint.route('/' + EmailCampaignEndpoints.VERSION + '/email-template-folders/<int:folder_id>',
                          methods=['DELETE'])
@require_oauth()
@require_all_roles(DomainRole.Roles.CAN_DELETE_EMAIL_TEMPLATE_FOLDER)
def delete_email_template_folder(folder_id):
    """
        DELETE /v1/email-template-folders
        Required parameters:
        :param folder_id: ID of of email template
        :return: Response with no content and status 200 (ok)
    """
    user_id = request.user.id
    domain_id = request.user.domain_id
    if not folder_id:
        raise InvalidUsage(error_message='template_id must be greater than 0')

    template_folder = EmailTemplateFolder.get_by_id(folder_id)

    if not template_folder:
        raise ResourceNotFound(error_message='Template folder not found')
    # Verify owned by same domain
    if not template_folder.domain_id == domain_id:
        raise ForbiddenError(error_message="Template folder (id:%d) is not owned by user(id:%d)'s domain(id:%d)"
                             % (folder_id, user_id, domain_id))
    else:
        EmailTemplateFolder.delete(template_folder)

    return '', requests.codes.NO_CONTENT