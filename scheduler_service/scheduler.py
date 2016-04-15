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
from urllib import urlencode
from dateutil.tz import tzutc
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.events import EVENT_JOB_EXECUTED
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from jsonschema import validate, FormatChecker, ValidationError
from apscheduler.schedulers.background import BackgroundScheduler

# Application imports
from scheduler_service.common.models import db
from scheduler_service.common.models.user import Token
from scheduler_service import logger, TalentConfigKeys, flask_app
from scheduler_service.apscheduler_config import executors, job_store, jobstores, job_defaults
from scheduler_service.common.models.user import User
from scheduler_service.common.error_handling import InvalidUsage
from scheduler_service.common.routes import AuthApiUrl
from scheduler_service.common.utils.datetime_utils import DatetimeUtils
from scheduler_service.common.utils.handy_functions import http_request
from scheduler_service.common.utils.scheduler_utils import SchedulerUtils
from scheduler_service.common.utils.test_utils import get_user
from scheduler_service.modules.json_schema import base_job_schema, one_time_task_job_schema
from scheduler_service.modules.json_schema import periodic_task_job_schema
from scheduler_service.validators import get_valid_data_from_dict, get_valid_url_from_dict, \
    get_valid_datetime_from_dict, get_valid_integer_from_dict, get_valid_task_name_from_dict
from scheduler_service.custom_exceptions import TriggerTypeError, JobNotCreatedError, TaskAlreadyScheduledError
from scheduler_service.tasks import send_request

# Set timezone to UTC
scheduler = BackgroundScheduler(jobstore=jobstores, executors=executors,
                                timezone='UTC')
scheduler.configure(job_defaults=job_defaults)
scheduler.add_jobstore(job_store)

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
            if isinstance(job.trigger,
                          IntervalTrigger) and job.next_run_time and job.next_run_time > job.trigger.end_date:
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
    run_datetime_obj = DatetimeUtils(get_valid_datetime_from_dict(data, 'run_datetime'))
    valid_data.update({'run_datetime': run_datetime_obj.value})

    # If job is not in 0-30 seconds in past or greater than current datetime.
    if not run_datetime_obj.is_in_future(neg_offset=REQUEST_TIMEOUT):
        raise InvalidUsage("Cannot schedule job of already passed time. run_datetime is in past")
    return valid_data


def validate_periodic_job(data):
    """
    Validate periodic job and check for missing or invalid data. If found then raise error
    :param data: JSON job post data
    """
    valid_data = dict()

    frequency = get_valid_integer_from_dict(data, 'frequency')
    start_datetime_obj = DatetimeUtils(get_valid_datetime_from_dict(data, 'start_datetime'))
    end_datetime = get_valid_datetime_from_dict(data, 'end_datetime')

    # If value of frequency is not integer or lesser than 1 hour then throw exception
    if frequency < SchedulerUtils.MIN_ALLOWED_FREQUENCY:
        raise InvalidUsage('Invalid value of frequency. Value should be greater than or equal to '
                           '%s' % SchedulerUtils.MIN_ALLOWED_FREQUENCY)
    valid_data.update({'frequency': frequency})

    # If job is not in 0-30 seconds in past or greater than current datetime.
    relative_end_datetime = end_datetime - datetime.timedelta(seconds=frequency)
    if not start_datetime_obj.is_in_future(neg_offset=REQUEST_TIMEOUT):
        raise InvalidUsage("start_datetime and end_datetime should be in future.")
    elif start_datetime_obj.value > relative_end_datetime:
        raise InvalidUsage("start_datetime should be less than (end_datetime - frequency)")

    valid_data.update({'start_datetime': start_datetime_obj.value})
    valid_data.update({'end_datetime': end_datetime})

    return valid_data


def run_job(user_id, access_token, url, content_type, post_data, is_jwt_request=False):
    """
    Function callback to run when job time comes, this method is called by APScheduler
    :param user_id:
    :param access_token: Bearer token for Authorization when sending request to url
    :param url: url to send post request
    :param content_type: format of post data
    :param post_data: post data like campaign name, smartlist ids etc
    :param is_jwt_request: (optional) if true, then use X-Talent-Secret-Id in header
    :return:
    """
    # In case of global tasks there is no access_token and token expires in 600 seconds. So, a new token should be
    # created because frequency is set to minimum (1 hour).
    secret_key_id = None
    if not user_id:
        secret_key_id, access_token = User.generate_jw_token()
    # If is_jwt_request parameter is false then send an auth service token request
    elif not is_jwt_request:
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        db.db.session.commit()
        if flask_app.config[TalentConfigKeys.ENV_KEY] in ['dev', 'jenkins']:
            user = User.get_by_id(user_id)

            # If user is deleted, then delete all its jobs too
            if not user:
                tasks = filter(lambda task: task.args[0] == user_id, scheduler.get_jobs())
                [scheduler.remove_job(job_id=task.id) for task in tasks]
                return

        token = Token.get_token(access_token=access_token.split(' ')[1])
        # If token has expired we refresh it
        if token and (token.expires - datetime.timedelta(seconds=REQUEST_TIMEOUT)) < datetime.datetime.utcnow():
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

    # If is_jwt_request parameter is true then send jwt token request
    elif is_jwt_request:
        secret_key_id, access_token = User.generate_jw_token(user_id=user_id)

    logger.info('Queueing data send. User ID: %s, URL: %s, Content-Type: %s', user_id, url, content_type)
    # Call celery task to send post_data to URL
    send_request.apply_async([access_token, secret_key_id, url, content_type, post_data, is_jwt_request],
                             serializer='json',
                             queue=SchedulerUtils.QUEUE,
                             routing_key=SchedulerUtils.CELERY_ROUTING_KEY)


def schedule_job(data, user_id=None, access_token=None):
    """
    Schedule job using POST data and add it to APScheduler. Which calls the callback method when job time comes
    :param data: the data like url, frequency, post_data, start_datetime and end_datetime of job which is required
    for creating job of APScheduler
    :param user_id: the user_id of user who is creating job
    :param access_token: CSRF access token for the sending post request to url with post_data
    :return:
    """
    # Validate json data
    try:
        validate(instance=data, schema=base_job_schema,
                 format_checker=FormatChecker())
        if data.get('task_type') == SchedulerUtils.PERIODIC:
            validate(instance=data, schema=periodic_task_job_schema,
                     format_checker=FormatChecker())
        elif data.get('task_type') == SchedulerUtils.ONE_TIME:
            validate(instance=data, schema=one_time_task_job_schema,
                     format_checker=FormatChecker())
    except ValidationError as e:
        raise InvalidUsage(error_message="Schema validation error: %s" % e.message)

    job_config = dict()
    job_config['post_data'] = data.get('post_data', dict())
    content_type = data.get('content-type', 'application/json')

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
            raise TaskAlreadyScheduledError('Task name %s is already scheduled' % jobs[0].name)
    else:
        job_config['task_name'] = None
        is_jwt_request = data.get('is_jwt_request')
        if is_jwt_request and (str(is_jwt_request).lower() not in ['true', 'false']):
            raise InvalidUsage('is_jwt_request(Optional) value is invalid. It should be either True or False')
        job_config['is_jwt_request'] = is_jwt_request if is_jwt_request and str(is_jwt_request).lower() == 'true' else None

    trigger = str(job_config['task_type']).lower().strip()

    if trigger == SchedulerUtils.PERIODIC:
        valid_data = validate_periodic_job(data)

        try:
            job = scheduler.add_job('scheduler:run_job',
                                    name=job_config['task_name'],
                                    trigger='interval',
                                    seconds=valid_data['frequency'],
                                    start_date=valid_data['start_datetime'],
                                    end_date=valid_data['end_datetime'],
                                    misfire_grace_time=SchedulerUtils.MAX_MISFIRE_TIME,
                                    args=[user_id, access_token, job_config['url'], content_type,
                                          job_config['post_data'], job_config.get('is_jwt_request')]
                                    )
            # Due to request timeout delay, there will be a delay in scheduling job sometimes.
            # And if start time is passed due to this request delay, then job should be run
            job_start_time_obj = DatetimeUtils(valid_data['start_datetime'])
            if not job_start_time_obj.is_in_future():
                run_job(user_id, access_token, job_config['url'], content_type, job_config['post_data'], job_config.get('is_jwt_request'))
            logger.info('schedule_job: Task has been added and will start at %s ' % valid_data['start_datetime'])
        except Exception:
            raise JobNotCreatedError("Unable to create the job.")
        return job.id
    elif trigger == SchedulerUtils.ONE_TIME:
        valid_data = validate_one_time_job(data)
        try:
            job = scheduler.add_job('scheduler:run_job',
                                    name=job_config['task_name'],
                                    trigger='date',
                                    run_date=valid_data['run_datetime'],
                                    misfire_grace_time=SchedulerUtils.MAX_MISFIRE_TIME,
                                    args=[user_id, access_token, job_config['url'], content_type,
                                          job_config['post_data'], job_config.get('is_jwt_request')]
                                    );
            logger.info('schedule_job: Task has been added and will run at %s ' % valid_data['run_datetime'])
            return job.id
        except Exception:
            raise JobNotCreatedError("Unable to create job. Invalid data given")
    else:
        raise TriggerTypeError("Task type not correct. Please use either %s or %s as task type."
                               % (SchedulerUtils.ONE_TIME, SchedulerUtils.PERIODIC))


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


def serialize_task(task, is_admin_api=False):
    """
    Serialize task data to JSON object
    :param task: APScheduler task to convert to JSON dict
                 task.args: user_id, access_token, url, content_type, post_data, is_jwt_request
    :param is_admin_api: In case of admin we want to assert user_email and
    :return: JSON converted dict object
    """
    task_dict = None
    # Interval Trigger is periodic task_type
    if isinstance(task.trigger, IntervalTrigger):
        task_dict = dict(
                id=task.id,
                url=task.args[2],
                start_datetime=task.trigger.start_date,
                end_datetime=task.trigger.end_date,
                next_run_datetime=task.next_run_time,
                frequency=dict(seconds=task.trigger.interval_length),
                post_data=task.args[4],
                is_jwt_request=task.args[5],
                pending=task.pending,
                task_type=SchedulerUtils.PERIODIC
        )
        if task_dict['start_datetime']:
            task_dict['start_datetime'] = DatetimeUtils.to_utc_str(task_dict['start_datetime'])

        if task_dict['end_datetime']:
            task_dict['end_datetime'] = DatetimeUtils.to_utc_str(task_dict['end_datetime'])

        if task_dict['next_run_datetime']:
            task_dict['next_run_datetime'] = DatetimeUtils.to_utc_str(task_dict['next_run_datetime'])

    # Date Trigger is a one_time task_type
    elif isinstance(task.trigger, DateTrigger):
        task_dict = dict(
                id=task.id,
                url=task.args[2],
                run_datetime=task.trigger.run_date,
                post_data=task.args[4],
                is_jwt_request=task.args[5],
                pending=task.pending,
                task_type=SchedulerUtils.ONE_TIME
        )

        if task_dict['run_datetime']:
            task_dict['run_datetime'] = DatetimeUtils.to_utc_str(task_dict['run_datetime'])

    if task_dict and task.name and not task.args[0]:
        task_dict['task_name'] = task.name

    # For scheduler admin API
    if is_admin_api and task_dict:
        if task.args[0]:
            task_dict['user_id'] = task.args[0]
            task_dict['user_email'] = User.get_by_id(task.args[0]).email

    return task_dict
