from candidate_pool_service.candidate_pool_app import app
from candidate_pool_service.common.tests.conftest import *
from common_functions import *

def test_talent_pool_api_post(access_token, domain_admin_access_token, domain_first, domain_second):

    data = {
        'talent_pools': [
            {
                'name': gen_salt(20),
                'description': gen_salt(20),
                'domain_id': domain_first.id
            }
        ]
    }

    # Add a new talent-pool in a domain using ordinary user
    response, status_code = talent_pool_api(access_token, data=data, action='POST')
    assert status_code == 401

    # Add a new talent-pool in a domain using domain_admin_user but with empty data
    response, status_code = talent_pool_api(domain_admin_access_token, action='POST')
    assert status_code == 400

    # Add a new talent-pool in a domain using domain_admin_user but with different domain
    data['talent_pools'][0]['domain_id'] = domain_second.id
    response, status_code = talent_pool_api(domain_admin_access_token, data=data, action='POST')
    assert status_code == 401

    # Add a new talent-pool in a domain using domain_admin_user but with non-numeric domain+id
    data['talent_pools'][0]['domain_id'] = 'abc'
    response, status_code = talent_pool_api(domain_admin_access_token, data=data, action='POST')
    assert status_code == 400

    # Add a new talent-pool in a domain using domain_admin_user but with non-existing domain
    data['talent_pools'][0]['domain_id'] = domain_second.id + 100
    response, status_code = talent_pool_api(domain_admin_access_token, data=data, action='POST')
    assert status_code == 404

    # Add a new talent-pool in a domain using domain_admin_user but with empty name
    data['talent_pools'][0]['domain_id'] = domain_first.id
    data['talent_pools'][0]['name'] = ''
    response, status_code = talent_pool_api(domain_admin_access_token, data=data, action='POST')
    assert status_code == 400

    # Add a new talent-pool in a domain using domain_admin_user
    data['talent_pools'][0]['domain_id'] = domain_first.id
    data['talent_pools'][0]['name'] = gen_salt(20)
    response, status_code = talent_pool_api(domain_admin_access_token, data=data, action='POST')
    assert status_code == 200
    assert len(response.get('talent_pools')) == 1

    # Add a new talent-pool in a domain using domain_admin_user with existing name
    data['talent_pools'][0]['domain_id'] = domain_first.id
    response, status_code = talent_pool_api(domain_admin_access_token, data=data, action='POST')
    assert status_code == 400


def test_talent_pool_api_put(admin_access_token, group_admin_access_token, manage_talent_pool_access_token, talent_pool):

    data = {
        'name': '',
        'description': ''
    }

    # Update a talent-pool using group admin
    response, status_code = talent_pool_api(group_admin_access_token, talent_pool_id=talent_pool.id, action='PUT')
    assert status_code == 401

    # Update a non-existing talent-pool
    response, status_code = talent_pool_api(manage_talent_pool_access_token, talent_pool_id=talent_pool.id + 100,
                                            action='PUT')
    assert status_code == 404

    # Update a talent-pool with empty request body
    response, status_code = talent_pool_api(manage_talent_pool_access_token, talent_pool_id=talent_pool.id, action='PUT')
    assert status_code == 400

    # Update a talent-pool with logged-in user of same domain but with empty name and description
    response, status_code = talent_pool_api(manage_talent_pool_access_token, data=data, talent_pool_id=talent_pool.id,
                                            action='PUT')
    assert status_code == 400

    # Update a talent-pool with admin user but with empty name and description
    response, status_code = talent_pool_api(admin_access_token, data=data, talent_pool_id=talent_pool.id,
                                            action='PUT')
    assert status_code == 400

    # Update a talent-pool with logged-in user of same domain
    data['name'] = gen_salt(20)
    response, status_code = talent_pool_api(manage_talent_pool_access_token, data=data, talent_pool_id=talent_pool.id,
                                            action='PUT')
    assert status_code == 200
    db.session.commit()
    assert talent_pool.name == data['name']

    # Update a talent-pool with logged-in user of same domain but with already existing name
    response, status_code = talent_pool_api(manage_talent_pool_access_token, data=data, talent_pool_id=talent_pool.id,
                                            action='PUT')
    assert status_code == 400


def test_talent_pool_api_delete(access_token, admin_access_token, talent_pool_second):

    # Delete a talent-pool using ordinary user
    response, status_code = talent_pool_api(access_token, talent_pool_id=talent_pool_second.id, action='DELETE')
    assert status_code == 401

    # Delete a non-existing talent-pool using admin user
    response, status_code = talent_pool_api(admin_access_token, talent_pool_id=talent_pool_second.id + 100,
                                            action='DELETE')
    assert status_code == 404

    # Delete a talent-pool using logged-in user of different domain
    response, status_code = talent_pool_api(manage_talent_pool_user, talent_pool_id=talent_pool_second.id,
                                            action='DELETE')
    assert status_code == 401

    # Delete a talent-pool using admin user
    talent_pool_second_id = talent_pool_second.id
    response, status_code = talent_pool_api(admin_access_token, talent_pool_id=talent_pool_second.id, action='DELETE')
    assert status_code == 200
    assert response['deleted_talent_pool']['id'] == talent_pool_second.id

    db.session.commit()
    assert not TalentPool.query.get(talent_pool_second_id)


def test_talent_pool_api_get(access_token, admin_access_token, domain_admin_access_token, group_admin_access_token,
                             manage_talent_pool_access_token, talent_pool, talent_pool_second):

    # GET a non-existing talent-pool using admin user
    response, status_code = talent_pool_api(admin_access_token, talent_pool_id=talent_pool.id + 100)
    assert status_code == 404

    # GET a talent-pool using group_admin_user of different domain
    response, status_code = talent_pool_api(group_admin_access_token, talent_pool_id=talent_pool.id)
    assert status_code == 401

    # GET a talent-pool using ordinary user of same group
    response, status_code = talent_pool_api(access_token, talent_pool_id=talent_pool.id)
    assert status_code == 200
    assert response['talent_pool']['name'] == talent_pool.name

    # GET a talent-pool using domain_admin_user of same domain as talent_pool
    response, status_code = talent_pool_api(domain_admin_access_token, talent_pool_id=talent_pool.id)
    assert status_code == 200
    assert response['talent_pool']['name'] == talent_pool.name

    # GET a talent-pool using ordinary user
    response, status_code = talent_pool_api(access_token, talent_pool_id=talent_pool_second.id)
    assert status_code == 401

    # GET all talent-pools of a domain using ordinary user
    response, status_code = talent_pool_api(access_token)
    assert status_code == 401

    # GET all talent-pools of a domain using talent-pool-manager user
    response, status_code = talent_pool_api(manage_talent_pool_access_token)
    assert status_code == 200
    assert len(response['talent_pools']) == 1
    assert response['talent_pools'][0]['name'] == talent_pool.name


def test_talent_pool_group_api_get(access_token, admin_access_token, domain_admin_access_token,
                                   group_admin_access_token, talent_pool, first_group, second_group):

    # Get all talent-pools of a non-existing user group using ordinary user
    response, status_code = talent_pool_group_api(access_token, user_group_id=first_group.id + 100)
    assert status_code == 404

    # Get all talent-pools of a user group using ordinary user belonging to same group
    response, status_code = talent_pool_group_api(access_token, user_group_id=first_group.id)
    assert status_code == 200
    assert len(response['talent_pools']) == 1
    assert response['talent_pools'][0]['name'] == talent_pool.name

    # Get all talent-pools of a user group using ordinary user belonging to different group
    response, status_code = talent_pool_group_api(access_token, user_group_id=second_group.id)
    assert status_code == 401

    # Get all talent-pools of a user group using group_admin user belonging to different group
    response, status_code = talent_pool_group_api(group_admin_access_token, user_group_id=first_group.id)
    assert status_code == 401

    # Get all talent-pools of a user group using group_admin user belonging to same group
    response, status_code = talent_pool_group_api(group_admin_access_token, user_group_id=second_group.id)
    assert status_code == 200
    assert len(response['talent_pools']) == 0

    # Get all talent-pools of a user group using domain_admin user belonging to same domain as user_group
    response, status_code = talent_pool_group_api(domain_admin_access_token, user_group_id=first_group.id)
    assert status_code == 200
    assert len(response['talent_pools']) == 1
    assert response['talent_pools'][0]['name'] == talent_pool.name

    # Get all talent-pools of a user group using domain_admin user belonging to same domain as user_group
    response, status_code = talent_pool_group_api(domain_admin_access_token, user_group_id=first_group.id)
    assert status_code == 200
    assert len(response['talent_pools']) == 1
    assert response['talent_pools'][0]['name'] == talent_pool.name

    # Get all talent-pools of a user group using admin_user
    response, status_code = talent_pool_group_api(admin_access_token, user_group_id=first_group.id)
    assert status_code == 200
    assert len(response['talent_pools']) == 1
    assert response['talent_pools'][0]['name'] == talent_pool.name


def test_talent_pool_group_api_post(access_token, admin_access_token, domain_admin_access_token, group_admin_access_token,
                             manage_talent_pool_access_token, talent_pool, talent_pool_second, first_group, second_group):

    data = {
        'talent_pools': [talent_pool.id, talent_pool_second.id]
    }

    # Add talent-pools to a user_group using ordinary user
    response, status_code = talent_pool_group_api(access_token, user_group_id=first_group.id, data=data, action='POST')
    assert status_code == 401

    # Add talent-pools to a non-exiting user group using admin user
    response, status_code = talent_pool_group_api(admin_access_token, user_group_id=first_group.id + 100, data=data,
                                                  action='POST')
    assert status_code == 404

    # Add talent-pools to a user group using admin user with empty request body
    response, status_code = talent_pool_group_api(admin_access_token, user_group_id=first_group.id, action='POST')
    assert status_code == 400

    # Add talent-pools to a user group using group admin user belonging to different group
    response, status_code = talent_pool_group_api(group_admin_access_token, user_group_id=first_group.id, data=data,
                                                  action='POST')
    assert status_code == 401

    # Add talent-pools to a user group using manage-talent-pool user belonging to different domain as user group
    response, status_code = talent_pool_group_api(manage_talent_pool_access_token, user_group_id=second_group.id,
                                                  data=data, action='POST')
    assert status_code == 401

    # Add talent-pools to a user group using domain_admin user belonging to different domain as user group
    response, status_code = talent_pool_group_api(domain_admin_access_token, user_group_id=second_group.id,
                                                  data=data, action='POST')
    assert status_code == 401

    # Add talent-pools to a user group using domain_admin user
    response, status_code = talent_pool_group_api(domain_admin_access_token, user_group_id=first_group.id,
                                                  data=data, action='POST')
    assert status_code == 400  # talent-pool already exist in first_group

    # Add non-existing talent-pool to a user group using domain_admin user
    data['talent_pools'][0] = talent_pool.id + 100
    response, status_code = talent_pool_group_api(domain_admin_access_token, user_group_id=first_group.id,
                                                  data=data, action='POST')
    assert status_code == 404

    # Add talent-pool to a user group using domain_admin user
    del data['talent_pools'][0]
    response, status_code = talent_pool_group_api(domain_admin_access_token, user_group_id=first_group.id,
                                                  data=data, action='POST')
    assert status_code == 400

    # Add talent-pool to a user group using group_admin user
    response, status_code = talent_pool_group_api(group_admin_access_token, user_group_id=second_group.id,
                                                  data=data, action='POST')
    assert status_code == 200
    assert len(response['added_talent_pools']) == 1
    assert response['added_talent_pools'] == [talent_pool_second.id]
    db.session.commit()
    assert TalentPoolGroup.query.filter_by(user_group_id=second_group.id, talent_pool_id=talent_pool_second.id)


def test_talent_pool_group_api_delete(access_token, admin_access_token, domain_admin_access_token, group_admin_access_token,
                             manage_talent_pool_access_token, talent_pool, talent_pool_second, first_group, second_group):

    data = {
        "talent_pools": [talent_pool_second.id, talent_pool.id]
    }

    # Delete talent-pools from a user_group using ordinary user
    response, status_code = talent_pool_group_api(access_token, user_group_id=first_group.id, data=data, action='DELETE')
    assert status_code == 401

    # Delete talent-pools from a non-exiting user group using admin user
    response, status_code = talent_pool_group_api(admin_access_token, user_group_id=first_group.id + 100, data=data,
                                                  action='DELETE')
    assert status_code == 404

    # Delete talent-pools from a user group using admin user with empty request body
    response, status_code = talent_pool_group_api(admin_access_token, user_group_id=first_group.id, action='DELETE')
    assert status_code == 400

    # Delete talent-pools from a user group using group admin user belonging to different group
    response, status_code = talent_pool_group_api(group_admin_access_token, user_group_id=first_group.id, data=data,
                                                  action='DELETE')
    assert status_code == 401

    # Delete talent-pools from a user group using manage-talent-pool user belonging to different domain as user group
    response, status_code = talent_pool_group_api(manage_talent_pool_access_token, user_group_id=second_group.id,
                                                  data=data, action='DELETE')
    assert status_code == 401

    # Delete talent-pools from a user group using domain_admin user belonging to different domain as user group
    response, status_code = talent_pool_group_api(domain_admin_access_token, user_group_id=second_group.id,
                                                  data=data, action='DELETE')
    assert status_code == 401

    # Delete talent-pools from a user group using domain_admin user
    response, status_code = talent_pool_group_api(domain_admin_access_token, user_group_id=first_group.id,
                                                  data=data, action='DELETE')
    assert status_code == 404  # talent-pool already exist in first_group

    # Add talent-pool to a user group using domain_admin user
    del data['talent_pools'][0]
    response, status_code = talent_pool_group_api(domain_admin_access_token, user_group_id=first_group.id,
                                                  data=data, action='DELETE')
    assert status_code == 200
    assert len(response['deleted_talent_pools']) == 1
    assert response['deleted_talent_pools'] == [talent_pool.id]


def test_talent_pool_candidate_api_post(access_token, admin_access_token, domain_admin_access_token,
                                        manage_talent_pool_access_token, talent_pool, talent_pool_second, candidate_first,
                                        candidate_second):

    data = {
        'talent_pool_candidates': ['a', candidate_second.id]
    }

    # Add candidates to a talent_pool using admin user but with empty request body
    response, status_code = talent_pool_candidate_api(admin_access_token, talent_pool.id, action='POST')
    assert status_code == 400

    # Add candidates to a non-existing talent_pool using admin user
    response, status_code = talent_pool_candidate_api(admin_access_token, talent_pool.id + 100, data=data, action='POST')
    assert status_code == 404

    # Add candidates to a talent_pool using ordinary user
    response, status_code = talent_pool_candidate_api(access_token, talent_pool_second.id, data=data, action='POST')
    assert status_code == 401

    # Add candidates to a talent_pool using domain_admin_user
    response, status_code = talent_pool_candidate_api(domain_admin_access_token, talent_pool_second.id, data=data,
                                                      action='POST')
    assert status_code == 401

    # Add candidates to a talent_pool using manage_talent_pool user
    response, status_code = talent_pool_candidate_api(manage_talent_pool_access_token, talent_pool_second.id, data=data,
                                                      action='POST')
    assert status_code == 401

    # Add candidates with non-integer id to a talent_pool using ordinary user
    response, status_code = talent_pool_candidate_api(access_token, talent_pool.id, data=data, action='POST')
    assert status_code == 400

    # Add non-existing candidates to a talent_pool using ordinary user
    data['talent_pool_candidates'][0] = candidate_first.id + 100
    response, status_code = talent_pool_candidate_api(access_token, talent_pool.id, data=data, action='POST')
    assert status_code == 404

    # Add candidates to a talent_pool using ordinary user
    data['talent_pool_candidates'][0] = candidate_first.id
    response, status_code = talent_pool_candidate_api(access_token, talent_pool.id, data=data, action='POST')
    assert status_code == 200
    assert len(response['added_talent_pool_candidates']) == 2
    assert response['added_talent_pool_candidates'] == data['talent_pool_candidates']

    # Add already existing candidates to a talent_pool using ordinary user
    response, status_code = talent_pool_candidate_api(access_token, talent_pool.id, data=data, action='POST')
    assert status_code == 400


def test_talent_pool_candidate_api_get(access_token, admin_access_token, domain_admin_access_token,
                                       manage_talent_pool_access_token, talent_pool, talent_pool_second, candidate_first,
                                       candidate_second):

    data = {
        'talent_pool_candidates': [candidate_first.id, candidate_second.id]
    }

    # Add candidates to a talent_pool using ordinary user
    response, status_code = talent_pool_candidate_api(access_token, talent_pool.id, data=data, action='POST')
    assert status_code == 200

    # Get candidates from non-existing talent_pool
    response, status_code = talent_pool_candidate_api(access_token, talent_pool.id + 100)
    assert status_code == 404

    # Get candidates from a talent_pool using ordinary user
    response, status_code = talent_pool_candidate_api(access_token, talent_pool_second.id)
    assert status_code == 401

    # Get candidates from a talent_pool using ordinary domain_admin_user
    response, status_code = talent_pool_candidate_api(domain_admin_access_token, talent_pool_second.id)
    assert status_code == 401

    # Get candidates from a talent_pool using manage_talent_pool user
    response, status_code = talent_pool_candidate_api(manage_talent_pool_access_token, talent_pool_second.id)
    assert status_code == 401

    # Get candidates from a talent_pool using ordinary user
    response, status_code = talent_pool_candidate_api(access_token, talent_pool.id)
    assert status_code == 200
    assert len(response['talent_pool_candidates']) == 2
    assert [candidate.get('id') for candidate in response['talent_pool_candidates']] == data['talent_pool_candidates']

    # Get candidates from a talent_pool using admin user
    response, status_code = talent_pool_candidate_api(admin_access_token, talent_pool_second.id)
    assert status_code == 200
    assert len(response['talent_pool_candidates']) == 0


def test_talent_pool_candidate_api_delete(access_token, admin_access_token, domain_admin_access_token,
                                          manage_talent_pool_access_token, talent_pool, talent_pool_second,
                                          candidate_first, candidate_second):

    data = {
        'talent_pool_candidates': [candidate_first.id, candidate_second.id]
    }

    # Add candidates to a talent_pool using ordinary user
    response, status_code = talent_pool_candidate_api(access_token, talent_pool.id, data=data, action='POST')
    assert status_code == 200

    # Delete candidates from a talent_pool using admin user but with empty request body
    response, status_code = talent_pool_candidate_api(admin_access_token, talent_pool.id, action='DELETE')
    assert status_code == 400

    # Delete candidates from a non-existing talent_pool using admin user
    response, status_code = talent_pool_candidate_api(admin_access_token, talent_pool.id + 100, data=data, action='DELETE')
    assert status_code == 404

    # Delete candidates from a talent_pool using ordinary user
    response, status_code = talent_pool_candidate_api(access_token, talent_pool_second.id, data=data, action='DELETE')
    assert status_code == 401

    # Delete candidates from a talent_pool using domain_admin_user
    response, status_code = talent_pool_candidate_api(domain_admin_access_token, talent_pool_second.id, data=data,
                                                      action='DELETE')
    assert status_code == 401

    # Delete candidates from a talent_pool using manage_talent_pool user
    response, status_code = talent_pool_candidate_api(manage_talent_pool_access_token, talent_pool_second.id, data=data,
                                                      action='DELETE')
    assert status_code == 401

    # Delete candidates with non-integer id from a talent_pool using ordinary user
    data['talent_pool_candidates'][0] = 'a'
    response, status_code = talent_pool_candidate_api(access_token, talent_pool.id, data=data, action='DELETE')
    assert status_code == 400

    # Delete non-existing candidates from a talent_pool using ordinary user
    data['talent_pool_candidates'][0] = candidate_first.id + 100
    response, status_code = talent_pool_candidate_api(access_token, talent_pool.id, data=data, action='DELETE')
    assert status_code == 404

    # Delete candidates from a talent_pool using ordinary user
    data['talent_pool_candidates'][0] = candidate_first.id
    response, status_code = talent_pool_candidate_api(access_token, talent_pool.id, data=data, action='DELETE')
    assert status_code == 200
    assert len(response['deleted_talent_pool_candidates']) == 2
    assert response['deleted_talent_pool_candidates'] == data['talent_pool_candidates']


def test_health_check():
    import requests
    response = requests.get(CANDIDATE_POOL_SERVICE_ENDPOINT % 'healthcheck')
    assert response.status_code == 200

