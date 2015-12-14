"""
Celery tasks are defined here. It will be a separate celery process.
These methods are called by run_job method asynchronously

- Running celery using commandline (scheduler_service directory) =>

    celery -A scheduler_service.run.celery  worker --concurrency=4 --loglevel=info

- Running celery flower using commandline (scheduler_service directory) =>

    celery flower -A scheduler_service.run.celery

default url for celery flower =>

    localhost:5555

"""
from scheduler_service.run import celery

# Third-Party imports
import json
import requests


@celery.task(name="send_request")
def send_request(access_token, url, content_type, kwargs):
    """
    This method will be called by run_job asynchronously
    :param access_token: authorization token for user
    :param url: the url where to send post request
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


