"""
    Run Celery Worker
For Celery to run from command line, script runs as separate process with celery command
 Usage: open terminal cd to talent-flask-services directory
 Run the following command to start celery worker:
     celery -A candidate_pool_service.run.celery  beat
"""

# Service Specific
from candidate_pool_service.candidate_pool_app import logger, celery_app as celery

logger.info("Celery Beat has been started successfully in CandidatePool Service")
celery.start(argv=['celery', 'beat', '-S', 'celerybeatredis.schedulers.RedisScheduler'])