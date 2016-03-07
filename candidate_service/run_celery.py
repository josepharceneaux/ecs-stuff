"""
    Run Celery Worker
For Celery to run from command line, script runs as separate process with celery command
 Usage: open terminal cd to talent-flask-services directory
 Run the following command to start celery worker:
     celery -A scheduler_service.run.celery  worker --concurrency=4 --loglevel=info
"""

# Service Specific
from candidate_service.candidate_app import logger, celery_app as celery

logger.info("Celery worker has been started successfully")
celery.start(argv=['celery', 'worker', '-Ofair', '--without-gossip', '-l', 'info', '-Q',
                   'celery_candidate_documents_scheduler'])
