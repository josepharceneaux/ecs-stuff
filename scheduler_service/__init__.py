

# Third Party imports
from celery import Celery
from flask import Flask

# Service specific imports
from scheduler_service.common.error_handling import register_error_handlers
from scheduler_service.common.models.db import db
from scheduler_service.common.redis_cache import redis_store
from scheduler_service.common.utils.models_utils import add_model_helpers
from scheduler_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys
from scheduler_service.common.utils.scheduler_utils import SchedulerUtils

__author__ = 'saad'


flask_app = Flask(__name__)
load_gettalent_config(flask_app.config)

logger = flask_app.config[TalentConfigKeys.LOGGER]

add_model_helpers(db.Model, logger=logger)
db.init_app(flask_app)
db.app = flask_app

# Initialize Redis Cache
redis_store.init_app(flask_app)

register_error_handlers(flask_app, logger)
logger.info("Starting scheduler service in %s environment",
            flask_app.config[TalentConfigKeys.ENV_KEY])

# Celery settings
default_queue = {'CELERY_DEFAULT_QUEUE': SchedulerUtils.QUEUE}
default_serializer = {'CELERY_RESULT_SERIALIZER': 'json'}
resultant_db_tables = {
    'CELERY_RESULT_DB_TABLENAMES': {
        'task': 'scheduler_taskmeta',
        'group': 'scheduler_groupmeta'
    }
}
accept_content = {
    'CELERY_ACCEPT_CONTENT': ['json', 'msgpack', 'yaml']
}
celery_app = Celery(flask_app, broker=flask_app.config['REDIS_URL'], backend=flask_app.config['BACKEND_URL'],
                    include=['scheduler_service.tasks'])
celery_app.conf.update(default_queue)
celery_app.conf.update(resultant_db_tables)
celery_app.conf.update(default_serializer)
celery_app.conf.update(accept_content)

from scheduler_service.api.scheduler_api import scheduler_blueprint
flask_app.register_blueprint(scheduler_blueprint)