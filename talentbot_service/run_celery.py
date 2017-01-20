"""
    Run Celery Worker

For Celery to run from command line, script runs as separate process with celery command

 Usage: open terminal cd to talent-flask-services directory

 Run the following command to start celery worker:

    $ celery -A talentbot_service.celery_app worker --concurrency=4 --loglevel=info
"""

# Service Specific
from talentbot_service.modules.constants import QUEUE_NAME
from talentbot_service.common.talent_celery import CELERY_WORKER_ARGS
from talentbot_service import celery_app, logger, app

logger.info("Starting Celery worker for:%s" % app.name)
celery_app.start(argv=CELERY_WORKER_ARGS + [QUEUE_NAME] + ['-n', 'talentbot_service'])
