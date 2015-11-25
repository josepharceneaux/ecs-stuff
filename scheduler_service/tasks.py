from celery import Celery
from flask import Flask
import time

app = Flask('scheduler_service')
celery = Celery(app.import_name, broker='redis://localhost:6379', backend='redis://localhost:6379')


@celery.task(name='send_sms_campaign')
def send_sms_campaign(*args, **kwargs):
    print('Sending SMS campaign')
    time.sleep(10)
    return 'SMS Campaign sent successfully'


@celery.task(name='send_email_campaign')
def send_email_campaign(*args, **kwargs):
    print('Sending Email campaign')
    #implement method here
    return 'Email Campaign sent successfully'


@celery.task(name='raise_exception')
def raise_exception(*args, **kwargs):
    print('raise_exception')
    #implement method here
    raise Exception('Internal exception raised')

methods = {
    'send_sms_campaign': send_sms_campaign,
    'send_email_campaign': send_email_campaign,
    'raise_exception': raise_exception
}
