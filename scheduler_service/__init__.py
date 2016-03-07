# Third Party imports
from celery import Celery
from kombu import Queue

# Service specific imports
from flask.ext.cors import CORS

from scheduler_service.common.error_handling import register_error_handlers
from scheduler_service.common.models.db import db
from scheduler_service.common.redis_cache import redis_store
from scheduler_service.common.utils.models_utils import add_model_helpers
from scheduler_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys
from scheduler_service.common.utils.scheduler_utils import SchedulerUtils
from scheduler_service.common.utils.talent_ec2 import get_ec2_instance_id
from scheduler_service.common.routes import GTApis
from scheduler_service.common.talent_flask import TalentFlask

__author__ = 'saad'


flask_app = TalentFlask(__name__)
load_gettalent_config(flask_app.config)
logger = flask_app.config[TalentConfigKeys.LOGGER]
logger.info("Starting app %s in EC2 instance %s", flask_app.import_name, get_ec2_instance_id())

add_model_helpers(db.Model)
db.init_app(flask_app)
db.app = flask_app

# Enable CORS for *.gettalent.com and localhost
CORS(flask_app, resources=GTApis.CORS_HEADERS)

# Initialize Redis Cache
redis_store.init_app(flask_app)

register_error_handlers(flask_app, logger)
logger.info("Starting scheduler service in %s environment",
            flask_app.config[TalentConfigKeys.ENV_KEY])

# Celery settings

celery_queue = {
    'CELERY_QUEUES': (
        Queue(SchedulerUtils.QUEUE, routing_key=SchedulerUtils.QUEUE + '_key'),
    ),
    'CELERY_DEFAULT_QUEUE': SchedulerUtils.QUEUE,
    'CELERY_DEFAULT_ROUTING_KEY': SchedulerUtils.QUEUE + '_key'
}
resultant_db_tables = {
    'CELERY_RESULT_DB_TABLENAMES': {
        'task': 'scheduler_taskmeta',
        'group': 'scheduler_groupmeta'
    }
}
accept_content = {
    'CELERY_ACCEPT_CONTENT': ['json', 'msgpack', 'yaml']
}

celery_app = Celery(flask_app, broker=flask_app.config[TalentConfigKeys.REDIS_URL_KEY],
                    backend=flask_app.config[TalentConfigKeys.CELERY_RESULT_BACKEND_URL],
                    include=['scheduler_service.tasks'])

celery_app.conf.update(celery_queue)
celery_app.conf.update(resultant_db_tables)
celery_app.conf.update(accept_content)

from scheduler_service.api.scheduler_api import scheduler_blueprint
flask_app.register_blueprint(scheduler_blueprint)

# Start APS Scheduler
from scheduler_service.scheduler import scheduler

scheduler.start()
