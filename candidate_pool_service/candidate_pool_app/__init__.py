__author__ = 'ufarooqi'

from flask import Flask
from healthcheck import HealthCheck
from candidate_pool_service.common.models.db import db
from candidate_pool_service.common.redis_cache import redis_store
from candidate_pool_service.common.talent_config_manager import TalentConfig, ConfigKeys

app = Flask(__name__)
app.config = TalentConfig(app.config).app_config

logger = app.config[ConfigKeys.LOGGER]
from candidate_pool_service.common.error_handling import register_error_handlers
print "register error handlers"
register_error_handlers(app, logger)

db.init_app(app)
db.app = app

# Initialize Redis Cache
redis_store.init_app(app)

# wrap the flask app and give a heathcheck url
health = HealthCheck(app, "/healthcheck")

from api.talent_pools import talent_pool_blueprint
from api.talent_pipelines import talent_pipeline_blueprint
from api.smartlists import smartlist_blueprint

app.register_blueprint(talent_pipeline_blueprint, url_prefix='/v1')
app.register_blueprint(talent_pool_blueprint, url_prefix='/v1')
app.register_blueprint(smartlist_blueprint, url_prefix='/v1')

db.create_all()
db.session.commit()

from candidate_pool_service.candidate_pool_app.talent_pools_pipelines_utilities import \
    schedule_talent_pool_and_pipelines_daily_stats_update

schedule_talent_pool_and_pipelines_daily_stats_update()

logger.info("Starting candidate_pool_service in %s environment", app.config[ConfigKeys.LOGGER])