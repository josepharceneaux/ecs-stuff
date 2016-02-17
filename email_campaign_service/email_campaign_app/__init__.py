"""Initialize Email campaign service app, register error handlers and register blueprint"""

from celery import Celery
from email_campaign_service.common.utils.models_utils import init_talent_app

app, logger = init_talent_app(__name__)

# Initialize Celery app
celery_app = Celery(app, broker=app.config['REDIS_URL'],
                    backend=app.config['CELERY_RESULT_BACKEND_URL'],
                    include=['email_campaign_service.modules.email_marketing'])

# Register API endpoints
from apis.email_campaigns import email_campaign_blueprint
app.register_blueprint(email_campaign_blueprint)

