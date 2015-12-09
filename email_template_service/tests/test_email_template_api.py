# -*- coding: utf-8 -*-

import time
import json
import sys
from email_template_service.email_template.api.api import create_email_template_folder
from email_template_service.common.tests.conftest import *
from email_template_service.common.models.misc import UserEmailTemplate, EmailTemplateFolder


EMAIL_TEMPLATE_URI = "http://127.0.0.1:8010/emailTemplate"


def test_create_email_template_folder_as_admin_user(sample_user, user_auth):
    """
    Tests creating new email campaign template folder
    It creates a test folder and asserts that it is created with correct name

    :param user_auth:
    :return:
    """
    folder_name = 'test_template_folder_as_user_manager_%i' % time.time()
    auth_token = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    # Add 'CAN_CREATE_EMAIL_TEMPLATE_FOLDER' to user_second
    # add_role_to_test_user(sample_user, ['CAN_CREATE_EMAIL_TEMPLATE_FOLDER'])
    data = {'name': folder_name}
    response = requests.post(
        url=EMAIL_TEMPLATE_URI, data=json.dumps(data),
        headers={'Authorization': 'Bearer %s' % auth_token['access_token'],
                 'Content-type': 'application/json'}
    )
    assert response.status_code == 200
    response_obj = response.json()
    template_folder_id = response_obj['id']
    # Assert that folder is created with correct name
    folder_row = EmailTemplateFolder.query.filter_by(id=template_folder_id).first()
    assert folder_row['name'] == folder_name


# def test_create_email_template_folder_as_normal_user(user_manager_id, passive_user_id):
#     """
#     Tests creating new email campaign template folder
#     It creates a test folder and asserts that it is created with correct name
#     :param user_manager_id:
#     :return:
#     """
#     folder_name = 'test_template_folder_as_passive_user_%i' % time.time()
#
#     # Create template folder
#     folder_id = create_email_template_folder(passive_user_id, folder_name)
#
#     # Assert that folder is created with correct name
#     folder = db(db.email_template_folder.id == folder_id).select(db.email_template_folder.name).first()
#     assert folder['name'] == folder_name
#
#
# def test_create_email_template_with_no_folder_as_user_manager(user_manager_id, email_template_body):
#     """
#     Tests creating campaign template with no folder as user manager
#     It asserts that the created template's folder is NULL by checking emailTemplateFolderId attribute of email template
#
#     :param user_manager_id:         user manager id
#     :param email_template_body:     email template html body
#     :return:
#     """
#     template_name = 'test_template_with_no_folder_as_user_manager_%i' % time.time()
#     template_id = create_email_template_folder(
#         user_manager_id,
#         template_name,
#         email_template_body,
#         '',
#         is_immutable="0",
#         folder_id=None
#     )
#
#     template = db(db.user_email_template.id == template_id).select(db.user_email_template.name, db.user_email_template.emailTemplateFolderId).first()
#     assert template['name'] == template_name
#     assert template['emailTemplateFolderId'] is None
#
#
# def test_create_email_template_with_no_folder_as_passive_user(passive_user_id, email_template_body):
#     """
#     Tests creating campaign template with no folder as passive user
#     It asserts that the created template's folder is NULL by checking emailTemplateFolderId attribute of email template
#
#     :param passive_user_id:         passive user id
#     :param email_template_body:     email template html body
#     :return:
#     """
#     template_name = 'test_template_with_no_folder_as_passive_user_%i' % time.time()
#     template_id = create_email_template_folder(
#         passive_user_id,
#         template_name,
#         email_template_body,
#         '',
#         is_immutable="0",
#         folder_id=None
#     )
#
#     template = db(db.user_email_template.id == template_id).select(db.user_email_template.name, db.user_email_template.emailTemplateFolderId).first()
#     assert template['name'] == template_name
#     assert template['emailTemplateFolderId'] is None
#
#
# def test_create_email_template_immutable(sample_user, email_template_body):
#     """
#     Tests creating immutable template as user manager
#     It asserts that created template is immutable by checking isImmutable attribute
#
#     :param user_manager_id:         user manager id
#     :param email_template_body:     email template html body
#     :return:
#     """
#     folder_name = 'test_template_folder_for_immutable_as_user_manager_%i' % time.time()
#
#     # Create template folder
#     folder_id = create_email_template_folder(sample_user.id, folder_name)
#
#     template_name = 'test_template_immutable_as_user_manager_%i' % time.time()
#
#     template_id = create_email_template_folder(
#         sample_user.id,
#         template_name,
#         email_template_body,
#         '',
#         is_immutable="1",
#         folder_id=folder_id
#     )
#     template = db.session.query(UserEmailTemplate).filter_by(id=template_id).select(
#         [UserEmailTemplate.name, UserEmailTemplate.is_immutable]).first()
#     template = db(db.user_email_template.id == template_id).select(db.user_email_template.name, db.user_email_template.isImmutable).first()
#     assert template['name'] == template_name
#     assert template['isImmutable'] == 1
#
#
# def test_create_campaign_template_immutable_as_passive_user(self, passive_user_id, email_template_body):
#     """
#     Tests creating immutable template as passive user
#     It asserts that exception occurs when passive user tries to create mutable template
#
#     :param passive_user_id:         passive_user id
#     :param email_template_body:     email template html body
#     :return:
#     """
#     folder_name = 'test_template_folder_for_immutable_as_passive_user_%i' % time.time()
#
#     # Create template folder
#     folder_id = create_email_template_folder(passive_user_id, folder_name)
#
#     template_name = 'test_template_immutable_as_passive_user_%i' % time.time()
#
#     with pytest.raises(HTTP) as e:
#         template_id = create_email_template_folder(
#             passive_user_id,
#             template_name,
#             email_template_body,
#             '',
#             is_immutable="1",
#             folder_id=folder_id
#         )
#
#     # Get exception information.
#     (_type, _redirection, _traceback) = sys.exc_info()
#
#     # Assert the passive user cannot create immutable template
#     assert _redirection.body == 'isImmutable = 1 but user is not admin'
#
#
# def test_create_campaign_template_mutable_as_user_manager(self, user_manager_id, email_template_body):
#     """
#     Tests creating mutable template as user manager
#     It asserts that created template is mutable by checking isImmutable attribute
#
#     :param user_manager_id:         user manager id
#     :param email_template_body:     email template html body
#     :return:
#     """
#     folder_name = 'test_template_folder_for_mutable_as_user_manager_%i' % time.time()
#
#     # Create template folder
#     folder_id = create_email_template_folder(user_manager_id, folder_name)
#
#     template_name = 'test_template_mutable_as_user_manager_%i' % time.time()
#     template_id = common.create_campaign_template(
#         user_manager_id,
#         template_name,
#         email_template_body,
#         '',
#         is_immutable="0",
#         folder_id=folder_id
#     )
#
#     template = db(db.user_email_template.id == template_id).select(db.user_email_template.name, db.user_email_template.isImmutable).first()
#     assert template['name'] == template_name
#     assert template['isImmutable'] == 0
#
#
# def test_create_campaign_template_mutable_as_passive_user(passive_user_id, email_template_body):
#     """
#     Tests creating mutable template as passive user
#     It asserts that created template is mutable by checking isImmutable attribute
#
#     :param passive_user_id:         passive_user id
#     :param email_template_body:     email template html body
#     :return:
#     """
#
#     folder_name = 'test_template_folder_for_mutable_as_passive_user_%i' % time.time()
#
#     # Create template folder
#     folder_id = create_email_template_folder(passive_user_id, folder_name)
#
#     template_name = 'test_template_mutable_as_passive_user_%i' % time.time()
#
#     template_id = common.create_campaign_template(
#         passive_user_id,
#         template_name,
#         email_template_body,
#         '',
#         is_immutable="0",
#         folder_id=folder_id
#     )
#
#     template = db(db.user_email_template.id == template_id).select(db.user_email_template.name, db.user_email_template.isImmutable).first()
#     assert template['name'] == template_name
#     assert template['isImmutable'] == 0
#
#
# def test_delete_campaign_template_immutable_as_user_manager(self, user_manager_id, email_template_body):
#     """
#     Tests deleting immutable template created by user manager as user manager
#     It asserts that created template can be deleted by running controller function which deletes template by id
#
#     :param user_manager_id:         user manager id
#     :param email_template_body:     email template html body
#     :return:
#     """
#     folder_name = 'test_template_folder_for_immutable_as_user_manager_%i' % time.time()
#
#     # Create template folder
#     folder_id = create_email_template_folder(user_manager_id, folder_name)
#
#     template_name = 'test_template_immutable_as_user_manager_%i' % time.time()
#     template_id = common.create_campaign_template(
#         user_manager_id,
#         template_name,
#         email_template_body,
#         '',
#         is_immutable="1",
#         folder_id=folder_id
#     )
#
#     delete_result = common.delete_campaign_template(user_manager_id, template_id)
#     assert 'success' in delete_result
#     assert delete_result['success'] == 1
#
#
# def test_delete_campaign_template_immutable_as_passive_user(self, user_manager_id, passive_user_id, email_template_body):
#     """
#     Tests deleting immutable template created by user manager as passive user
#     It asserts that created template can be deleted by running controller function which deletes template by id
#
#     :param user_manager_id:         user manager id
#     :param passive_user_id:         passive user id
#     :param email_template_body:     email template html body
#     :return:
#     """
#     folder_name = 'test_template_folder_for_immutable_as_user_manager_%i' % time.time()
#
#     # Create template folder
#     folder_id = create_email_template_folder(user_manager_id, folder_name)
#
#     template_name = 'test_template_immutable_as_user_manager_%i' % time.time()
#     template_id = common.create_campaign_template(
#         web2py,
#         user_manager_id,
#         template_name,
#         email_template_body,
#         '',
#         is_immutable="1",
#         folder_id=folder_id
#     )
#
#     with pytest.raises(HTTP) as e:
#         delete_result = common.delete_campaign_template(passive_user_id, template_id)
#
#     # Get exception information.
#     (_type, _redirection, _traceback) = sys.exc_info()
#
#     # Assert the passive user cannot delete immutable template
#     assert _redirection.body == 'Non-admin user trying to delete immutable template'
#
#
# def test_delete_campaign_template_mutable_as_user_manager(self, user_manager_id, email_template_body):
#     """
#     Tests deleting mutable template created by user manager as user manager
#     It asserts that created template can be deleted by running controller function which deletes template by id
#
#     :param user_manager_id:         user manager id
#     :param email_template_body:     email template html body
#     :return:
#     """
#     folder_name = 'test_template_folder_for_mutable_as_user_manager_%i' % time.time()
#
#     # Create template folder
#     folder_id = create_email_template_folder(user_manager_id, folder_name)
#
#     template_name = 'test_template_mutable_as_user_manager_%i' % time.time()
#     template_id = common.create_campaign_template(
#         web2py,
#         user_manager_id,
#         template_name,
#         email_template_body,
#         '',
#         is_immutable="0",
#         folder_id=folder_id
#     )
#
#     delete_result = common.delete_campaign_template(user_manager_id, template_id)
#     assert 'success' in delete_result
#     assert delete_result['success'] == 1
#
# def test_delete_campaign_template_mutable_as_passive_user(self, user_manager_id, passive_user_id, email_template_body):
#     """
#     Tests deleting mutable template created by user manager as passive user
#     It asserts that created template can be deleted by running controller function which deletes template by id
#
#     :param user_manager_id:         user manager id
#     :param passive_user_id:         passive user id
#     :param email_template_body:     email template html body
#     :return:
#     """
#     folder_name = 'test_template_folder_for_mutable_as_user_manager_%i' % time.time()
#
#     # Create template folder
#     folder_id = create_email_template_folder(user_manager_id, folder_name)
#
#     template_name = 'test_template_mutable_as_user_manager_%i' % time.time()
#     template_id = common.create_campaign_template(
#         web2py,
#         user_manager_id,
#         template_name,
#         email_template_body,
#         '',
#         is_immutable="0",
#         folder_id=folder_id
#     )
#
#     delete_result = common.delete_campaign_template(passive_user_id, template_id)
#     assert 'success' in delete_result
#     assert delete_result['success'] == 1
#
#
# # Test to create template folder with existing folder name under same domain
# def test_create_duplicate_template_folder(user_manager_id):
#     """
#     :param user_manager_id: user id of admin user
#     :return:
#     """
#     import uuid
#     folder_name = 'test_folder_%s' % str(uuid.uuid4())
#
#     # Create template folder
#     create_email_template_folder(user_manager_id, folder_name)
#
#     # Login user manager
#     web2py.auth.login_user(web2py.db.user(user_manager_id))
#     common_functions.clear_web2py_request(web2py)
#     data = {'name': folder_name}
#     # Update the request.vars data
#     web2py.request.vars.update(data)
#     result = run_controller_in("campaign", "create_email_template_folder", web2py)
#     assert result['error']['message'] == "Template folder already exists"
#
#
# # Test to create template with existing template name
# def test_create_duplicate_template(user_manager_id):
#
#     """
#     :param user_manager_id: user id of admin user
#     """
#     import uuid
#     folder_name = 'test_folder_%s' % str(uuid.uuid4())
#
#     # Create template folder
#     folder_id = create_email_template_folder(user_manager_id, folder_name)
#
#     template_name = 'test_template_%s' % str(uuid.uuid4())
#     # Get the template id
#     common_functions.create_campaign_template(user_manager_id, template_name, "", "Hello", "1", folder_id)
#     # Login user manager
#     web2py.auth.login_user(web2py.db.user(user_manager_id))
#     common_functions.clear_web2py_request(web2py)
#     data = {'name': template_name}
#     # Update the request.vars data
#     web2py.request.vars.update(data)
#     result = run_controller_in("campaign", "create_user_email_template", web2py)
#     assert result['error']['message'] == "Template name already exists"
#
