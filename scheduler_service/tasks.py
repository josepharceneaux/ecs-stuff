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
import requests


@celery.task(name="send_request")
def send_request(access_token, secret_key, url, content_type, kwargs):
    """
    This method will be called by run_job asynchronously
    :param access_token: authorization token for user
    :param url: the url where to send post request
    :param content_type: the content type i.e json or xml
    :param secret_key: Redis key which have a corresponding secret value to decrypt data
    :param kwargs: post data i.e campaign name, smartlist ids
    :return:
    """
    headers = {
        'Content-Type': content_type,
        'Authorization': access_token,
        'X-Talent-Server-Key': secret_key
    }
    #TODO use http_request()
    response = requests.post(url, data=kwargs, headers=headers)
    try:
        # TODO use response.content
        return response.json()
    except: #TODO catch Exception and also comment here that following is for flower
        # TODO
        return {'message': "JSON object couldn't be decoded", 'status_code': response.status_code}


