from conftest import *


# Test GET operation of user API
def test_user_service_get(access_token, admin_access_token, domain_admin_access_token, sample_user, admin_user,
                          domain_admin_user):

    # Get info of ordinary user when logged-in user is DOMAIN_ADMIN
    assert user_api(domain_admin_access_token, sample_user.id) == sample_user.id

    # Ordinary user getting his own info
    assert user_api(access_token, sample_user.id) == sample_user.id

    # DOMAIN_ADMIN getting ADMIN user's info
    assert user_api(domain_admin_access_token, admin_user.id) == 401

    # ADMIN getting DOMAIN_ADMIN user's info
    assert user_api(admin_access_token, domain_admin_user.id) == domain_admin_user.id

    # ADMIN getting info of some non-existing user
    assert user_api(admin_access_token, domain_admin_user.id + 100) == 404

    # Ordinary User getting all user ids of its domain
    assert user_api(access_token) == 401

    # DOMAIN_ADMIN getting all user ids of its domain
    assert user_api(domain_admin_access_token) == [sample_user.id, domain_admin_user.id]


# Test DELETE operation of user API
def test_user_service_delete(access_token, admin_access_token, domain_admin_access_token, sample_user, admin_user,
                          domain_admin_user):

    # Non-admin user trying to delete some user
    assert user_api(access_token, sample_user.id, action='DELETE') == 401

    # DOMAIN_ADMIN user trying to delete itself
    assert user_api(domain_admin_access_token, domain_admin_user.id, action='DELETE') == 401

    # DOMAIN_ADMIN user trying to delete some non-existing user
    assert user_api(domain_admin_access_token, domain_admin_user.id + 100, action='DELETE') == 404

    # DOMAIN_ADMIN trying to delete a role of different domain
    assert user_api(domain_admin_access_token, admin_user.id, action='DELETE') == 401

    # DOMAIN_ADMIN trying to delete a user in its domain where there are only 2 users in that domain
    assert user_api(domain_admin_access_token, sample_user.id, action='DELETE') == 400

    # ADMIN trying to delete a DOMAIN_ADMIN
    assert user_api(admin_access_token, domain_admin_user.id, action='DELETE') == domain_admin_user.id

    # Refresh domain_admin user object
    db.session.refresh(domain_admin_user)
    db.session.commit()

    # Check either domain_admin_user has been deleted/disabled or not
    assert domain_admin_user.is_disabled == 1


# Test PUT operation of user API
def test_user_service_put(access_token, admin_access_token, domain_admin_access_token, sample_user, admin_user,
                          domain_admin_user):

    data = {'first_name': gen_salt(6), 'last_name': gen_salt(6), 'phone': '+1 226-581-1027', 'email': ''}

    # ADMIN user trying to update non-existing user
    assert user_api(domain_admin_access_token, sample_user.id + 100, data=data, action='PUT') == 404

    # ADMIN user trying to update a DOMAIN_ADMIN user but with empty request body
    assert user_api(admin_access_token, domain_admin_user.id, action='PUT') == 400

    # DOMAIN_ADMIN user trying to update a user in different domain
    assert user_api(domain_admin_user, admin_user.id, data=data, action='PUT') == 401

    # Ordinary user trying to delete some user other than itself
    assert user_api(access_token, domain_admin_user.id, data=data, action='PUT') == 401

    # DOMAIN_ADMIN user trying to update ordinary user but with invalid email
    data['email'] = 'INVALID_EMAIL'
    assert user_api(domain_admin_access_token, sample_user.id, data=data, action='PUT') == 400

    # DOMAIN_ADMIN user trying to update ordinary user but with already existing email in ordinary user's domain
    data['email'] = domain_admin_user.email
    assert user_api(domain_admin_access_token, sample_user.id, data=data, action='PUT') == 400

    # DOMAIN_ADMIN user trying to update ordinary user
    data['email'] = 'sample_%s@gettalent.com' % gen_salt(15)
    assert user_api(domain_admin_access_token, sample_user.id, data=data, action='PUT') == sample_user.id

    # Refresh ordinary user
    db.session.refresh(sample_user)
    db.session.commit()

    # Check if ordinary user has been updated successfully
    assert sample_user.email == data['email']
    assert sample_user.first_name == data['first_name']
    assert sample_user.last_name == data['last_name']
    assert sample_user.phone == data['phone']


# Test POST operation of user API
def test_user_service_post(access_token, admin_access_token, domain_admin_access_token, sample_user, admin_user,
                          domain_admin_user):

    first_user = {
        'first_name': gen_salt(6),
        'last_name': gen_salt(6),
        'phone': '+1 226-581-1027',
        'domain': sample_user.domain_id,
        'is_admin': '1'
    }

    second_user = {
        'first_name': gen_salt(6),
        'last_name': gen_salt(6),
        'phone': '+1 226-581-1027',
        'is_domain_admin': '1'
    }

    data = {'users': [first_user, second_user]}

    # ADMIN user trying to add a new users but with empty request body
    assert user_api(admin_access_token, action='POST') == 400

    # Ordinary user trying to add new users
    assert user_api(access_token, data=data, action='POST') == 401

    # ADMIN user trying to add new users but without a email address
    assert user_api(admin_access_token, data=data, action='POST') == 400

    # Adding missing email address in request body
    data['users'][0]['email'] = '%s.sample@example.com' % gen_salt(15)
    data['users'][1]['email'] = sample_user.email

    # DOMAIN_ADMIN is trying to add a new admin user
    assert user_api(domain_admin_access_token, data=data, action='POST') == 401

    # DOMAIN_ADMIN trying to add a new user with already existing email
    assert user_api(domain_admin_access_token,  data={'users': [second_user]}, action='POST') == 400

    data['users'][1]['email'] = '%s.sample@example.com' % gen_salt(15)

    # ADMIN trying to add new users
    user_ids = user_api(admin_access_token,  data=data, action='POST')
    assert len(user_ids) == 2

    db.session.commit()
    first_user_object = User.query.get(int(user_ids[0]))
    second_user_object = User.query.get(user_ids[1])

    assert first_user_object.email == data['users'][0]['email']
    assert first_user_object.first_name == data['users'][0]['first_name']
    assert first_user_object.last_name == data['users'][0]['last_name']

    assert second_user_object.email == data['users'][1]['email']
    assert second_user_object.first_name == data['users'][1]['first_name']
    assert second_user_object.last_name == data['users'][1]['last_name']

    # Remove these temporary users from user table
    first_user_object.delete()
    second_user_object.delete()
