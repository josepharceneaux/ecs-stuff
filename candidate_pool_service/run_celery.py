"""
    Run Celery Worker
For Celery to run from command line, script runs as separate process with celery command
 Usage: open terminal cd to talent-flask-services directory
 Run the following command to start celery worker:
     celery -A scheduler_service.run.celery  worker --concurrency=4 --loglevel=info
"""

# Service Specific
from candidate_pool_service.candidate_pool_app import logger, celery_app as celery

logger.info("Celery worker has been started successfully")
celery.start(argv=['celery', 'worker', '-Ofair', '-l', 'info', '-Q', 'celery_stats_scheduler'])
