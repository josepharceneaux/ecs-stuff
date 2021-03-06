# Candidate Pool Service app instance
from candidate_pool_service.candidate_pool_app import app

from candidate_pool_service.common.tests.conftest import *
from candidate_pool_service.common.utils.test_utils import response_info
from candidate_pool_service.common.models.user import Role
from common_functions import *


def test_talent_pool_api_post(access_token_first, access_token_second, user_first, user_second):

    data = {
        'talent_pools': [
            {
                'name': gen_salt(20),
                'description': gen_salt(20)
            }
        ]
    }

    # Logged-in user trying to add a new talent-pool in a domain
    response, status_code = talent_pool_api(access_token_first, data=data, action='POST')
    assert status_code == 401

    user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
    db.session.commit()

    # Logged-in user trying to add a new talent-pool in a domain with empty request body
    response, status_code = talent_pool_api(access_token_first, action='POST')
    assert status_code == 400

    # Logged-in user trying to add a new talent-pool in a domain with empty name
    data['talent_pools'][0]['name'] = ''
    response, status_code = talent_pool_api(access_token_first, data=data, action='POST')
    assert status_code == 400

    # Logged-in user trying to add a new talent-pool in a domain
    data['talent_pools'][0]['name'] = gen_salt(20)
    response, status_code = talent_pool_api(access_token_first, data=data, action='POST')
    assert status_code == 200
    assert len(response.get('talent_pools')) == 1

    # Logged-in user trying to add a new talent-pool with existing name in a domain
    response, status_code = talent_pool_api(access_token_first, data=data, action='POST')
    assert status_code == 400

    user_second.role_id = Role.get_by_name('TALENT_ADMIN').id
    db.session.commit()

    # Admin user trying to add a new talent-pool in another domain
    data['talent_pools'][0]['user_id'] = user_first.id
    data['talent_pools'][0]['name'] = gen_salt(20)
    response, status_code = talent_pool_api(access_token_second, data=data, action='POST')
    assert status_code == 200
    assert len(response.get('talent_pools')) == 1


def test_talent_pool_api_put(access_token_first, user_first, talent_pool, talent_pool_second):

    data = {
        'talent_pool': {
            'name': '',
            'description': ''
        }
    }
    # Logged-in user trying to update a talent-pool
    response, status_code = talent_pool_api(access_token_first, talent_pool_id=talent_pool.id, data=data, action='PUT')
    assert status_code == 401

    user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
    db.session.commit()

    # Logged-in user trying to update a non-existing talent-pool
    response, status_code = talent_pool_api(access_token_first, talent_pool_id=talent_pool.id + 1000, data=data,
                                            action='PUT')
    assert status_code == 404

    # Logged-in user trying to update a talent-pool but with empty request body
    response, status_code = talent_pool_api(access_token_first, talent_pool_id=talent_pool.id, action='PUT')
    assert status_code == 400

    # Logged-in user trying to update a talent-pool of different domain
    response, status_code = talent_pool_api(access_token_first, talent_pool_id=talent_pool_second.id, data=data,
                                            action='PUT')
    assert status_code == 403

    # Logged-in user trying to update a talent-pool but with empty name and description
    response, status_code = talent_pool_api(access_token_first, talent_pool_id=talent_pool.id, data=data, action='PUT')
    assert status_code == 400

    # Update a talent-pool with logged-in user of same domain
    data['talent_pool']['name'] = gen_salt(20)
    response, status_code = talent_pool_api(access_token_first, talent_pool_id=talent_pool.id, data=data, action='PUT')
    assert status_code == 200
    db.session.commit()
    assert talent_pool.name == data['talent_pool']['name']

    # Update a talent-pool with logged-in user of same domain but with already existing name
    response, status_code = talent_pool_api(access_token_first, talent_pool_id=talent_pool.id, data=data, action='PUT')
    assert status_code == 400

    user_first.role_id = Role.get_by_name('TALENT_ADMIN').id
    db.session.commit()

    # Logged-in user trying to update a talent-pool of different domain
    response, status_code = talent_pool_api(access_token_first, talent_pool_id=talent_pool_second.id, data=data,
                                            action='PUT')
    assert status_code == 200
    db.session.commit()
    assert talent_pool_second.name == data['talent_pool']['name']


def test_talent_pool_api_delete(access_token_first, user_first, talent_pool, talent_pool_second,
                                candidate_first, candidate_second):

    data = {
        'talent_pool_candidates': [candidate_first.id, candidate_second.id]
    }

    # Logged-in user trying to add candidates to talent_pool
    response, status_code = talent_pool_candidate_api(access_token_first, talent_pool.id, data=data, action='POST')
    assert status_code == 200

    user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
    db.session.commit()

    # Logged-in user trying to delete a non-existing talent-pool
    response, status_code = talent_pool_api(access_token_first, talent_pool_id=talent_pool_second.id + 1000,
                                            action='DELETE')
    assert status_code == 404

    # Delete a talent-pool using logged-in user of different domain
    response, status_code = talent_pool_api(access_token_first, talent_pool_id=talent_pool_second.id, action='DELETE')
    assert status_code == 403

    # Delete a talent-pool using admin user
    talent_pool_id = talent_pool.id
    response, status_code = talent_pool_api(access_token_first, talent_pool_id=talent_pool_id, action='DELETE')
    assert status_code == 200
    assert response['talent_pool']['id'] == talent_pool_id

    db.session.commit()
    assert not TalentPool.query.get(talent_pool_id)

    user_first.role_id = Role.get_by_name('TALENT_ADMIN').id
    db.session.commit()

    # Delete a talent-pool using logged-in user of different domain
    talent_pool_id = talent_pool_second.id
    response, status_code = talent_pool_api(access_token_first, talent_pool_id=talent_pool_second.id, action='DELETE')
    assert status_code == 200
    assert response['talent_pool']['id'] == talent_pool_id

    db.session.commit()
    assert not TalentPool.query.get(talent_pool_id)


def test_talent_pool_api_get(access_token_first, access_token_second, user_first, user_second, talent_pool,
                             talent_pool_second):

    # Logged-in user trying to get non-existing talent-pool's info
    response, status_code = talent_pool_api(access_token_first, talent_pool_id=talent_pool.id + 1000)
    assert status_code == 404

    # Logged-in user trying to get talent-pool's info of different domain
    response, status_code = talent_pool_api(access_token_first, talent_pool_id=talent_pool_second.id)
    assert status_code == 403

    # Logged-in user of same group trying to get talent-pool's info
    response, status_code = talent_pool_api(access_token_first, talent_pool_id=talent_pool.id)
    assert status_code == 200
    assert response['talent_pool']['name'] == talent_pool.name

    user_first.role_id = Role.get_by_name('TALENT_ADMIN').id
    db.session.commit()

    # Logged-in user trying to get talent-pool's info of different domain
    response, status_code = talent_pool_api(access_token_first, talent_pool_id=talent_pool_second.id)
    assert status_code == 200
    assert response['talent_pool']['name'] == talent_pool_second.name

    user_second.domain_id = user_first.domain_id
    db.session.commit()

    # Logged-in user trying to get talent-pool's info
    response, status_code = talent_pool_api(access_token_second, talent_pool_id=talent_pool.id)
    assert status_code == 403

    user_second.role_id = Role.get_by_name('TALENT_ADMIN').id
    db.session.commit()

    # Logged-in user trying to get talent-pool's info
    response, status_code = talent_pool_api(access_token_second, talent_pool_id=talent_pool.id)
    assert status_code == 200
    assert response['talent_pool']['name'] == talent_pool.name

    # GET all talent-pools of a domain using talent-pool-manager user
    response, status_code = talent_pool_api(access_token_first, params={'domain_id': user_first.domain_id})
    assert status_code == 200
    assert len(response['talent_pools']) == 1
    assert response['talent_pools'][0]['name'] == talent_pool.name


def test_talent_pool_group_api_get(access_token_first, access_token_second, user_first, user_second, talent_pool,
                                   first_group, second_group):

    user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
    db.session.commit()

    # Logged-in user trying to get talent pools of non-existing group
    response, status_code = talent_pool_group_api(access_token_first, user_group_id=first_group.id + 1000)
    print response_info(response)
    assert status_code == 404

    # Logged-in user trying to get talent pools of group of different domain
    response, status_code = talent_pool_group_api(access_token_first, user_group_id=second_group.id)
    assert status_code == 403

    # Logged-in user trying to get talent pools of group
    response, status_code = talent_pool_group_api(access_token_first, user_group_id=first_group.id)
    assert status_code == 200
    assert len(response['talent_pools']) == 1
    assert response['talent_pools'][0]['name'] == talent_pool.name

    user_first.role_id = Role.get_by_name('TALENT_ADMIN').id
    db.session.commit()

    # Logged-in user trying to get talent pools of group of different domain
    response, status_code = talent_pool_group_api(access_token_first, user_group_id=second_group.id)
    assert status_code == 200
    assert len(response['talent_pools']) == 0

    user_second.domain_id = user_first.domain_id
    db.session.commit()

    user_second.role_id = Role.get_by_name('DOMAIN_ADMIN').id
    db.session.commit()

    # Logged-in user of same domain but different group trying to get talent pools of another group
    response, status_code = talent_pool_group_api(access_token_second, user_group_id=second_group.id)
    assert status_code == 403

    # Logged-in user of same domain but different group trying to get talent pools of another group
    response, status_code = talent_pool_group_api(access_token_second, user_group_id=first_group.id)
    assert status_code == 200
    assert len(response['talent_pools']) == 1
    assert response['talent_pools'][0]['name'] == talent_pool.name


def test_talent_pool_group_api_post(access_token_first, user_first, user_second, talent_pool, talent_pool_second,
                                    first_group, second_group):

    data = {
        'talent_pools': [talent_pool.id, talent_pool_second.id]
    }

    # Logged-in user trying to add talent-pools in a group
    response, status_code = talent_pool_group_api(access_token_first, user_group_id=first_group.id, data=data,
                                                  action='POST')
    assert status_code == 401

    user_first.role_id = Role.get_by_name('TALENT_ADMIN').id
    db.session.commit()

    # Logged-in user trying to add talent-pools in a non-existing group
    response, status_code = talent_pool_group_api(access_token_first, user_group_id=first_group.id + 1000, data=data,
                                                  action='POST')
    assert status_code == 404

    # Logged-in user trying to add talent-pools in a group with empty request body
    response, status_code = talent_pool_group_api(access_token_first, user_group_id=first_group.id, action='POST')
    assert status_code == 400

    # Logged-in user trying to add talent-pools in a group of a different domain
    response, status_code = talent_pool_group_api(access_token_first, user_group_id=second_group.id, data=data,
                                                  action='POST')
    assert status_code == 403

    # Logged-in user trying to add talent-pools in a group
    data['talent_pools'].pop(1)
    response, status_code = talent_pool_group_api(access_token_first, user_group_id=first_group.id, data=data,
                                                  action='POST')
    assert status_code == 400

    talent_pool.domain_id = user_second.domain_id
    db.session.commit()

    # Logged-in user trying to add talent-pools in a group
    response, status_code = talent_pool_group_api(access_token_first, user_group_id=second_group.id, data=data,
                                                  action='POST')
    assert status_code == 200
    assert len(response['added_talent_pools']) == 1
    assert response['added_talent_pools'] == [talent_pool.id]
    db.session.commit()
    assert TalentPoolGroup.query.filter_by(user_group_id=second_group.id, talent_pool_id=talent_pool.id).first()


def test_talent_pool_group_api_delete(access_token_first, user_first, talent_pool, talent_pool_second, first_group,
                                      second_group):

    data = {
        "talent_pools": [talent_pool_second.id, talent_pool.id]
    }

    # Logged-in user trying to remove talent-pools from a group
    response, status_code = talent_pool_group_api(access_token_first, user_group_id=first_group.id, data=data,
                                                  action='DELETE')
    assert status_code == 401

    user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
    db.session.commit()

    # Logged-in user trying to remove talent-pools from a non-existing group
    response, status_code = talent_pool_group_api(access_token_first, user_group_id=first_group.id + 1000, data=data,
                                                  action='DELETE')
    assert status_code == 404

    # Logged-in user trying to remove talent-pools from a group with empty request body
    response, status_code = talent_pool_group_api(access_token_first, user_group_id=first_group.id, action='DELETE')
    assert status_code == 400

    # Logged-in user trying to remove talent-pools from a group of different domain
    response, status_code = talent_pool_group_api(access_token_first, user_group_id=second_group.id, data=data,
                                                  action='DELETE')
    assert status_code == 403

    # Logged-in user trying to remove non-existing talent-pools from a group
    response, status_code = talent_pool_group_api(access_token_first, user_group_id=first_group.id, data=data,
                                                  action='DELETE')
    assert status_code == 404

    # Logged-in user trying to remove talent-pools from a group
    data['talent_pools'].pop(0)
    response, status_code = talent_pool_group_api(access_token_first, user_group_id=first_group.id, data=data,
                                                  action='DELETE')
    assert status_code == 200
    assert len(response['talent_pools']) == 1
    assert response['talent_pools'] == [talent_pool.id]

    db.session.commit()
    assert not TalentPoolGroup.query.filter_by(user_group_id=first_group.id, talent_pool_id=talent_pool.id).first()

    user_first.role_id = Role.get_by_name('TALENT_ADMIN').id
    db.session.commit()

    # Logged-in user trying to remove talent-pools from a group of different domain
    data['talent_pools'] = [talent_pool_second.id]
    response, status_code = talent_pool_group_api(access_token_first, user_group_id=second_group.id, data=data,
                                                  action='DELETE')
    assert status_code == 200
    assert len(response['talent_pools']) == 1
    assert response['talent_pools'] == [talent_pool_second.id]

    db.session.commit()
    assert not TalentPoolGroup.query.filter_by(user_group_id=second_group.id, talent_pool_id=talent_pool_second.id).first()


def test_talent_pool_candidate_api_post(access_token_first, user_first, talent_pool, talent_pool_second,
                                        candidate_first, candidate_second):

    data = {
        'talent_pool_candidates': ['a', candidate_second.id]
    }

    # Logged-in user trying to add candidates to a talent-pool with empty request body
    response, status_code = talent_pool_candidate_api(access_token_first, talent_pool.id, action='POST')
    assert status_code == 400

    # Logged-in user trying to add candidates to a non-existing talent-pool
    response, status_code = talent_pool_candidate_api(access_token_first, talent_pool.id + 1000, data=data, action='POST')
    assert status_code == 404

    # Logged-in user trying to add candidates to a talent-pool of different domain
    response, status_code = talent_pool_candidate_api(access_token_first, talent_pool_second.id, data=data,
                                                      action='POST')
    assert status_code == 403

    # Logged-in user trying to add candidates to a talent-pool with non-integer candidate ids
    response, status_code = talent_pool_candidate_api(access_token_first, talent_pool.id, data=data, action='POST')
    assert status_code == 400

    # Logged-in user trying to add non-existing candidates to a talent-pool
    data['talent_pool_candidates'][0] = candidate_first.id + 1000
    response, status_code = talent_pool_candidate_api(access_token_first, talent_pool.id, data=data, action='POST')
    assert status_code == 404

    # Logged-in user trying to add candidates to a talent-pool
    data['talent_pool_candidates'][0] = candidate_first.id
    response, status_code = talent_pool_candidate_api(access_token_first, talent_pool.id, data=data, action='POST')
    assert status_code == 200
    assert len(response['added_talent_pool_candidates']) == 2
    assert response['added_talent_pool_candidates'] == data['talent_pool_candidates']

    user_first.user_group_id = None
    db.session.commit()

    user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
    db.session.commit()

    # Logged-in user trying to add existing candidates to a talent-pool
    response, status_code = talent_pool_candidate_api(access_token_first, talent_pool.id, data=data, action='POST')
    assert status_code == 400


def test_talent_pool_candidate_api_get(access_token_first, user_first, talent_pool, talent_pool_second,
                                        candidate_first, candidate_second):

    data = {
        'talent_pool_candidates': [candidate_first.id, candidate_second.id]
    }

    # Logged-in user trying to add candidates to talent_pool
    response, status_code = talent_pool_candidate_api(access_token_first, talent_pool.id, data=data, action='POST')
    assert status_code == 200

    # Logged-in user trying to get candidates from non-existing talent_pool
    response, status_code = talent_pool_candidate_api(access_token_first, talent_pool.id + 1000)
    assert status_code == 404

    # Logged-in user trying to get candidates from talent_pool of different domain
    response, status_code = talent_pool_candidate_api(access_token_first, talent_pool_second.id)
    assert status_code == 403

    # Logged-in user trying to get candidates from talent_pool
    response, status_code = talent_pool_candidate_api(access_token_first, talent_pool.id, expected_count=2)
    assert status_code == 200
    assert response['talent_pool_candidates']['total_found'] == 2

    user_first.user_group_id = None
    db.session.commit()

    # Logged-in user trying to get candidates from talent_pool of different group
    response, status_code = talent_pool_candidate_api(access_token_first, talent_pool.id)
    assert status_code == 403

    user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
    db.session.commit()

    # Logged-in user trying to get candidates from talent_pool
    response, status_code = talent_pool_candidate_api(access_token_first, talent_pool.id, expected_count=2)
    assert status_code == 200
    assert response['talent_pool_candidates']['total_found'] == 2


def test_talent_pool_candidate_api_delete(access_token_first, user_first, talent_pool, talent_pool_second,
                                          candidate_first, candidate_second):

    data = {
        'talent_pool_candidates': [candidate_first.id, candidate_second.id]
    }

    # Logged-in user trying to add candidates to talent_pool
    response, status_code = talent_pool_candidate_api(access_token_first, talent_pool.id, data=data, action='POST')
    assert status_code == 200

    user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
    db.session.commit()

    # Logged-in user trying to delete candidates from talent_pool with empty request body
    response, status_code = talent_pool_candidate_api(access_token_first, talent_pool.id, action='DELETE')
    assert status_code == 400

    # Logged-in user trying to delete candidates from non-existing talent_pool
    response, status_code = talent_pool_candidate_api(access_token_first, talent_pool.id + 1000, data=data, action='DELETE')
    assert status_code == 404

    # Logged-in user trying to delete candidates from talent_pool of different domain
    response, status_code = talent_pool_candidate_api(access_token_first, talent_pool_second.id, data=data, action='DELETE')
    assert status_code == 403

    # Logged-in user trying to delete candidates with non-integer id from talent_pool
    data['talent_pool_candidates'][0] = 'a'
    response, status_code = talent_pool_candidate_api(access_token_first, talent_pool.id, data=data, action='DELETE')
    assert status_code == 400

    # Logged-in user trying to delete non-existing candidates from talent_pool
    data['talent_pool_candidates'][0] = candidate_first.id + 1000
    response, status_code = talent_pool_candidate_api(access_token_first, talent_pool.id, data=data, action='DELETE')
    assert status_code == 404

    # Logged-in user trying to delete candidates from talent_pool
    data['talent_pool_candidates'][0] = candidate_first.id
    response, status_code = talent_pool_candidate_api(access_token_first, talent_pool.id, data=data, action='DELETE')
    assert status_code == 200
    assert len(response['talent_pool_candidates']) == 2
    assert response['talent_pool_candidates'] == data['talent_pool_candidates']

    user_first.user_group_id = None
    db.session.commit()

    # Logged-in user trying to delete existing candidates from a talent-pool
    response, status_code = talent_pool_candidate_api(access_token_first, talent_pool.id, data=data, action='DELETE')
    assert status_code == 404


def test_get_all_talent_pipelines_of_talent_pools(access_token_first, user_first, talent_pool, talent_pool_second,
                                                  talent_pipeline):

    # Logged-in user trying to get all talent-pipelines of a non-existing talent_pool
    response, status_code = get_talent_pipelines_of_talent_pools(access_token_first, talent_pool.id + 1000)
    assert status_code == 404

    # Logged-in user trying to get all talent-pipelines of a non-existing talent_pool
    response, status_code = get_talent_pipelines_of_talent_pools(access_token_first, talent_pool_second.id)
    assert status_code == 403

    # Logged-in user trying to get all talent-pipelines of a talent_pool
    response, status_code = get_talent_pipelines_of_talent_pools(access_token_first, talent_pool.id)
    assert status_code == 200
    assert len(response.get('talent_pipelines')) == 1
    assert response.get('talent_pipelines')[0].get('id') == talent_pipeline.id

    user_first.user_group_id = None
    db.session.commit()

    # Logged-in user trying to get all talent-pipelines of a talent_pool of different group
    response, status_code = get_talent_pipelines_of_talent_pools(access_token_first, talent_pool.id)
    assert status_code == 403

    user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
    db.session.commit()

    # Logged-in user trying to get all talent-pipelines of a talent_pool
    response, status_code = get_talent_pipelines_of_talent_pools(access_token_first, talent_pool.id)
    assert status_code == 200
    assert len(response.get('talent_pipelines')) == 1


def test_health_check():
    import requests
    response = requests.get(CandidatePoolApiUrl.HEALTH_CHECK)
    assert response.status_code == 200

    # Testing Health Check URL with trailing slash
    response = requests.get(CandidatePoolApiUrl.HEALTH_CHECK + '/')
    assert response.status_code == 200

