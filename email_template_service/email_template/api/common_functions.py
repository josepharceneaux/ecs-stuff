from email_template_service.tests.helpers import *


def create_email_template(token, user_id, template_name, body_html, body_text, is_immutable="1",
                          folder_id=None, domain_id=None):
    """
    Creates a campaign template with params provided

    :param user_id:                 User id
    :param template_name:           Template name
    :param body_html:               Body html
    :param body_text:               Body text
    :param is_immutable:            "1" if immutable, otherwise "0"
    :param folder_id:               folder id
    :return:                        Id of template created
    """
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
    assert create_resp.status_code == 201
    print response_info(create_resp.request, create_resp.json(), create_resp.status_code)
    json_resonse = create_resp.json()['template_id'][0]
    return json_resonse['id']


def update_email_template(email_template_id, request, token, user_id, template_name, body_html, body_text='',
                          is_immutable="1", folder_id=None, domain_id=None):
    """

    :param email_template_id
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
