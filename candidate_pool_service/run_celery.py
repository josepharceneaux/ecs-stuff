"""
    Run Celery Worker
For Celery to run from command line, script runs as separate process with celery command
 Usage: open terminal cd to talent-flask-services directory
 Run the following command to start celery worker:
     celery -A candidate_pool_service.candidate_pool_app.celery_app worker --concurrency=4 --loglevel=info

"""

# Service Specific
from candidate_pool_service.common.talent_celery import CELERY_WORKER_ARGS
from candidate_pool_service.candidate_pool_app import logger, celery_app as celery

logger.info("Celery worker has been started successfully")
celery.start(argv=CELERY_WORKER_ARGS + ['celery_stats_scheduler'] + ['-n', 'celery_stats_scheduler'])
