"""
Script for developers to reset their database and remove all dangling candidate documents in Amazon CloudSearch.

Prerequisites:
You must have MySQL running locally and a database called talent_local.

Run:
python setup_environment/reset_database_and_cloud_search.py

"""
# Third Party
from sqlalchemy import text

# App specific
from common.talent_config_manager import load_gettalent_config, TalentConfigKeys
from common.talent_flask import TalentFlask
# Flush redis-cache
from common.redis_cache import redis_store
from common.models.db import db
from candidate_service.candidate_app import app
from setup_environment.create_dummy_users import create_dummy_users

static_tables = ['candidate_status', 'classification_type', 'country', 'culture', 'email_label', 'phone_label',
                 'frequency', 'organization', 'product', 'rating_tag', 'social_network', 'web_auth_group',
                 'email_client', 'migration', 'permission', 'permissions_of_role', 'role']

flush_redis_entries = ['apscheduler.jobs', 'apscheduler.run_times', 'count_*_request', 'apscheduler_job_ids:user_*',
                       'apscheduler_job_ids:general_*']

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
            if '*' in entry:
                for key in _redis.keys(entry):
                    _redis.delete(key)
            else:
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


create_dummy_users()
# TODO: Add comment about following query
q = '''INSERT INTO user_social_network_credential(Id, UserId, SocialNetworkId, RefreshToken, webhook, MemberId, AccessToken) VALUES (NULL, '1', '18', NULL, '217041', '164351364314', 'YZASRSWZO5CWKSEXMELQ');'''
sql = text(q)
result = db.engine.execute(sql)

from candidate_service.candidate_app import app

with app.app_context():
    from candidate_service.modules.talent_cloud_search import delete_all_candidate_documents
    delete_all_candidate_documents()

print 'Candidate Documents have been removed successfully from Amazon CloudSearch'
