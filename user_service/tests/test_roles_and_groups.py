import requests
from user_service.user_app import app
from user_service.common.tests.conftest import *
from user_service.common.models.user import Role
from common_functions import *


def test_user_scoped_roles_get(access_token_first, user_first, user_second):

    user_first.role_id = Role.get_by_name('ADMIN').id
    db.session.commit()

    # Logged-in user getting roles of a non-existing user
    response, status_code = user_scoped_roles(access_token_first, user_id=user_first.id + 1000)
    assert status_code == 404

    # Logged-in user getting roles of a user of different domain
    response, status_code = user_scoped_roles(access_token_first, user_id=user_second.id)
    assert status_code == 401

    # Logged-in user getting roles of itself
    response, status_code = user_scoped_roles(access_token_first, user_id=user_first.id)
    assert status_code == 200
    assert response.get('role_name') == 'ADMIN'

    user_first.role_id = Role.get_by_name('TALENT_ADMIN').id
    db.session.commit()

    # Logged-in user getting roles of itself
    response, status_code = user_scoped_roles(access_token_first, user_id=user_second.id)
    assert status_code == 200
    assert response.get('role_name') == 'USER'


def test_user_scoped_roles_put(access_token_first, user_first, user_second):

    data = {'role': 'TALENT_ADMIN'}
    # Logged-in user trying to add roles to an existing user
    response, status_code = user_scoped_roles(access_token_first, user_first.id, 'PUT', data)
    assert status_code == 401

    user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
    db.session.commit()

    # Logged-in user trying to add roles to a non-existing user
    response, status_code = user_scoped_roles(access_token_first, user_first.id + 1000, 'PUT', data)
    assert status_code == 404

    # Logged-in user trying to add roles to an existing user of different domain
    response, status_code = user_scoped_roles(access_token_first, user_second.id, 'PUT', data)
    assert status_code == 401

    # Logged-in user trying to add 'TALENT_ADMIN' to an existing user of same domain
    response, status_code = user_scoped_roles(access_token_first, user_first.id, 'PUT', data)
    assert status_code == 401

    # Logged-in user trying to add roles to an existing user of same domain
    data = {'role': 'ADMIN'}
    response, status_code = user_scoped_roles(access_token_first, user_first.id, 'PUT', data)
    assert status_code == 201
    db.session.commit()


# def test_get_all_roles(access_token_first, user_first):
#
#     user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
#     db.session.commit()
#
#     headers = {'Authorization': 'Bearer %s' % access_token_first}
#
#     # Logged-in user trying to get all given roles in DB
#     response = requests.get(UserServiceApiUrl.ALL_ROLES_API, headers=headers)
#     assert response.status_code == 200
#     assert len(response.json().get('roles')) == Role.query.count()
#
#     user_first.role_id = Role.get_by_name('USER').id
#     db.session.commit()
#
#     # Logged-in user trying to get all given roles in DB
#     response = requests.get(UserServiceApiUrl.ALL_ROLES_API, headers=headers)
#     assert response.status_code == 401
s

def test_user_groups_get(access_token_first, user_first, user_second, first_group, second_group):

    # Logged-in user getting all users of a non-existing user_group
    response, status_code = user_groups(access_token_first, first_group.id + 1000)
    assert status_code == 404

    # Logged-in user getting all users of a user_group belonging to different domain
    response, status_code = user_groups(access_token_first, second_group.id)
    assert status_code == 401

    # Logged-in user getting all users of a user_group belonging to same domain
    response, status_code = user_groups(access_token_first, first_group.id)
    assert status_code == 200
    assert len(response['users']) == 1

    # Logged-in user getting all users of a user_group belonging to different domain
    user_first.role_id = Role.get_by_name('TALENT_ADMIN').id
    db.session.commit()

    response, status_code = user_groups(access_token_first, second_group.id)
    assert status_code == 200
    assert len(response['users']) == 1


def test_user_groups_post(access_token_first, user_first, user_second, first_group, second_group):

    # Remove user from default groups
    user_first.user_group_id = None
    user_second.user_group_id = None
    db.session.commit()

    # Logged-in user adding a user to user group
    response, status_code = user_groups(access_token_first, first_group.id, user_ids=[user_first.id], action='POST')
    assert status_code == 401

    user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
    db.session.commit()

    # Logged-in user adding a user to non-existing user group
    response, status_code = user_groups(access_token_first, first_group.id + 1000, user_ids=[user_first.id], action='POST')
    assert status_code == 404

    # Logged-in user of different domain adding a user to a user group of different domain
    response, status_code = user_groups(access_token_first, second_group.id, user_ids=[user_first.id], action='POST')
    assert status_code == 401

    # Logged-in user adding a user to a user group
    response, status_code = user_groups(access_token_first, first_group.id, user_ids=[user_first.id], action='POST')
    assert status_code == 201

    db.session.refresh(user_first)
    db.session.commit()

    assert user_first.user_group_id == first_group.id

    # Logged-in user adding a user to a user group
    user_first.role_id = Role.get_by_name('TALENT_ADMIN').id
    db.session.commit()
    response, status_code = user_groups(access_token_first, second_group.id, user_ids=[user_second.id], action='POST')
    assert status_code == 201

    db.session.refresh(user_second)
    db.session.commit()

    assert user_second.user_group_id == second_group.id


def test_domain_groups_api_get(access_token_first, first_group, user_first, user_second):

    # Logged in user trying to get groups of a non-existing domain
    response, status_code = domain_groups(access_token_first, user_first.domain_id + 1000)
    assert status_code == 404

    # Logged in user of different domain trying to get groups of a domain
    response, status_code = domain_groups(access_token_first, user_second.domain_id)
    assert status_code == 401

    # Logged in user trying to get groups of a domain
    response, status_code = domain_groups(access_token_first, user_first.domain_id)
    assert status_code == 200

    assert len(response['user_groups']) == 1
    assert response['user_groups'][0].get('id') == first_group.id


def test_domain_groups_api_post(access_token_first, first_group, user_first, user_second):

    data = {
        'groups': [
            {
                'name': first_group.name
            },
            {
                'name': gen_salt(20)
            }
        ]
    }

    # Logged in user trying to add groups to given domain
    response, status_code = domain_groups(access_token_first, user_first.domain_id, data=data, action='POST')
    assert status_code == 401

    user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
    db.session.commit()

    # Logged in user trying to add groups to non-existing domain
    response, status_code = domain_groups(access_token_first, user_first.domain_id + 1000, data=data, action='POST')
    assert status_code == 404

    # Logged in user of different domain trying to add groups to given domain
    response, status_code = domain_groups(access_token_first, user_second.domain_id, data=data, action='POST')
    assert status_code == 401

    # Logged in user trying to add groups to given domain with empty request_body
    response, status_code = domain_groups(access_token_first, user_first.domain_id, action='POST')
    assert status_code == 400

    # Logged in user trying to add already existing groups to given domain
    response, status_code = domain_groups(access_token_first, user_first.domain_id, data=data, action='POST')
    assert status_code == 400

    # Logged in user trying to add groups to given domain
    data['groups'][0]['name'] = gen_salt(20)
    response, status_code = domain_groups(access_token_first, user_first.domain_id, data=data, action='POST')
    assert status_code == 200
    assert len(response['user_groups']) == 2


def test_domain_groups_api_delete(access_token_first, first_group, second_group, user_first, user_second):

    data = {
        'groups': [first_group.name, gen_salt(20), second_group.name]
    }

    # Logged in user trying to delete groups from a given domain
    response, status_code = domain_groups(access_token_first, user_first.domain_id, data=data, action='DELETE')
    assert status_code == 401

    user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
    db.session.commit()

    # Logged in user trying to delete groups from a non-existing domain
    response, status_code = domain_groups(access_token_first, user_first.domain_id + 1000, data=data, action='DELETE')
    assert status_code == 404

    # Logged in user of different domain trying to delete groups from a domain
    response, status_code = domain_groups(access_token_first, user_second.domain_id, data=data, action='DELETE')
    assert status_code == 401

    # Logged in user trying to delete groups from a domain with empty request body
    response, status_code = domain_groups(access_token_first, user_first.domain_id, action='DELETE')
    assert status_code == 400

    # Logged in user trying to delete groups of different domain from a different domain
    response, status_code = domain_groups(access_token_first, user_first.domain_id, data=data, action='DELETE')
    assert status_code == 400

    # Logged in user trying to delete non-existing groups from a domain
    data['groups'].pop()
    response, status_code = domain_groups(access_token_first, user_first.domain_id, data=data, action='DELETE')
    assert status_code == 400

    # Logged in user trying to delete non-existing groups from a domain
    data['groups'].pop()
    response, status_code = domain_groups(access_token_first, user_first.domain_id, data=data, action='DELETE')
    assert status_code == 200


def test_domain_groups_api_put(access_token_first, first_group, second_group, user_first):

    data = {
        'name': first_group.name,
        'description': gen_salt(20)
    }

    # Logged in user trying to edit group
    response, status_code = domain_groups(access_token_first, data=data, group_id=first_group.id, action='PUT')
    assert status_code == 401

    user_first.role_id = Role.get_by_name('DOMAIN_ADMIN').id
    db.session.commit()

    # Logged in user trying to edit non-existing group
    response, status_code = domain_groups(access_token_first, data=data, group_id=first_group.id + 1000, action='PUT')
    assert status_code == 404

    # Logged in user trying to edit group of different domain
    response, status_code = domain_groups(access_token_first, data=data, group_id=second_group.id, action='PUT')
    assert status_code == 401

    # Logged in user trying to edit group of domain with existing name
    response, status_code = domain_groups(access_token_first, data=data, group_id=first_group.id, action='PUT')
    assert status_code == 400

    # Logged in user trying to edit group of domain
    data['name'] = gen_salt(20)
    response, status_code = domain_groups(access_token_first, data=data, group_id=first_group.id, action='PUT')
    assert status_code == 201

    db.session.refresh(first_group)
    db.session.commit()

    assert first_group.name == data['name']
    assert first_group.description == data['description']


def test_health_check():
    import requests
    response = requests.get(UserServiceApiUrl.HEALTH_CHECK)
    assert response.status_code == 200

    # Testing Health Check URL with trailing slash
    response = requests.get(UserServiceApiUrl.HEALTH_CHECK + '/')
    assert response.status_code == 200
