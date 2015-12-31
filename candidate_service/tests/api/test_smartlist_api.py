import requests
import json
from faker import Faker
from candidate_service.common.models.smartlist import Smartlist
from candidate_service.common.models.talent_pools_pipelines import SmartlistCandidate
from candidate_service.common.tests.conftest import UserAuthentication
from candidate_service.common.tests.conftest import *
from candidate_service.common.tests.sample_data import generate_single_candidate_data

__author__ = 'jitesh'

BASE_URI = "http://127.0.0.1:8005/"
SMARTLIST_API_URI = "v1/smartlist/"
CANDIDATE_API_URI = "v1/candidates"

fake = Faker()


def test_get_smart_list(sample_user, user_auth):

    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    list_id, list_name = create_smartlist_with_candidate_ids(auth_token_row)
    resp = requests.get(
        url=BASE_URI + SMARTLIST_API_URI + str(list_id),
        headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )

    assert resp.status_code == 200
    assert json.loads(resp.text)['list']['name'] == list_name


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
    list_obj = Smartlist(name=fake.word(), user_id=auth_token_row['user_id'])
    db.session.add(list_obj)
    db.session.commit()
    smartlist_candidate = SmartlistCandidate(smart_list_id=list_obj.id, candidate_id=candidate_id)
    db.session.add(smartlist_candidate)
    db.session.commit()
    return list_obj.id, list_obj.name

