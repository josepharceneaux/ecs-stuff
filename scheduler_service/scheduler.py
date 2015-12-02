import pytz
from dateutil.parser import parse
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.events import EVENT_JOB_EXECUTED
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.redis import RedisJobStore

from apscheduler.schedulers.background import BackgroundScheduler
from scheduler_service import logger
from scheduler_service.tasks import send_request

job_store = RedisJobStore()
jobstores = {
    'redis': job_store
}
executors = {
    'default': ThreadPoolExecutor(20)
}
# set timezone to UTC
scheduler = BackgroundScheduler(jobstore=jobstores, executors=executors,
                                timezone='UTC')
scheduler.add_jobstore(job_store)


def apscheduler_listener(event):
    """
    apschudler listener for logging on job crashed or job time expires
    :param event:
    :return:
    """
    if event.exception:
        logger.error('The job crashed :(\n')
        logger.exception(str(event.exception.message) + '\n')
    else:
        logger.info('The job worked :)')
        job = scheduler.get_job(event.job_id)
        if job.next_run_time > job.trigger.end_date:
            logger.info('Stopping job')
            try:
                scheduler.remove_job(job_id=job.id)
            except Exception as e:
                logger.exception(e.message)
                raise e
            else:
                logger.info("Job removed successfully")


scheduler.add_listener(apscheduler_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)


def schedule_job(data, user_id, access_token):
    """
    schedule job using post data and add it to apscheduler
    :return:
    """
    start_datetime = data['start_datetime']
    end_datetime = data['end_datetime']
    frequency = data['frequency']
    post_data = data['post_data']
    content_type = data.get('content_type', 'application/json')
    url = data['url']
    try:
        job = scheduler.add_job(run_job,
                                'interval',
                                seconds=frequency.get('seconds', 0),
                                minutes=frequency.get('minutes', 0),
                                hours=frequency.get('hours', 0),
                                days=frequency.get('days', 0),
                                weeks=frequency.get('weeks', 0),
                                start_date=start_datetime,
                                end_date=end_datetime,
                                args=[user_id, access_token, url, content_type],
                                kwargs=post_data)
    except Exception as e:
        logger.exception(e.message)
        raise e
    logger.info('Task has been added and will run at %s ' % start_datetime)
    return job.id


def run_job(user_id, access_token, url, content_type, **kwargs):
    """
    function callback to run when job time comes
    :param user_id:
    :param url: url to send post request
    :param content_type: format of post data
    :param kwargs: post data like campaign name, smartlist ids etc
    :return:
    """
    logger.info('User ID: %s, Url: %s, Content-Type: %s' % (user_id, url, content_type))
    send_request.apply_async([user_id, access_token, url, content_type, kwargs])


def remove_tasks(ids, user_id):
    """
    remove jobs from apscheduler redisStore
    :param ids: ids of tasks which are in apscheduler
    :param user_id: tasks owned by user
    :return: tasks which are removed
    """
    jobs_aps = scheduler.get_jobs()
    jobs_av = filter(lambda job_id: scheduler.get_job(job_id=job_id) in jobs_aps, ids)
    jobs_ = map(lambda job_id: scheduler.get_job(job_id=job_id), jobs_av)
    jobs = filter(lambda job: job.args[0] == user_id, jobs_)

    removed = map(lambda job: (scheduler.remove_job(job.id), job.id), jobs)
    return removed


def serialize_task(task):
    """
    serialize task data to json object
    :param task:
    :return: json converted dict object
    """
    task_dict = dict(
        id=task.id,
        url=task.args[1],
        start_datetime=str(task.trigger.start_date),
        end_datetime=str(task.trigger.end_date),
        next_run_time=str(task.next_run_time),
        frequency=dict(days=task.trigger.interval.days, seconds=task.trigger.interval.seconds),
        post_data=task.kwargs,
        pending=task.pending
    )
    return task_dict
