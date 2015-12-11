import requests
import json
from email_template_service.common.models.misc import EmailTemplateFolder, UserEmailTemplate
from email_template_service.tests.helpers import post_to_email_template_resource, response_info


def create_email_template(token, user_id, template_name, body_html, body_text, is_immutable="1", folder_id=None):
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
        user_id=user_id,
        type=0,
        email_body_html=body_html,
        email_body_text=body_text,
        is_immutable=is_immutable
    )

    create_resp = post_to_email_template_resource(token, data=data)
    print response_info(create_resp.request, create_resp.json(), create_resp.status_code)

    return response_info['id']

