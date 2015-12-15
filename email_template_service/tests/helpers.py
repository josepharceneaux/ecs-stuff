import requests
import json

BASE_URL = "http://127.0.0.1:8010"
EMAIL_TEMPLATE_URL = BASE_URL + "/v1/email-templates"
EMAIL_TEMPLATE_FOLDER_URL = BASE_URL + "/v1/email-template-folders"


def post_to_email_template_resource(access_token, data=None, domain_id=None):
    """
    Function sends a post request to EmailTemplate,
    i.e. EmailTemplate/post()
    """
    response = requests.post(
        url=EMAIL_TEMPLATE_URL, data=json.dumps(data),
        headers={'Authorization': 'Bearer %s' % access_token,
                 'Content-type': 'application/json'}
    )
    return response


def response_info(resp_request, resp_json, resp_status):
    """
    Function returns the following information about the request:
        1. Request, 2. Response dict, and 3. Response status
    :type resp_json:        dict
    :type resp_status:      int
    """
    args = (resp_request, resp_json, resp_status)
    return "\nRequest: %s \nResponse JSON: %s \nResponse status: %s" % args


def define_and_send_request(request, url, access_token, template_id= None, data=None):
    """
    Function will define request based on params and make the appropriate call.
    :param  request:  can only be get, post, put, patch, or delete
    """
    request = request.lower()
    assert request in ['get', 'put', 'patch', 'delete']
    method = getattr(requests, request)
    if not data:
        data = dict(id=template_id)
    return method(url=url, data=json.dumps(data), headers={'Authorization': 'Bearer %s' % access_token})


def request_to_email_template_resource(access_token, request, email_template_id, data=None):
    """
    Function sends a request to email template resource
    :param request: get, post, patch, delete
    """
    url = EMAIL_TEMPLATE_URL
    return define_and_send_request(request, url, access_token, email_template_id, data)


def check_for_id(_dict):
    """
    Checks for id-key in email_template_dict and all its nested objects that must have an id-key
    :type _dict:    dict
    :return False if an id-key is missing in email_template_dict or any of its nested objects
    """
    assert isinstance(_dict, dict)
    # Get top level keys
    top_level_keys = _dict.keys()

    # Top level dict must have an id-key
    if not 'id' in top_level_keys:
        return False

    # Remove id-key from top level keys
    top_level_keys.remove('id')

    # Remove contact_history key since it will not have an id-key to begin with
    if 'contact_history' in top_level_keys:
        top_level_keys.remove('contact_history')

    for key in top_level_keys:
        obj = _dict[key]
        if isinstance(obj, dict):
            # If obj is an empty dict, e.g. obj = {}, continue with the loop
            if not any(obj):
                continue

            check = id_exists(_dict=obj)
            if check is False:
                return check

        if isinstance(obj, list):
            list_of_dicts = obj
            for dictionary in list_of_dicts:
                # Invoke function again if any of dictionary's key's value is a list-of-objects
                for _key in dictionary:
                    if type(dictionary[_key]) == list:
                        for i in range(0, len(dictionary[_key])):
                            check = check_for_id(_dict=dictionary[_key][i])  # recurse
                            if check is False:
                                return check

                check = id_exists(_dict=dictionary)
                if check is False:
                    return check


def id_exists(_dict):
    """
    :return True if id-key is found in _dict, otherwise False
    """
    assert isinstance(_dict, dict)
    check = True
    # Get _dict's keys
    keys = _dict.keys()

    # Ensure id-key exists
    if not 'id' in keys:
        check = False

    return check
