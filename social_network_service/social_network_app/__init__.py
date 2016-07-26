from social_network_service.modules.constants import QUEUE_NAME

__author__ = 'zohaib'

from social_network_service.common.talent_celery import init_celery_app
from social_network_service.common.utils.models_utils import init_talent_app


app, logger = init_talent_app(__name__)

# Celery app
celery_app = init_celery_app(app, QUEUE_NAME,
                             ['social_network_service.tasks'])

