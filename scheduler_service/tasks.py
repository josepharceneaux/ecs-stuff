"""
Celery tasks are defined here. It will be a separate celery process.
These methods are called by run_job method asynchronously

- Running celery using commandline (scheduler_service directory) =>

    celery -A scheduler_service.run.celery  worker --concurrency=4 --loglevel=info

- Running celery flower using commandline (scheduler_service directory) =>

    celery flower -A scheduler_service.run.celery

For Scheduler Service, celery flower is =>

    localhost:5511

"""
# Std imports
import json

# Application imports
from scheduler_service.common.utils.handy_functions import http_request
from scheduler_service import celery_app as celery, flask_app as app, TalentConfigKeys, SchedulerUtils


@celery.task(name="send_request", queue=SchedulerUtils.QUEUE)
def send_request(*args, **kwargs):
    """
    This method will be called by run_job asynchronously
    :param kwargs:
        access_token: authorization token for user
        url: the URL where to send post request
        content_type: the content type i.e json or xml
        post_data: Data to post with post request
        is_jwt_request: If true, then request will be send using JWT authorization
        request_method: The type of request i.e POST, DELETE, GET, UPDATE, PATCH
    :return:
    """
    access_token = kwargs['access_token']
    url, content_type = kwargs['url'], kwargs['content_type']
    post_data, is_jwt_request, request_method = kwargs['post_data'], kwargs.get('is_jwt_request', False), \
                                                kwargs.get('request_method', 'post')
    with app.app_context():
        logger = app.config[TalentConfigKeys.LOGGER]
        logger.info('Celery Task (send_request): kwargs passed: {}'.format(kwargs))
        headers = {
            'Content-Type': content_type,
            'Authorization': access_token
        }
        # If content_type is json then it should dump json data
        if content_type == 'application/json':
            post_data = json.dumps(post_data)

        # Send request to URL with job post data
        logger.info("Sending %s request to %s" % (request_method, url))
        response = http_request(method_type=request_method, url=url, data=post_data, headers=headers)

        try:
            logger.info(response.text)
            return response.text
        except Exception as e:
            # This exception will be caught by flower
            return {'message': e.message, 'status_code': response.status_code}
