from social_network_service.common.utils.celery_utils import init_celery_app
from social_network_service.common.utils.models_utils import init_talent_app

__author__ = 'zohaib'

# Assign a queue name
queue_name = 'social_network'
app, logger = init_talent_app(__name__)

# Celery app
celery_app = init_celery_app(app, queue_name,
                             ['social_network_service.tasks'])
