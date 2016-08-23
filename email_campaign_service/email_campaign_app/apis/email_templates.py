"""Email Templates API: Provides the endpoints to create, retrieve, update and delete
Email Templates. Also contains endpoints for creating and deleting Email Template Folders
"""
# Standard Library
import types

# Third Party
import requests
from flask import request
from flask import Blueprint
from flask_restful import Resource

# Application Specific
from email_campaign_service.common.talent_api import TalentApi
from email_campaign_service.common.utils.api_utils import api_route
from email_campaign_service.common.models.user import (User, Permission)
from email_campaign_service.common.utils.handy_functions import get_valid_json_data
from email_campaign_service.common.routes import (EmailCampaignApi, EmailCampaignApiUrl)
from email_campaign_service.common.utils.validators import validate_and_return_immutable_value
from email_campaign_service.common.utils.auth_utils import (require_oauth, require_all_permissions)
from email_campaign_service.common.models.email_campaign import (UserEmailTemplate, EmailTemplateFolder)
from email_campaign_service.common.error_handling import (InvalidUsage, ForbiddenError, ResourceNotFound)

# Blueprint for email-templates API
template_blueprint = Blueprint('email_templates', __name__)
api = TalentApi()
api.init_app(template_blueprint)
api.route = types.MethodType(api_route, api)


@api.route(EmailCampaignApi.TEMPLATES)
class EmailTemplates(Resource):
    """
    Endpoint looks like /v1/email-templates
    """
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CAMPAIGNS)
    def get(self, **kwargs):
        pass

    @require_all_permissions(Permission.PermissionNames.CAN_ADD_CAMPAIGNS)
    def post(self):
        """
        Function will create an email template based on the values provided by user in post data.
        Values required from data are template name, html body of template, template folder id and
        either a 0 or 1 as is_immutable value for the template.

        :return: ID of the created template.
        :rtype: json
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
            raise ForbiddenError(error_message="Email template's folder (id:%d) is not in the user's domain (id:%d)"
                                               % (template_folder.id, template_folder.domain_id))

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
        return {'id': template_id}, requests.codes.CREATED


@api.route(EmailCampaignApi.TEMPLATE)
class EmailTemplate(Resource):
    """
    Endpoint looks like /v1/email-template/:id
    """
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CAMPAIGNS)
    def get(self, template_id):
        """
            GET /v1/email-templates/:id
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

        return {'template': {'body_html': template.body_html, 'id': template_id}}

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CAMPAIGNS)
    def patch(self, template_id):
        """
            PATCH /v1/email-templates/:id
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

        return {'template': {'body_html': body_html, 'id': template_id}}

    @require_all_permissions(Permission.PermissionNames.CAN_DELETE_CAMPAIGNS)
    def delete(self, template_id):

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


@api.route(EmailCampaignApi.TEMPLATE_FOLDERS)
class TemplateFolders(Resource):
    """
    Endpoint looks like /v1/email-template-folders
    """
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_ADD_CAMPAIGNS)
    def post(self):
        """
            POST /v1/email-template-folders
            Create email template folder
            Required parameters:
            name:          Name of email template folder
            parent_id:     Parent ID of email template folder
            is_immutable:  Parameter to determine is the email template folder is mutable or not
            :return:       Template folder id

        .. Status:: 201 (Resource created)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Referenced email-template-folder does not belong to user's domain)
                    404 (Referenced email-template-folder not found)
                    500 (Internal server error)
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
                raise ForbiddenError(error_message='Email Template Folder with (id:%d) does not belong to '
                                                   'domain(id:%d)' % (parent_id, domain_id))

        # If is_immutable value is not passed, make it as 0
        is_immutable = data.get('is_immutable', 0)
        is_immutable = validate_and_return_immutable_value(is_immutable)

        template_folder = EmailTemplateFolder(name=folder_name, domain_id=domain_id, parent_id=parent_id,
                                              is_immutable=is_immutable)
        EmailTemplateFolder.save(template_folder)
        template_folder_id = template_folder.id

        return {'id': template_folder_id}, requests.codes.CREATED


@api.route(EmailCampaignApi.TEMPLATE_FOLDER)
class TemplateFolder(Resource):
    """
    Endpoint looks like /v1/email-template-folders/:id.
    """
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_DELETE_CAMPAIGNS)
    def delete(self, folder_id):
        """
        DELETE /v1/email-template-folders
        Required parameters:
        :param int|long folder_id: ID of of email template
        :return: Response with no content and status 204

        :Example:

        >>> import requests
        >>> headers = {'Authorization': 'Bearer <access_token>'}
        >>> template_folder_id = 1
        >>> response = requests.get(EmailCampaignApiUrl.TEMPLATE_FOLDER % template_folder_id,
        >>>                         headers=headers)

        .. Status:: 204 (Resource deleted)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Requested email-template-folder does not belong to user's domain)
                    404 (Requested email-template-folder not found)
                    500 (Internal server error)
        """
        if not folder_id:
            raise InvalidUsage(error_message='folder_id must be greater than 0')

        user_id = request.user.id
        domain_id = request.user.domain_id
        # Get template-folder object from database
        template_folder = EmailTemplateFolder.get_by_id(folder_id)
        if not template_folder:
            raise ResourceNotFound(error_message='Template folder not found')
        # Verify owned by same domain
        if not template_folder.domain_id == domain_id:
            raise ForbiddenError(error_message="Template folder(id:%d) is not owned by user(id:%d)'s domain(id:%d)"
                                               % (folder_id, user_id, domain_id))
        # Delete the requested template-folder
        EmailTemplateFolder.delete(template_folder)
        return '', requests.codes.NO_CONTENT
