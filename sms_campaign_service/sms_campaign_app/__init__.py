""" Initializer for SMS Campaign Service App and Celery App"""

# Third Party
from celery import Celery
from healthcheck import HealthCheck

# Common Utils
from sms_campaign_service.common.routes import HEALTH_CHECK
from sms_campaign_service.common.utils.models_utils import init_talent_app

app, logger = init_talent_app(__name__)
# # healthcheck URL
# health = HealthCheck(app, HEALTH_CHECK)

# Celery settings
celery_app = Celery(app, broker=app.config['REDIS_URL'],
                    backend=app.config['CELERY_RESULT_BACKEND_URL'],
                    include=['sms_campaign_service.modules.sms_campaign_base'])