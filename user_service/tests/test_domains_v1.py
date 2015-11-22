__author__ = 'ufarooqi'
from user_service.user_app import app
from candidate_pool_service.common.tests.conftest import *
from common_functions import *


# Test GET operation of Domain API
def test_domain_service_get(access_token, admin_access_token, domain_admin_access_token, domain_first, domain_second):

    # Get info of domain when no domain_id is provided
    assert domain_api(domain_admin_access_token) == 400

    # ADMIN user getting info of a domain which doesn't exist
    assert domain_api(admin_access_token, domain_first.id + 100) == 404

    # User trying to get info of domain which different than its own domain
    assert domain_api(domain_admin_access_token, domain_second.id) == 401

    # User trying to get info of its own domain
    response = domain_api(access_token, domain_first.id)
    assert response.get('id') == domain_first.id
    assert response.get('name') == domain_first.name

    # Admin trying to get info of a domain different than its own
    response = domain_api(admin_access_token, domain_first.id)
    assert response.get('id') == domain_first.id
    assert response.get('name') == domain_first.name


# Test DELETE operation of domain API
def test_domain_service_delete(admin_access_token, domain_admin_access_token, domain_first):

    # Non-admin user trying to delete some domain
    assert domain_api(domain_admin_access_token, domain_first.id, action='DELETE') == 401

    # DOMAIN_ADMIN user trying to delete a domain where domain_id not provided
    assert domain_api(admin_access_token, action='DELETE') == 400

    # ADMIN user trying to delete a non-existing Domain
    assert domain_api(admin_access_token, domain_first.id + 100, action='DELETE') == 404

    # ADMIN user trying to delete a domain
    assert domain_api(admin_access_token, domain_first.id, action='DELETE') == domain_first.id

    # Refresh domain object
    db.session.refresh(domain_first)
    db.session.commit()

    # Check either domain has been deleted/disabled or not
    assert domain_first.is_disabled == 1

    # Check either users of that domain has been disabled or not
    users = User.query.filter(User.domain_id == domain_first.id).all()
    for user in users:
        assert user.is_disabled == 1


# Test PUT operation of domain API
def test_domain_service_put(access_token, admin_access_token, domain_admin_access_token, domain_first, domain_second):

    data = {'name': gen_salt(6), 'expiration': gen_salt(6)}

    # Ordinary user trying to update a domain
    assert domain_api(access_token, domain_first.id, data=data, action='PUT') == 401

    # DOMAIN_ADMIN user trying to update a non-existing domain
    assert domain_api(domain_admin_access_token, domain_first.id + 100, data=data, action='PUT') == 404

    # ADMIN user trying to update a domain but with empty request body
    assert domain_api(admin_access_token, domain_first.id, action='PUT') == 400

    # DOMAIN_ADMIN user trying to update a domain different than its own
    assert domain_api(domain_admin_access_token, domain_second.id, data=data, action='PUT') == 401

    # ADMIN user trying to update a domain but with invalid expiration time
    assert domain_api(admin_access_token, domain_first.id, data=data, action='PUT') == 400

    data['expiration'] = str(datetime.now().replace(microsecond=0))

    # ADMIN user trying to update a domain
    assert domain_api(admin_access_token, domain_first.id, data=data, action='PUT') == domain_first.id

    # Refresh domain object
    db.session.refresh(domain_first)
    db.session.commit()

    assert domain_first.name == data['name']
    assert str(domain_first.expiration) == data['expiration']


# Test POST operation of domain API
def test_domain_service_post(access_token, admin_access_token, domain_first):

    first_domain = {
        'name': '',
        'expiration': gen_salt(6),
        'default_culture_id': '100'
    }

    second_domain = {
        'name': gen_salt(6),
        'expiration': str(datetime.now().replace(microsecond=0)),
        'dice_company_id': 1
    }

    data = {'domains': [first_domain, second_domain]}

    # Ordinary user trying to add new domains
    assert domain_api(access_token, data=data, action='POST') == 401

    # ADMIN user trying to add new domains with empty body
    assert domain_api(admin_access_token, action='POST') == 400

    # ADMIN user trying to add new domains but with empty name
    assert domain_api(admin_access_token, data=data, action='POST') == 400

    first_domain['name'] = gen_salt(6)

    # ADMIN user trying to add new domains but with non-existing culture id
    assert domain_api(admin_access_token, data=data, action='POST') == 400

    del first_domain['default_culture_id']

    # ADMIN user trying to add new domains but with invalid expiration
    assert domain_api(admin_access_token, data=data, action='POST') == 400

    first_domain['expiration'] = str(datetime.now().replace(microsecond=0))
    first_domain['name'] = domain_first.name

    # ADMIN user trying to add new domains with already existing
    assert domain_api(admin_access_token, data=data, action='POST') == 400

    first_domain['name'] = gen_salt(6)

    # ADMIN user trying to add new domains with already existing
    response = domain_api(admin_access_token, data=data, action='POST')
    assert len(response) == 2
    db.session.commit()

    first_domain_object = Domain.query.get(response[0])
    second_domain_object = Domain.query.get(response[1])

    assert first_domain_object.name == data['domains'][0]['name']
    assert str(first_domain_object.expiration) == data['domains'][0]['expiration']

    assert second_domain_object.name == data['domains'][1]['name']
    assert str(second_domain_object.expiration) == data['domains'][1]['expiration']
    assert second_domain_object.dice_company_id == data['domains'][1]['dice_company_id']

    # Remove these temporary domains from domain table
    first_domain_object.delete()
    second_domain_object.delete()
