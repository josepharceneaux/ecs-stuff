""" Run Celery Worker """

from push_campaign_service.push_campaign_app.app import celery_app

celery_app.start(argv=['celery', 'worker', '-l', 'info'])

