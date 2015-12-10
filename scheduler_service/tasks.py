import json
from celery import Celery
import requests


celery = Celery('scheduler_service', broker='redis://localhost:6379', backend='redis://localhost:6379')


@celery.task(name="send_request")
def send_request(access_token, url, content_type, kwargs):
    """
    :param user_id: the user_id of user who is sending post request
    :param url: the url where to send post requests
    :param content_type: the content type i.e json or xml
    :param kwargs: post data i.e campaign name, smartlist ids
    :return:
    """
    headers = {
        'Content-Type': content_type,
        'Authorization': 'Bearer %s' % access_token
    }
    if content_type == 'application/json':
        kwargs = json.dumps(kwargs)

    response = requests.post(url, data=kwargs, headers=headers)
    return response.json()


