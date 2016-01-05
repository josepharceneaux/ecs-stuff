"""
Scheduler - APScheduler initialization, set jobstore, threadpoolexecutor
- Add task to APScheduler
- run_job callback method, runs when times come
- remove multiple tasks from APScheduler
- get tasks from APScheduler and serialize tasks using json
"""

# Standard imports
import datetime
import os

# Third-party imports
import requests
from pytz import timezone
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.events import EVENT_JOB_EXECUTED
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.schedulers.background import BackgroundScheduler
from urllib import urlencode

# Application imports
from scheduler_service.common.models.user import Token
from scheduler_service import logger
from scheduler_service.common.models.user import User
from scheduler_service.apscheduler_config import executors, job_store, jobstores
from scheduler_service.common.error_handling import InvalidUsage
from scheduler_service.common.routes import AuthApiUrl
from scheduler_service.common.utils.handy_functions import http_request
from scheduler_service.common.utils.scheduler_utils import SchedulerUtils
from scheduler_service.common.utils.validators import get_valid_data, get_valid_url, get_valid_datetime, \
    get_valid_integer
from scheduler_service.custom_exceptions import TriggerTypeError, JobNotCreatedError
from scheduler_service.tasks import send_request


# Set timezone to UTC
scheduler = BackgroundScheduler(jobstore=jobstores, executors=executors,
                                timezone='UTC')
scheduler.add_jobstore(job_store)

# Set the minimum frequency in seconds
if os.environ.get('GT_ENVIRONMENT') == 'dev' or os.environ.get('GT_ENVIRONMENT') == 'circle':
    MIN_ALLOWED_FREQUENCY = 4
else:
    # For qa and production minimum frequency would be one hour
    MIN_ALLOWED_FREQUENCY = 3600


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
        if job:
            logger.info('The job with id %s worked :)' % job.id)
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
    run_datetime = get_valid_datetime(data, 'run_datetime')
    valid_data.update({'run_datetime': run_datetime})

    current_datetime = datetime.datetime.utcnow()
    current_datetime = current_datetime.replace(tzinfo=timezone('UTC'))
    # If job is not in 0-30 seconds in past or greater than current datetime.
    if run_datetime < current_datetime:
        raise InvalidUsage("No need to schedule job of already passed time")

    return valid_data


def validate_periodic_job(data):
    """
    Validate periodic job and check for missing or invalid data. if found then raise error
    :param data:
    :return:
    """
    valid_data = dict()
    frequency = get_valid_integer(data, 'frequency')
    start_datetime = get_valid_datetime(data, 'start_datetime')
    end_datetime = get_valid_datetime(data, 'end_datetime')

    valid_data.update({'start_datetime': start_datetime})
    valid_data.update({'end_datetime': end_datetime})

    # If value of frequency is not integer or lesser than 1 hour then throw exception
    if int(frequency) < MIN_ALLOWED_FREQUENCY:
        raise InvalidUsage(error_message='Invalid value of frequency. Value should '
                                         'be greater than or equal to %s' % MIN_ALLOWED_FREQUENCY)

    frequency = int(frequency)
    valid_data.update({'frequency': frequency})

    current_datetime = datetime.datetime.utcnow()
    current_datetime = current_datetime.replace(tzinfo=timezone('UTC'))

    # If job is not in 0-30 seconds in past or greater than current datetime.
    if not ((current_datetime - datetime.timedelta(seconds=30)) < start_datetime <
                (end_datetime - datetime.timedelta(seconds=frequency))):
        raise InvalidUsage("start_datetime and end_datetime should be in future.")

    return valid_data


def schedule_job(data, user_id=None, access_token=None):
    """
    Schedule job using POST data and add it to APScheduler. Which calls the callback method when job time comes
    :param data: the data like url, frequency, post_data, start_datetime and end_datetime of job which is required
    for creating job of APScheduler
    :param user_id: the user_id of user who is creating job
    :param access_token: CSRF access token for the sending post request to url with post_data
    :return:
    """
    job_config = dict()
    job_config['post_data'] = data.get('post_data', dict())
    content_type = data.get('content_type', 'application/json')
    # TODO; am unsure if following comment belongs to above line or lines below
    # will return None if key not found. We also need to check for valid values not just keys
    # in dict because a value can be '' and it can be valid or invalid
    job_config['task_type'] = get_valid_data(data, 'task_type')
    job_config['url'] = get_valid_url(data, 'url')

    # Server to Server call. We check if a job with a certain 'task_name'
    # is already running as we only allow one such task to run at a time.
    # If there is already such task we raise an exception.
    if user_id is None:
        job_config['task_name'] = get_valid_data(data, 'task_name')
        jobs = scheduler.get_jobs()
        jobs = filter(lambda task: task.name == job_config['task_name'], jobs)
        if jobs:
            raise InvalidUsage('Task name %s is already scheduled' % jobs[0].name)
    else:
        job_config['task_name'] = None

    trigger = str(job_config['task_type']).lower().strip()

    if trigger == SchedulerUtils.PERIODIC:
        valid_data = validate_periodic_job(data)

        try:
            job = scheduler.add_job(run_job,
                                    name=job_config['task_name'],
                                    trigger='interval',
                                    seconds=valid_data['frequency'],
                                    start_date=valid_data['start_datetime'],
                                    end_date=valid_data['end_datetime'],
                                    args=[user_id, access_token, job_config['url'], content_type],
                                    kwargs=job_config['post_data'])

            current_datetime = datetime.datetime.utcnow()
            current_datetime = current_datetime.replace(tzinfo=timezone('UTC'))

            # TODO; need to understand this more
            # If job is in past but in range of 0-30 seconds interval then run the job
            if (current_datetime - datetime.timedelta(seconds=30)) < valid_data['start_datetime']:
                run_job(user_id, access_token, job_config['url'], content_type)
            logger.info('schedule_job: Task has been added and will start at %s ' % valid_data['start_datetime'])
        except Exception:
            raise JobNotCreatedError("Unable to create the job.")
        return job.id
    elif trigger == SchedulerUtils.ONE_TIME:
        valid_data = validate_one_time_job(data)
        try:
            job = scheduler.add_job(run_job,
                                    name=job_config['task_name'],
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
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    secret_key = None
    # TODO; comment why are we doing this
    if not access_token:
        secret_key, access_token = User.generate_auth_token(user_id=user_id)
    elif 'bearer' in access_token.lower():
        token = Token.get_token(access_token=access_token)
        # If token has expired we refresh it
        if token and (token.expires - datetime.timedelta(seconds=30)) < datetime.datetime.utcnow():
            data = {
                'client_id': token.client_id,
                'client_secret': token.client.client_secret,
                'refresh_token': token.refresh_token,
                'grant_type': u'refresh_token'
            }
            # TODO; need to use Basit's code that takes care of the errors
            resp = http_request('POST', AuthApiUrl.AUTH_SERVICE_TOKEN_CREATE_URI, headers=headers,
                                 data=urlencode(data))
            access_token = "Bearer " + resp.json()['access_token']

    logger.info('User ID: %s, URL: %s, Content-Type: %s' % (user_id, url, content_type))
    # Call celery task to send post_data to URL
    send_request.apply_async([access_token, secret_key, url, content_type, kwargs])


def remove_tasks(ids, user_id):
    """
    Remove jobs from APScheduler redisStore
    :param ids: ids of tasks which are in APScheduler
    :param user_id: tasks owned by user
    :return: tasks which are removed
    """
    # Get all jobs from APScheduler
    jobs_aps = map(lambda job_id: scheduler.get_job(job_id=job_id), ids)
    # Now only keep those that belong to the user
    jobs_aps = filter(lambda job: job is not None and job.args[0] == user_id, jobs_aps)
    # Finally remove all such jobs
    removed = map(lambda job: (scheduler.remove_job(job.id), job.id), jobs_aps)
    return removed


def serialize_task(task):
    """
    Serialize task data to JSON object
    :param task: APScheduler task to convert to json dict
                 task.args: user_id, access_token, url, content_type
    :return: json converted dict object
    """
    task_dict = None
    # TODO; comment what task, kwargs, task.arg[0] and task.arg[2] contains
    # TODO; comment the significance of IntervalTrigger and DateTrigger
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
            task_dict['start_datetime'] = task_dict['start_datetime'].strftime('%Y-%m-%dT%H:%M:%SZ')

        if task_dict['end_datetime'] is not None:
            task_dict['end_datetime'] = task_dict['end_datetime'].strftime('%Y-%m-%dT%H:%M:%SZ')

        if task_dict['next_run_datetime'] is not None:
            task_dict['next_run_datetime'] = task_dict['next_run_datetime'].strftime('%Y-%m-%dT%H:%M:%SZ')

        if task.name is not None and task.args[0] is None:
            task_dict['task_name'] = task.name

    elif isinstance(task.trigger, DateTrigger):
        task_dict = dict(
            id=task.id,
            url=task.args[2],
            run_datetime=task.trigger.run_date,
            post_data=task.kwargs,
            pending=task.pending,
            task_type='one_time'
        )

        # TODO; Following is a bug
        if task_dict['run_datetime'] is None:
            task_dict['run_datetime'] = task_dict['run_datetime'].strftime('%Y-%m-%dT%H:%M:%SZ')

        # TODO; We can take out the following line out of if/else as it's common
        if task.name is not None and task.args[0] is None:
            task_dict['task_name'] = task.name

    return task_dict
