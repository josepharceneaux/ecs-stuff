import requests
import json
from faker import Faker
from candidate_service.common.models.smart_list import SmartList, SmartListCandidate
from candidate_service.common.tests.conftest import UserAuthentication
from candidate_service.common.tests.conftest import *
from candidate_service.common.tests.sample_data import generate_single_candidate_data
from candidate_service.tests import populate_candidates

__author__ = 'jitesh'

BASE_URI = "http://127.0.0.1:8005/"
SMARTLIST_API_URI = "v1/smartlist"
CANDIDATE_API_URI = "v1/candidates"

fake = Faker()


def teast_get_smart_list(sample_user, user_auth):

    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    list_id, list_name = create_smartlist_with_candidate_ids(auth_token_row)
    resp = requests.get(
        url="%s%s/%s" % (BASE_URI, SMARTLIST_API_URI, list_id),
        headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )

    assert resp.status_code == 200
    assert json.loads(resp.content)['list']['name'] == list_name


def create_smartlist_with_candidate_ids(auth_token_row):
    # create candidate
    r = requests.post(
        url=BASE_URI + CANDIDATE_API_URI,
        data=json.dumps(generate_single_candidate_data()),
        headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )
    resp_object = r.json()
    candidate_id = resp_object['candidates'][0]['id']
    # Create smartlist
    # TODO: Add create function once it is created
    list_obj = SmartList(name=fake.word(), user_id=auth_token_row['user_id'])
    db.session.add(list_obj)
    db.session.commit()
    smartlist_candidate = SmartListCandidate(smart_list_id=list_obj.id, candidate_id=candidate_id)
    db.session.add(smartlist_candidate)
    db.session.commit()
    return list_obj.id, list_obj.name


def teast_create_smartlist_with_search_params(sample_user, user_auth):
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    name = fake.word()
    search_params = '{"maximum_years_experience": "5", "location": "San Jose, CA", "minimum_years_experience": "2"}'
    data = {'name': name,
            'search_params': search_params}
    resp = requests.post(
        url="%s%s" % (BASE_URI, SMARTLIST_API_URI),
        data=data,
        headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )
    # assert resp.status_code == 200
    response = json.loads(resp.content)
    assert 'smartlist' in response
    assert 'id' in response['smartlist']


def test_create_smartlist_with_blank_search_params(sample_user, user_auth):
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    name = 'smart list with blank search params'
    search_params = ''
    data = {'name': name,
            'search_params': search_params}
    resp = requests.post(
        url="%s%s" % (BASE_URI, SMARTLIST_API_URI),
        data=data,
        headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )
    assert resp.status_code == 400


def test_create_smartlist_with_candidate_ids(sample_user, user_auth):
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    candidate_ids = populate_candidates(auth_token_row['user_id'], count=5)
    name = fake.word()
    data = {'name': name,
            'candidate_ids': candidate_ids}
    resp = requests.post(
        url="%s%s" % (BASE_URI, SMARTLIST_API_URI),
        data=data,
        headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )
    response = json.loads(resp.content)
    assert 'smartlist' in response
    assert 'id' in response['smartlist']