""" Script runs as separate process with celery command

 Usage: open terminal cd to talent-flask-services directory

 Run the following command to start celery worker:
    $ celery -A sms_campaign_service.modules.celery_config worker --loglevel=info

    $ celery -A sms_campaign_service.modules.celery_config worker --concurrency=10 --loglevel=info
    $ celery -A sms_campaign_service.modules.celery_config.celery_app worker --concurrency=4 --loglevel=info

"""
# Third Party
from celery import Celery

# Application specific
from sms_campaign_service.sms_campaign_app.app import app
from sms_campaign_service.common.common_config import BROKER_URL

# Celery settings
celery_app = Celery(app, broker=BROKER_URL, backend=BROKER_URL,
                    include=['sms_campaign_service.sms_campaign_base'])

#
#
# @celery_app.task(name='send_scheduled_campaign')
# def send_scheduled_campaign(*args, **kwargs):
#     sents = 0
#     try:
#         import time
#         time.sleep(5)
#         return 1
#     except Exception:
#         print ' error '
#     return sents
#
#
# @celery_app.task(name='tsum')
# def tsum(res):
#     print 'Got Callback %s'
#     ones = res.count(1)
#     print 'campaign sent to %s candidates' % ones
