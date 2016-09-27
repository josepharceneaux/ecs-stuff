# Third Party imports
import socket

from scheduler_service.common.error_handling import register_error_handlers
from scheduler_service.common.models.db import db
from scheduler_service.common.redis_cache import redis_store
from scheduler_service.common.routes import GTApis
from scheduler_service.common.talent_celery import init_celery_app
from scheduler_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys
from scheduler_service.common.talent_flask import TalentFlask
from scheduler_service.common.utils.models_utils import add_model_helpers
from scheduler_service.common.utils.models_utils import init_talent_app
from scheduler_service.common.utils.scheduler_utils import SchedulerUtils
from scheduler_service.common.utils.talent_ec2 import get_ec2_instance_id


__author__ = 'saad'

flask_app, logger = init_talent_app(__name__)

# Celery settings
celery_app = init_celery_app(flask_app=flask_app,
                             default_queue=SchedulerUtils.QUEUE,
                             modules_to_include=['scheduler_service.tasks'])

from scheduler_service.api.scheduler_api import scheduler_blueprint
flask_app.register_blueprint(scheduler_blueprint)

# Start APS Scheduler
try:
    # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock.bind(("127.0.0.1", 47200))
    pass
except socket.error:
    print "!!!scheduler already started, DO NOTHING"
else:
    from scheduler_service.modules.apscheduler_instance import get_scheduler
    scheduler = get_scheduler()
    if scheduler:
        scheduler.start()
    print "scheduler started"
