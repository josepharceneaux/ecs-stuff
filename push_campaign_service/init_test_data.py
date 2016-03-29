"""
This script initializes data to run tests for push campaign service which involves creation of domains, user_gorups,
users, client, token etc.

Run:
python push_campaign_service/init_test_data.py

"""
import os

from sqlalchemy import text
from common.talent_config_manager import load_gettalent_config, TalentConfigKeys
from common.talent_flask import TalentFlask

app = TalentFlask(__name__)
load_gettalent_config(app.config)

if app.config[TalentConfigKeys.ENV_KEY] != 'dev':
    print "This script is only to populate test data in dev environment."
    raise SystemExit(0)


from common.models.db import db
db.init_app(app)
db.app = app
db.reflect()

query = ''
db.session.connection().execute('SET FOREIGN_KEY_CHECKS = 0;')

print 'Generating initial test data'

# Create two domains
domain_names = ["test_domain_first", "test_domain_second"]
domain_ids = []
for domain_name in domain_names:
    q = 'select * from domain where name = "%s";' % domain_name
    sql = text(q)
    result = db.engine.execute(sql)
    if result.rowcount == 0:
        q = 'INSERT INTO domain (name,organizationId) VALUES ("%s",1);' % domain_name
        sql = text(q)
        result = db.engine.execute(sql)
        domain_ids.append(result.lastrowid)
    elif result.rowcount == 1:
        domain_ids.append(result.cursor._rows[0][0])
    else:
        print "More than one domain found with name %s" % domain_name
        raise SystemExit(0)

# Create user groups
group_names = ["test_group_first", "test_group_second"]
group_ids = []
for index, group_name in enumerate(group_names):
    q = 'select * from user_group where name = "%s";' % group_name
    sql = text(q)
    result = db.engine.execute(sql)
    if result.rowcount == 0:
        q = 'INSERT INTO user_group (name, DomainId) VALUES ("%s", %s);' % (group_name, domain_ids[index])
        sql = text(q)
        result = db.engine.execute(sql)
        group_ids.append(result.lastrowid)
    elif result.rowcount == 1:
        group_ids.append(result.cursor._rows[0][0])
    else:
        print "More than one user_groups were found with name %s" % group_name
        raise SystemExit(0)

# Create 3 users, two from domain first and one from second domain
user_data = [("test_email@test.com", domain_ids[0], group_ids[0]),
             ("test_email_same_domain@test.com", domain_ids[0], group_ids[0]),
             ("test_email_second@test.com", domain_ids[1], group_ids[1])]
user_ids = []
for email, domain_id, group_id in user_data:
    q = 'select * from user where email = "%s";' % email
    sql = text(q)
    result = db.engine.execute(sql)
    if result.rowcount == 0:
        q = '''INSERT INTO user (email, password, domainId, userGroupId)
        VALUES ("%s", "pbkdf2:sha512:1000$lf3teYeJ$7bb470eb0a2d10629e4835cac771e51d2b1e9ed577b849c27551ab7b244274a10109c8d7a7b8786f4de176b764d9763e4fd1954ad902d6041f6d46fab16219c6", %s , %s);''' % (email, domain_id, group_id)
        sql = text(q)
        result = db.engine.execute(sql)
        user_ids.append(result.lastrowid)
    elif result.rowcount == 1:
        user_ids.append(result.cursor._rows[0][0])
    else:
        print "More than one users were found with email %s" % email
        raise SystemExit(0)

# Add domain roles in db
roles = ["CAN_ADD_USER_ROLES", "CAN_DELETE_USER_ROLES", "CAN_ADD_USERS", "CAN_GET_USERS", "CAN_DELETE_USERS",
         "CAN_ADD_TALENT_POOLS", "CAN_GET_TALENT_POOLS", "CAN_DELETE_TALENT_POOLS", "CAN_ADD_TALENT_POOLS_TO_GROUP",
         "CAN_ADD_CANDIDATES", "CAN_GET_CANDIDATES", "CAN_DELETE_CANDIDATES", "CAN_ADD_TALENT_PIPELINE_SMART_LISTS",
         "CAN_DELETE_TALENT_PIPELINE_SMART_LISTS", "CAN_ADD_TALENT_PIPELINES"]

domain_roles = {}
for domain_role in roles:
    q = 'select * from domain_role where role_name = "%s";' % domain_role
    sql = text(q)
    result = db.engine.execute(sql)
    if result.rowcount == 0:
        q = 'INSERT INTO domain_role (role_name) VALUES ("%s")' % domain_role
        sql = text(q)
        result = db.engine.execute(sql)
        domain_roles[domain_role] = result.lastrowid
    elif result.rowcount == 1:
        domain_roles[domain_role] = result.cursor._rows[0][0]
    else:
        print "More than one records were found for domain role %s" % domain_role
        raise SystemExit(0)

# Add user scoped roles
for user_id in user_ids:
    q = 'select * from user_scoped_roles where UserId = %s and RoleId = %s' % (user_id, domain_roles['CAN_ADD_USER_ROLES'])
    sql = text(q)
    result = db.engine.execute(sql)
    if result.rowcount == 0:
        q = 'INSERT INTO user_scoped_roles (UserId, RoleId) VALUES (%s, %s);' % (user_id, domain_roles['CAN_ADD_USER_ROLES'])
        sql = text(q)
        result = db.engine.execute(sql)

    q = 'select * from user_scoped_roles where UserId = %s and RoleId = %s' % (user_id, domain_roles['CAN_DELETE_USER_ROLES'])
    sql = text(q)
    result = db.engine.execute(sql)
    if result.rowcount == 0:
        q = 'INSERT INTO user_scoped_roles (UserId, RoleId) VALUES (%s, %s);' % (user_id, domain_roles['CAN_DELETE_USER_ROLES'])
        sql = text(q)
        result = db.engine.execute(sql)

CLIENT_ID = 'KGy3oJySBTbMmubglOXnhVqsRQDoRcFjJ3921U1Z'
CLIENT_SECRET = 'DbS8yb895bBw4AXFe182bjYmv5XfF1x7dOftmBHMlxQmulYj1Z'
TEST_ACCESS_TOKEN = 'uTl6zNUdoNATwwUg0GOuSFvyrtyCCW'
TEST_REFRESH_TOKEN = 'uTl6zNUdoNATwwUg0GOuSFvyrtyCCW'

# Create client
q = 'select * from client where client_id = "%s" and client_secret = "%s"' % (CLIENT_ID, CLIENT_SECRET)
sql = text(q)
result = db.engine.execute(sql)
if result.rowcount == 0:
    q = '''INSERT INTO client (client_id, client_secret, client_name)
           VALUES ("%s", "%s", "test_client");''' % (CLIENT_ID, CLIENT_SECRET)
    sql = text(q)
    result = db.engine.execute(sql)

# Create token for all test users
for user_id in user_ids:
    q = 'select * from token where user_id = %s;' % user_id
    sql = text(q)
    result = db.engine.execute(sql)
    if result.rowcount == 0:
        q = '''INSERT INTO token (client_id, user_id, token_type, access_token, refresh_token, expires)
               VALUES ("%s", %s ,"Bearer","%s", "%s","2020-03-11 08:44:18");''' % (CLIENT_ID, user_id, TEST_ACCESS_TOKEN + str(user_id), TEST_REFRESH_TOKEN + str(user_id))
        sql = text(q)
        result = db.engine.execute(sql)

db.session.connection().execute('SET FOREIGN_KEY_CHECKS = 1;')

# Now write test config file
CONFIG_FILE_NAME = "common_test.cfg"
LOCAL_CONFIG_PATH = os.path.expanduser('~') + "/.talent/%s" % CONFIG_FILE_NAME
file = open(LOCAL_CONFIG_PATH, mode='w+')

for user_id, email, order in zip(user_ids, ["test_email@test.com", "test_email_same_domain@test.com", "test_email_second@test.com"], ['FIRST', 'SAME_DOMAIN', 'SECOND']):
    file.write('[USER_%s]\n' % order)
    file.write('USER_ID=%s\n' % user_id)
    file.write('USER_NAME=%s\n' % email)
    file.write('PASSWORD=test_user\n')
    file.write('TOKEN=%s\n\n' % (TEST_ACCESS_TOKEN + str(user_id)))

file.write('[CLIENT]\n')
file.write('CLIENT_ID=%s\n' % CLIENT_ID)
file.write('CLIENT_SECRET=%s\n\n' % CLIENT_SECRET)

file.write('[PUSH_CONFIG]\n')
file.write('DEVICE_ID_1=56c1d574-237e-4a41-992e-c0094b6f2ded\n')
file.write('DEVICE_ID_2=6a81ab5d-9e71-44f7-99dc-eb72eeaff311\n\n')

file.flush()
