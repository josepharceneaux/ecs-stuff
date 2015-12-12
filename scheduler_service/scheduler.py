"""
Scheduler - APScheduler initialization, set jobstore, threadpoolexecutor
- Add task to APScheduler
- run_job callback method, runs when times come # TODO: modify this
- remove multiple tasks from APScheduler
- get tasks from APScheduler and serialize tasks using json
"""

# Third-party imports
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.events import EVENT_JOB_EXECUTED
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.schedulers.background import BackgroundScheduler

# Application imports
from scheduler_service import logger
from scheduler_service.apscheduler_config import executors
from scheduler_service.custom_exceptions import FieldRequiredError, TriggerTypeError, JobNotCreatedError
from scheduler_service.tasks import send_request

job_store = RedisJobStore()
jobstores = {
    'redis': job_store
}
# Set timezone to UTC
scheduler = BackgroundScheduler(jobstore=jobstores, executors=executors,
                                timezone='UTC')
scheduler.add_jobstore(job_store)


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
        logger.info('The job worked :)')
        job = scheduler.get_job(event.job_id)
        if job.next_run_time is not None and job.next_run_time > job.trigger.end_date:
            logger.info('Stopping job')
            try:
                scheduler.remove_job(job_id=job.id)
                logger.info("APScheduler_listener: Job removed successfully")
            except Exception as e:
                logger.exception("apscheduler_listener: Error occured while removing job")
                raise e


scheduler.add_listener(apscheduler_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)


def schedule_job(data, user_id, access_token):
    """
    Schedule job using post data and add it to APScheduler
    # TODO: parameters doc strings are missing and it is most important method
    :return:
    """
    job_config = dict()
    # TODO: default value should be a dict not a string
    job_config['post_data'] = data.get('post_data', '{}')
    content_type = data.get('content_type', 'application/json')
    # TODO: -1 is not a good choice , and if it is, we should define meaningful constants
    # TODO: and if just want to check for missing inputs, None is sufficient data.get('task_type')
    # will return None if key not found. We also need to check for valid values not just keys
    # in dict because a value can be '' and it can be valid or invalid
    job_config['trigger'] = data.get('task_type', -1)
    job_config['url'] = data.get('url', -1)
    job_config['frequency'] = data.get('frequency', -1)

    # Get missing keys
    missing_keys = filter(lambda _key: job_config[_key] == -1, job_config.keys())
    if len(missing_keys) > 0:
        logger.exception("schedule_job: Missing keys %s" % ', '.join(missing_keys))
        raise FieldRequiredError(error_message="Missing keys %s" % ', '.join(missing_keys))

    trigger = job_config['trigger'].lower().strip()

    if trigger == 'periodic':
        try:
            frequency = data['frequency']
            start_datetime = data['start_datetime']
            end_datetime = data['end_datetime']

            # Possible frequency dictionary keys
            temp_time_list = ['seconds', 'minutes', 'hours', 'days', 'weeks']

            # Check if keys in frequency are valid time period otherwise throw exception
            for key in frequency.keys():
                if key not in temp_time_list:
                    # TODO: exception name is not what it does. IMHO it should be `InvalidInput`
                    raise FieldRequiredError(error_message='Invalid key %s in frequency' % key)

            # If value of frequency keys are not integer then throw exception
            for value in frequency.values():
                if value <= 0:
                    raise FieldRequiredError(error_message='Invalid value %s in frequency' % value)

        except Exception:
            logger.exception('schedule_job: Error while scheduling a job')
            raise FieldRequiredError(error_message="Missing or invalid data.")
        try:
            job = scheduler.add_job(run_job,
                                    trigger='interval',
                                    seconds=frequency.get('seconds', 0),
                                    minutes=frequency.get('minutes', 0),
                                    hours=frequency.get('hours', 0),
                                    days=frequency.get('days', 0),
                                    weeks=frequency.get('weeks', 0),
                                    start_date=start_datetime,
                                    end_date=end_datetime,
                                    args=[user_id, access_token, job_config['url'], content_type],
                                    kwargs=job_config['post_data'])
            logger.info('schedule_job: Task has been added and will run at %s ' % start_datetime)
        except Exception:
            raise JobNotCreatedError("Unable to create the job.")
        return job.id
    elif trigger == 'one_time':
        try:
            run_datetime = data['run_datetime']
            job = scheduler.add_job(run_job,
                                    trigger='date',
                                    run_date=run_datetime,
                                    args=[access_token, job_config['url'], content_type],
                                    kwargs=job_config['post_data'])
            logger.info('schedule_job: Task has been added and will run at %s ' % run_datetime)
            return job.id
        except KeyError:
            logger.exception("schedule_job: couldn't find 'run_datetime'")
            raise FieldRequiredError(error_message="Missing or invalid data. Field 'run_datetime' is missing")
    else:
        logger.error("schedule_job: Task type not correct. Please use periodic or one_time as task type.")
        raise TriggerTypeError("Task type not correct. Please use periodic or one_time as task type.")


def run_job(user_id, access_token, url, content_type, **kwargs):
    """
    # TODO: comment is not correct because this method `run_job` will run when user will send a POST request
    Function callback to run when job time comes
    :param user_id:
    :param url: url to send post request
    :param content_type: format of post data
    :param kwargs: post data like campaign name, smartlist ids etc
    :return:
    """
    logger.info('User ID: %s, URL: %s, Content-Type: %s' % (user_id, url, content_type))
    send_request.apply_async([user_id, access_token, url, content_type, kwargs])


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
    :param task:
    :return: json converted dict object
    """
    task_dict = None
    if isinstance(task.trigger, IntervalTrigger):
        task_dict = dict(
            id=task.id,
            url=task.args[1],
            start_datetime=str(task.trigger.start_date),
            end_datetime=str(task.trigger.end_date),
            next_run_datetime=str(task.next_run_time),
            frequency=dict(days=task.trigger.interval.days, seconds=task.trigger.interval.seconds),
            post_data=task.kwargs,
            pending=task.pending,
            task_type='periodic'
        )
    elif isinstance(task.trigger, DateTrigger):
        task_dict = dict(
            id=task.id,
            url=task.args[1],
            run_datetime=str(task.trigger.run_date),
            post_data=task.kwargs,
            pending=task.pending,
            task_type='one_time'
        )
    return task_dict
