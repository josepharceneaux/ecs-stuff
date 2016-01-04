from user_service.user_app import app
from user_service.common.tests.conftest import *
from user_service.common.utils.handy_functions import add_role_to_test_user
from common_functions import *


# Test GET operation of user API
def test_user_service_get(access_token_first, user_first, user_second):

    # Logged-in user trying to get info of non-existing user
    response, status_code = user_api(access_token_first, user_first.id + 100)
    assert status_code == 404

    # Logged-in user trying to get info of user of different domain
    response, status_code = user_api(access_token_first, user_second.id)
    assert status_code == 401

    # Changing domain of user_second
    user_second.domain_id = user_first.domain_id
    db.session.commit()

    # Logged-in user trying to get info of user of different domain
    response, status_code = user_api(access_token_first, user_second.id)
    assert status_code == 401

    # Logged-in user trying to get info of user
    response, status_code = user_api(access_token_first, user_first.id)
    assert status_code == 200
    assert response['user'].get('id') == user_first.id

    # Logged-in user trying to get all users of a domain
    response, status_code = user_api(access_token_first)
    assert status_code == 401

    # Adding 'CAN_GET_USERS' to user_first
    add_role_to_test_user(user_first, ['CAN_GET_USERS'])

    # Logged-in user trying to get info of user
    response, status_code = user_api(access_token_first, user_first.id)
    assert status_code == 200
    assert response['user'].get('id') == user_first.id

    # Logged-in user trying to get info of user
    response, status_code = user_api(access_token_first, user_second.id)
    assert status_code == 200
    assert response['user'].get('id') == user_second.id

    # Logged-in user trying to get all users of a domain
    response, status_code = user_api(access_token_first)
    assert status_code == 200
    assert len(response['users']) == 2


# Test DELETE operation of user API
def test_user_service_delete(access_token_first, user_first, user_second):

    # User trying to delete user
    response, status_code = user_api(access_token_first, user_first.id, action='DELETE')
    assert status_code == 401

    # Adding 'CAN_DELETE_USERS' to user_first
    add_role_to_test_user(user_first, ['CAN_DELETE_USERS'])

    # User trying to delete non-existing user
    response, status_code = user_api(access_token_first, user_first.id + 100, action='DELETE')
    assert status_code == 404

    # User trying to delete user of different domain
    response, status_code = user_api(access_token_first, user_second.id, action='DELETE')
    assert status_code == 401

    # User trying to delete itself
    response, status_code = user_api(access_token_first, user_first.id, action='DELETE')
    assert status_code == 401

    # Changing domain of user_second
    user_second.domain_id = user_first.domain_id
    db.session.commit()

    # User trying to delete user but as there are only two users in Domain so this user cannot be deleted
    response, status_code = user_api(access_token_first, user_second.id, action='DELETE')
    assert status_code == 400

    temp_user = User(domain_id=user_first.domain_id, email='%s@gettalent.com' % gen_salt(20))
    db.session.add(temp_user)
    db.session.commit()

    # User trying to delete user
    response, status_code = user_api(access_token_first, user_second.id, action='DELETE')
    assert status_code == 200
    db.session.refresh(user_second)
    db.session.commit()
    assert user_second.is_disabled == 1

    db.session.delete(temp_user)
    db.session.commit()


# Test PUT operation of user API
def test_user_service_put(access_token_first, user_first, user_second):

    data = {'first_name': gen_salt(6), 'last_name': gen_salt(6), 'phone': '+1 226-581-1027', 'email': ''}

    # Logged-in user trying to update non-existing user
    response, status_code = user_api(access_token_first, user_first.id + 100, data=data, action='PUT')
    assert status_code == 404

    # Logged-in user trying to update user with empty request body
    response, status_code = user_api(access_token_first, user_first.id, action='PUT')
    assert status_code == 400

    # Logged-in user trying to update user of different domain
    response, status_code = user_api(access_token_first, user_second.id, data=data, action='PUT')
    assert status_code == 401

    # Changing domain of user_second
    user_second.domain_id = user_first.domain_id
    db.session.commit()

    # Logged-in user trying to update a different user
    response, status_code = user_api(access_token_first, user_second.id, data=data, action='PUT')
    assert status_code == 401

    # Logged-in user trying to update user with invalid email
    data['email'] = 'INVALID_EMAIL'
    response, status_code = user_api(access_token_first, user_first.id, data=data, action='PUT')
    assert status_code == 400

    # Logged-in user trying to update user with an existing email
    data['email'] = user_second.email
    response, status_code = user_api(access_token_first, user_first.id, data=data, action='PUT')
    assert status_code == 400

    # Logged-in user trying to update user
    data['email'] = 'sample_%s@gettalent.com' % gen_salt(15)
    response, status_code = user_api(access_token_first, user_first.id, data=data, action='PUT')
    assert status_code == 200

    # Refresh user
    db.session.refresh(user_first)
    db.session.commit()

    # Check if ordinary user has been updated successfully
    assert user_first.email == data['email']
    assert user_first.first_name == data['first_name']
    assert user_first.last_name == data['last_name']
    assert user_first.phone == data['phone']

    # Adding 'CAN_EDIT_USERS' in user_first
    add_role_to_test_user(user_first, ['CAN_EDIT_USERS'])

    # Logged-in user trying to update a different user
    data['email'] = 'sample_%s@gettalent.com' % gen_salt(15)
    response, status_code = user_api(access_token_first, user_second.id, data=data, action='PUT')
    assert status_code == 200


# Test POST operation of user API
def test_user_service_post(access_token_first, user_first):

    first_user = {
        'first_name': '',
        'last_name': gen_salt(6),
        'phone': '+1 226-581-1027'
    }
    second_user = {
        'first_name': gen_salt(6),
        'last_name': '',
        'phone': '+1 226-581-1027'
    }

    data = {'users': [first_user, second_user]}

    # Logged-in user trying to add new users
    response, status_code = user_api(access_token_first, data=data, action='POST')
    assert status_code == 401

    # Adding 'CAN_ADD_USERS' role to user_first
    add_role_to_test_user(user_first, ['CAN_ADD_USERS'])

    # Logged-in user trying to add new users with empty request body
    response, status_code = user_api(access_token_first, action='POST')
    assert status_code == 400

    # Logged-in user trying to add new users but without an email address
    response, status_code = user_api(access_token_first, data=data, action='POST')
    assert status_code == 400

    # Adding missing email address in request body
    data['users'][0]['email'] = '%s.sample@example.com' % gen_salt(15)
    data['users'][1]['email'] = user_first.email

    # Logged-in user trying to add new users but without first_names and last_names
    response, status_code = user_api(access_token_first, data=data, action='POST')
    assert status_code == 400

    # Adding missing first_name and last_name in request body
    data['users'][0]['first_name'] = gen_salt(6)
    data['users'][1]['last_name'] = gen_salt(6)

    # Logged-in user trying to add  new users but with an existing email address
    response, status_code = user_api(access_token_first, data=data, action='POST')
    assert status_code == 400

    data['users'][1]['email'] = '%s.sample@example.com' % gen_salt(15)

    # Logged-in user trying to add new users
    response, status_code = user_api(access_token_first, data=data, action='POST')
    assert status_code == 200

    user_ids = response['users']
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
