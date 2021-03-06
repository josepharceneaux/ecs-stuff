"""
Scheduler - APScheduler initialization, set jobstore, threadpoolexecutor
- Add task to APScheduler
- run_job callback method, runs when times come
- remove multiple tasks from APScheduler
- get tasks from APScheduler and serialize tasks using JSON
"""

# Standard imports
import datetime
import uuid

# Third-party imports
from urllib import urlencode
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_MISSED, \
    EVENT_JOB_BEFORE_REMOVE
from apscheduler.events import EVENT_JOB_EXECUTED
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from jsonschema import validate, FormatChecker, ValidationError
from apscheduler.schedulers.background import BackgroundScheduler

# Application imports
from scheduler_service.common.models import db
from scheduler_service.common.models.user import Token
from scheduler_service import logger, TalentConfigKeys, flask_app, redis_store
from scheduler_service.apscheduler_config import executors, job_store, jobstores, job_defaults, LOCK_KEY
from scheduler_service.common.models.user import User
from scheduler_service.common.error_handling import InvalidUsage
from scheduler_service.common.routes import AuthApiUrl
from scheduler_service.common.talent_config_manager import TalentEnvs
from scheduler_service.common.utils.datetime_utils import DatetimeUtils
from scheduler_service.common.utils.handy_functions import http_request
from scheduler_service.common.utils.scheduler_utils import SchedulerUtils
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


def scheduler_remove_job(job_id):
    """
    Removes the job from redis as well as apscheduler
    :param job_id: job_id returned by scheduler when job was scheduled e.g. w4523kd1sdf23kljfdjflsdf
    :type job_id: str
    """
    scheduler.remove_job(job_id=job_id)


def apscheduler_listener(event):
    """
    APScheduler listener for logging on job crashed or job time expires
    The method also checks if a job time is passed. If yes, then it remove job from apscheduler because there is no
    use of expired job.
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
                    scheduler_remove_job(job_id=job.id)
                    logger.info("apscheduler_listener: Job with id %s removed successfully"
                                % job.id)
                except Exception as e:
                    logger.exception("apscheduler_listener: Error occurred while removing job")
                    raise e
            elif isinstance(job.trigger, DateTrigger) and not job.run_date:
                scheduler_remove_job(job_id=job.id)
                logger.info("apscheduler_listener: Job with id %s removed successfully."
                            % job.id)


def apscheduler_job_added(event):
    """
    Event callback handler of apscheduler which calls this method when a job is added or removed.
    """
    if event.code == EVENT_JOB_ADDED:
        # If its user type job then add a prefix user_ continued by user_id, if its general job then add a general
        # prefix continued by name of job
        task = scheduler.get_job(job_id=event.job_id)
        redis_store.rpush(SchedulerUtils.REDIS_SCHEDULER_USER_TASK % task.args[0]
                          if task.args[0] else SchedulerUtils.REDIS_SCHEDULER_GENERAL_TASK % task.name,
                          event.job_id)

    if event.code == EVENT_JOB_BEFORE_REMOVE:
        # Get the job and remove it from redis table then from scheduler
        task = scheduler.get_job(job_id=event.job_id)
        if task:
            redis_store.lrem(SchedulerUtils.REDIS_SCHEDULER_USER_TASK % task.args[0]
                             if task.args[0] else SchedulerUtils.REDIS_SCHEDULER_GENERAL_TASK % task.name,
                             event.job_id)


# Register event listener methods to apscheduler
scheduler.add_listener(apscheduler_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED)
scheduler.add_listener(apscheduler_job_added, EVENT_JOB_ADDED | EVENT_JOB_BEFORE_REMOVE)


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


def run_job(user_id, access_token, url, content_type, post_data, is_jwt_request=False, request_method="post", **kwargs):
    """
    Function callback to run when job time comes, this method is called by APScheduler
    :param user_id:
    :param access_token: Bearer token for Authorization when sending request to url
    :param url: url to send post request
    :param content_type: format of post data
    :param post_data: post data like campaign name, smartlist ids etc
    :param is_jwt_request: (optional) if true, then use X-Talent-Secret-Id in header
    :param kwargs: lock_uuid string
    """

    """
    Problem:
        On jenkins, staging and prod, uwsgi initializes multiple Flask app instances(5 different processes) and
    along with each Flask instance, APScheduler instance is initialized. The problem occurs when all 5 APScheduler
    instances that are watching a job, executes that one job in parallel.

    Solution:
        One solution can be to run APScheduler in a single separate process and using RPC, Flask apps can communicate
    with APScheduler process to create/get/execute/delete job(s). But that requires alot of changes in existing
    service code.

        Other solution can be to restrict scheduler callback method (run_job) to be called by one instance only.
    To do this, when multiple instances call this method we can lock this method for next few seconds. So, first calling
    APScheduler instance will set the lock and other 4 instances check that the function already has lock. So, they
    will ignore job execution and simply return.

    Legend:
    ---->     time

    Scenario:

                0(ms)           20(ms)              30(ms)
    Instance 1: --------->                                                            Ignored
    Instance 2: ----------------->                                                    Ignored
    Instance 3: ----->                                                                Acquires Lock
    Instance 4: ------------->                                                        Ignored
    Instance 5: ----------------------->                                              Ignored

    """
    lock_uuid = kwargs.get('lock_uuid')
    if lock_uuid:
        if not redis_store.get(LOCK_KEY + lock_uuid):
            res = redis_store.set(LOCK_KEY + lock_uuid, True, nx=True, ex=4)
            # Multiple executions. No need to execute job if race condition occurs
            if not res:
                logger.info('CODE-VERONICA: Race Escaping {}'.format(lock_uuid))
                return
            logger.info('CODE-VERONICA: Worked {}'.format(lock_uuid))
        else:
            # Multiple executions. No need to execute job
            logger.info('CODE-VERONICA: Escaping {}'.format(lock_uuid))
            return

    # In case of global tasks there is no access_token and token expires in 600 seconds. So, a new token should be
    # created because frequency is set to minimum (1 hour).
    if not user_id:
        access_token = User.generate_jw_token()
    # If is_jwt_request parameter is false then send an auth service token request
    elif not is_jwt_request:
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        db.db.session.commit()
        if flask_app.config[TalentConfigKeys.ENV_KEY] in [TalentEnvs.DEV, TalentEnvs.JENKINS]:
            user = User.get_by_id(user_id)

            # If user is deleted, then delete all its jobs too
            if not user:
                tasks = filter(lambda task: task.args[0] == user_id, scheduler.get_jobs())
                [scheduler_remove_job(job_id=task.id) for task in tasks]
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
        access_token = User.generate_jw_token(user_id=user_id)

    logger.info('Queueing data send. User ID: %s, URL: %s, Content-Type: %s', user_id, url, content_type)
    # Call celery task to send post_data to URL
    send_request.apply_async(kwargs={'access_token': access_token,
                                     'url': url, 'content_type': content_type,
                                     'post_data': post_data, 'is_jwt_request': is_jwt_request,
                                     'request_method': request_method },
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
        job_config['is_jwt_request'] = True
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
    request_method = data.get('request_method', 'post')

    callback_method = 'scheduler_service.modules.scheduler:run_job'

    # make a UUID based on the host ID and current time and pass it to add job method to fix race condition.
    # See run_job method above
    lock_uuid = str(uuid.uuid1()) + str(uuid.uuid4())

    if trigger == SchedulerUtils.PERIODIC:
        valid_data = validate_periodic_job(data)

        try:
            job = scheduler.add_job(callback_method,
                                    name=job_config['task_name'],
                                    trigger='interval',
                                    seconds=valid_data['frequency'],
                                    start_date=valid_data['start_datetime'],
                                    end_date=valid_data['end_datetime'],
                                    misfire_grace_time=SchedulerUtils.MAX_MISFIRE_TIME,
                                    args=[user_id, access_token, job_config['url'], content_type,
                                          job_config['post_data'], job_config.get('is_jwt_request'), request_method],
                                    kwargs=dict(lock_uuid=lock_uuid)
                                    )
            # Due to request timeout delay, there will be a delay in scheduling job sometimes.
            # And if start time is passed due to this request delay, then job should be run
            job_start_time_obj = DatetimeUtils(valid_data['start_datetime'])
            if not job_start_time_obj.is_in_future():
                run_job(user_id, access_token, job_config['url'], content_type, job_config['post_data'], job_config.get('is_jwt_request'),
                        kwargs=dict(lock_uuid=lock_uuid))
            logger.info('schedule_job: Task has been added and will start at %s ' % valid_data['start_datetime'])
        except Exception as e:
            logger.error(e.message)
            raise JobNotCreatedError("Unable to create the job.")
        logger.info('CODE-VERONICA: job id: {} schedule {}'.format(job.id, lock_uuid))
        return job.id
    elif trigger == SchedulerUtils.ONE_TIME:
        valid_data = validate_one_time_job(data)
        try:
            job = scheduler.add_job(callback_method,
                                    name=job_config['task_name'],
                                    trigger='date',
                                    coalesce=True,
                                    run_date=valid_data['run_datetime'],
                                    misfire_grace_time=SchedulerUtils.MAX_MISFIRE_TIME,
                                    args=[user_id, access_token, job_config['url'], content_type,
                                          job_config['post_data'], job_config.get('is_jwt_request'),
                                          request_method],
                                    kwargs=dict(lock_uuid=lock_uuid)
                                    )
            logger.info('schedule_job: Task has been added and will run at %s ' % valid_data['run_datetime'])
            logger.info('CODE-VERONICA: job id: {} schedule {}'.format(job.id, lock_uuid))
            return job.id
        except Exception as e:
            logger.error(e.message)
            raise JobNotCreatedError("Unable to create job. Invalid data given")
    else:
        raise TriggerTypeError("Task type not correct. Please use either %s or %s as task type."
                               % (SchedulerUtils.ONE_TIME, SchedulerUtils.PERIODIC))


def remove_tasks(ids, user_id):
    """
    Remove jobs from APScheduler and redis
    :param ids: ids of tasks which are in APScheduler
    :param user_id: tasks owned by user
    :return: tasks which are removed
    """
    # Get all jobs from APScheduler
    # Now only keep those jobs that belong to the user
    valid_jobs = [scheduler.get_job(job_id=job_id) for job_id in ids]
    valid_job_ids = [job.id for job in valid_jobs if job and job.args[0] == user_id]
    # Finally remove all such jobs
    removed = [(scheduler_remove_job(job_id=job_id), job_id) for job_id in valid_job_ids]
    return removed


def serialize_task(task):
    """
    Serialize task data to JSON object
    :param task: APScheduler task to convert to JSON dict
                 task.args: user_id, access_token, url, content_type, post_data, is_jwt_request, request_type
    :return: JSON converted dict object
    """
    task_dict = None
    # Interval Trigger is periodic task_type
    if isinstance(task.trigger, IntervalTrigger):
        task_dict = dict(
                id=task.id,
                url=task.args[2],
                request_method=task.args[6] if len(task.args) >= 7 else "post",
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
                request_method=task.args[6] if len(task.args) >= 7 else "post",
                post_data=task.args[4],
                is_jwt_request=task.args[5],
                pending=task.pending,
                task_type=SchedulerUtils.ONE_TIME
        )

        if task_dict['run_datetime']:
            task_dict['run_datetime'] = DatetimeUtils.to_utc_str(task_dict['run_datetime'])

    if task_dict and task.name and not task.args[0]:
        task_dict['task_name'] = task.name

    return task_dict


def serialize_task_admin(task):
    """
    Serialize task data to JSON object (for admin)
    :param task: APScheduler task
    :type task: object
    :return: JSON converted dict object
    :rtype: dict
    """
    task_dict = serialize_task(task)

    # Create a new field `data` and add all request info in it
    task_dict['data'] = dict(URL=task_dict.get('url'),
                             RequestMethod=task_dict.get('request_method'),
                             post_data=task_dict.get('post_data'))

    # Delete redundant fields
    for entry in ['post_data', 'url', 'request_method']:
        del task_dict[entry]

    # task.args[0] -> user_id
    if task.args[0]:
        task_dict['user_id'] = task.args[0]
        task_dict['task_category'] = SchedulerUtils.CATEGORY_USER
        user = User.get_by_id(task.args[0])
        if not user:
            logger.error("serialize_task: user with id %s doesn't exist." % task.args[0])
            task_dict['user_email'] = 'user_id: %s, User deleted' % task.args[0]
        else:
            task_dict['user_email'] = user.email
    else:
        task_dict['task_category'] = SchedulerUtils.CATEGORY_GENERAL

    return task_dict


def get_user_job_ids(user_id):
    """
    Return job_ids of a specific user
    :param user_id:
    :type user_id: int
    :return:
    :rtype: list
    """
    start_index = 0
    end_index = -1
    job_ids = redis_store.lrange(SchedulerUtils.REDIS_SCHEDULER_USER_TASK % user_id, start_index,
                                 end_index)
    return job_ids


def get_general_job_id(task_name):
    """
    Returns id of scheduled general task
    :param task_name: general task name which is scheduled
    :type task_name: str
    :return:str|None
    """
    start_index = 0
    end_index = -1
    job_id = redis_store.lrange(SchedulerUtils.REDIS_SCHEDULER_GENERAL_TASK % task_name, start_index, end_index)
    return job_id[0] if job_id else None


def get_all_general_job_ids():
    """
    Return id of scheduled general task:
    """
    general_task_keys = redis_store.keys(SchedulerUtils.REDIS_SCHEDULER_GENERAL_TASK % '*')
    general_task_ids = [next(iter(redis_store.lrange(key, 0, -1)), None) for key in general_task_keys]
    return general_task_ids
