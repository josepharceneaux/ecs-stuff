from celery import Celery
from flask import Flask
import time
import requests
from scheduler_service import logger
from scheduler_service.app_utils import JsonResponse

app = Flask('scheduler_service')
celery = Celery(app.import_name, broker='redis://localhost:6379', backend='redis://localhost:6379')


@celery.task(name='raise_exception')
def raise_exception(*args, **kwargs):
    logger.error('raise_exception')
    #implement method here
    raise Exception('Intentional exception raised')

methods = {
    'raise_exception': raise_exception
}


@celery.task(name="send_request")
def send_request(user_id, access_token, url, content_type, **kwargs):
    """
    :param user_id: the user_id of user who is sending post request
    :param url: the url where to send post requests
    :param content_type: the content type i.e json or xml
    :param kwargs: post data i.e campaign name, smartlist ids
    :return:
    """
    headers = {
        'Content-Type': content_type,
        'Authentication': 'Bearer %s' % access_token
    }
    try:
        response = requests.post(url, data=kwargs, headers=headers)
        return JsonResponse(response.json())
    except Exception as e:
        logger.error(e.message)
        raise e

