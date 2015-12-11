import requests
import json


class EmailTemplateResourceUrl:
    def __init__(self):
        pass

    BASE_URL = "http://127.0.0.1:8010/v1/EmailTemplate"


def post_to_email_template_resource(access_token, data=None, domain_id=None):
    """
    Function sends a post request to EmailTemplate,
    i.e. EmailTemplate/post()
    """
    resp = requests.post(
        url=EmailTemplateResourceUrl.BASE_URL,
        headers={'Authorization': 'Bearer %s' % access_token},
        data=json.dumps(data)
    )
    return resp


def response_info(resp_request, resp_json, resp_status):
    """
    Function returns the following information about the request:
        1. Request, 2. Response dict, and 3. Response status
    :type resp_json:        dict
    :type resp_status:      int
    """
    args = (resp_request, resp_json, resp_status)
    return "\nRequest: %s \nResponse JSON: %s \nResponse status: %s" % args

