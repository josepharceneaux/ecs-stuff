""" Run Celery Worker """

from sms_campaign_service.sms_campaign_app.app import celery_app

celery_app.start(argv=['celery', 'worker', '-l', 'info'])

