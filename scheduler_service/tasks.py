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
def send_request(access_token, secret_key_id, url, content_type, post_data, is_jwt_request=False, request_method='post'):
    """
    This method will be called by run_job asynchronously
    :param access_token: authorization token for user
    :param url: the URL where to send post request
    :param content_type: the content type i.e json or xml
    :param secret_key_id: Redis key which have a corresponding secret value to decrypt data
    :param post_data: Data to post with post request
    :param is_jwt_request: If true, then request will be send using JWT authorization
    :param request_method: The type of request i.e POST, DELETE, GET, UPDATE, PATCH
    :param kwargs: post data i.e campaign name, smartlist ids
    :return:
    """
    with app.app_context():
        logger = app.config[TalentConfigKeys.LOGGER]
        headers = {
            'Content-Type': content_type,
            'Authorization': access_token
        }
        # If content_type is json then it should dump json data
        if content_type == 'application/json':
            post_data = json.dumps(post_data)
        if secret_key_id:
            headers.update({'X-Talent-Secret-Key-ID': secret_key_id})
            # If user doesn't want to send jwt request, then delete 'X-Talent-Secret-Key-ID' key to avoid jwt auth
            if not is_jwt_request:
                del headers['X-Talent-Secret-Key-ID']

        # Send request to URL with job post data
        logger.info("Sending post request to %s" % url)
        response = http_request(method_type=request_method, url=url, data=post_data, headers=headers)

        try:
            logger.info(response.text)
            return response.text
        except Exception as e:
            # This exception will be caught by flower
            return {'message': e.message, 'status_code': response.status_code}
