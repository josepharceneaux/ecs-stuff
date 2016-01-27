
"""
    Run Celery Worker
For Celery Flower to run from command line, script runs as separate process with celery command
 Usage: open terminal cd to talent-flask-services directory
 Run the following command to start celery flower:
      celery flower -A scheduler_service.run.celery
"""

# Service Specific
from scheduler_service.common.routes import SchedulerApiUrl
from scheduler_service.common.utils.scheduler_utils import SchedulerUtils
from scheduler_service import celery_app as celery


celery.start(argv=['celery', 'flower', SchedulerApiUrl.FLOWER_MONITORING, 'Q', SchedulerUtils.QUEUE, '-l', 'info'])
