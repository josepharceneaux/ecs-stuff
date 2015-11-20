from celery import Celery
from flask import Flask
import time

app = Flask('scheduler_service')
celery = Celery(app.import_name, broker='redis://localhost:6379', backend='redis://localhost:6379')


@celery.task(name='send_campaign')
def send_campaign(*args, **kwargs):
    print('Sending campaign')
    time.sleep(5)
    return 'Campaign sent successfully'
