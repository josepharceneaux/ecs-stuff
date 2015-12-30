__author__ = 'ufarooqi'
import json
from werkzeug.security import gen_salt
from candidate_pool_service.common.routes import CandidateApiUrl
from candidate_pool_service.common.models.smartlist import Smartlist, SmartlistCandidate

import requests

CANDIDATE_POOL_SERVICE_ENDPOINT = 'http://127.0.0.1:8008/%s'
TALENT_POOL_API = CANDIDATE_POOL_SERVICE_ENDPOINT % 'talent-pools'
TALENT_POOL_GROUP_API = CANDIDATE_POOL_SERVICE_ENDPOINT % 'groups/%s/talent_pools'
TALENT_POOL_CANDIDATE_API = CANDIDATE_POOL_SERVICE_ENDPOINT % 'talent-pools/%s/candidates'
TALENT_PIPELINE_API = CANDIDATE_POOL_SERVICE_ENDPOINT % 'talent-pipelines'
TALENT_PIPELINE_SMART_LIST_API = CANDIDATE_POOL_SERVICE_ENDPOINT % 'talent-pipeline/%s/smart_lists'
TALENT_PIPELINE_CANDIDATE_API = CANDIDATE_POOL_SERVICE_ENDPOINT % 'talent-pipeline/%s/candidates'


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


def talent_pipeline_candidate_api(access_token, talent_pipeline_id, params=''):

    headers = {'Authorization': 'Bearer %s' % access_token}
    response = requests.get(url=TALENT_PIPELINE_CANDIDATE_API % talent_pipeline_id, headers=headers, params=params)
    return response.json(), response.status_code


def prepare_pipeline_candidate_data(session, talent_pipeline, user):
    """
    This function will add a test dumb_list and smart_list to database and talent-pipeline
    :param session: SQLAlchemy Session object
    :param talent_pipeline: TalentPipeline object
    :param user: User object
    :return: test smart_list and dumb_list objects
    """

    test_smart_list = Smartlist(name=gen_salt(5), user_id=user.id, talent_pipeline_id=talent_pipeline.id)
    test_dumb_list = Smartlist(name=gen_salt(5), user_id=user.id, talent_pipeline_id=talent_pipeline.id)
    session.add(test_smart_list)
    session.add(test_dumb_list)
    talent_pipeline.search_params = json.dumps({})
    session.commit()

    return test_smart_list, test_dumb_list


def add_candidates_to_dumb_list(session, access_token, test_dumb_list, candidate_ids):
    """
    This function will add a test dumb_list and smart_list to database and talent-pipeline
    :param session: SQLAlchemy Session object
    :param test_dumb_list: SmartList object
    :param list candidate_ids: List of candidate_ids that will be added to test dumb_list
    :return: None
    """

    for candidate_id in candidate_ids:
        dumb_list_candidate = SmartlistCandidate(candidate_id=candidate_id, smartlist_id=test_dumb_list.id)
        session.add(dumb_list_candidate)

    session.commit()

    # Updating Candidate Info in Amazon Cloud SEarch
    headers = {'Authorization': 'Bearer %s' % access_token, 'Content-Type': 'application/json'}
    response = requests.post(CandidateApiUrl.CANDIDATES_DOCUMENTS_URI, headers=headers,
                             data=json.dumps({'candidate_ids': candidate_ids}))
    assert response.status_code == 204


def create_candidates_from_candidate_api(access_token, data):
    """
    Function sends a request to CandidateResource/post()
    Returns: list of created candidate ids
    """
    resp = requests.post(
        url=CandidateApiUrl.CANDIDATES,
        headers={'Authorization': access_token if 'Bearer' in access_token else 'Bearer %s' % access_token},
        data=json.dumps(data)
    )
    assert resp.status_code == 201
    return [candidate['id'] for candidate in resp.json()['candidates']]