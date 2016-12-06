"""
This file contains migration script that will accept arguments from the user and it will:
  1. Delete existing-CandidateSource belonging to user's domain
  2. Add new-CandidateSource from input in user's domain
  3. Update all domain-candidates' source IDs from the existing-CandidateSource ID to the new-CandidateSource ID
"""
from candidate_service.candidate_app import app
import requests
import json
import time
from candidate_service.common.models.db import db
from candidate_service.common.routes import AuthApiUrlV2, CandidateApiUrl, UserServiceApiUrl
from candidate_service.common.models.candidate import Candidate
from candidate_service.common.models.user import User, CandidateSource
from candidate_service.common.utils.test_utils import response_info


def get_access_token(username, password):
    """
    Function will get an access token using username & password
    :rtype: dict
    """
    data = {"username": username, "password": password}
    r = requests.post(url=AuthApiUrlV2.TOKEN_CREATE, data=data)
    print "get_access_token_response: {}".format(response_info(r))
    assert r.status_code == 200
    return r.json()


def _add_source_to_domain(source_data, headers, domain_id):
    """
    Function will check for domain's source from source_data's description & domain_id, if
     domain source does not exist, it will add it and return its ID
    :rtype: int
    """
    # Retrieve domain source and make sure source does not already exist
    domain_source = CandidateSource.query.filter_by(
        description=source_data['source']['description'], domain_id=domain_id
    ).first()
    if domain_source:
        return domain_source.id

    r = requests.post(url=UserServiceApiUrl.DOMAIN_SOURCES, headers=headers, data=json.dumps(source_data))
    print "_add_source_to_domain_response: {}".format(response_info(r))
    assert r.status_code == 201
    return r.json()['source']['id']


def update_domain_candidates_source_ids(domain_id, source_description, access_token, source_to_delete=None):
    """
    Function will update domain candidate's source ID
    """
    headers = {"Authorization": "Bearer %s" % access_token, 'content-type': 'application/json'}

    domain_candidates = None
    if source_to_delete:
        domain_source = CandidateSource.query.filter_by(description=source_to_delete, domain_id=domain_id).first()
        if domain_source:
            domain_candidates = Candidate.query.join(User). \
                filter(User.domain_id == domain_id). \
                filter(Candidate.source_id == domain_source.id).all()
            db.session.delete(domain_source)
            db.session.commit()
            print "deleted domain source: ID = {}".format(domain_source.id)

    if domain_candidates:
        candidate_ids = (candidate.id for candidate in domain_candidates)

        source_id = _add_source_to_domain(
            source_data={'source': {'description': source_description}},
            headers=headers,
            domain_id=domain_id)

        data = {"candidates": [{"id": candidate_id, "source_id": source_id} for candidate_id in set(candidate_ids)]}
        r = requests.patch(url=CandidateApiUrl.CANDIDATES, headers=headers, data=json.dumps(data))
        print "update_candidate_response: {}".format(response_info(r))
        assert r.status_code == 200
        return r.json()


if __name__ == '__main__':
    try:
        start_time = time.time()
        username_ = raw_input("enter your gettalent username: ")
        password_ = raw_input("enter your gettalent password: ")
        source_to_delete = raw_input("enter source description to DELETE: ")
        source_description_ = raw_input("enter source description to CREATE: ")
        auth_service_response = get_access_token(username_, password_)
        user_domain_id = User.get_domain_id(auth_service_response['user_id'])
        update_domain_candidates_source_ids(domain_id=user_domain_id,
                                            source_description=source_description_,
                                            access_token=auth_service_response['access_token'],
                                            source_to_delete=source_to_delete)
        print "Migration script complete. Time: {}".format(time.time() - start_time)
    except Exception as e:
        print "ERROR: {}".format(e)
