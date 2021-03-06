"""Email Templates API: Provides the endpoints to create, retrieve, update and delete
Email Templates. Also contains endpoints for creating and deleting Email Template Folders
"""
# Standard Library
import types

# Third Party
from flask import request
from requests import codes
from flask import Blueprint
from flask_restful import Resource

# Application Specific
from email_campaign_service.common.talent_api import TalentApi
from email_campaign_service.common.models.user import Permission
from email_campaign_service.common.utils.handy_functions import (get_valid_json_data)
from email_campaign_service.common.routes import (EmailCampaignApi, EmailCampaignApiUrl)
from email_campaign_service.common.utils.api_utils import (api_route, get_paginated_response,
                                                           get_pagination_params)
from email_campaign_service.common.utils.auth_utils import (require_oauth, require_all_permissions)
from email_campaign_service.common.models.email_campaign import (UserEmailTemplate, EmailTemplateFolder)
from email_campaign_service.modules.validators import (validate_domain_id_for_email_templates,
                                                       validate_and_format_data_for_template_folder_creation,
                                                       validate_and_format_data_for_email_template_creation)
from email_campaign_service.common.custom_errors.campaign import (INVALID_REQUEST_BODY,
                                                                  INVALID_VALUE_OF_PAGINATION_PARAM)

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
    decorators = [validate_domain_id_for_email_templates(), require_oauth()]

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
        # TODO: Add JSON schema validation, GET-2559
        data = get_valid_json_data(request, error_code=INVALID_REQUEST_BODY[1])
        domain_id = request.user.domain_id
        folder_data = validate_and_format_data_for_template_folder_creation(data, domain_id)
        # Create EmailTemplateFolder object
        template_folder = EmailTemplateFolder(name=folder_data['name'],
                                              domain_id=domain_id,
                                              parent_id=folder_data['parent_id'],
                                              is_immutable=folder_data['is_immutable'])
        EmailTemplateFolder.save(template_folder)
        return {'id': template_folder.id}, codes.CREATED

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CAMPAIGNS)
    def get(self):
        """
            GET /v1/email-template-folders
            Returns all email-template folders in a user's domain
                {
                      "template_folders": [
                        {
                          "name": "My Template Folder",
                          "updated_datetime": "2016-08-23 18:04:45",
                          "is_immutable": 1,
                          "id": 8,
                          "parent_id": "",
                          "domain_id": 1
                        },
                        {
                          "name": "My Template123456",
                          "updated_datetime": "2016-09-06 15:03:51",
                          "is_immutable": 1,
                          "id": 347,
                          "parent_id": "",
                          "domain_id": 1
                        }
                     ]
                    }
        """
        domain_id = request.user.domain_id
        template_folders = EmailTemplateFolder.filter_by_keywords(domain_id=domain_id)
        return {"template_folders": [template_folder.to_json() for template_folder in template_folders]}, codes.OK


@api.route(EmailCampaignApi.TEMPLATE_FOLDER)
class TemplateFolder(Resource):
    """
    Endpoint looks like /v1/email-template-folders/:id.
    """
    decorators = [validate_domain_id_for_email_templates(), require_oauth()]

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
        template_folder = EmailTemplateFolder.get_valid_template_folder(folder_id, request.user.domain_id)
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
        template_folder = EmailTemplateFolder.get_valid_template_folder(folder_id, request.user.domain_id)
        # Delete the requested template-folder
        EmailTemplateFolder.delete(template_folder)
        return '', codes.NO_CONTENT


@api.route(EmailCampaignApi.TEMPLATES_IN_FOLDER)
class TemplatesInFolder(Resource):
    """
    Endpoint looks like /v1/email-template-folders/:id/email-templates.
    """
    decorators = [validate_domain_id_for_email_templates(), require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CAMPAIGNS)
    def get(self, folder_id):
        """
        GET /v1/email-template-folders/:id/email-templates
        Required parameters:
        :param int|long folder_id: ID of of email template
        :return: template-folder object in dict format, status 200

        :Example:

        >>> import requests
        >>> headers = {'Authorization': 'Bearer <access_token>'}
        >>> template_folder_id = 1
        >>> response = requests.get(EmailCampaignApiUrl.TEMPLATES_IN_FOLDER % template_folder_id,
        >>>                         headers=headers)

        ..Response::

                {
                  "email_templates": [
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
                    }
                  ]
                }
        .. Status:: 200 (Resource found)
                    401 (Unauthorized to access getTalent)
                    403 (Requested email-template-folder does not belong to user's domain)
                    404 (Requested email-template-folder not found)
                    500 (Internal server error)
        """
        template_folder = EmailTemplateFolder.get_valid_template_folder(folder_id, request.user.domain_id)
        return {"email_templates": [template.to_json() for template in template_folder.user_email_template]}, codes.OK


@api.route(EmailCampaignApi.TEMPLATES)
class EmailTemplates(Resource):
    """
    Endpoint looks like /v1/email-templates
    """
    decorators = [validate_domain_id_for_email_templates(), require_oauth()]

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
        page, per_page = get_pagination_params(request, error_code=INVALID_VALUE_OF_PAGINATION_PARAM[1])
        domain_id = request.user.domain_id
        # Get all email campaigns from logged in user's domain
        query = UserEmailTemplate.query_by_domain_id(domain_id)
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
        # TODO: Add JSON schema validation, GET-2559
        data = get_valid_json_data(request, error_code=INVALID_REQUEST_BODY[1])
        domain_id = request.user.domain_id
        template_data = validate_and_format_data_for_email_template_creation(data, domain_id)

        # Create UserEmailTemplate object
        template = UserEmailTemplate(user_id=request.user.id, type=0,
                                     name=template_data['name'],
                                     body_html=template_data['body_html'],
                                     body_text=template_data['body_text'],
                                     template_folder_id=template_data['template_folder_id'],
                                     is_immutable=template_data['is_immutable'])
        UserEmailTemplate.save(template)
        return {'id': template.id}, codes.CREATED


@api.route(EmailCampaignApi.TEMPLATE)
class EmailTemplate(Resource):
    """
    Endpoint looks like /v1/email-template/:id
    """
    decorators = [validate_domain_id_for_email_templates(), require_oauth()]

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
        template = UserEmailTemplate.get_valid_email_template(template_id, request.user)
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
        template = UserEmailTemplate.get_valid_email_template(template_id, request.user)
        data = get_valid_json_data(request, INVALID_REQUEST_BODY[1])
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
        template = UserEmailTemplate.get_valid_email_template(template_id, request.user)
        # Delete the template
        UserEmailTemplate.delete(template)
        return '', codes.NO_CONTENT
