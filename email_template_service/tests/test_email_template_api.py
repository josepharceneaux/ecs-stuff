# -*- coding: utf-8 -*-

import time
from email_template_service.common.tests.conftest import *
from email_template_service.email_template.api.common_functions import create_email_template, update_email_template
from helpers import *
from email_template_service.common.utils.common_functions import add_role_to_test_user
from email_template_service.common.models.user import DomainRole


def test_create_email_template_folder(sample_user, user_auth):
    """
    Tests creating new email campaign template folder
    It creates a test folder and asserts that it is created with correct name

    :param user_auth:
    :return:
    """
    auth_token = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    token = auth_token['access_token']
    # Add 'CAN_CREATE_EMAIL_TEMPLATE_FOLDER' to sample_user
    add_role_to_test_user(sample_user, ['CAN_CREATE_EMAIL_TEMPLATE_FOLDER'])
    # Get Template Folder Id
    template_folder_id, template_folder_name = get_template_folder(token)
    # Assert that folder is created with correct name
    db.session.commit()
    folder_row = EmailTemplateFolder.query.filter_by(id=template_folder_id).first()
    assert folder_row.name == template_folder_name


def test_delete_email_template_folder(sample_user, sample_user_2, user_auth):
    """
    Tests creating new email campaign template folder
    It creates a test folder and asserts that it is created with correct name

    :param user_auth:
    :return:
    """
    auth_token = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    token1 = auth_token['access_token']
    # Add 'CAN_CREATE_EMAIL_TEMPLATE_FOLDER' to sample_user
    add_role_to_test_user(sample_user, ['CAN_CREATE_EMAIL_TEMPLATE_FOLDER'])
    # Get Template Folder Id
    template_folder_id, template_folder_name = get_template_folder(token1)
    # Assert that folder is created with correct name
    db.session.commit()
    folder_row = EmailTemplateFolder.query.filter_by(id=template_folder_id).first()
    assert folder_row.name == template_folder_name

    token2 = auth_token['access_token']
    # Add 'CAN_DELETE_EMAIL_TEMPLATE' to sample_user_2
    add_role_to_test_user(sample_user, ['CAN_DELETE_EMAIL_TEMPLATE_FOLDER'])

    data = {'name': template_folder_name}
    response = requests.delete(
        url=EMAIL_TEMPLATE_FOLDER_URL, data=json.dumps(data),
        headers={'Authorization': 'Bearer %s' % token2,
                 'Content-type': 'application/json'}
    )
    assert response.status_code == 200

    template_folder_after_delete = EmailTemplateFolder.query.get(template_folder_id)
    assert template_folder_after_delete is None


# Tests for creating email templates
def test_create_email_template(sample_user, user_auth, email_template_body):
    """
    Tests creating template
    :param sample_user:         user manager id
    :param email_template_body:     email template html body
    :return:
    """
    # Add Email template
    email_template = add_email_template(user_auth, sample_user)
    email_template_id = email_template["email_template_id"]
    template_name = email_template["template_name"]
    # Get added template row
    template = db.session.query(UserEmailTemplate).filter_by(id=email_template_id).first()
    # Assert with template_name
    assert template.name == template_name
    assert template.is_immutable == 1


# Test for deleting emain templates
def test_delete_email_template(sample_user, sample_user_2, email_template_body, user_auth):
    """
    Tests deleting user's email template
    :param sample_user:         user1
    :param sample_user_2:         user2
    :param email_template_body:     email template html body
    :return:
    """
    # Add Email template
    email_template = add_email_template(user_auth, sample_user)
    email_template_id = email_template["email_template_id"]

    token2 = user_auth.get_auth_token(sample_user_2, get_bearer_token=True)['access_token']

    # Add 'CAN_DELETE_EMAIL_TEMPLATE' to sample_user_2
    add_role_to_test_user(sample_user, ['CAN_DELETE_EMAIL_TEMPLATE'])

    request_to_email_template_resource(token2, 'delete', email_template["email_template_id"])

    template_after_delete = UserEmailTemplate.query.get(email_template_id)
    assert template_after_delete is None


# Tests to retrieve email templates
def test_get_email_template_via_id(sample_user, sample_user_2, email_template_body, user_auth):
    """
    Test:   Retrieve email_template via template's ID
    Expect: 200
    :type sample_user:    User
    :type user_auth:      UserAuthentication
    """
    # Add Email template
    email_template = add_email_template(user_auth, sample_user)
    # Get access token for sample_user_2
    token2 = user_auth.get_auth_token(sample_user_2, True)['access_token']

    # Add 'CAN_GET_EMAIL_TEMPLATE' to sample_user_2
    add_role_to_test_user(sample_user, ['CAN_GET_EMAIL_TEMPLATE'])

    # Get email_template via template ID
    resp = request_to_email_template_resource(token2, 'get', email_template["email_template_id"])
    assert resp.status_code == 200
    resp_dict = resp.json()
    print resp_dict
    assert isinstance(resp_dict, dict)
    assert check_for_id(_dict=resp_dict['email_template']) is not False


# Tests to update email templates
def test_update_email_template(sample_user, sample_user_2, email_template_body, user_auth):
    """
    Test to update email template by other user in the same domain
    :param sample_user:
    :param sample_user_2:
    :param email_template_body:
    :param user_auth:
    :return:
    """
    # Add Email template
    email_template = add_email_template(user_auth, sample_user)
    # Get access token for sample_user_2
    token2 = user_auth.get_auth_token(sample_user_2, True)['access_token']

    # Add 'CAN_UPDATE_EMAIL_TEMPLATE' to sample_user_2
    add_role_to_test_user(sample_user, ['CAN_UPDATE_EMAIL_TEMPLATE'])

    updated_email_template_body = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\r\n<html>\r\n<head>\r\n\t<title></title>\r\n</head>\r\n<body>\r\n<p>test for update campaign mail testing through script</p>\r\n</body>\r\n</html>\r\n'

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


def add_email_template(auth_user, template_owner):
    """
    This function will create email template
    :param auth_user:
    :param template_owner:
    :return:
    """
    # Get access token
    auth_token = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    token = auth_token['access_token']
    # Add 'CAN_CREATE_EMAIL_TEMPLATE' to sample_user
    add_role_to_test_user(sample_user, ['CAN_CREATE_EMAIL_TEMPLATE'])
    domain_id = sample_user.domain_id
    # Get Template Folder Id
    template_folder_id, template_folder_name = get_template_folder(token)

    template_name = 'test_email_template%i' % time.time()

    email_template_id = create_email_template(token, sample_user.id, template_name, email_template_body, '',
                                              is_immutable="1", folder_id=template_folder_id, domain_id=domain_id)
    db.session.commit()

    return {"email_template_id": email_template_id,
            "template_folder_id": template_folder_id,
            "template_folder_name": template_folder_name,
            "template_name": template_name,
            "domain_id": domain_id}


def get_template_folder(token):
    """

    :param auth_token:
    :return:
    """
    template_folder_name = 'test_template_folder_%i' % time.time()

    data = {'name': template_folder_name}
    response = requests.post(
        url=EMAIL_TEMPLATE_FOLDER_URL, data=json.dumps(data),
        headers={'Authorization': 'Bearer %s' % token,
                 'Content-type': 'application/json'}
    )
    assert response.status_code == 200
    response_obj = response.json()
    template_folder_id = response_obj["template_folder_id"][0]
    return template_folder_id['id'], template_folder_name

