import requests
import json
from email_template_service.common.utils.app_rest_urls import EmailTemplateApiUrl
import time

def post_to_email_template_resource(access_token, data, domain_id=None):
    """
    Function sends a post request to email-templates,
    i.e. EmailTemplate/post()
    :param access_token
    :param data
    :param domain_id
    """
    response = requests.post(
        url=EmailTemplateApiUrl.EMAIL_TEMPLATE, data=json.dumps(data),
        headers={'Authorization': 'Bearer %s' % access_token,
                 'Content-type': 'application/json'}
    )
    return response


def response_info(resp_request, resp_json, resp_status):
    """
    Function returns the following information about the request:
        1. Request, 2. Response dict, and 3. Response status
    :param resp_request
    :type resp_json:        dict
    :type resp_status:      int
    """
    args = (resp_request, resp_json, resp_status)
    return "\nRequest: %s \nResponse JSON: %s \nResponse status: %s" % args


def define_and_send_request(request_method, url, access_token, template_id= None, data=None):
    """
    Function will define request based on params and make the appropriate call.
    :param  request_method:  can only be get, post, put, patch, or delete
    :param url
    :param access_token
    :param template_id
    :param data
    """
    request_method = request_method.lower()
    assert request_method in ['get', 'put', 'patch', 'delete']
    method = getattr(requests, request_method)
    if not data:
        data = dict(id=template_id)
    return method(url=url, data=json.dumps(data), headers={'Authorization': 'Bearer %s' % access_token})


def request_to_email_template_resource(access_token, request, email_template_id, data=None):
    """
    Function sends a request to email template resource
    :param access_token
    :param request: get, post, patch, delete
    :param email_template_id
    :param data
    """
    url = EmailTemplateApiUrl.EMAIL_TEMPLATE
    return define_and_send_request(request, url, access_token, email_template_id, data)


def get_template_folder(token):
    """
    Function will create and retrieve template folder
    :param token:
    :return: template_folder_id, template_folder_name
    """
    template_folder_name = 'test_template_folder_%i' % time.time()

    data = {'name': template_folder_name}
    response = requests.post(
        url=EmailTemplateApiUrl.EMAIL_TEMPLATE_FOLDER, data=json.dumps(data),
        headers={'Authorization': 'Bearer %s' % token,
                 'Content-type': 'application/json'}
    )
    assert response.status_code == 201
    response_obj = response.json()
    template_folder_id = response_obj["template_folder_id"][0]
    return template_folder_id['id'], template_folder_name
