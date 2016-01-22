__author__ = 'erikfarmer'
import os
# from widget_service.common.utils.handy_functions import random_word
#
# def valid_oauth_credentials():
#     client = Client(client_id=random_word(16), client_secret=random_word(18))
#     db.session.add(client)
#     db.session.commit()
#     c_id = client.client_id
#     c_secret = client.client_secret
#     org = Organization(name='Rocket League All Stars - {}'.format(random_word(8)))
#     culture= Culture(description='Foo {}'.format(random_word(12)), code=random_word(5))
#     domain = Domain(name=random_word(40),
#                          expiration=datetime.datetime(2050, 4, 26),
#                          added_time=datetime.datetime.today(),
#                          organization_id=org.id, is_fair_check_on=False, is_active=1,
#                          default_tracking_code=1, default_from_name=(random_word(100)),
#                          default_culture_id=culture.id,
#                          settings_json=random_word(55))
#     db.session.add(domain)
#     db.session.commit()
#     user = User(
#         domain_id=domain.id, first_name='Jamtry', last_name='Jonas',
#         password='password', email='jamtry@{}.com'.format(random_word(7)),
#         added_time=datetime.datetime.today()
#     )
#     db.session.add(user)
#     db.session.commit()
#
#     token = Token(client_id=client.client_id, user_id=user.id, token_type='bearer',
#                        access_token=random_word(18), refresh_token=random_word(18),
#                        expires=datetime.datetime.now() - datetime.timedelta(days=30))
#
#     return c_id, c_secret


env = os.getenv('GT_ENVIRONMENT') or 'dev'
if env == 'dev':
    ENVIRONMENT = 'dev'
    WIDGET_CLIENT_ID = 'dev_client_id'
    WIDGET_CLIENT_SECRET = 'dev_client_secret'
    CANDIDATE_CREATION_URI = 'http://127.0.0.1:8005/v1/candidates'
    OAUTH_ROOT = 'http://0.0.0.0:8001%s'
    OAUTH_AUTHORIZE_URI = OAUTH_ROOT % '/oauth2/authorize'
    OAUTH_TOKEN_URI = OAUTH_ROOT % '/oauth2/token'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!loc976892@localhost/talent_local'
    DEBUG = True
elif env == 'jenkins':
    ENVIRONMENT = 'jenkins'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_ci:s!ci976892@circleci.cp1kv0ecwo23.us-west-1.rds.amazonaws.com/talent_ci'
    DEBUG = True
elif env == 'qa':
    ENVIRONMENT = 'qa'
    CANDIDATE_CREATION_URI = 'https://webdev.gettalent.com/web/api/candidates.json'
    OAUTH_ROOT = 'https://secure-webdev.gettalent.com%s'
    OAUTH_AUTHORIZE_URI = OAUTH_ROOT % '/oauth2/authorize'
    OAUTH_TOKEN_URI = OAUTH_ROOT % '/oauth2/token'
    SQLALCHEMY_DATABASE_URI = 'mysql://talent_web:s!web976892@devdb.gettalent.com/talent_staging'
    DEBUG = False
elif env == 'prod':
    ENVIRONMENT = 'prod'
    OAUTH_ROOT = 'https://secure.gettalent.com%s'
    OAUTH_AUTHORIZE_URI = OAUTH_ROOT % '/oauth2/authorize'
    OAUTH_TOKEN_URI = OAUTH_ROOT % '/oauth2/token'
    DEBUG = False
else:
    raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not run app.")

ENCRYPTION_KEY = 'heylookeveryonewegotasupersecretkeyoverhere'
SECRET_KEY = os.getenv('SECRET_KEY')
