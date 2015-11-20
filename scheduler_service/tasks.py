from celery import Celery
from flask import Flask
import time

app = Flask('scheduler_service')
celery = Celery(app.import_name, broker='redis://localhost:6379', backend='redis://localhost:6379')


@celery.task(name='send_sms_campaign')
def send_sms_campaign(*args, **kwargs):
    print('Sending campaign')
    # time.sleep(5)
    return 'SMS Campaign sent successfully'


@celery.task(name='send_email_campaign')
def send_email_campaign(*args, **kwargs):
    print('Sending campaign')
    # time.sleep(5)
    return 'Email Campaign sent successfully'

methods = {
    'send_sms_campaign': send_sms_campaign,
    'send_email_campaign': send_email_campaign
}
