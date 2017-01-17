"""
    Run Celery Worker

For Celery to run from command line, script runs as separate process with celery command

 Usage: open terminal cd to talent-flask-services directory

 Run the following command to start celery worker:

    $ celery -A push_campaign_service.push_campaign_app.celery_app worker --concurrency=4 --loglevel=info
"""

# Service Specific
from push_campaign_service.common.talent_celery import CELERY_WORKER_ARGS
from push_campaign_service.push_campaign_app import celery_app, logger, app
from push_campaign_service.common.talent_config_manager import TalentConfigKeys
from push_campaign_service.common.campaign_services.campaign_utils import CampaignUtils

try:
    logger.info("Celery worker has been started successfully for:%s" % app.name)
    celery_app.start(argv=CELERY_WORKER_ARGS + [CampaignUtils.PUSH] + ['-n', CampaignUtils.PUSH])
except Exception as e:
    logger.exception("Couldn't start Celery worker for push_campaign_service in "
                     "%s environment." % (app.config[TalentConfigKeys.ENV_KEY]))
