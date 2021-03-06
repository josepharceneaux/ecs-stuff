"""
    Run Celery Worker

For Celery to run from command line, script runs as separate process with celery command

 Usage: open terminal cd to talent-flask-services directory

 Run the following command to start celery worker:

    $ celery -A sms_campaign_service.sms_campaign_app.celery_app worker --concurrency=4 --loglevel=info
"""

# Service Specific
from sms_campaign_service.common.talent_celery import CELERY_WORKER_ARGS
from sms_campaign_service.sms_campaign_app import celery_app, logger, app
from sms_campaign_service.common.talent_config_manager import TalentConfigKeys
from sms_campaign_service.common.campaign_services.campaign_utils import CampaignUtils

try:
    logger.info('Starting celery app for %s' % app.name)
    celery_app.start(argv=CELERY_WORKER_ARGS + [CampaignUtils.SMS] + ['-n', CampaignUtils.SMS])
except Exception as e:
    logger.exception("Couldn't start Celery worker for sms_campaign_service in "
                     "%s environment." % (app.config[TalentConfigKeys.ENV_KEY]))
