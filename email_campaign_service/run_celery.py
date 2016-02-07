"""
    Run Celery Worker

For Celery to run from command line, script runs as separate process with celery command

 Usage: open terminal cd to talent-flask-services directory

 Run the following command to start celery worker:

    $ celery -A email_campaign_service.email_campaign_app.celery_app worker --concurrency=4 --loglevel=info
"""

# Service Specific
from email_campaign_service.email_campaign_app import celery_app
from email_campaign_service.common.campaign_services.campaign_utils import CampaignUtils


celery_app.start(argv=['celery', 'worker', '-l', 'info', '-Q', CampaignUtils.EMAIL])
