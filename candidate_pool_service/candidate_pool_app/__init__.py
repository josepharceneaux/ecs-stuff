__author__ = 'ufarooqi'

from flask.ext.cors import CORS
from flask.ext.cache import Cache

from candidate_pool_service.common.utils.models_utils import init_talent_app
from candidate_pool_service.common.routes import HEALTH_CHECK, CandidatePoolApi, GTApis
from candidate_pool_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys
from candidate_pool_service.common.utils.talent_ec2 import get_ec2_instance_id
from candidate_pool_service.common.talent_flask import TalentFlask
from candidate_pool_service.common.talent_celery import init_celery_app
from candidate_pool_service.common.models.db import db

app, logger = init_talent_app(__name__)

try:
    # Instantiate Flask-Cache object
    cache = Cache(app, config={'CACHE_TYPE': 'redis', 'CACHE_REDIS_URL': app.config['REDIS_URL']})

    # Instantiate Celery
    celery_app = init_celery_app(app, 'celery_stats_scheduler')

    from api.talent_pools import talent_pool_blueprint
    from api.talent_pipelines import talent_pipeline_blueprint
    from api.smartlists import smartlist_blueprint

    app.register_blueprint(talent_pipeline_blueprint, url_prefix=CandidatePoolApi.URL_PREFIX)
    app.register_blueprint(talent_pool_blueprint, url_prefix=CandidatePoolApi.URL_PREFIX)
    app.register_blueprint(smartlist_blueprint, url_prefix=CandidatePoolApi.URL_PREFIX)

    db.create_all()
    db.session.commit()

except Exception as e:
    logger.exception("Couldn't start candidate_pool_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], e.message))
