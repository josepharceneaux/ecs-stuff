"""
Scheduler - APScheduler initialization, set jobstore, threadpoolexecutor
- Add task to APScheduler
- run_job callback method, runs when times come
- remove multiple tasks from APScheduler
- get tasks from APScheduler and serialize tasks using JSON
"""

# Standard imports
import datetime

# Third-party imports
from dateutil.tz import tzutc
from pytz import timezone
from urllib import urlencode
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.events import EVENT_JOB_EXECUTED
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.schedulers.background import BackgroundScheduler

# Application imports
from scheduler_service.common.models.user import Token
from scheduler_service import logger, TalentConfigKeys, flask_app
from scheduler_service.apscheduler_config import executors, job_store, jobstores
from scheduler_service.common.models.user import User
from scheduler_service.common.error_handling import InvalidUsage
from scheduler_service.common.routes import AuthApiUrl
from scheduler_service.common.utils.handy_functions import http_request, to_utc_str
from scheduler_service.common.utils.scheduler_utils import SchedulerUtils
from scheduler_service.validators import get_valid_data_from_dict, get_valid_url_from_dict, \
    get_valid_datetime_from_dict, get_valid_integer_from_dict, get_valid_task_name_from_dict
from scheduler_service.custom_exceptions import TriggerTypeError, JobNotCreatedError
from scheduler_service.tasks import send_request


# Set timezone to UTC
scheduler = BackgroundScheduler(jobstore=jobstores, executors=executors,
                                timezone='UTC')
scheduler.add_jobstore(job_store)

# Set the minimum frequency in seconds
if flask_app.config.get(TalentConfigKeys.ENV_KEY) in ['dev', 'circle']:
    MIN_ALLOWED_FREQUENCY = 4
else:
    # For qa and production minimum frequency would be one hour
    MIN_ALLOWED_FREQUENCY = 3600


# Request timeout is 30 seconds.
REQUEST_TIMEOUT = 30


def apscheduler_listener(event):
    """
    APScheduler listener for logging on job crashed or job time expires
    The method also checks if a job time is passed. If yes, then it remove job from apscheduler because there is no
    use of expired job.
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
            # In case of periodic job, if next_run_time is greater than end_date. This mean job is expired and will
            # not run in future. So, just simply delete.
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
                logger.info("apscheduler_listener: Job with id %s removed successfully" % job.id)


scheduler.add_listener(apscheduler_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)


def validate_one_time_job(data):
    """
    Validate one time job POST data.
    if run_datetime is already passed then raise error 500
    :param data:
    :return:
    """
    valid_data = dict()
    run_datetime = get_valid_datetime_from_dict(data, 'run_datetime')
    valid_data.update({'run_datetime': run_datetime})

    current_datetime = datetime.datetime.utcnow()
    current_datetime = current_datetime.replace(tzinfo=timezone('UTC'))
    # If job is not in 0-30 seconds in past or greater than current datetime.
    if run_datetime < current_datetime:
        raise InvalidUsage("No need to schedule job of already passed time. run_datetime is in past")

    return valid_data


def validate_periodic_job(data):
    """
    Validate periodic job and check for missing or invalid data. if found then raise error
    :param data: JSON job post data
    :return:
    """
    valid_data = dict()
    frequency = get_valid_integer_from_dict(data, 'frequency')
    start_datetime = get_valid_datetime_from_dict(data, 'start_datetime')
    end_datetime = get_valid_datetime_from_dict(data, 'end_datetime')

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
    past_datetime = current_datetime - datetime.timedelta(seconds=REQUEST_TIMEOUT)
    future_datetime = end_datetime - datetime.timedelta(seconds=frequency)
    if not past_datetime < start_datetime < future_datetime:
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
    job_config['task_type'] = get_valid_data_from_dict(data, 'task_type')
    job_config['url'] = get_valid_url_from_dict(data, 'url')

    # Server to Server call. We check if a job with a certain 'task_name'
    # is already running as we only allow one such task to run at a time.
    # If there is already such task we raise an exception.
    if user_id is None:
        job_config['task_name'] = get_valid_task_name_from_dict(data, 'task_name')
        jobs = scheduler.get_jobs()
        jobs = filter(lambda task: task.name == job_config['task_name'], jobs)
        # There should be a unique task named job. If a job already exist then it should raise error
        if jobs and len(jobs) == 1:
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
            current_datetime = current_datetime.replace(tzinfo=tzutc())
            job_start_time = valid_data['start_datetime']

            # Due to request timeout delay, there will be a delay in scheduling job sometimes.
            # And if start time is passed due to this request delay, then job should be run
            if job_start_time < current_datetime:
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
        raise TriggerTypeError("Task type not correct. Please use either %s or %s as task type."
                               % (SchedulerUtils.ONE_TIME, SchedulerUtils.PERIODIC))


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
    # In case of global tasks there is no access_token and token expires in 600 seconds. So, a new token should be
    # created because frequency can be set to minimum of 1 hour.
    secret_key_id = None
    if not access_token:
        secret_key_id, access_token = User.generate_jw_token(user_id=user_id)
    else:
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        Token.session.commit()
        token = Token.get_token(access_token=access_token.split(' ')[1])
        # If token has expired we refresh it
        past_datetime = token.expires - datetime.timedelta(seconds=REQUEST_TIMEOUT)
        if token and past_datetime < datetime.datetime.utcnow():
            data = {
                'client_id': token.client_id,
                'client_secret': token.client.client_secret,
                'refresh_token': token.refresh_token,
                'grant_type': u'refresh_token'
            }
            # We need to refresh token if token is expired. For that send request to auth service and request a
            # refresh token.
            with flask_app.app_context():
                resp = http_request('POST', AuthApiUrl.TOKEN_CREATE, headers=headers,
                                    data=urlencode(data))
                logger.info('Token refreshed %s' % resp.json()['expires_at'])
                access_token = "Bearer " + resp.json()['access_token']

    logger.info('User ID: %s, URL: %s, Content-Type: %s' % (user_id, url, content_type))
    # Call celery task to send post_data to URL
    send_request.apply_async([access_token, secret_key_id, url, content_type, kwargs],
                             serializer='json',
                             queue=SchedulerUtils.QUEUE)


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
    jobs_aps = filter(lambda job: job and job.args[0] == user_id, jobs_aps)
    # Finally remove all such jobs
    removed = map(lambda job: (scheduler.remove_job(job.id), job.id), jobs_aps)
    return removed


def serialize_task(task):
    """
    Serialize task data to JSON object
    :param task: APScheduler task to convert to JSON dict
                 task.args: user_id, access_token, url, content_type
    :return: JSON converted dict object
    """
    task_dict = None
    # Interval Trigger is periodic task_type
    if isinstance(task.trigger, IntervalTrigger):
        task_dict = dict(
            id=task.id,
            url=task.args[2],
            start_datetime=to_utc_str(task.trigger.start_date),
            end_datetime=to_utc_str(task.trigger.end_date),
            next_run_datetime=str(task.next_run_time),
            frequency=int(task.trigger.interval_length),
            post_data=task.kwargs,
            pending=task.pending,
            task_type=SchedulerUtils.PERIODIC
        )

    # Date Trigger is a one_time task_type
    elif isinstance(task.trigger, DateTrigger):
        task_dict = dict(
            id=task.id,
            url=task.args[2],
            run_datetime=to_utc_str(task.trigger.run_date),
            post_data=task.kwargs,
            pending=task.pending,
            task_type=SchedulerUtils.ONE_TIME
        )

        if task_dict['run_datetime']:
            task_dict['run_datetime'] = task_dict['run_datetime'].strftime('%Y-%m-%dT%H:%M:%SZ')

    if task_dict and task.name and not task.args[0]:
        task_dict['task_name'] = task.name

    return task_dict
