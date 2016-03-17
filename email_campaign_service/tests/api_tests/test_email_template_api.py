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


def test_create_email_template_folder(sample_user, user_auth):
    """
    Test for creating new email template folder
    It creates a test folder and asserts that it is created with correct name
    """
    auth_token = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    token = auth_token['access_token']

    # Add or get Role
    role = DomainRole.Roles.CAN_CREATE_EMAIL_TEMPLATE_FOLDER

    # Add 'CAN_CREATE_EMAIL_TEMPLATE_FOLDER' to sample_user
    add_role_to_test_user(sample_user, [role])

    # Get Template Folder Id
    template_folder_id, template_folder_name = get_template_folder(token)

    # Assert that folder is created with correct name
    folder_row = EmailTemplateFolder.get_by_id(template_folder_id)
    assert folder_row.name == template_folder_name


def test_delete_email_template_folder(sample_user, sample_user_2, user_auth):
    """
    Test for deleting email template folder
    It creates a test folder by sample_user and deletes that by the sample_user_2 of same domain
    """
    # TODO; above needs more comment. Why are we deleting with sample_user_2?
    # TODO: What will happen after we try deleting with sample_user_2? Must be answered in the commnet

    auth_token = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    token1 = auth_token['access_token']

    # Add or get Role
    role1 = DomainRole.Roles.CAN_CREATE_EMAIL_TEMPLATE_FOLDER

    # Add 'CAN_CREATE_EMAIL_TEMPLATE_FOLDER' to sample_user
    add_role_to_test_user(sample_user, [role1])

    # Get Template Folder Id
    template_folder_id, template_folder_name = get_template_folder(token1)

    # Assert that folder is created with correct name
    folder_row = EmailTemplateFolder.get_by_id(template_folder_id)
    assert folder_row.name == template_folder_name

    auth_token2 = user_auth.get_auth_token(sample_user_2, get_bearer_token=True)
    token2 = auth_token2['access_token']
    # Add or get Role
    role = DomainRole.Roles.CAN_DELETE_EMAIL_TEMPLATE_FOLDER

    # Add 'CAN_DELETE_EMAIL_TEMPLATE' to sample_user_2
    add_role_to_test_user(sample_user_2, [role])

    data = {'name': template_folder_name}
    response = requests.delete(
            url=EmailCampaignUrl.TEMPLATES_FOLDER + '/' + str(template_folder_id), data=json.dumps(data),
            headers={'Authorization': 'Bearer %s' % token2,
                     'Content-type': 'application/json'}
    )
    assert response.status_code == requests.codes.NO_CONTENT


def test_create_email_template(sample_user, user_auth):
    """
    Test for creating email template
    :param user_auth: For user authentication
    :param sample_user: sample user
    """
    # Add Email template
    template = add_email_template(user_auth, sample_user, template_body())
    template_id = template['template_id']
    template_name = template['template_name']
    # Get added template row
    template = UserEmailTemplate.get_by_id(template_id)
    # Assert with template_name
    assert template.name == template_name
    assert template.is_immutable == ON


def test_create_email_template_without_name(sample_user, user_auth):
    """
    Test for creating email template without passing name
    :param sample_user: sample user
    :param user_auth: For user authentication
    result : The response should be Bad Request - 400
    """
    # TODO; above one also needs a more thorough comment
    # Add or get Role
    role = DomainRole.Roles.CAN_CREATE_EMAIL_TEMPLATE

    # Add 'CAN_CREATE_EMAIL_TEMPLATE' to sample_user
    add_role_to_test_user(sample_user, [role])
    # Get access token
    auth_token = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    token = auth_token['access_token']

    role = DomainRole.Roles.CAN_CREATE_EMAIL_TEMPLATE_FOLDER

    # Add 'CAN_CREATE_EMAIL_TEMPLATE_FOLDER' to sample_user
    add_role_to_test_user(sample_user, [role])
    # Get Template Folder Id
    template_folder_id, template_folder_name = get_template_folder(token)

    # Empty template name
    template_name = ''

    resp = create_email_template(token, sample_user.id, template_name, template_body(), template_name,
                                 is_immutable=ON, folder_id=template_folder_id)
    assert resp.status_code == requests.codes.BAD_REQUEST


def test_create_template_without_email_body(sample_user, user_auth):
    """
    Test for creating email template without passing email body
    :param sample_user: sample user
    :param user_auth: For user authentication
    result: The response should be Bad Request - 400
    """
    # Add or get Role
    role = DomainRole.Roles.CAN_CREATE_EMAIL_TEMPLATE
    add_role_to_test_user(sample_user, [role])
    # Get access token
    auth_token = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    token = auth_token['access_token']

    role = DomainRole.Roles.CAN_CREATE_EMAIL_TEMPLATE_FOLDER

    # Add 'CAN_CREATE_EMAIL_TEMPLATE_FOLDER' to sample_user
    add_role_to_test_user(sample_user, [role])

    # Get Template Folder Id
    template_folder_id, template_folder_name = get_template_folder(token)

    template_name = 'test_email_template%i' % datetime.datetime.now().microsecond

    # TODO--add in the comment which one is the email template body param
    # Pass empty email template body
    resp = create_email_template(token, sample_user.id, template_name, '', template_name,
                                 is_immutable=ON, folder_id=template_folder_id)
    assert resp.status_code == requests.codes.BAD_REQUEST


def test_delete_email_template(sample_user, sample_user_2, user_auth):
    """
    Tests deleting user's email template
    :param sample_user: user1
    :param sample_user_2: user2
    :param user_auth: For user authentication
    result: Template should be deleted successfully returning a no content response
    """
    # Add Email template
    template = add_email_template(user_auth, sample_user, template_body())
    template_id = template['template_id']

    token2 = user_auth.get_auth_token(sample_user_2, get_bearer_token=True)['access_token']

    # Add or get Role
    role = DomainRole.Roles.CAN_DELETE_EMAIL_TEMPLATE

    # Add 'CAN_DELETE_EMAIL_TEMPLATE' to sample_user_2
    add_role_to_test_user(sample_user_2, [role])

    resp = request_to_email_template_resource(token2, 'delete', template['template_id'])
    assert resp.status_code == requests.codes.NO_CONTENT
    template_after_delete = UserEmailTemplate.get_by_id(template_id)
    assert template_after_delete is None


def test_delete_template_with_non_existing_template_id(sample_user, sample_user_2, user_auth):
    """
    Tests deleting user's email template with non existing template_id
    :param user_auth:           For user authorization
    :param sample_user:         user1
    :param sample_user_2:       user2
    result : The response should be Not Found - 404
    """
    # TODO; in all of the comments above is 'result' the Sphinx way of doing the comments
    # Add Email template
    template = add_email_template(user_auth, sample_user, template_body())
    template_id = template['template_id']

    token2 = user_auth.get_auth_token(sample_user_2, get_bearer_token=True)['access_token']

    # Add or get Role
    role = DomainRole.Roles.CAN_DELETE_EMAIL_TEMPLATE

    # Add 'CAN_DELETE_EMAIL_TEMPLATE' to sample_user_2
    add_role_to_test_user(sample_user_2, [role])

    resp = request_to_email_template_resource(token2, 'delete', template_id + 1000)
    assert resp.status_code == requests.codes.NOT_FOUND


def test_delete_template_from_different_domain(sample_user, user_from_diff_domain, user_auth):
    """
    Tests deleting user's email template from different domain
    :param user_auth: For user authentication
    :param sample_user: user1
    :param user_from_diff_domain: user2
    result : The response should be Forbidden error - 403
    """
    # TODO---what makes the deleting from different domain? Is it user_from_diff_domain's token?
    # TODO--kindly shed some light in comments if possible
    # Add Email template
    template = add_email_template(user_auth, sample_user, template_body())
    template_id = template['template_id']

    token2 = user_auth.get_auth_token(user_from_diff_domain, get_bearer_token=True)['access_token']

    # Add or get Role
    role = DomainRole.Roles.CAN_DELETE_EMAIL_TEMPLATE

    # Add 'CAN_DELETE_EMAIL_TEMPLATE' to sample_user_2
    add_role_to_test_user(user_from_diff_domain, [role])

    resp = request_to_email_template_resource(token2, 'delete', template_id)
    assert resp.status_code == requests.codes.FORBIDDEN


def test_get_email_template_via_id(sample_user, sample_user_2, user_auth):
    """
    Test:   Retrieve email_template via template's ID
    Expect: 200 - ok
    """
    # TODO--I am slightly confused. So template is added using sample_user
    # TODO-- but we successfully retrieve it using sample_user_2--how does that work? Comments should explain
    # Add Email template
    template = add_email_template(user_auth, sample_user, template_body())
    template_id = template['template_id']
    # Get access token for sample_user_2
    token2 = user_auth.get_auth_token(sample_user_2, True)['access_token']

    # Add or get Role
    role = DomainRole.Roles.CAN_GET_EMAIL_TEMPLATE

    # Add 'CAN_GET_EMAIL_TEMPLATE' to sample_user_2
    add_role_to_test_user(sample_user_2, [role])
    url = EmailCampaignUrl.TEMPLATES + '/' + str(template_id)
    # Get email_template via template ID
    response = requests.get(
            url=url, headers={
                'Authorization': 'Bearer %s' % token2, 'Content-type': 'application/json'}
    )
    assert response.status_code == requests.codes.OK
    resp_dict = response.json()['template']
    assert isinstance(resp_dict, dict)
    assert resp_dict['id'] == template_id


def test_get_email_template_with_non_existing_id(sample_user, sample_user_2, user_auth):
    """
    Test:   Retrieve email_template via template's ID
    Expect: 404 - NOT FOUND
    """
    # TODO--same comment as above
    # Add Email template
    template = add_email_template(user_auth, sample_user, template_body())
    template_id = template['template_id']
    # Get access token for sample_user_2
    token2 = user_auth.get_auth_token(sample_user_2, True)['access_token']

    # Add or get Role
    role = DomainRole.Roles.CAN_GET_EMAIL_TEMPLATE

    # Add 'CAN_GET_EMAIL_TEMPLATE' to sample_user_2
    add_role_to_test_user(sample_user_2, [role])
    # TODO--now that I am thinking there could be a template with id of 1000 in future, we should generate a random str with
    # timestampe I guess

    url = EmailCampaignUrl.TEMPLATES + '/' + str(template_id) + '1000'
    # Get email_template via template ID
    response = requests.get(
            url=url, headers={
                'Authorization': 'Bearer %s' % token2, 'Content-type': 'application/json'}
    )
    assert response.status_code == requests.codes.NOT_FOUND


def test_update_email_template(sample_user, sample_user_2, user_auth):
    """
    Test :To update email template by other user in the same domain
    Expect: 200 - ok
    """
    # Add Email template
    template = add_email_template(user_auth, sample_user, template_body())
    # Get access token for sample_user_2
    token2 = user_auth.get_auth_token(sample_user_2, True)['access_token']
    # Add or get Role
    role = DomainRole.Roles.CAN_UPDATE_EMAIL_TEMPLATE
    # Add 'CAN_UPDATE_EMAIL_TEMPLATE' to sample_user_2
    add_role_to_test_user(sample_user_2, [role])

    updated_template_body = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" ' \
                            '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\r\n<html>\r\n<head>' \
                            '\r\n\t<title></title>\r\n</head>\r\n<body>\r\n<p>test for update campaign mail' \
                            ' testing through script</p>\r\n</body>\r\n</html>\r\n'

    # Get email_template via template ID
    resp = update_email_template(template['template_id'], 'put', token2, sample_user_2.id,
                                 template['template_name'],
                                 updated_template_body, template['template_folder_id'],
                                 template['domain_id'])
    assert resp.status_code == requests.codes.OK
    resp_dict = resp.json()['template']
    print resp_dict
    assert resp_dict['body_html'] == updated_template_body


def test_update_non_existing_email_template(sample_user, sample_user_2, user_auth):
    """
    Test : To update email template by other user in the same domain
    Expect: 404 - NOT FOUND
    """
    # Add Email template
    template = add_email_template(user_auth, sample_user, template_body())
    template_id = template['template_id']
    # Get access token for sample_user_2
    token2 = user_auth.get_auth_token(sample_user_2, True)['access_token']
    # Add or get Role
    role = DomainRole.Roles.CAN_UPDATE_EMAIL_TEMPLATE
    # Add 'CAN_UPDATE_EMAIL_TEMPLATE' to sample_user_2
    add_role_to_test_user(sample_user_2, [role])

    updated_template_body = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" ' \
                            '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">' \
                            '\r\n<html>\r\n<head>\r\n\t<title></title>\r\n</head>\r\n<body>' \
                            '\r\n<p>test for update campaign mail testing through script</p>\r\n<' \
                            '/body>\r\n</html>\r\n'

    # TODO -- same comment about template_id as above
    # Get email_template via template ID
    resp = update_email_template(template_id + 1000, 'put', token2, sample_user_2.id,
                                 template['template_name'],
                                 updated_template_body, '', template['template_folder_id'],
                                 template['is_immutable'])
    assert resp.status_code == requests.codes.NOT_FOUND
