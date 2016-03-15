"""
    Run Celery Worker

For Celery to run from command line, script runs as separate process with celery command
 Usage: open terminal cd to talent-flask-services directory
 Run the following command to start celery worker:
     celery -A scheduler_service.celery_app worker --concurrency=4 --loglevel=info
"""

# Service Specific
from scheduler_service import celery_app as celery
from scheduler_service.common.talent_celery import CELERY_WORKER_ARGS
from scheduler_service.common.utils.scheduler_utils import SchedulerUtils

celery.start(argv=CELERY_WORKER_ARGS + [SchedulerUtils.QUEUE])