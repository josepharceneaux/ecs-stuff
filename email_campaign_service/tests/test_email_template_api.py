"""Test Email Template API: Contains tests for Email Templates and Email Template Folders endpoints
"""
import time

from email_campaign_service.common.tests.conftest import *
from email_campaign_service.common.routes import EmailCampaignUrl
from email_campaign_service.common.utils.handy_functions import add_role_to_test_user
from email_campaign_service.tests.modules.handy_functions import (request_to_email_template_resource,
                                                                  get_template_folder, create_email_template,
                                                                  update_email_template, add_domain_role,
                                                                  del_domain_roles)


def test_create_email_template_folder(sample_user, user_auth):
    """
    Test for creating new email template folder
    It creates a test folder and asserts that it is created with correct name
    """
    auth_token = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    token = auth_token['access_token']
    domain_id = sample_user.domain_id

    # Add or get Role
    role = "CAN_CREATE_EMAIL_TEMPLATE_FOLDER"
    role_id = add_domain_role(role, domain_id)

    # Add 'CAN_CREATE_EMAIL_TEMPLATE_FOLDER' to sample_user
    add_role_to_test_user(sample_user, [role])

    # Get Template Folder Id
    template_folder_id, template_folder_name = get_template_folder(token)

    # Assert that folder is created with correct name
    db.session.commit()
    folder_row = EmailTemplateFolder.query.filter_by(id=template_folder_id).first()
    assert folder_row.name == template_folder_name
    del_domain_roles(role_id)


def test_delete_email_template_folder(sample_user, sample_user_2, user_auth):
    """
    Test for deleting email template folder
    It creates a test folder by sample_user and deletes that by the sample_user_2 of same domain
    """
    auth_token = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    token1 = auth_token['access_token']
    domain_id = sample_user.domain_id

    # Add or get Role
    role1 = "CAN_CREATE_EMAIL_TEMPLATE_FOLDER"
    role_id1 = add_domain_role(role1, domain_id)

    # Add 'CAN_CREATE_EMAIL_TEMPLATE_FOLDER' to sample_user
    add_role_to_test_user(sample_user, [role1])

    # Get Template Folder Id
    template_folder_id, template_folder_name = get_template_folder(token1)

    # Assert that folder is created with correct name
    db.session.commit()
    folder_row = EmailTemplateFolder.query.filter_by(id=template_folder_id).first()
    assert folder_row.name == template_folder_name

    token2 = auth_token['access_token']
    # Add or get Role
    role = "CAN_DELETE_EMAIL_TEMPLATE_FOLDER"
    role_id2 = add_domain_role(role, domain_id)

    # Add 'CAN_DELETE_EMAIL_TEMPLATE' to sample_user_2
    add_role_to_test_user(sample_user_2, [role])

    data = {'name': template_folder_name, 'id': template_folder_id}
    response = requests.delete(
        url=EmailCampaignUrl.EMAIL_TEMPLATE_FOLDER, data=json.dumps(data),
        headers={'Authorization': 'Bearer %s' % token2,
                 'Content-type': 'application/json'}
    )
    assert response.status_code == 204
    del_domain_roles([role_id1, role_id2])


def test_create_email_template(sample_user, user_auth, email_template_body):
    """
    Test for creating email template
    :param sample_user:         sample user
    :param email_template_body: email template html body
    :return:
    """
    # Add Email template
    email_template = add_email_template(user_auth, sample_user, email_template_body)
    email_template_id = email_template["email_template_id"]
    template_name = email_template["template_name"]

    # Get added template row
    template = db.session.query(UserEmailTemplate).filter_by(id=email_template_id).first()
    # Assert with template_name
    assert template.name == template_name
    assert template.is_immutable == 1


def test_create_email_template_without_name(sample_user, user_auth, email_template_body):
    """
    Test for creating email template without passing name
    :param sample_user:         sample user
    :param email_template_body: email template html body
    result : The response should be Bad Request - 400
    """
    domain_id = sample_user.domain_id
    # Add or get Role
    role = "CAN_CREATE_EMAIL_TEMPLATE"
    role_id = add_domain_role(role, domain_id)

    # Add 'CAN_CREATE_EMAIL_TEMPLATE' to sample_user
    add_role_to_test_user(sample_user, [role])
    # Get access token
    auth_token = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    token = auth_token['access_token']
    domain_id = sample_user.domain_id

    # Get Template Folder Id
    template_folder_id, template_folder_name = get_template_folder(token)

    # Empty template name
    template_name = ''

    resp = create_email_template(token, sample_user.id, template_name, email_template_body, template_name,
                                 is_immutable="1", folder_id=template_folder_id, domain_id=domain_id, role_id=role_id)
    assert resp.status_code == 400
    del_domain_roles(role_id)


def test_create_template_without_email_body(sample_user, user_auth):
    """
    Test for creating email template without passing email body
    :param sample_user:         sample user
    result : The response should be Bad Request - 400
    """
    domain_id = sample_user.domain_id
    # Add or get Role
    role = "CAN_CREATE_EMAIL_TEMPLATE"
    role_id = add_domain_role(role, domain_id)
    # Get access token
    auth_token = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    token = auth_token['access_token']

    # Get Template Folder Id
    template_folder_id, template_folder_name = get_template_folder(token)

    template_name = 'test_email_template%i' % time.time()

    # Pass empty email template body
    resp = create_email_template(token, sample_user.id, template_name, '', template_name,
                                 is_immutable="1", folder_id=template_folder_id, domain_id=domain_id, role_id=role_id)
    assert resp.status_code == 400
    del_domain_roles(role_id)


def test_delete_email_template(sample_user, sample_user_2, email_template_body, user_auth):
    """
    Tests deleting user's email template
    :param sample_user:         user1
    :param sample_user_2:       user2
    :param email_template_body: email template html body
    """
    # Add Email template
    email_template = add_email_template(user_auth, sample_user, email_template_body)
    email_template_id = email_template["email_template_id"]

    token2 = user_auth.get_auth_token(sample_user_2, get_bearer_token=True)['access_token']

    # Add or get Role
    role = "CAN_DELETE_EMAIL_TEMPLATE"
    role_id2 = add_domain_role(role, sample_user_2.domain_id)

    # Add 'CAN_DELETE_EMAIL_TEMPLATE' to sample_user_2
    add_role_to_test_user(sample_user_2, [role])

    resp = request_to_email_template_resource(token2, 'delete', email_template["email_template_id"])
    assert resp.status_code == 204
    template_after_delete = UserEmailTemplate.query.get(email_template_id)
    assert template_after_delete is None
    del_domain_roles(role_id2)


def test_delete_email_template_with_no_id(sample_user, sample_user_2, email_template_body, user_auth):
    """
    Tests deleting user's email template
    :param sample_user:         user1
    :param sample_user_2:       user2
    :param email_template_body: email template html body
    :return:
    """
    # Add Email template
    add_email_template(user_auth, sample_user, email_template_body)

    token2 = user_auth.get_auth_token(sample_user_2, get_bearer_token=True)['access_token']

    # Add or get Role
    role = "CAN_DELETE_EMAIL_TEMPLATE"
    role_id = add_domain_role(role, sample_user_2.domain_id)

    # Add 'CAN_DELETE_EMAIL_TEMPLATE' to sample_user_2
    add_role_to_test_user(sample_user_2, [role])

    resp = request_to_email_template_resource(token2, 'delete', '')
    assert resp.status_code == 400
    del_domain_roles(role_id)


def test_delete_template_with_non_existing_template_id(sample_user, sample_user_2, email_template_body, user_auth):
    """
    Tests deleting user's email template with non existing template_id
    :param sample_user:         user1
    :param sample_user_2:       user2
    :param email_template_body: email template html body
    result : The response should be Not Found - 404
    """
    # Add Email template
    email_template = add_email_template(user_auth, sample_user, email_template_body)
    email_template_id = email_template["email_template_id"]

    token2 = user_auth.get_auth_token(sample_user_2, get_bearer_token=True)['access_token']

    # Add or get Role
    role = "CAN_DELETE_EMAIL_TEMPLATE"
    role_id = add_domain_role(role, sample_user_2.domain_id)

    # Add 'CAN_DELETE_EMAIL_TEMPLATE' to sample_user_2
    add_role_to_test_user(sample_user_2, [role])

    resp = request_to_email_template_resource(token2, 'delete', email_template_id+1)
    assert resp.status_code == 404
    del_domain_roles(role_id)


def test_delete_template_from_different_domain(sample_user, user_from_diff_domain, email_template_body, user_auth):
    """
    Tests deleting user's email template from different domain
    :param sample_user:             user1
    :param user_from_diff_domain:   user2
    :param email_template_body:     email template html body
    result : The response should be Forbidden error - 403
    """
    # Add Email template
    email_template = add_email_template(user_auth, sample_user, email_template_body)
    email_template_id = email_template["email_template_id"]

    token2 = user_auth.get_auth_token(user_from_diff_domain, get_bearer_token=True)['access_token']

    # Add or get Role
    role = "CAN_DELETE_EMAIL_TEMPLATE"
    role_id = add_domain_role(role, user_from_diff_domain.domain_id)

    # Add 'CAN_DELETE_EMAIL_TEMPLATE' to sample_user_2
    add_role_to_test_user(user_from_diff_domain, [role])

    resp = request_to_email_template_resource(token2, 'delete', email_template_id)
    assert resp.status_code == 403
    del_domain_roles(role_id)


def test_get_email_template_via_id(sample_user, sample_user_2, email_template_body, user_auth):
    """
    Test:   Retrieve email_template via template's ID
    Expect: 200
    :type sample_user:    User
    :type user_auth:      UserAuthentication
    """
    # Add Email template
    email_template = add_email_template(user_auth, sample_user, email_template_body)
    email_template_id = email_template["email_template_id"]
    # Get access token for sample_user_2
    token2 = user_auth.get_auth_token(sample_user_2, True)['access_token']

    # Add or get Role
    role = 'CAN_GET_EMAIL_TEMPLATE'
    role_id2 = add_domain_role(role, sample_user_2.domain_id)

    # Add 'CAN_GET_EMAIL_TEMPLATE' to sample_user_2
    add_role_to_test_user(sample_user_2, [role])
    url = EmailCampaignUrl.EMAIL_TEMPLATE + '/' + str(email_template_id)
    # Get email_template via template ID
    response = requests.get(
        url=url, headers={
            'Authorization': 'Bearer %s' % token2, 'Content-type': 'application/json'}
    )
    assert response.status_code == 200
    resp_dict = response.json()['email_template']
    assert isinstance(resp_dict, dict)
    assert resp_dict['id'] == email_template_id
    del_domain_roles(role_id2)


def test_get_email_template_with_non_existing_id(sample_user, sample_user_2, email_template_body, user_auth):
    """
    Test:   Retrieve email_template via template's ID
    Expect: 404 - NOT FOUND
    :type sample_user:    User
    :type user_auth:      UserAuthentication
    """
    # Add Email template
    email_template = add_email_template(user_auth, sample_user, email_template_body)
    email_template_id = email_template["email_template_id"]
    # Get access token for sample_user_2
    token2 = user_auth.get_auth_token(sample_user_2, True)['access_token']

    # Add or get Role
    role = 'CAN_GET_EMAIL_TEMPLATE'
    role_id2 = add_domain_role(role, sample_user_2.domain_id)

    # Add 'CAN_GET_EMAIL_TEMPLATE' to sample_user_2
    add_role_to_test_user(sample_user_2, [role])

    url = EmailCampaignUrl.EMAIL_TEMPLATE + '/' + str(email_template_id) + '1'
    # Get email_template via template ID
    response = requests.get(
        url=url, headers={
            'Authorization': 'Bearer %s' % token2, 'Content-type': 'application/json'}
    )
    assert response.status_code == 404
    del_domain_roles(role_id2)


def test_update_email_template(sample_user, sample_user_2, email_template_body, user_auth):
    """
    Test :To update email template by other user in the same domain
    Expect: 200
    """
    # Add Email template
    email_template = add_email_template(user_auth, sample_user, email_template_body)
    # Get access token for sample_user_2
    token2 = user_auth.get_auth_token(sample_user_2, True)['access_token']
    # Add or get Role
    role = 'CAN_UPDATE_EMAIL_TEMPLATE'
    role_id2 = add_domain_role(role, sample_user_2.domain_id)
    # Add 'CAN_UPDATE_EMAIL_TEMPLATE' to sample_user_2
    add_role_to_test_user(sample_user_2, [role])

    updated_email_template_body = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" ' \
                                  '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\r\n<html>\r\n<head>' \
                                  '\r\n\t<title></title>\r\n</head>\r\n<body>\r\n<p>test for update campaign mail' \
                                  ' testing through script</p>\r\n</body>\r\n</html>\r\n'

    # Get email_template via template ID
    resp = update_email_template(email_template["email_template_id"], 'put', token2, sample_user_2.id,
                                 email_template["template_name"],
                                 updated_email_template_body, email_template["template_folder_id"],
                                 email_template["domain_id"])
    db.session.commit()
    assert resp.status_code == 200
    resp_dict = resp.json()['email_template']
    print resp_dict
    assert resp_dict['email_body_html'] == updated_email_template_body
    del_domain_roles(role_id2)


def test_update_non_existing_email_template(sample_user, sample_user_2, email_template_body, user_auth):
    """
    Test : To update email template by other user in the same domain
    Expect: 404 - NOT FOUND
    """
    # Add Email template
    email_template = add_email_template(user_auth, sample_user, email_template_body)
    email_template_id = email_template["email_template_id"]
    # Get access token for sample_user_2
    token2 = user_auth.get_auth_token(sample_user_2, True)['access_token']
    # Add or get Role
    role = 'CAN_UPDATE_EMAIL_TEMPLATE'
    role_id2 = add_domain_role(role, sample_user_2.domain_id)
    # Add 'CAN_UPDATE_EMAIL_TEMPLATE' to sample_user_2
    add_role_to_test_user(sample_user_2, [role])

    updated_email_template_body = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" ' \
                                  '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">' \
                                  '\r\n<html>\r\n<head>\r\n\t<title></title>\r\n</head>\r\n<body>' \
                                  '\r\n<p>test for update campaign mail testing through script</p>\r\n<' \
                                  '/body>\r\n</html>\r\n'

    # Get email_template via template ID
    resp = update_email_template(email_template_id+1, 'put', token2, sample_user_2.id,
                                 email_template["template_name"],
                                 updated_email_template_body, email_template["template_folder_id"],
                                 email_template["domain_id"])
    db.session.commit()
    assert resp.status_code == 404
    del_domain_roles(role_id2)


def add_email_template(user_auth, template_owner, email_template_body):
    """
    This function will create email template
    """
    # Get access token
    auth_token = user_auth.get_auth_token(template_owner, get_bearer_token=True)
    token = auth_token['access_token']
    domain_id = template_owner.domain_id
    # Add or get Role
    role = "CAN_CREATE_EMAIL_TEMPLATE"
    role_id = add_domain_role(role, domain_id)

    # Add 'CAN_CREATE_EMAIL_TEMPLATE' to sample_user
    add_role_to_test_user(template_owner, [role])

    # Get Template Folder Id
    template_folder_id, template_folder_name = get_template_folder(token)

    template_name = 'test_email_template%i' % time.time()

    resp = create_email_template(token, template_owner.id, template_name, email_template_body, '', is_immutable="1",
                                 folder_id=template_folder_id, domain_id=domain_id, role_id=role_id)
    db.session.commit()
    resp_obj = resp.json()
    resp_dict = resp_obj['template_id'][0]
    del_domain_roles(role_id)

    return {"email_template_id": resp_dict['id'],
            "template_folder_id": template_folder_id,
            "template_folder_name": template_folder_name,
            "template_name": template_name,
            "domain_id": domain_id}
