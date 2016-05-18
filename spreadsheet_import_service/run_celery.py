"""
    Run Celery Worker
For Celery to run from command line, script runs as separate process with celery command
 Usage: open terminal cd to talent-flask-services directory
 Run the following command to start celery worker:
     celery -A spreadsheet_import_service.app.celery_app worker --concurrency=4 --loglevel=info

"""

# Service Specific
from spreadsheet_import_service.common.talent_celery import CELERY_WORKER_ARGS
from spreadsheet_import_service.app import logger, celery_app as celery

logger.info("Celery worker has been started successfully")
celery.start(argv=CELERY_WORKER_ARGS + ['celery_spreadsheet_import_scheduler'] + ['-n', 'celery_spreadsheet_import_scheduler'])
