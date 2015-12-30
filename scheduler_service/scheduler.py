"""
Scheduler - APScheduler initialization, set jobstore, threadpoolexecutor
- Add task to APScheduler
- run_job callback method, runs when times come
- remove multiple tasks from APScheduler
- get tasks from APScheduler and serialize tasks using json
"""

import re

# Third-party imports
import datetime
from pytz import timezone
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.events import EVENT_JOB_EXECUTED
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.schedulers.background import BackgroundScheduler
from dateutil.parser import parse

# Application imports
from scheduler_service import logger
from scheduler_service.apscheduler_config import executors, job_store, jobstores
from scheduler_service.common.error_handling import InvalidUsage
from scheduler_service.custom_exceptions import FieldRequiredError, TriggerTypeError, JobNotCreatedError, \
    JobTimeExpiredError, InvalidJobTimeError
from scheduler_service.tasks import send_request


# Set timezone to UTC
scheduler = BackgroundScheduler(jobstore=jobstores, executors=executors,
                                timezone='UTC')
scheduler.add_jobstore(job_store)


def get_valid_data(data, key, object_type=None):
    """
    Check if key exist and returns associated value
    :param data:
    :param key:
    :return: value of associated key
    """
    try:
        value = data[key]
    except KeyError:
        raise FieldRequiredError(error_message="Missing key: %s" % key)
    if object_type == 'datetime':
        try:
            value = parse(value).replace(tzinfo=timezone('UTC'))
        except Exception:
            raise InvalidUsage(
                error_message="Invalid value of %s %s. %s should be datetime format" % (key, value, key))
    elif object_type == 'int':
        if not str(value).isdigit():
            raise InvalidUsage(error_message='Invalid value of %s. It should be integer' % key)
    return value


def is_valid_url(url):
    """
    Reference: https://github.com/django/django-old/blob/1.3.X/django/core/validators.py#L42
    """
    regex = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url is not None and regex.search(url)


def apscheduler_listener(event):
    """
    APScheduler listener for logging on job crashed or job time expires
    :param event:
    :return:
    """
    if event.exception:
        logger.error('The job crashed :(\n')
        logger.error(str(event.exception.message) + '\n')
    else:
        job = scheduler.get_job(event.job_id)
        logger.info('The job with id %s worked :)' % job.id)
        if job:
            if isinstance(job.trigger, IntervalTrigger) and job.next_run_time and job.next_run_time > job.trigger.end_date:
                logger.info('Stopping job')
                try:
                    scheduler.remove_job(job_id=job.id)
                    logger.info("apscheduler_listener: Job with id %s removed successfully" % job.id)
                except Exception as e:
                    logger.exception("apscheduler_listener: Error occurred while removing job")
                    raise e
            elif isinstance(job.trigger, DateTrigger) and not job.run_date:
                scheduler.remove_job(job_id=job.id)
                logger.info("apscheduler_listener: Job with %s removed successfully" % job.id)


scheduler.add_listener(apscheduler_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)


def validate_one_time_job(data):
    """
    Validate one time job post data.
    if run_datetime is already passed then raise error 500
    :param data:
    :return:
    """
    valid_data = dict()
    run_datetime = get_valid_data(data, 'run_datetime', 'datetime')
    valid_data.update({'run_datetime': run_datetime})

    current_datetime = datetime.datetime.utcnow()
    current_datetime = current_datetime.replace(tzinfo=timezone('UTC'))
    if run_datetime < current_datetime:
        raise JobTimeExpiredError("No need to schedule job of already passed time")

    return valid_data


def validate_periodic_job(data):
    """
    Validate periodic job and check for missing or invalid data. if found then raise error
    :param data:
    :return:
    """
    valid_data = dict()
    frequency = get_valid_data(data, 'frequency', 'int')
    start_datetime = get_valid_data(data, 'start_datetime', 'datetime')
    end_datetime = get_valid_data(data, 'end_datetime', 'datetime')

    valid_data.update({'start_datetime': start_datetime})
    valid_data.update({'end_datetime': end_datetime})

    # If value of frequency is not integer or lesser than 1 hour then throw exception
    if int(frequency) < 3600:
        raise InvalidUsage(error_message='Invalid value of frequency. Value should '
                                         'be greater than or equal to 3600')

    frequency = int(frequency)
    valid_data.update({'frequency': frequency})

    current_datetime = datetime.datetime.utcnow()
    current_datetime = current_datetime.replace(tzinfo=timezone('UTC'))

    if start_datetime > end_datetime:
        raise InvalidJobTimeError("Start datetime should be lesser than end datetime.")

    if current_datetime > end_datetime:
        raise JobTimeExpiredError("Current datetime is greater than end_datetime. No need to schedule expired job")

    if current_datetime > start_datetime:
        raise JobTimeExpiredError("Current datetime is greater than start_datetime. Start datetime should be in future")

    return valid_data


def schedule_job(data, user_id=None, access_token=None):
    """
    Schedule job using post data and add it to APScheduler. Which calls the callback method when job time comes
    :param data: the data like url, frequency, post_data, start_datetime and end_datetime of job which is required
    for creating job of APScheduler
    :param user_id: the user_id of user who is creating job
    :param access_token: CSRF access token for the sending post request to url with post_data
    :return:
    """
    job_config = dict()
    job_config['post_data'] = data.get('post_data', dict())
    content_type = data.get('content_type', 'application/json')
    # will return None if key not found. We also need to check for valid values not just keys
    # in dict because a value can be '' and it can be valid or invalid
    job_config['task_type'] = data.get('task_type')
    job_config['url'] = data.get('url')

    # Get missing keys
    missing_keys = filter(lambda _key: job_config[_key] is None, job_config.keys())
    if len(missing_keys) > 0:
        raise FieldRequiredError(error_message="Missing keys: %s" % ', '.join(missing_keys))

    if not is_valid_url(job_config['url']):
        raise InvalidUsage("URL is not valid")

    trigger = str(job_config['task_type']).lower().strip()

    if trigger == 'periodic':
        valid_data = validate_periodic_job(data)

        try:
            job = scheduler.add_job(run_job,
                                    trigger='interval',
                                    seconds=valid_data['frequency'],
                                    start_date=valid_data['start_datetime'],
                                    end_date=valid_data['end_datetime'],
                                    args=[user_id, access_token, job_config['url'], content_type],
                                    kwargs=job_config['post_data'])
            logger.info('schedule_job: Task has been added and will start at %s ' % valid_data['start_datetime'])
        except Exception:
            raise JobNotCreatedError("Unable to create the job.")
        return job.id
    elif trigger == 'one_time':
        valid_data = validate_one_time_job(data)
        try:
            job = scheduler.add_job(run_job,
                                    trigger='date',
                                    run_date=valid_data['run_datetime'],
                                    args=[user_id, access_token, job_config['url'], content_type],
                                    kwargs=job_config['post_data'])
            logger.info('schedule_job: Task has been added and will run at %s ' % valid_data['run_datetime'])
            return job.id
        except Exception:
            raise JobNotCreatedError("Unable to create job. Invalid data given")
    else:
        raise TriggerTypeError("Task type not correct. Please use either 'periodic' or 'one_time' as task type.")


def run_job(user_id, access_token, url, content_type, **kwargs):
    """
    Function callback to run when job time comes, this method is called by APScheduler
    :param user_id:
    :param access_token: Bearer token for Authorization when sending request to url
    :param url: url to send post request
    :param content_type: format of post data
    :param kwargs: post data like campaign name, smartlist ids etc
    :return:
    """
    logger.info('User ID: %s, URL: %s, Content-Type: %s' % (user_id, url, content_type))
    # Call celery task to send post_data to url
    send_request.apply_async([access_token, url, content_type, kwargs])


def remove_tasks(ids, user_id):
    """
    Remove jobs from APScheduler redisStore
    :param ids: ids of tasks which are in APScheduler
    :param user_id: tasks owned by user
    :return: tasks which are removed
    """
    jobs_aps = map(lambda job_id: scheduler.get_job(job_id=job_id), ids)
    jobs_aps = filter(lambda job: job is not None and job.args[0] == user_id, jobs_aps)

    removed = map(lambda job: (scheduler.remove_job(job.id), job.id), jobs_aps)
    return removed


def serialize_task(task):
    """
    Serialize task data to json object
    :param task: APScheduler task to convert to json dict
    :return: json converted dict object
    """
    task_dict = None
    if isinstance(task.trigger, IntervalTrigger):
        task_dict = dict(
            id=task.id,
            url=task.args[2],
            start_datetime=task.trigger.start_date,
            end_datetime=task.trigger.end_date,
            next_run_datetime=task.next_run_time,
            frequency=dict(seconds=task.trigger.interval_length),
            post_data=task.kwargs,
            pending=task.pending,
            task_type='periodic'
        )
        if task_dict['start_datetime'] is not None:
            task_dict['start_datetime'] = task_dict['start_datetime'].strftime('%Y-%m-%d %H:%M:%S')

        if task_dict['end_datetime'] is not None:
            task_dict['end_datetime'] = task_dict['end_datetime'].strftime('%Y-%m-%d %H:%M:%S')

        if task_dict['next_run_datetime'] is not None:
            task_dict['next_run_datetime'] = task_dict['next_run_datetime'].strftime('%Y-%m-%d %H:%M:%S')

        task_dict['start_datetime'] = str(task_dict['start_datetime'])
        task_dict['end_datetime'] = str(task_dict['end_datetime'])
        task_dict['next_run_datetime'] = str(task_dict['next_run_datetime'])

    elif isinstance(task.trigger, DateTrigger):
        task_dict = dict(
            id=task.id,
            url=task.args[2],
            run_datetime=task.trigger.run_date,
            post_data=task.kwargs,
            pending=task.pending,
            task_type='one_time'
        )
        if task_dict['run_datetime'] is None:
            task_dict['run_datetime'] = task_dict['run_datetime'].strftime('%Y-%m-%d %H:%M:%S')

        task_dict['run_datetime'] = str(task_dict['run_datetime'])
    return task_dict
