__author__ = 'ufarooqi'
import requests
import json

CANDIDATE_POOL_SERVICE_ENDPOINT = 'http://127.0.0.1:8008/%s'
TALENT_POOL_API = CANDIDATE_POOL_SERVICE_ENDPOINT % 'talent-pools'
TALENT_POOL_GROUP_API = CANDIDATE_POOL_SERVICE_ENDPOINT % 'groups/%s/talent_pools'
TALENT_POOL_CANDIDATE_API = CANDIDATE_POOL_SERVICE_ENDPOINT % 'talent-pools/%s/candidates'
TALENT_PIPELINE_API = CANDIDATE_POOL_SERVICE_ENDPOINT % 'talent-pipelines'
TALENT_PIPELINE_SMART_LIST_API = CANDIDATE_POOL_SERVICE_ENDPOINT % 'talent-pipeline/%s/smart_lists'


def talent_pool_api(access_token, talent_pool_id='', data='', action='GET'):
    headers = {'Authorization': 'Bearer %s' % access_token}
    if action == 'GET':
        if talent_pool_id:
            response = requests.get(url=TALENT_POOL_API + '/%s' % talent_pool_id, headers=headers)
            return response.json(), response.status_code
        else:
            response = requests.get(url=TALENT_POOL_API, headers=headers)
            return response.json(), response.status_code
    elif action == 'DELETE':
        response = requests.delete(url=TALENT_POOL_API + '/%s' % talent_pool_id, headers=headers)
        return response.json(), response.status_code
    elif action == 'PUT':
        headers['content-type'] = 'application/json'
        response = requests.put(url=TALENT_POOL_API + '/%s' % talent_pool_id, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code
    elif action == 'POST':
        headers['content-type'] = 'application/json'
        response = requests.post(url=TALENT_POOL_API, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code


def talent_pool_group_api(access_token, user_group_id, data='', action='GET'):
    headers = {'Authorization': 'Bearer %s' % access_token}
    if action == 'GET':
        response = requests.get(url=TALENT_POOL_GROUP_API % user_group_id, headers=headers)
        return response.json(), response.status_code
    elif action == 'DELETE':
        headers['content-type'] = 'application/json'
        response = requests.delete(url=TALENT_POOL_GROUP_API % user_group_id, data=json.dumps(data), headers=headers)
        return response.json(), response.status_code
    elif action == 'POST':
        headers['content-type'] = 'application/json'
        response = requests.post(url=TALENT_POOL_GROUP_API % user_group_id, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code
    else:
        raise Exception('No valid action is provided')


def talent_pool_candidate_api(access_token, talent_pool_id, data='', action='GET'):
    headers = {'Authorization': 'Bearer %s' % access_token}
    if action == 'GET':
        response = requests.get(url=TALENT_POOL_CANDIDATE_API % talent_pool_id, headers=headers)
        return response.json(), response.status_code
    elif action == 'DELETE':
        headers['content-type'] = 'application/json'
        response = requests.delete(url=TALENT_POOL_CANDIDATE_API % talent_pool_id, data=json.dumps(data), headers=headers)
        return response.json(), response.status_code
    elif action == 'POST':
        headers['content-type'] = 'application/json'
        response = requests.post(url=TALENT_POOL_CANDIDATE_API % talent_pool_id, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code
    else:
        raise Exception('No valid action is provided')


def talent_pipeline_api(access_token, talent_pipeline_id='', data='', action='GET'):
    headers = {'Authorization': 'Bearer %s' % access_token}
    if action == 'GET':
        if talent_pipeline_id:
            response = requests.get(url=TALENT_PIPELINE_API + '/%s' % talent_pipeline_id, headers=headers)
            return response.json(), response.status_code
        else:
            response = requests.get(url=TALENT_PIPELINE_API, headers=headers)
            return response.json(), response.status_code
    elif action == 'DELETE':
        response = requests.delete(url=TALENT_PIPELINE_API + '/%s' % talent_pipeline_id, headers=headers)
        return response.json(), response.status_code
    elif action == 'PUT':
        headers['content-type'] = 'application/json'
        response = requests.put(url=TALENT_PIPELINE_API + '/%s' % talent_pipeline_id, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code
    elif action == 'POST':
        headers['content-type'] = 'application/json'
        response = requests.post(url=TALENT_PIPELINE_API, headers=headers, data=json.dumps(data))
        return response.json(), response.status_code


def talent_pipeline_smart_list_api(access_token, talent_pipeline_id, data='', action='GET'):
    headers = {'Authorization': 'Bearer %s' % access_token}
    if action == 'GET':
        response = requests.get(url=TALENT_PIPELINE_SMART_LIST_API % talent_pipeline_id, headers=headers)
        return response.json(), response.status_code
    elif action == 'DELETE':
        headers['content-type'] = 'application/json'
        response = requests.delete(url=TALENT_PIPELINE_SMART_LIST_API % talent_pipeline_id, data=json.dumps(data),
                                   headers=headers)
        return response.json(), response.status_code
    elif action == 'POST':
        headers['content-type'] = 'application/json'
        response = requests.post(url=TALENT_PIPELINE_SMART_LIST_API % talent_pipeline_id, headers=headers,
                                 data=json.dumps(data))
        return response.json(), response.status_code
    else:
        raise Exception('No valid action is provided')