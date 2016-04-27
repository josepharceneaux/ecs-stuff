"""
Script for developers to reset their database and remove all dangling candidate documents in Amazon CloudSearch.

Prerequisites:
You must have MySQL running locally and a database called talent_local.

Run:
python setup_environment/reset_database_and_cloud_search.py

"""
from sqlalchemy import text
from common.talent_config_manager import load_gettalent_config, TalentConfigKeys
from common.talent_flask import TalentFlask
# Flush redis-cache
from common.redis_cache import redis_store
from common.models.db import db
from candidate_service.candidate_app import app

static_tables = ['candidate_status', 'classification_type', 'country', 'culture', 'email_label', 'phone_label',
                 'frequency', 'organization', 'product', 'rating_tag', 'social_network', 'web_auth_group', 'email_client']

flush_redis_entries = ['apscheduler.jobs', 'apscheduler.run_times']

app = TalentFlask(__name__)
load_gettalent_config(app.config)

if app.config[TalentConfigKeys.ENV_KEY] not in ['dev', 'jenkins']:
    print "You can reset your database and CloudSearch domain only in 'dev' or 'jenkins' environment"
    raise SystemExit(0)


def save_meetup_token_and_flushredis(_redis):
    if _redis.get('Meetup'):
        _token = _redis.get('Meetup')
        # Commenting this out because we need persistence in redis to store parsed resumes to save our
        # BG transactions.
        # _redis.flushall()
        _redis.set('Meetup', _token)


# Delete entries of redis given in a list (entries)
def delete_entries(_redis, entries):
    for entry in entries:
        try:
            _redis.delete(entry)
        except Exception as e:
            print e.message


redis_store.init_app(app)
# save_meetup_token_and_flushredis(redis_store)
delete_entries(redis_store, flush_redis_entries)

db.init_app(app)
db.app = app
db.reflect()

query = ''
db.session.connection().execute('SET FOREIGN_KEY_CHECKS = 0;')
for table_key in db.metadata.tables.keys():
    if table_key not in static_tables:
        query += 'TRUNCATE %s;' % db.metadata.tables[table_key]

try:
    db.session.connection().execute(query)
except Exception as e:
    print e.message
    raise SystemExit(0)

db.session.connection().execute('SET FOREIGN_KEY_CHECKS = 1;')

print 'DB reset is successful'

print 'Generating initial test data'


q = '''INSERT INTO domain (name,organizationId, is_disabled) VALUES ("test_domain_first",1, 0);
INSERT INTO domain (name,organizationId, is_disabled) VALUES ("test_domain_second",1,0);
INSERT INTO user_group (name, DomainId) VALUES ("test_group_first", 1), ("test_group_second", 2);
INSERT INTO user (email, password, domainId, userGroupId, is_disabled)
VALUES ("test_email@test.com", "pbkdf2:sha512:1000$lf3teYeJ$7bb470eb0a2d10629e4835cac771e51d2b1e9ed577b849c27551ab7b244274a10109c8d7a7b8786f4de176b764d9763e4fd1954ad902d6041f6d46fab16219c6", 1, 1, 0);
INSERT INTO user (email, password, domainId, userGroupId, is_disabled)
VALUES ("test_email_same_domain@test.com", "pbkdf2:sha512:1000$lf3teYeJ$7bb470eb0a2d10629e4835cac771e51d2b1e9ed577b849c27551ab7b244274a10109c8d7a7b8786f4de176b764d9763e4fd1954ad902d6041f6d46fab16219c6", 1, 1, 0);
INSERT INTO user (email, password, domainId, userGroupId, is_disabled)
VALUES ("test_email_second@test.com", "pbkdf2:sha512:1000$lf3teYeJ$7bb470eb0a2d10629e4835cac771e51d2b1e9ed577b849c27551ab7b244274a10109c8d7a7b8786f4de176b764d9763e4fd1954ad902d6041f6d46fab16219c6", 2, 2, 0);
INSERT INTO client (client_id, client_secret, client_name)
VALUES ("KGy3oJySBTbMmubglOXnhVqsRQDoRcFjJ3921U1Z", "DbS8yb895bBw4AXFe182bjYmv5XfF1x7dOftmBHMlxQmulYj1Z", "test_client");
INSERT INTO token VALUES (1,'KGy3oJySBTbMmubglOXnhVqsRQDoRcFjJ3921U1Z',1,'Bearer','uTl6zNUdoNATwwUg0GOuSFvyrtyCCW','N1tLeTlP7LZUt3QILZyQw957s38AKB','2017-03-11 08:44:18',''),
(2,'KGy3oJySBTbMmubglOXnhVqsRQDoRcFjJ3921U1Z',2,'Bearer','9ery8pVOxTOvQU0oJsENRek4lj6ZT6','oRojE4Gu4KY29TXO11yh1AcZLGjOhM','2017-03-25 12:29:49',''),
(3,'KGy3oJySBTbMmubglOXnhVqsRQDoRcFjJ3921U1Z',3,'Bearer','iM0WU5y76laIJph5LS1jidKcdjWk4a','JdRrBdcm9N7cfhjjcUUIRWGU7UVBuy','2017-03-27 00:40:30','');
INSERT INTO domain_role (role_name) VALUES ("CAN_ADD_USER_ROLES"),("CAN_DELETE_USER_ROLES"), ("CAN_ADD_USERS"),
("CAN_GET_USERS"),("CAN_DELETE_USERS"),("CAN_ADD_TALENT_POOLS"),("CAN_GET_TALENT_POOLS"),("CAN_DELETE_TALENT_POOLS"),("CAN_ADD_TALENT_POOLS_TO_GROUP"),("CAN_ADD_CANDIDATES"),("CAN_GET_CANDIDATES"),
("CAN_DELETE_CANDIDATES"),("CAN_ADD_TALENT_PIPELINE_SMART_LISTS"), ("CAN_DELETE_TALENT_PIPELINE_SMART_LISTS"), ("CAN_ADD_TALENT_PIPELINES");
INSERT INTO user_scoped_roles (UserId, RoleId) VALUES (1, 1), (1,2),(2,1),(2,2),(3,1),(3,2);
'''

sql = text(q)
result = db.engine.execute(sql)

from candidate_service.candidate_app import app

with app.app_context():
    from candidate_service.modules.talent_cloud_search import delete_all_candidate_documents
    delete_all_candidate_documents()

print 'Candidate Documents have been removed successfully from Amazon CloudSearch'
