"""Test Email Template API: Contains tests for Email Templates and Email Template Folders endpoints
"""
import json
import datetime
import requests

from email_campaign_service.common.models.user import DomainRole
from email_campaign_service.common.routes import EmailCampaignUrl
from email_campaign_service.common.utils.handy_functions import add_role_to_test_user
from email_campaign_service.common.models.email_campaign import (EmailTemplateFolder, UserEmailTemplate)
from email_campaign_service.tests.modules.handy_functions import (request_to_email_template_resource, template_body,
                                                                  get_template_folder, create_email_template,
                                                                  update_email_template, add_email_template)

ON = 1  # Global variable for comparing value of is_immutable in the functions to avoid hard-coding 1


def test_create_email_template_folder(user_first, access_token_first):
    """
    Test for creating new email template folder
    It creates a test folder and asserts that it is created with correct name.
    :param user_first: we would use this to create the template.
    :param access_token_first: For user authorization
    """
    # Add or get Role
    role = DomainRole.Roles.CAN_CREATE_EMAIL_TEMPLATE_FOLDER

    # Add 'CAN_CREATE_EMAIL_TEMPLATE_FOLDER' to user_first
    add_role_to_test_user(user_first, [role])

    # Get Template Folder Id
    template_folder_id, template_folder_name = get_template_folder(access_token_first)

    # Assert that folder is created with correct name
    folder_row = EmailTemplateFolder.get_by_id(template_folder_id)
    assert folder_row.name == template_folder_name


def test_delete_email_template_folder(user_first, user_same_domain, access_token_first, access_token_same):
    """
    Test for deleting email template folder.
    It creates a test folder by user_first and deletes that by the user_same_domain of same domain.
    This verifies that the users of the same domain having appropriate privileges are able to delete
    email template folders created by users of same domain. Deletion should be successful and
    a response of 204 (NO_CONTENT) must be returned.

    :param user_first: we would use this to create the template folder.
    :param user_same_domain: This is the user from same domain as user_first and would be used to delete the folder.
    :param access_token_first: For user_first authorization
    :param access_token_same: For user_same_domain authorization
    """

    # Add or get Role
    role1 = DomainRole.Roles.CAN_CREATE_EMAIL_TEMPLATE_FOLDER

    # Add 'CAN_CREATE_EMAIL_TEMPLATE_FOLDER' to user_first
    add_role_to_test_user(user_first, [role1])

    # Get Template Folder Id
    template_folder_id, template_folder_name = get_template_folder(access_token_first)

    # Assert that folder is created with correct name
    folder_row = EmailTemplateFolder.get_by_id(template_folder_id)
    assert folder_row.name == template_folder_name

    # Add or get Role
    role = DomainRole.Roles.CAN_DELETE_EMAIL_TEMPLATE_FOLDER

    # Add 'CAN_DELETE_EMAIL_TEMPLATE' to user_same_domain
    add_role_to_test_user(user_same_domain, [role])

    data = {'name': template_folder_name}
    response = requests.delete(
            url=EmailCampaignUrl.TEMPLATES_FOLDER + '/' + str(template_folder_id), data=json.dumps(data),
            headers={'Authorization': 'Bearer %s' % access_token_same,
                     'Content-type': 'application/json'}
    )
    assert response.status_code == requests.codes.NO_CONTENT


def test_create_email_template(user_first, access_token_first):
    """
    Test for creating email template
    :param access_token_first: For user authentication
    :param user_first: sample user
    """
    # Add Email template
    template = add_email_template(access_token_first, user_first, template_body())
    template_id = template['template_id']
    template_name = template['template_name']
    # Get added template row
    template = UserEmailTemplate.get_by_id(template_id)
    # Assert with template_name
    assert template.name == template_name
    assert template.is_immutable == ON


def test_create_email_template_without_name(user_first, access_token_first):
    """
    Test for creating email template without passing name. The response should be Bad Request - 400
    because we are requesting to create an email template without passing the appropriate
    value for template name.
    :param user_first: sample user
    :param access_token_first: For user authentication
    """
    # Add or get Role
    role = DomainRole.Roles.CAN_CREATE_EMAIL_TEMPLATE

    # Add 'CAN_CREATE_EMAIL_TEMPLATE' to user_first
    add_role_to_test_user(user_first, [role])
    role = DomainRole.Roles.CAN_CREATE_EMAIL_TEMPLATE_FOLDER

    # Add 'CAN_CREATE_EMAIL_TEMPLATE_FOLDER' to user_first
    add_role_to_test_user(user_first, [role])
    # Get Template Folder Id
    template_folder_id, template_folder_name = get_template_folder(access_token_first)

    # Empty template name
    template_name = ''

    resp = create_email_template(access_token_first, user_first.id, template_name, template_body(), template_name,
                                 is_immutable=ON, folder_id=template_folder_id)
    assert resp.status_code == requests.codes.BAD_REQUEST


def test_create_template_without_email_body(user_first, access_token_first):
    """
    Test for creating email template without passing email body. The response should be Bad Request - 400
    because template_body is mandatory for creating an email template.

    :param user_first: sample user
    :param access_token_first: For user authentication
    """
    # Add or get Role
    role = DomainRole.Roles.CAN_CREATE_EMAIL_TEMPLATE
    add_role_to_test_user(user_first, [role])
    role = DomainRole.Roles.CAN_CREATE_EMAIL_TEMPLATE_FOLDER

    # Add 'CAN_CREATE_EMAIL_TEMPLATE_FOLDER' to user_first
    add_role_to_test_user(user_first, [role])

    # Get Template Folder Id
    template_folder_id, template_folder_name = get_template_folder(access_token_first)

    template_name = 'test_email_template%i' % datetime.datetime.now().microsecond

    # Pass empty email template body
    resp = create_email_template(access_token_first, user_first.id, template_name, '',  # empty template body
                                 template_name, is_immutable=ON, folder_id=template_folder_id)
    assert resp.status_code == requests.codes.BAD_REQUEST


def test_delete_email_template(user_first, user_same_domain, access_token_first, access_token_same):
    """
    Tests deleting user's email template. Template should be deleted successfully returning
    204 (NO CONTENT) response.

    :param user_first: user1
    :param user_same_domain: user2
    :param access_token_first: For user_first authorization
    :param access_token_same: For user_same_domain authorization
    """
    # Add Email template
    template = add_email_template(access_token_first, user_first, template_body())
    template_id = template['template_id']

    # Add or get Role
    role = DomainRole.Roles.CAN_DELETE_EMAIL_TEMPLATE

    # Add 'CAN_DELETE_EMAIL_TEMPLATE' to user_same_domain
    add_role_to_test_user(user_same_domain, [role])

    resp = request_to_email_template_resource(access_token_same, 'delete', template['template_id'])
    assert resp.status_code == requests.codes.NO_CONTENT
    template_after_delete = UserEmailTemplate.get_by_id(template_id)
    assert template_after_delete is None


def test_delete_template_with_non_existing_template_id(user_first, user_same_domain, access_token_first,
                                                       access_token_same):
    """
    Tests deleting user's email template with non existing template_id. The response should be Not Found - 404
    as we are trying to delete a template which does not exist.

    :param user_first: we would use this to create the template.
    :param user_same_domain: This is the user from same domain as user_first and would be used to delete the template.
    :param access_token_first: For user authorization
    :param access_token_same: For user_same_domain authorization
    """
    # Add Email template
    template = add_email_template(access_token_first, user_first, template_body())
    template_id = template['template_id']

    # Add or get Role
    role = DomainRole.Roles.CAN_DELETE_EMAIL_TEMPLATE

    # Add 'CAN_DELETE_EMAIL_TEMPLATE' to user_same_domain
    add_role_to_test_user(user_same_domain, [role])

    resp = request_to_email_template_resource(access_token_same, 'delete', str(template_id) +
                                              str(datetime.datetime.now().microsecond))
    assert resp.status_code == requests.codes.NOT_FOUND


def test_delete_template_from_different_domain(user_first, user_from_diff_domain, access_token_first,
                                               access_token_other):
    """
    Tests deleting user's email template from different domain. The response should be Forbidden error - 403
    as a user with a different domain than template owner user is not allowed to delete the email template.

    :param access_token_first: For user authorization
    :param user_first: user whose token will be used to create the template.
    :param user_from_diff_domain: user2 with a different domain from user_first. We will try
                                  to delete the template using the token for user2.
    :param access_token_other: For user_from_diff_domain authorization
    """
    # Add Email template
    template = add_email_template(access_token_first, user_first, template_body())
    template_id = template['template_id']

    # Add or get Role
    role = DomainRole.Roles.CAN_DELETE_EMAIL_TEMPLATE

    # Add 'CAN_DELETE_EMAIL_TEMPLATE' to user_same_domain
    add_role_to_test_user(user_from_diff_domain, [role])

    resp = request_to_email_template_resource(access_token_other, 'delete', template_id)
    assert resp.status_code == requests.codes.FORBIDDEN


def test_get_email_template_via_id(user_first, user_same_domain, access_token_first, access_token_same):
    """
    Retrieve email_template via template's ID. We will create the email template using user_first
    and try to retrieve it using the template id returned in the response. user_same_domain with the same domain
    as the creator would be used to get the email template via id, verifying the users with same domain are
    allowed to access the templates created by fellow domain users. Response should be 200 (OK).

    :param user_first: we would use this to create the template.
    :param user_same_domain: This is the user from same domain as user_first and would be used to retrieve the template.
    :param access_token_first: For user_first authorization
    :param access_token_same: For user_same_domain authorization
    """

    # Add Email template
    template = add_email_template(access_token_first, user_first, template_body())
    template_id = template['template_id']
    # Get access token for user_same_domain
    # Add or get Role
    role = DomainRole.Roles.CAN_GET_EMAIL_TEMPLATE

    # Add 'CAN_GET_EMAIL_TEMPLATE' to user_same_domain
    add_role_to_test_user(user_same_domain, [role])
    url = EmailCampaignUrl.TEMPLATES + '/' + str(template_id)
    # Get email_template via template ID using token for 2nd user
    response = requests.get(
            url=url, headers={
                'Authorization': 'Bearer %s' % access_token_same, 'Content-type': 'application/json'}
    )
    assert response.status_code == requests.codes.OK
    resp_dict = response.json()['template']
    assert isinstance(resp_dict, dict)
    assert resp_dict['id'] == template_id


def test_get_email_template_with_non_existing_id(user_first, user_same_domain, access_token_first, access_token_same):
    """
    Retrieve email_template via ID for which email template doesn't exist.We will create the email
    template using user_first and try to retrieve it by appending some random value to the template id returned
    in the response. user_same_domain with the same domain as the creator would be used to get the email template via id,
    as users with same domain are allowed to access the templates created by fellow domain users.
    Response should be 400 (NOT FOUND) as template id we are using to get is non-existent.

    :param user_first: we would use this to create the template.
    :param user_same_domain: This is the user from same domain as user_first and would be used to retrieve the template.
    :param access_token_first: For user authorization
    """
    # Add Email template
    template = add_email_template(access_token_first, user_first, template_body())
    template_id = template['template_id']

    # Add or get Role
    role = DomainRole.Roles.CAN_GET_EMAIL_TEMPLATE

    # Add 'CAN_GET_EMAIL_TEMPLATE' to user_same_domain
    add_role_to_test_user(user_same_domain, [role])

    url = EmailCampaignUrl.TEMPLATES + '/' + str(template_id) + str(datetime.datetime.now().microsecond)
    # Get email_template via template ID
    response = requests.get(
            url=url, headers={
                'Authorization': 'Bearer %s' % access_token_same, 'Content-type': 'application/json'}
    )
    assert response.status_code == requests.codes.NOT_FOUND


def test_update_email_template(user_first, user_same_domain, access_token_first, access_token_same):
    """
    To update email template by other user in the same domain
    Response should be 200 (OK)
    :param user_first: we would use this to create the template.
    :param user_same_domain: This is the user from same domain as user_first and would be used to update the template.
    :param access_token_first: For user_first authorization
    :param access_token_same: For user_same_domain authorization
    """
    # Add Email template
    template = add_email_template(access_token_first, user_first, template_body())
    # Add or get Role
    role = DomainRole.Roles.CAN_UPDATE_EMAIL_TEMPLATE
    # Add 'CAN_UPDATE_EMAIL_TEMPLATE' to user_same_domain
    add_role_to_test_user(user_same_domain, [role])

    updated_template_body = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" ' \
                            '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\r\n<html>\r\n<head>' \
                            '\r\n\t<title></title>\r\n</head>\r\n<body>\r\n<p>test for update campaign mail' \
                            ' testing through script</p>\r\n</body>\r\n</html>\r\n'

    # Get email_template via template ID
    resp = update_email_template(template['template_id'], 'patch', access_token_same, user_same_domain.id,
                                 template['template_name'],
                                 updated_template_body, template['template_folder_id'],
                                 template['domain_id'])
    assert resp.status_code == requests.codes.OK
    resp_dict = resp.json()['template']
    print resp_dict
    assert resp_dict['body_html'] == updated_template_body


def test_update_non_existing_email_template(user_first, user_same_domain, access_token_first, access_token_same):
    """
    Test : To update email template by other user in the same domain
    :param user_first: we would use this to create the template.
    :param user_same_domain: This is the user from same domain as user_first and would be used to retrieve the template.
    :param access_token_first: For user authorization
    Expect: 404 - NOT FOUND
    """
    # Add Email template
    template = add_email_template(access_token_first, user_first, template_body())
    template_id = template['template_id']
    # Add or get Role
    role = DomainRole.Roles.CAN_UPDATE_EMAIL_TEMPLATE
    # Add 'CAN_UPDATE_EMAIL_TEMPLATE' to user_same_domain
    add_role_to_test_user(user_same_domain, [role])

    updated_template_body = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" ' \
                            '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">' \
                            '\r\n<html>\r\n<head>\r\n\t<title></title>\r\n</head>\r\n<body>' \
                            '\r\n<p>test for update campaign mail testing through script</p>\r\n<' \
                            '/body>\r\n</html>\r\n'

    # Get email_template via template ID
    resp = update_email_template(str(template_id) + str(datetime.datetime.now().microsecond),
                                 'patch', access_token_same, user_same_domain.id,
                                 template['template_name'],
                                 updated_template_body, '', template['template_folder_id'],
                                 template['is_immutable'])
    assert resp.status_code == requests.codes.NOT_FOUND
