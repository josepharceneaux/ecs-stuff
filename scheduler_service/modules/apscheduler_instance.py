import os

from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from werkzeug.local import Local

from scheduler_service import logger, redis_store, SchedulerUtils
from scheduler_service.apscheduler_config import executors, job_store, jobstores, job_defaults
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_MISSED, \
    EVENT_JOB_BEFORE_REMOVE
from apscheduler.events import EVENT_JOB_EXECUTED
from apscheduler.schedulers.background import BackgroundScheduler

local = Local()


class APSchedulerInstance:
    """
    APScheduler class to return scheduler instance
    """
    def __init__(self):
        # Set timezone to UTC
        scheduler = BackgroundScheduler(jobstore=jobstores, executors=executors,
                                        timezone='UTC')
        scheduler.configure(job_defaults=job_defaults)
        scheduler.add_jobstore(job_store)

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
                            scheduler.remove_job(job_id=job.id)
                            logger.info("apscheduler_listener: Job with id %s removed successfully"
                                        % job.id)
                        except Exception as e:
                            logger.exception("apscheduler_listener: Error occurred while removing job")
                            raise e
                    elif isinstance(job.trigger, DateTrigger) and not job.run_date:
                        scheduler.remove_job(job_id=job.id)
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
        local.scheduler_instance = scheduler


def get_scheduler():
    """

    :return:
    """
    if not os.environ.get('ISAPP'):
        return None
    try:
        local.scheduler_instance
        print 'CODE-VERONICA: RUN'
    except:
        APSchedulerInstance()
    return local.scheduler_instance
