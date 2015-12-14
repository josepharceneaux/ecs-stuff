# -*- coding: utf-8 -*-

import time
from email_template_service.common.tests.conftest import *
from email_template_service.email_template.api.common_functions import create_email_template
from helpers import *


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


def test_create_email_template_folder(sample_user, user_auth):
    """
    Tests creating new email campaign template folder
    It creates a test folder and asserts that it is created with correct name

    :param user_auth:
    :return:
    """
    auth_token = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    token = auth_token['access_token']
    # Add 'CAN_CREATE_EMAIL_TEMPLATE_FOLDER' to user_second
    # add_role_to_test_user(sample_user, ['CAN_CREATE_EMAIL_TEMPLATE_FOLDER'])
    # Get Template Folder Id
    template_folder_id, template_folder_name = get_template_folder(token)
    # Assert that folder is created with correct name
    folder_row = EmailTemplateFolder.query.filter_by(id=template_folder_id).first()
    assert folder_row.name == template_folder_name


class TestEmailTemplate:
    """
    Test creating immutable template
    """

    def test_create_email_template(self, sample_user, user_auth, email_template_body):
        """
        Tests creating immutable template as user manager
        It asserts that created template is immutable by checking isImmutable attribute

        :param sample_user:         user manager id
        :param email_template_body:     email template html body
        :return:
        """
        # Get access token
        auth_token = user_auth.get_auth_token(sample_user, get_bearer_token=True)
        token = auth_token['access_token']
        domain_id = sample_user.domain_id
        # Get Template Folder Id
        template_folder_id, template_folder_name = get_template_folder(token)

        template_name = 'test_email_template%i' % time.time()

        email_template_id = create_email_template(token, sample_user.id, template_name, email_template_body, '',
                                                  is_immutable="1", folder_id=template_folder_id, domain_id=domain_id)
        template = db.session.query(UserEmailTemplate).filter_by(id=email_template_id).first()

        assert template.name == template_name
        assert template.is_immutable == 1

    # def test_delete_email_template(self, sample_user, sample_user_2, email_template_body):
    #     """
    #     Tests deleting mutable template created by user manager as passive user
    #     It asserts that created template can be deleted by running controller function which deletes template by id
    #
    #     :param sample_user:         user manager id
    #     :param sample_user_2:         passive user id
    #     :param email_template_body:     email template html body
    #     :return:
    #     """
    #     # Get access token
    #     auth_token = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    #     token = auth_token['access_token']
    #     domain_id = sample_user.domain_id
    #     # Get Template Folder Id
    #     template_folder_id, template_folder_name = get_template_folder(token)
    #
    #     template_name = 'test_template_mutable_as_user_manager_%i' % time.time()
    #     email_template_id = create_email_template(token, sample_user.id, template_name, email_template_body, '',
    #                                               is_immutable="1", folder_id=template_folder_id, domain_id=domain_id)
    #     resp = request_to_email_template_resource(token, 'delete', email_template_id)
    #     print response_info(resp)
    #     # Retrieve Candidate
    #     get_resp = get_from_candidate_resource(token, email_template_id)
    #     print response_info(get_resp)
    #     assert get_resp.status_code == 404
    #
    # def test_get_email_template_via_id(self, sample_user, user_auth):
    #     """
    #     Test:   Retrieve email_template via template's ID
    #     Expect: 200
    #     :type sample_user:    User
    #     :type user_auth:      UserAuthentication
    #     """
    #     # Get access token
    #     token = user_auth.get_auth_token(sample_user, True)['access_token']
    #
    #     # Create candidate
    #     resp = post_to_email_template_resource(access_token=token, data=None, domain_id=sample_user.domain_id)
    #     print response_info(resp)
    #
    #     db.session.commit()
    #
    #     email_template = db.session.query(UserEmailTemplate).filter(
    #         UserEmailTemplate.user_id == sample_user.id).first()
    #     email_template_id = email_template.id
    #     # Get email_template via template ID
    #     resp = get_from_email_template_resource(token, email_template_id)
    #
    #     resp_dict = resp.json()
    #     print response_info(resp)
    #     assert resp.status_code == 200
    #     assert isinstance(resp_dict, dict)
    #     assert check_for_id(_dict=resp_dict['email_template']) is not False
    #
