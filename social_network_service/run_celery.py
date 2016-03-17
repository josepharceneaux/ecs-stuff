"""
    Run Celery Worker

For Celery to run from command line, script runs as separate process with celery command

 Usage: open terminal cd to talent-flask-services directory

 Run the following command to start celery worker:

    $ celery -A social_network_service.social_network_app.celery_app worker --concurrency=4 --loglevel=info
"""

# Service Specific
from social_network_service.common.talent_celery import CELERY_WORKER_ARGS
from social_network_service.social_network_app import celery_app, logger, app, queue_name
from social_network_service.common.talent_config_manager import TalentConfigKeys

try:
    celery_app.start(argv=CELERY_WORKER_ARGS + [queue_name])
    logger.info("Celery worker has been started successfully for %s" % app.import_name)
except Exception as e:
    logger.exception("Couldn't start Celery app for social_network_service in "
                     "%s environment." % (app.config[TalentConfigKeys.ENV_KEY]))

