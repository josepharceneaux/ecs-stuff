from user_service.user_app import app
from user_service.common.tests.conftest import *
from user_service.common.utils.common_functions import add_role_to_test_user
from user_service.common.models.user import UserScopedRoles
from common_functions import *


def test_user_scoped_roles_get(access_token_first, access_token_second, user_first, user_second, domain_roles, domain_first):

    # Logged-in user getting roles of a non-existing user
    response, status_code = user_scoped_roles(access_token_first, user_id=user_first.id + 100)
    assert status_code == 404

    # Logged-in user getting roles of a user of different domain
    response, status_code = user_scoped_roles(access_token_first, user_id=user_second.id)
    assert status_code == 401

    # Logged-in user getting roles of itself
    response, status_code = user_scoped_roles(access_token_first, user_id=user_first.id)
    assert status_code == 200
    assert not response.get('roles')  # user doesn't have any roles

    # Add roles to user
    add_role_to_test_user(user_first, domain_roles['test_roles'])

    # Logged-in user getting roles of itself
    response, status_code = user_scoped_roles(access_token_first, user_id=user_first.id)
    assert status_code == 200
    assert set(response.get('roles')) == set([domain_role.id for domain_role in DomainRole.query.filter(
        DomainRole.role_name.in_(domain_roles['test_roles']))])

    # Add 'CAN_GET_USER_ROLES' to user_second
    add_role_to_test_user(user_second, ['CAN_GET_USER_ROLES'])

    # Logged-in user with 'CAN_GET_USER_ROLES' role trying to get roles of an existing user of different domain
    response, status_code = user_scoped_roles(access_token_second, user_id=user_first.id)
    assert status_code == 401

    # Change domain of user_second
    user_second.domain_id = domain_first.id
    db.session.commit()

    # Logged-in user with 'CAN_GET_USER_ROLES' role trying to get roles of an existing user of same domain
    response, status_code = user_scoped_roles(access_token_second, user_id=user_first.id)
    assert status_code == 200
    assert set(response.get('roles')) == set([domain_role.id for domain_role in DomainRole.query.filter(
        DomainRole.role_name.in_(domain_roles['test_roles']))])


def test_user_scoped_roles_post(access_token_first, user_first, user_second, domain_roles):

    # Logged-in user trying to add roles to an existing user
    response, status_code = user_scoped_roles(access_token_first, user_id=user_first.id, action='POST',
                                              test_roles=domain_roles['test_roles'])
    assert status_code == 401

    # Add 'CAN_ADD_USER_ROLES' role to user
    add_role_to_test_user(user_first, ['CAN_ADD_USER_ROLES'])

    # Logged-in user trying to add roles to a non-existing user
    response, status_code = user_scoped_roles(access_token_first, user_id=user_first.id + 100, action='POST',
                                              test_roles=domain_roles['test_roles'])
    assert status_code == 404

    # Logged-in user trying to add roles to an existing user of different domain
    response, status_code = user_scoped_roles(access_token_first, user_id=user_second.id, action='POST',
                                              test_roles=domain_roles['test_roles'])
    assert status_code == 401

    # Logged-in user trying to add non-existing roles to an existing user of same domain
    response, status_code = user_scoped_roles(access_token_first, user_id=user_first.id, action='POST',
                                              test_roles=domain_roles['test_roles'], false_case=True)
    assert status_code == 400

    # Logged-in user trying to add roles to an existing user of same domain
    response, status_code = user_scoped_roles(access_token_first, user_id=user_first.id, action='POST',
                                              test_roles=domain_roles['test_roles'])
    assert status_code == 200
    db.session.commit()
    assert len(UserScopedRoles.get_all_roles_of_user(user_first.id)) == 3


def test_user_scoped_roles_delete(access_token_first, user_first, user_second, domain_roles):

    # Logged-in user trying to remove roles from an existing user
    response, status_code = user_scoped_roles(access_token_first, user_id=user_first.id, action='DELETE',
                                              test_roles=domain_roles['test_roles'])
    assert status_code == 401

    # Add 'CAN_DELETE_USER_ROLES' role to user
    add_role_to_test_user(user_first, ['CAN_DELETE_USER_ROLES'])

    # Logged-in user trying to remove roles from a non-existing user
    response, status_code = user_scoped_roles(access_token_first, user_id=user_first.id + 100, action='DELETE',
                                              test_roles=domain_roles['test_roles'])
    assert status_code == 404

    # Logged-in user trying to remove roles from an existing user of different domain
    response, status_code = user_scoped_roles(access_token_first, user_id=user_second.id, action='DELETE',
                                              test_roles=domain_roles['test_roles'])
    assert status_code == 401

    # Logged-in user trying to remove roles from an existing user of same domain
    response, status_code = user_scoped_roles(access_token_first, user_id=user_first.id, action='DELETE',
                                              test_roles=domain_roles['test_roles'])
    assert status_code == 400

    add_role_to_test_user(user_first, domain_roles['test_roles'])

    # Logged-in user trying to remove roles from an existing user of same domain
    response, status_code = user_scoped_roles(access_token_first, user_id=user_first.id, action='DELETE',
                                              test_roles=domain_roles['test_roles'])
    assert status_code == 200
    db.session.commit()
    assert len(UserScopedRoles.get_all_roles_of_user(user_first.id)) == 1


def test_user_groups_get(access_token_first, user_first, first_group, second_group):

    # Logged-in user getting all users of a user_group
    response, status_code = user_groups(access_token_first, first_group.id)
    assert status_code == 401

    # Add 'CAN_GET_GROUP_USERS' role to user
    add_role_to_test_user(user_first, ['CAN_GET_GROUP_USERS'])

    # Logged-in user getting all users of a non-existing user_group
    response, status_code = user_groups(access_token_first, first_group.id + 100)
    assert status_code == 404

    # Logged-in user getting all users of a user_group belonging to different domain
    response, status_code = user_groups(access_token_first, second_group.id)
    assert status_code == 401

    # Logged-in user getting all users of a user_group belonging to same domain
    response, status_code = user_groups(access_token_first, first_group.id)
    assert status_code == 200
    assert len(response['users']) == 1


def test_user_groups_get(access_token_first, user_first, first_group, second_group):

    # Logged-in user getting all users of a user_group
    response, status_code = user_groups(access_token_first, first_group.id)
    assert status_code == 401

    # Add 'CAN_GET_GROUP_USERS' role to user
    add_role_to_test_user(user_first, ['CAN_GET_GROUP_USERS'])

    # Logged-in user getting all users of a non-existing user_group
    response, status_code = user_groups(access_token_first, first_group.id + 100)
    assert status_code == 404

    # Logged-in user getting all users of a user_group belonging to different domain
    response, status_code = user_groups(access_token_first, second_group.id)
    assert status_code == 401

    # Logged-in user getting all users of a user_group belonging to same domain
    response, status_code = user_groups(access_token_first, first_group.id)
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

    # Add 'CAN_ADD_GROUP_USERS' role to user
    add_role_to_test_user(user_first, ['CAN_ADD_GROUP_USERS'])

    # Logged-in user adding a user to non-existing user group
    response, status_code = user_groups(access_token_first, first_group.id + 100, user_ids=[user_first.id], action='POST')
    assert status_code == 404

    # Logged-in user of different domain adding a user to a user group of different domain
    response, status_code = user_groups(access_token_first, second_group.id, user_ids=[user_first.id], action='POST')
    assert status_code == 401

    # Logged-in user adding a user of different domain to a user group of different domain
    response, status_code = user_groups(access_token_first, first_group.id, user_ids=[user_second.id], action='POST')
    assert status_code == 400

    # Changing domain of user_second
    user_second.domain_id = user_first.domain_id
    db.session.commit()

    # Logged-in user adding a user to a user group
    response, status_code = user_groups(access_token_first, first_group.id, user_ids=[user_first.id, user_second.id],
                                        action='POST')
    assert status_code == 200

    db.session.refresh(user_second)
    db.session.refresh(user_first)
    db.session.commit()

    assert user_first.user_group_id == first_group.id
    assert user_second.user_group_id == first_group.id


def test_get_all_roles_of_domain(access_token_first, user_first, user_second, domain_roles, domain_first):

    # Getting all roles of a domain
    response, status_code = get_roles_of_domain(access_token_first, domain_first.id)
    assert status_code == 401

    # ADD 'CAN_GET_DOMAIN_ROLES' role to user
    add_role_to_test_user(user_first, ['CAN_GET_DOMAIN_ROLES'])

    # Getting all roles of a non-existing domain
    response, status_code = get_roles_of_domain(access_token_first, domain_first.id + 100)
    assert status_code == 400

    # Getting all roles of a different domain
    response, status_code = get_roles_of_domain(access_token_first, user_second.domain_id)
    assert status_code == 400

    # Getting all roles of a domain
    response, status_code = get_roles_of_domain(access_token_first, domain_first.id)
    assert status_code == 200
    assert len(response['roles']) == 0

    DomainRole.get_by_name(domain_roles['test_roles'][0]).domain_id = domain_first.id
    db.session.commit()

    # Getting all roles of a domain
    response, status_code = get_roles_of_domain(access_token_first, domain_first.id)
    assert status_code == 200
    assert len(response['roles']) == 1


def test_domain_groups_api_get(access_token_first, first_group, user_first, user_second):

    # Logged in user trying to get groups of a given domain
    response, status_code = domain_groups(access_token_first, user_first.domain_id)
    assert status_code == 401

    # Adding 'CAN_GET_DOMAIN_GROUPS' to user_first
    add_role_to_test_user(user_first, ['CAN_GET_DOMAIN_GROUPS'])

    # Logged in user trying to get groups of a non-existing domain
    response, status_code = domain_groups(access_token_first, user_first.domain_id + 100)
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

    # Adding 'CAN_ADD_DOMAIN_GROUPS' to user_first
    add_role_to_test_user(user_first, ['CAN_ADD_DOMAIN_GROUPS'])

    # Logged in user trying to add groups to non-existing domain
    response, status_code = domain_groups(access_token_first, user_first.domain_id + 100, data=data, action='POST')
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

    # Adding 'CAN_DELETE_DOMAIN_GROUPS' to user_first
    add_role_to_test_user(user_first, ['CAN_DELETE_DOMAIN_GROUPS'])

    # Logged in user trying to delete groups from a non-existing domain
    response, status_code = domain_groups(access_token_first, user_first.domain_id + 100, data=data, action='DELETE')
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
    response, status_code = domain_groups(access_token_first, data=data, group_id=first_group.id,action='PUT')
    assert status_code == 401

    # Adding 'CAN_EDIT_DOMAIN_GROUPS' to user_first
    add_role_to_test_user(user_first, ['CAN_EDIT_DOMAIN_GROUPS'])

    # Logged in user trying to edit non-existing group
    response, status_code = domain_groups(access_token_first, data=data, group_id=first_group.id + 100, action='PUT')
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
    assert status_code == 200

    db.session.refresh(first_group)
    db.session.commit()

    assert first_group.name == data['name']
    assert first_group.description == data['description']


def test_health_check():
    import requests
    response = requests.get('http://127.0.0.1:8004/healthcheck')
    assert response.status_code == 200
