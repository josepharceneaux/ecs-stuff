from user_service.user_app import app
from candidate_pool_service.common.tests.conftest import *
from common_functions import *


def test_user_scoped_roles(access_token, domain_admin_access_token, ordinary_user, domain_roles, domain_first):

    # Add roles to existing user
    assert user_scoped_roles(access_token=domain_admin_access_token, user_id=ordinary_user.id, action="POST",
                             test_roles=domain_roles['test_roles']) == 200

    # Add false roles to existing user
    assert user_scoped_roles(access_token=domain_admin_access_token, user_id=ordinary_user.id, action="POST",
                             test_roles=domain_roles['test_roles'], false_case=True) == 400

    # Check if roles has been added successfully in existing user
    assert user_scoped_roles(access_token=domain_admin_access_token, user_id=ordinary_user.id) == \
           [DomainRole.get_by_name(domain_roles['test_roles'][0]).id,
            DomainRole.get_by_name(domain_roles['test_roles'][1]).id]

    # Add a existing role to existing user
    assert user_scoped_roles(access_token=domain_admin_access_token, user_id=ordinary_user.id, action="POST",
                             test_roles=domain_roles['test_roles']) == 400

    # verify a user role
    assert verify_user_scoped_role(ordinary_user, domain_roles['test_roles'][0])
    assert verify_user_scoped_role(ordinary_user, domain_roles['test_roles'][1])
    #
    # Get all roles of a domain
    assert get_roles_of_domain(access_token=domain_admin_access_token, domain_id=domain_first.id) == domain_roles['test_roles']

    # Get all roles of a domain using non-admin user
    assert get_roles_of_domain(access_token=access_token, domain_id=domain_first.id) == 401

    # Delete roles from a user
    assert user_scoped_roles(access_token=domain_admin_access_token, user_id=ordinary_user.id, action="DELETE",
                             test_roles=domain_roles['test_roles']) == 200

    # Check if roles have been deleted successfully from a user
    assert not user_scoped_roles(access_token=domain_admin_access_token, user_id=ordinary_user.id)


def test_user_groups(access_token, domain_admin_access_token, ordinary_user, domain_first):

    group_names = {
        'test_groups': [gen_salt(20), gen_salt(20)]
    }

    # Add Groups to domain
    assert domain_groups(access_token=domain_admin_access_token, domain_id=domain_first.id, action="POST",
                         test_groups=group_names['test_groups']) == 200

    # Check If groups have been added successfully in a domain
    assert set(group_names['test_groups']).issubset(set(domain_groups(
        access_token=domain_admin_access_token, domain_id=domain_first.id)))

    # Check If groups have been added successfully in a domain with non-admin user
    assert domain_groups(access_token=access_token, domain_id=domain_first.id) == 401

    # Add existing groups to a domain
    assert domain_groups(access_token=domain_admin_access_token, domain_id=domain_first.id, action="POST",
                         test_groups=group_names['test_groups']) == 400

    # Add non-admin user to a group
    assert user_groups(access_token=domain_admin_access_token, action='POST',
                       group_id=UserGroup.get_by_name(group_names['test_groups'][0]).id, user_ids=[ordinary_user.id]) == 200

    # Get all users of a group
    assert user_groups(access_token=domain_admin_access_token,
                       group_id=UserGroup.get_by_name(group_names['test_groups'][0]).id) == [ordinary_user.id]

    # Delete Groups of a domain
    assert domain_groups(access_token=domain_admin_access_token, domain_id=domain_first.id, action="DELETE",
                         test_groups=group_names['test_groups']) == 200


def test_update_password(access_token, domain_admin_access_token, ordinary_user, domain_admin_user):

    # Changing password of non-existing user
    assert update_password(access_token, ordinary_user.id + 100, PASSWORD, CHANGED_PASSWORD) == 404

    # Ordinary user updating password of admin_user
    assert update_password(access_token, domain_admin_user.id, PASSWORD, CHANGED_PASSWORD) == 401

    # Admin user updating its password but providing empty values of old and new password
    assert update_password(domain_admin_access_token, domain_admin_user.id, '', '') == 404

    # Admin user updating its password but providing wrong value of old_password
    assert update_password(domain_admin_access_token, domain_admin_user.id, PASSWORD + 'temp', CHANGED_PASSWORD) == 401

    # Admin user updating password of ordinary user
    assert update_password(domain_admin_access_token, ordinary_user.id, PASSWORD, CHANGED_PASSWORD) == 200

    # Admin user updating its password
    assert update_password(domain_admin_access_token, domain_admin_user.id, PASSWORD, CHANGED_PASSWORD) == 200

    # Ordinary user changing its own password but as its password has changed before so all of its tokens have been
    # revoked. So 401 status code should be returned
    assert update_password(access_token, ordinary_user.id, CHANGED_PASSWORD, PASSWORD) == 401


def test_health_check():
    import requests
    response = requests.get('http://127.0.0.1:8004/healthcheck')
    assert response.status_code == 200
