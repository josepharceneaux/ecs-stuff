"""
This script initializes data to run tests for push campaign service which involves creation of domains, user_gorups,
users, client, token etc.
We have to run this script only once and will be required to run again if you deleted those records.

Run:
python push_campaign_service/init_test_data.py

"""
import os
from datetime import datetime, timedelta

from common.error_handling import InvalidUsage
from common.utils.models_utils import init_talent_app
app, logger = init_talent_app('test_app')

from common.talent_config_manager import TalentConfigKeys, TalentEnvs
from common.models.user import Domain, DomainRole, User, UserScopedRoles, UserGroup, Token, Client

Roles = DomainRole.Roles
roles = [Roles.CAN_ADD_USER_ROLES, Roles.CAN_DELETE_USER_ROLES, Roles.CAN_ADD_USERS,
         Roles.CAN_GET_USERS, Roles.CAN_DELETE_USERS, Roles.CAN_ADD_TALENT_POOLS, Roles.CAN_GET_TALENT_POOLS,
         Roles.CAN_DELETE_TALENT_POOLS, Roles.CAN_ADD_TALENT_POOLS_TO_GROUP, Roles.CAN_ADD_CANDIDATES,
         Roles.CAN_GET_CANDIDATES, Roles.CAN_DELETE_CANDIDATES, Roles.CAN_ADD_TALENT_PIPELINE_SMART_LISTS,
         Roles.CAN_DELETE_TALENT_PIPELINE_SMART_LISTS, Roles.CAN_ADD_TALENT_PIPELINES]

CLIENT_ID = 'KGy3oJySBTbMmubglOXnhVqsRQDoRcFjJ3921U1Z'
CLIENT_SECRET = 'DbS8yb895bBw4AXFe182bjYmv5XfF1x7dOftmBHMlxQmulYj1Z'
TEST_ACCESS_TOKEN = 'uTl6zNUdoNATwwUg0GOuSFvyrtyCCW'
TEST_REFRESH_TOKEN = 'uTl6zNUdoNATwwUg0GOuSFvyrtyCCW'
TEST_PASSWORD = "pbkdf2:sha512:1000$lf3teYeJ$7bb470eb0a2d10629e4835cac771e51d2b1e9ed577b849c27551ab7b244274a10109c8d7a7b8786f4de176b764d9763e4fd1954ad902d6041f6d46fab16219c6"

if app.config[TalentConfigKeys.ENV_KEY] != TalentEnvs.DEV:
    print "This script is only to populate test data in dev environment."
    raise SystemExit(0)


def create_test_domain(names):
    ids = []
    for domain_name in names:
        domain = Domain.query.filter_by(name=domain_name).one()
        if not domain:
            domain = Domain(name=domain_name, organization_id=1)
            Domain.save(domain)
        logger.debug('Domain Name %s', domain.name)
        ids.append(domain.id)
    return ids


def create_user_groups(group_names, domain_ids):
    assert len(group_names) == len(domain_ids), 'group names and domain ids should be equal'
    ids = []
    for group_name, domain_id in zip(group_names, domain_ids):
        user_group = UserGroup.get_by_name(group_name)
        if not user_group:
            user_group = UserGroup.add_groups({'name': group_name}, domain_id)[0]
        logger.debug('User Group: %s', user_group.name)
        ids.append(user_group.id)
    return ids


def create_test_user(email, domain_id, group_id):
    user = User.get_by_email(email)
    if not user:
        user = User(email=email, domain_id=domain_id, user_group_id=group_id, password=TEST_PASSWORD)
        User.save(user)
    logger.debug('User: %s', user.name)
    return user


def add_domain_roles(roles):
    ids = []
    for role_name in roles:
        domain_role = DomainRole.get_by_name(role_name)
        if not domain_role:
            domain_role = DomainRole.save(role_name)
        logger.debug('User: %s', domain_role.role_name)
        ids.append(domain_role.id)
    return ids


def add_scoped_roles(users, roles_ids):
    for user in users:
        try:
            UserScopedRoles.add_roles(user, roles_ids)
        except InvalidUsage:
            pass


def create_test_client(client_id, client_secret):
    client = Client.query.filter_by(client_id=client_id, client_secret=client_secret).first()
    if not client:
        client = Client(client_id=client_id, client_secret=client_secret, client_name='test_client')
        Client.save(client)


def create_test_token(user_id):
    token = Token.get_token(TEST_ACCESS_TOKEN + str(user_id))
    if not token:
        token = Token(client_id=CLIENT_ID, user_id=user_id, token_type='Bearer',
                      access_token=TEST_ACCESS_TOKEN + str(user_id),
                      refresh_token=TEST_REFRESH_TOKEN + str(user_id), expires=datetime(2020, 12, 31))
        Token.save(token)
    else:
        one_hour_later = datetime.utcnow() + timedelta(hours=1)
        if token.expires < one_hour_later:
            token.expires += timedelta(days=30)


# Create two domains
domain_names = ["test_domain_first", "test_domain_second"]
domain_ids = create_test_domain(domain_names)

# # Create user groups
group_names = ["test_group_first", "test_group_second"]
group_ids = create_user_groups(group_names, domain_ids)

# Create 3 users
user_emails = ["test_email@test.com", "test_email_same_domain@test.com", "test_email_second@test.com"]
user_data = zip(user_emails, domain_ids, group_ids)

user_ids = []
users = []
for email, domain_id, group_id in user_data:
    users.append(create_test_user(email, domain_id, group_id))
user_ids = [user.id for user in users]

# Add domain roles in db
domain_roles = add_domain_roles(roles)

# Add user scoped roles
add_scoped_roles(users, domain_roles)

# Create client
create_test_client(CLIENT_ID, CLIENT_SECRET)

# Create token for all test users
for user_id in user_ids:
    create_test_token(user_id)

# # Now write test config file
CONFIG_FILE_NAME = "common_test.cfg"
LOCAL_CONFIG_PATH = os.path.expanduser('~') + "/.talent/%s" % CONFIG_FILE_NAME
with open(LOCAL_CONFIG_PATH, mode='w+') as cfg:
    for user_id, email, order in zip(user_ids, user_emails, ['FIRST', 'SAME_DOMAIN', 'SECOND']):
        cfg.write('[USER_%s]\n' % order)
        cfg.write('USER_ID=%s\n' % user_id)
        cfg.write('USER_NAME=%s\n' % email)
        cfg.write('PASSWORD=test_user\n')
        cfg.write('TOKEN=%s\n\n' % (TEST_ACCESS_TOKEN + str(user_id)))

    cfg.write('[CLIENT]\n')
    cfg.write('CLIENT_ID=%s\n' % CLIENT_ID)
    cfg.write('CLIENT_SECRET=%s\n\n' % CLIENT_SECRET)

    cfg.write('[PUSH_CONFIG]\n')
    cfg.write('DEVICE_ID_1=56c1d574-237e-4a41-992e-c0094b6f2ded\n')
    cfg.write('DEVICE_ID_2=6a81ab5d-9e71-44f7-99dc-eb72eeaff311\n\n')

    cfg.flush()
