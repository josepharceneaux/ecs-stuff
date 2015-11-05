from conftest import *


def test_user_scoped_roles(access_token, domain_admin_access_token, sample_user, domain_roles, domain_id):

    # Add roles to existing user
    assert user_scoped_roles(access_token=domain_admin_access_token, user_id=sample_user.id, action="POST",
                             test_roles=domain_roles['test_roles']) == 200

    # Add false roles to existing user
    assert user_scoped_roles(access_token=domain_admin_access_token, user_id=sample_user.id, action="POST",
                             test_roles=domain_roles['test_roles'], false_case=True) == 400

    # Check if roles has been added successfully in existing user
    assert user_scoped_roles(access_token=domain_admin_access_token, user_id=sample_user.id) == \
           [DomainRole.get_by_name(domain_roles['test_roles'][0]).id,
            DomainRole.get_by_name(domain_roles['test_roles'][1]).id]

    # Add a existing role to existing user
    assert user_scoped_roles(access_token=domain_admin_access_token, user_id=sample_user.id, action="POST",
                             test_roles=domain_roles['test_roles']) == 400

    # verify a user role
    assert verify_user_scoped_role(sample_user, domain_roles['test_roles'][0])
    assert verify_user_scoped_role(sample_user, domain_roles['test_roles'][1])
    #
    # Get all roles of a domain
    assert get_roles_of_domain(access_token=domain_admin_access_token, domain_id=domain_id) == domain_roles['test_roles']

    # Get all roles of a domain using non-admin user
    assert get_roles_of_domain(access_token=access_token, domain_id=domain_id) == 401

    # Delete roles from a user
    assert user_scoped_roles(access_token=domain_admin_access_token, user_id=sample_user.id, action="DELETE",
                             test_roles=domain_roles['test_roles']) == 200

    # Check if roles have been deleted successfully from a user
    assert not user_scoped_roles(access_token=domain_admin_access_token, user_id=sample_user.id)


def test_user_groups(access_token, domain_admin_access_token, sample_user, group_names, domain_id):

    # Add Groups to domain
    assert domain_groups(access_token=domain_admin_access_token, domain_id=domain_id, action="POST",
                         test_groups=group_names['test_groups']) == 200

    # Check If groups have been added successfully in a domain
    assert domain_groups(access_token=domain_admin_access_token, domain_id=domain_id) == group_names['test_groups']

    # Check If groups have been added successfully in a domain with non-admin user
    assert domain_groups(access_token=access_token, domain_id=domain_id) == 401

    # Add existing groups to a domain
    assert domain_groups(access_token=domain_admin_access_token, domain_id=domain_id, action="POST",
                         test_groups=group_names['test_groups']) == 400

    # Add non-admin user to a group
    assert user_groups(access_token=domain_admin_access_token, action='POST',
                       group_id=UserGroup.get_by_name(group_names['test_groups'][0]).id, user_ids=[sample_user.id]) == 200

    # Get all users of a group
    assert user_groups(access_token=domain_admin_access_token,
                       group_id=UserGroup.get_by_name(group_names['test_groups'][0]).id) == [sample_user.id]

    # Delete Groups of a domain
    assert domain_groups(access_token=domain_admin_access_token, domain_id=domain_id, action="DELETE",
                         test_groups=group_names['test_groups']) == 200


def test_update_password(access_token, domain_admin_access_token, sample_user, domain_admin_user):

    # Changing password of non-existing user
    assert update_password(access_token, sample_user.id + 100, PASSWORD, CHANGED_PASSWORD) == 404

    # Ordinary user updating password of admin_user
    assert update_password(access_token, domain_admin_user.id, PASSWORD, CHANGED_PASSWORD) == 401

    # Admin user updating its password but providing empty values of old and new password
    assert update_password(domain_admin_access_token, domain_admin_user.id, '', '') == 404

    # Admin user updating its password but providing wrong value of old_password
    assert update_password(domain_admin_access_token, domain_admin_user.id, PASSWORD + 'temp', CHANGED_PASSWORD) == 401

    # Admin user updating password of ordinary user
    assert update_password(domain_admin_access_token, sample_user.id, PASSWORD, CHANGED_PASSWORD) == 200

    # Admin user updating its password
    assert update_password(domain_admin_access_token, domain_admin_user.id, PASSWORD, CHANGED_PASSWORD) == 200

    # Ordinary user changing its own password but as its password has changed before so all of its tokens have been
    # revoked. So 401 status code should be returned
    assert update_password(access_token, sample_user.id, CHANGED_PASSWORD, PASSWORD) == 401

