"""
    Run Celery Worker

For Celery to run from command line, script runs as separate process with celery command

 Usage: open terminal cd to talent-flask-services directory

 Run the following command to start celery worker:

    $ celery -A push_campaign_service.push_campaign_app.celery_app worker --concurrency=4 --loglevel=info
"""

# Service Specific
from push_campaign_app import celery_app, app
from push_campaign_service.modules.constants import CELERY_QUEUE
with app.app_context():
    celery_app.start(argv=['celery', 'worker', '-l', 'info', '-Q', CELERY_QUEUE])
