from email_template_service.common.models.user import DomainRole
from email_template_service.tests.api.helpers import *


def create_email_template(token, user_id, template_name, body_html, body_text, is_immutable="1",
                          folder_id=None, domain_id=None, role_id=None):
    """
    Creates a email campaign template with params provided

    :param token
    :param user_id:                 User id
    :param template_name:           Template name
    :param body_html:               Body html
    :param body_text:               Body text
    :param is_immutable:            "1" if immutable, otherwise "0"
    :param folder_id:               folder id
    :param domain_id                domain_id
    :param role_id                  user scoped role id
    :return:                        Id of template created
    """
    # Check the user has role to create template
    role = DomainRole.query.get(role_id)
    domain_role_name = role.role_name
    assert domain_role_name == "CAN_CREATE_EMAIL_TEMPLATE"
    data = dict(
        name=template_name,
        email_template_folder_id=folder_id,
        user_id=user_id,
        type=0,
        email_body_html=body_html,
        email_body_text=body_text,
        is_immutable=is_immutable
    )

    create_resp = post_to_email_template_resource(token, data=data, domain_id=domain_id)
    return create_resp


def update_email_template(email_template_id, request, token, user_id, template_name, body_html, body_text='',
                          is_immutable="1", folder_id=None, domain_id=None):
    """

    :param email_template_id
    :param request
    :param token:
    :param user_id:
    :param template_name:
    :param body_html:
    :param body_text:
    :param is_immutable:
    :param folder_id:
    :param domain_id:
    :return:
    """
    data = dict(
        id=email_template_id,
        name=template_name,
        email_template_folder_id=folder_id,
        user_id=user_id,
        type=0,
        email_body_html=body_html,
        email_body_text=body_text,
        is_immutable=is_immutable
    )

    create_resp = request_to_email_template_resource(token, request, email_template_id, data)
    return create_resp
