"""Email Templates API: Provides the endpoints to create, retrieve, update and delete
Email Templates. Also contains endpoints for creating and deleting Email Template Folders
"""
# Standard Library
import types

# Third Party
import requests
from flask import request
from requests import codes
from flask import Blueprint
from flask_restful import Resource

# Application Specific
from email_campaign_service.common.talent_api import TalentApi
from email_campaign_service.common.models.user import Permission
from email_campaign_service.common.error_handling import InvalidUsage
from email_campaign_service.modules.validations import (get_valid_template_folder,
                                                        get_valid_email_template)
from email_campaign_service.common.utils.handy_functions import get_valid_json_data
from email_campaign_service.common.routes import (EmailCampaignApi, EmailCampaignApiUrl)
from email_campaign_service.common.utils.api_utils import (api_route, get_paginated_response,
                                                           get_pagination_params)
from email_campaign_service.common.utils.validators import validate_and_return_immutable_value
from email_campaign_service.common.utils.auth_utils import (require_oauth, require_all_permissions)
from email_campaign_service.common.models.email_campaign import (UserEmailTemplate, EmailTemplateFolder)

# Blueprint for email-templates API
template_blueprint = Blueprint('email_templates', __name__)
api = TalentApi()
api.init_app(template_blueprint)
api.route = types.MethodType(api_route, api)


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

        .. Request Body::

                            {
                                "name": "My Template Folder",
                                "is_immutable": 1
                                "parent_id": 12
                            }
        .. Response::
                           {
                              "id": 347
                           }

        .. Status:: 201 (Resource created)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Referenced email-template-folder does not belong to user's domain)
                    404 (Referenced email-template-folder not found)
                    500 (Internal server error)
        """
        # TODO: Add JSON schema validation
        data = get_valid_json_data(request)
        folder_name = data.get('name')
        if not folder_name:
            raise InvalidUsage('Folder name must be provided.')
        if not isinstance(folder_name, basestring):
            raise InvalidUsage('Invalid input: Folder name must be a valid string.')
        domain_id = request.user.domain_id
        # Check if the name already exists under same domain
        duplicate = EmailTemplateFolder.get_by_name_and_domain_id(folder_name, domain_id)
        if duplicate:
            raise InvalidUsage('Template folder with name=%s already exists' % folder_name)
        parent_id = data.get('parent_id')
        if parent_id:
            # Validate parent_id is valid
            get_valid_template_folder(parent_id, request)
        # If is_immutable value is not passed, make it as 0
        is_immutable = data.get('is_immutable', 0)
        is_immutable = validate_and_return_immutable_value(is_immutable)
        # Create EmailTemplateFolder object
        template_folder = EmailTemplateFolder(name=folder_name, domain_id=domain_id, parent_id=parent_id,
                                              is_immutable=is_immutable)
        EmailTemplateFolder.save(template_folder)
        return {'id': template_folder.id}, requests.codes.CREATED


@api.route(EmailCampaignApi.TEMPLATE_FOLDER)
class TemplateFolder(Resource):
    """
    Endpoint looks like /v1/email-template-folders/:id.
    """
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CAMPAIGNS)
    def get(self, folder_id):
        """
        GET /v1/email-template-folders/:id
        Required parameters:
        :param int|long folder_id: ID of of email template
        :return: template-folder object in dict format, status 200

        :Example:

        >>> import requests
        >>> headers = {'Authorization': 'Bearer <access_token>'}
        >>> template_folder_id = 1
        >>> response = requests.get(EmailCampaignApiUrl.TEMPLATE_FOLDER % template_folder_id,
        >>>                         headers=headers)

        ..Response::

                {
                     "email_template_folder":
                                {
                                    "name": "My Template Folder",
                                    "is_immutable": 1,
                                    "id": 8,
                                    "parent_id": "",
                                    "updated_time": "2016-08-23 18:04:45",
                                    "domain_id": 1
                                }
                }

        .. Status:: 200 (Resource found)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Requested email-template-folder does not belong to user's domain)
                    404 (Requested email-template-folder not found)
                    500 (Internal server error)
        """
        template_folder = get_valid_template_folder(folder_id, request)
        return {"email_template_folder": template_folder.to_json()}, codes.OK

    @require_all_permissions(Permission.PermissionNames.CAN_DELETE_CAMPAIGNS)
    def delete(self, folder_id):
        """
        DELETE /v1/email-template-folders/:id
        Required parameters:
        :param int|long folder_id: ID of of email template
        :return: Response with no content and status 204

        :Example:

        >>> import requests
        >>> headers = {'Authorization': 'Bearer <access_token>'}
        >>> template_folder_id = 1
        >>> response = requests.delete(EmailCampaignApiUrl.TEMPLATE_FOLDER % template_folder_id,
        >>>                         headers=headers)

        .. Status:: 204 (Resource deleted)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Requested email-template-folder does not belong to user's domain)
                    404 (Requested email-template-folder not found)
                    500 (Internal server error)
        """
        template_folder = get_valid_template_folder(folder_id, request)
        # Delete the requested template-folder
        EmailTemplateFolder.delete(template_folder)
        return '', codes.NO_CONTENT


@api.route(EmailCampaignApi.TEMPLATES)
class EmailTemplates(Resource):
    """
    Endpoint looks like /v1/email-templates
    """
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CAMPAIGNS)
    def get(self):
        """
        This resource will return all the email-templates in logged-in user's domain

        .. Response::

            {
                "email_templates":
                                [
                                    {
                                          "user_id": 1,
                                          "name": "My Template",
                                          "body_text": "This is the text part of the email",
                                          "template_folder_id": 8,
                                          "updated_datetime": "2016-09-05 15:11:22",
                                          "body_html": "<html><body>Email Body</body></html>",
                                          "is_immutable": 1,
                                          "type": 0,
                                          "id": 41
                                    },
                                    {
                                              "user_id": 1,
                                              "name": "My Template 2",
                                              "body_text": "This is the text part of the email",
                                              "template_folder_id": 12,
                                              "updated_datetime": "2016-09-05 15:11:22",
                                              "body_html": "<html><body>Email Body</body></html>",
                                              "is_immutable": 0,
                                              "type": 0,
                                              "id": 234
                                    }
                                ]
            }

        .. Status:: 200 (OK)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    500 (Internal server error)
        """
        page, per_page = get_pagination_params(request)
        domain_id = request.user.domain_id
        # Get all email campaigns from logged in user's domain
        query = UserEmailTemplate.get_by_domain_id(domain_id)
        return get_paginated_response('email_templates', query, page, per_page)

    @require_all_permissions(Permission.PermissionNames.CAN_ADD_CAMPAIGNS)
    def post(self):
        """
        Function will create an email template based on the values provided by user in post data.
        Values required from data are template name, html body of template, template folder id and
        either a 0 or 1 as is_immutable value for the template.

        :return: ID of the created template.
        :rtype: json

        .. Request Body::
                        {
                            "type": 0,
                            "name": "My Template",
                            "body_html": "<html><body>Email Body</body></html>",
                            "body_text": "This is the text part of the email",
                            "template_folder_id":8,
                            "is_immutable": 1
                        }

        .. Response::
                       {
                          "id": 347
                       }

        .. Status:: 201 (Resource created)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Requested email-template-folder does not belong to user's domain)
                    404 (Requested email-template-folder not found)
                    500 (Internal server error)
        """
        # TODO: Add JSON schema validation
        data = get_valid_json_data(request)
        template_name = data.get('name')
        if not template_name:
            raise InvalidUsage('Template name is empty')
        template_html_body = data.get('body_html')
        if not template_html_body:
            raise InvalidUsage('Email HTML body is empty')
        # Check if the name is already exists in the domain
        existing_template = UserEmailTemplate.get_by_name(template_name)
        if existing_template:
            raise InvalidUsage('Email template with name=%s already exists' % template_name)
        template_folder_id = data.get('template_folder_id')
        if template_folder_id:
            # Validate parent_id is valid
            get_valid_template_folder(template_folder_id, request)
        # If is_immutable value is not passed, make it as 0
        is_immutable = data.get('is_immutable', 0)
        is_immutable = validate_and_return_immutable_value(is_immutable)
        # Create UserEmailTemplate object
        template = UserEmailTemplate(user_id=request.user.id, type=0,
                                     name=template_name, body_html=template_html_body,
                                     body_text=data.get('body_text'),
                                     template_folder_id=template_folder_id if
                                     template_folder_id else None,
                                     is_immutable=is_immutable)
        UserEmailTemplate.save(template)
        return {'id': template.id}, requests.codes.CREATED


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

    .. Response::

                {
                      "template": {
                            "user_id": 1,
                            "name": "test_email_template850323",
                            "body_text": "",
                            "template_folder_id": 23,
                            "updated_datetime": "2016-09-06 18:14:42",
                            "body_html": "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Transitional//EN\"
                                            \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd\">\r\n<html>
                                            \r\n<head>\r\n\t<title></title>\r\n</head>\r\n<body>\r\n<p>test campaign
                                            mail testing through script</p>\r\n</body>\r\n</html>\r\n",
                            "is_immutable": 1,
                            "type": 0,
                            "id": 3
                      }
                }

        .. Status:: 200 (Resource found)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Requested email-template does not belong to user's domain)
                    404 (Requested email-template not found)
                    500 (Internal server error)
        """
        # Validate email template id
        template = get_valid_email_template(template_id, request)
        return {'template': template.to_json()}, codes.OK

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CAMPAIGNS)
    def patch(self, template_id):
        """
            PATCH /v1/email-templates/:id
            Function would update existing email template
            Required parameters:
            :param template_id: ID of of email template
            :return: Updated email template

    .. Response::

                {
                      "template": {
                            "user_id": 1,
                            "name": "test_email_template850323",
                            "body_text": "",
                            "template_folder_id": 23,
                            "updated_datetime": "2016-09-06 18:14:42",
                            "body_html": "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Transitional//EN\"
                                            \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd\">\r\n<html>
                                            \r\n<head>\r\n\t<title></title>\r\n</head>\r\n<body>\r\n<p>test campaign
                                            mail testing through script</p>\r\n</body>\r\n</html>\r\n",
                            "is_immutable": 1,
                            "type": 0,
                            "id": 3
                      }
                }


        .. Status:: 200 (Resource updated)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Requested email-template does not belong to user's domain)
                    404 (Requested email-template not found)
                    500 (Internal server error)
        """
        template = get_valid_email_template(template_id, request)
        data = get_valid_json_data(request)
        updated_data = {'body_html': data.get('body_html') or template.body_html,
                        'body_text': data.get('body_text') or template.body_text}
        template.update(**updated_data)
        return {'template': template.to_json()}, codes.OK

    @require_all_permissions(Permission.PermissionNames.CAN_DELETE_CAMPAIGNS)
    def delete(self, template_id):
        """
        This deletes the requested email-template.
        :param int|long template_id: Id of email-template

        .. Status:: 204 (Resource deleted)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Requested email-template does not belong to user's domain)
                    404 (Requested email-template not found)
                    500 (Internal server error)
        """
        template = get_valid_email_template(template_id, request)
        # Delete the template
        UserEmailTemplate.delete(template)
        return '', requests.codes.NO_CONTENT
