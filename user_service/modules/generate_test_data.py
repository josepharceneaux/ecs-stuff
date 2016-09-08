"""
This script initializes data to run tests which involves creation of domains, user_gorups,
users, client, token etc.

"""
# Standard imports
import time
from datetime import datetime

# 3rd party imports
from werkzeug.security import gen_salt

# Application specific imports
from user_service.common.error_handling import InternalServerError
from user_service.common.models.user import Domain, User, UserGroup, Token, Client, Role
from user_service.user_app import logger

TEST_PASSWORD = "pbkdf2:sha512:1000$lf3teYeJ$7bb470eb0a2d10629e4835cac771e51d2b1e9ed577b849c27551ab7b244274a10109c8d7a7b8786f4de176b764d9763e4fd1954ad902d6041f6d46fab16219c6"


def create_test_domain(names):
    """
    This function takes list of domain names, creates domains with given names and then returns domains list.
    :param list | tuple names: list of domain names
    :rtype: tuple[list]
    """
    domains = []
    for domain_name in names:
        domain = Domain(name=domain_name)
        Domain.save(domain)
        logger.debug('Domain Name %s', domain.name)
        domains.append(domain)
    return domains, [domain.id for domain in domains]


def create_user_groups(group_names, domain_ids):
    """
    This function creates user groups in database. It takes group names ad domain ids as input.
    :param list(string) group_names: user group names
    :param list(int | long) domain_ids: domain ids
    :rtype: tuple[list]
    """
    assert len(group_names) == len(domain_ids), 'group names and domain ids should be equal'
    groups = []
    for group_name, domain_id in zip(group_names, domain_ids):
        user_group = UserGroup.get_by_name(group_name)
        if not user_group:
            user_group = UserGroup.add_groups([{'name': group_name}], domain_id)[0]
        logger.debug('User Group: %s', user_group.name)
        groups.append(user_group)
    return groups, [group.id for group in groups]


def create_test_user(email, domain_id, group_id):
    """
    This function creates a test user with given domain and group with `TEST_ADMIN` as role.
    :param int | long domain_id: user's domain id
    :param int | long group_id: user's group id
    :rtype: User
    """
    user = User.get_by_email(email)
    role = Role.get_by_name('TEST_ADMIN')
    if not user:
        user = User(email=email, domain_id=domain_id, user_group_id=group_id, password=TEST_PASSWORD, role_id=role.id)
        User.save(user)
    logger.debug('User: %s', user.name)
    return user


def create_test_client(client_id, client_secret):
    """
    This function creates a test client.
    :param string client_id: client unique id
    :param string client_secret: client secret
    :rtype: Client
    """
    client = Client(client_id=client_id, client_secret=client_secret, client_name='test_client')
    return Client.save(client)


def create_test_token(user_id, client_id):
    """
    This function creates a access token for given test user.
    :param int | long user_id: user primary id
    :param string client_id: client unique id
    :rtype: Token
    """

    token = Token(client_id=client_id, user_id=user_id, token_type='Bearer',
                  access_token=gen_salt(60),
                  refresh_token=gen_salt(60), expires=datetime(2020, 12, 31))
    return Token.save(token)


def create_test_data():
    """
    To create test data (Domains, Users, Groups, Client, Token etc.)
    :rtype: dict
    """
    timestamp = str(time.time()) + gen_salt(10)
    # Create two domains
    domain_names = ["test_domain_first", "test_domain_second"]
    domain_names = [name + timestamp for name in domain_names]
    domains, domain_ids = create_test_domain(domain_names)

    # # Create user groups
    group_names = ["test_group_first", "test_group_second"]
    group_names = [group_name + timestamp for group_name in group_names]
    groups, group_ids = create_user_groups(group_names, domain_ids)

    # Create 3 users

    user_emails = [("test_email@test.com", "test_email_same_domain@test.com"), ("test_email_second@test.com",)]
    user_emails = [(timestamp + email for email in domain_emails) for domain_emails in user_emails]
    user_data = zip(user_emails, domain_ids, group_ids)

    users = []
    for emails, domain_id, group_id in user_data:
        for email in emails:
            users.append(create_test_user(email, domain_id, group_id))
    user_ids = [user.id for user in users]

    # Create client
    client_id = gen_salt(40)
    client_secret = gen_salt(55)
    client = create_test_client(client_id, client_secret)

    tokens = []
    # Create token for all test users
    for user_id in user_ids:
        tokens.append(create_test_token(user_id, client_id))

    return {
        'domains': [domain.to_json() for domain in domains],
        'users': [user.to_json(include_fields=('id', 'domain_id', 'email', 'role_id',
                                               'user_group_id')) for user in users],
        'groups_ids': group_ids,
        'client': client.to_json(),
        'tokens': [token.to_json() for token in tokens]
    }

