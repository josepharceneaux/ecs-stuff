"""
Script for developers to reset their database and remove all dangling candidate documents in Amazon CloudSearch.

Prerequisites:
You must have MySQL running locally and a database called talent_local.

Run:
python setup_environment/reset_database_and_cloud_search.py

"""

from common.talent_config_manager import load_gettalent_config, TalentConfigKeys
from common.talent_flask import TalentFlask

static_tables = ['candidate_status', 'classification_type', 'country', 'culture', 'email_label', 'phone_label',
                 'frequency', 'organization', 'product', 'rating_tag', 'social_network', 'web_auth_group', 'email_client']

app = TalentFlask(__name__)
load_gettalent_config(app.config)

if app.config[TalentConfigKeys.ENV_KEY] not in ['dev', 'jenkins']:
    print "You can reset your database and CloudSearch domain only in 'dev' or 'jenkins' environment"
    raise SystemExit(0)


def save_meetup_token_and_flushredis(_redis):
    if _redis.get('Meetup'):
        _token = _redis.get('Meetup')
        _redis.flushall()
        _redis.set('Meetup', _token)

# Flush redis-cache
from common.redis_cache import redis_store
redis_store.init_app(app)
save_meetup_token_and_flushredis(redis_store)

from common.models.db import db
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

# Create domain
from common.models.user import Domain, User

domain_first = Domain(name='test_domain_first', organization_id=1)
domain_second = Domain(name='test_domain_first', organization_id=1)

db.session.add(domain_first)
db.session.add(domain_second)
db.session.commit()

user_first = User(email='test_email_first@gmail.com', default_culture_id=1, domain_id=domain_first.id)
user_same_domain = User(email='test_email_same_domain@gmail.com', default_culture_id=1, domain_id=domain_first.id)
user_second = User(email='test_email_second@gmail.com', default_culture_id=1, domain_id=domain_second.id)

db.session.add(user_first)
db.session.add(user_same_domain)
db.session.add(user_second)
db.session.commit()

from candidate_service.candidate_app import app
with app.app_context():
    from candidate_service.modules.talent_cloud_search import delete_all_candidate_documents
    delete_all_candidate_documents()

print 'Candidate Documents have been removed successfully from Amazon CloudSearch'
