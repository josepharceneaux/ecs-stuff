
__author__ = 'ufarooqi'

from flask import Flask
from candidate_pool_service.common.routes import HEALTH_CHECK
from candidate_pool_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys

app = Flask(__name__)
load_gettalent_config(app.config)

logger = app.config[TalentConfigKeys.LOGGER]

try:
    from candidate_pool_service.common.error_handling import register_error_handlers
    print "register error handlers"
    register_error_handlers(app, logger)


    from candidate_pool_service.common.models.db import db
    db.init_app(app)
    db.app = app

    # Initialize Redis Cache
    from candidate_pool_service.common.redis_cache import redis_store
    redis_store.init_app(app)

    # wrap the flask app and give a heathcheck url
    from healthcheck import HealthCheck
    health = HealthCheck(app, HEALTH_CHECK)

    from api.talent_pools import talent_pool_blueprint
    from api.talent_pipelines import talent_pipeline_blueprint
    from api.smartlists import smartlist_blueprint

    app.register_blueprint(talent_pipeline_blueprint, url_prefix='/v1')
    app.register_blueprint(talent_pool_blueprint, url_prefix='/v1')
    app.register_blueprint(smartlist_blueprint, url_prefix='/v1')

    db.create_all()
    db.session.commit()

    from candidate_pool_service.candidate_pool_app.talent_pools_pipelines_utilities import \
        schedule_candidate_daily_stats_update

    schedule_candidate_daily_stats_update()

    logger.info("Starting candidate_pool_service in %s environment", app.config[TalentConfigKeys.ENV_KEY])

except Exception as e:
    logger.exception("Couldn't start candidate_pool_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], e.message))
