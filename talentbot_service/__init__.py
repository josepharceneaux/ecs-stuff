"""
Getting app and logger from common services
"""
from talentbot_service.common.talent_celery import init_celery_app
from talentbot_service.common.utils.models_utils import init_talent_app
from talentbot_service.modules.constants import QUEUE_NAME

app, logger = init_talent_app(__name__)

# Celery App
celery_app = init_celery_app(app, QUEUE_NAME,
                             ['talentbot_service.tasks'])
