"""
    Run Celery Worker

For Celery to run from command line, script runs as separate process with celery command
 Usage: open terminal cd to talent-flask-services directory
 Run the following command to start celery worker:
     celery -A scheduler_service.run.celery  worker --concurrency=4 --loglevel=info
"""

# Service Specific
from scheduler_service import celery_app as celery
from scheduler_service.common.utils.scheduler_utils import SchedulerUtils


celery.start(argv=['celery', 'worker', '-l', 'info', '-Q', SchedulerUtils.QUEUE])
