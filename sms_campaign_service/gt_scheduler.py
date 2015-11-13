from common.models.scheduler import SchedulerTask

__author__ = 'basit'

# Standard Library
import sys
import time
from datetime import datetime, timedelta

# Third party imports
from apscheduler.job import MaxInstancesReachedError, Job
from apscheduler.scheduler import Scheduler, logger
from apscheduler.events import JobEvent, EVENT_JOB_MISSED, EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

COMPLETED = 'Completed'
QUEUED = 'Queued'
RUNNING = 'Running'
EXPIRED = 'Expired'


class GTScheduler(Scheduler):
    """
        This overrides necessary methods to save/update job and their status in gt-database.
    """
    def unschedule_job(self, job):
        """
        Removes a job, preventing it from being run any more.
        """
        self._jobstores_lock.acquire()
        iteritems = lambda d: d.items()
        try:
            for alias, jobstore in iteritems(self._jobstores):
                if job in list(jobstore.jobs):
                    add_or_update_job_in_db(job, status=COMPLETED)
                    self._remove_job(job, alias, jobstore)
                    return
        finally:
            self._jobstores_lock.release()

        raise KeyError('Job "%s" is not scheduled in any job store' % job)

    def _run_job(self, job, run_times):
        """
        Acts as a harness that runs the actual job code in a thread.
        """
        for run_time in run_times:
            # See if the job missed its run time window, and handle possible
            # misfires accordingly
            difference = datetime.now() - run_time
            grace_time = timedelta(seconds=job.misfire_grace_time)
            if difference > grace_time:
                # Notify listeners about a missed run
                event = JobEvent(EVENT_JOB_MISSED, job, run_time)
                self._notify_listeners(event)
                logger.warning('Run time of job "%s" was missed by %s',
                               job, difference)
            else:
                try:
                    job.add_instance()
                except MaxInstancesReachedError:
                    event = JobEvent(EVENT_JOB_MISSED, job, run_time)
                    self._notify_listeners(event)
                    logger.warning('Execution of job "%s" skipped: '
                                   'maximum number of running instances '
                                   'reached (%d)', job, job.max_instances)
                    break

                logger.info('Running job "%s" (scheduled at %s)', job,
                            run_time)
                add_or_update_job_in_db(job)
                try:
                    retval = job.func(*job.args, **job.kwargs)
                except:
                    # Notify listeners about the exception
                    exc, tb = sys.exc_info()[1:]
                    event = JobEvent(EVENT_JOB_ERROR, job, run_time,
                                     exception=exc, traceback=tb)
                    self._notify_listeners(event)

                    logger.exception('Job "%s" raised an exception', job)
                else:
                    # Notify listeners about successful execution
                    event = JobEvent(EVENT_JOB_EXECUTED, job, run_time,
                                     retval=retval)
                    self._notify_listeners(event)

                    logger.info('Job "%s" executed successfully', job)

                job.remove_instance()

                # If coalescing is enabled, don't attempt any further runs
                if job.coalesce:
                    break

    def add_job(self, trigger, func, args, kwargs, jobstore='default',
                **options):
        """
        Adds the given job to the job list and notifies the scheduler thread.
        Any extra keyword arguments are passed along to the constructor of the
        :class:`~apscheduler.job.Job` class (see :ref:`job_options`).

        :param trigger: trigger that determines when ``func`` is called
        :param func: callable to run at the given time
        :param args: list of positional arguments to call func with
        :param kwargs: dict of keyword arguments to call func with
        :param jobstore: alias of the job store to store the job in
        :rtype: :class:`~apscheduler.job.Job`
        """
        job = Job(trigger, func, args or [], kwargs or {},
                  options.pop('misfire_grace_time', self.misfire_grace_time),
                  options.pop('coalesce', self.coalesce), **options)
        if not self.running:
            self._pending_jobs.append((job, jobstore))
            logger.info('Adding job tentatively -- it will be properly '
                        'scheduled when the scheduler starts')
        else:
            self._real_add_job(job, jobstore, True)
            time.sleep(1)
            add_or_update_job_in_db(job)

        return job


def add_or_update_job_in_db(job, status=None):
    record_in_db = SchedulerTask.get_by_job_id(job.id)
    data = {'job_id': job.id,
            'next_run_time': job.next_run_time,
            'end_time': job.args[2],
            'status': status if status else status_decider(job)}
    if record_in_db:
        if record_in_db.status != 'Expired':
            record_in_db.update(**data)
    else:
        new_record = SchedulerTask(**data)
        SchedulerTask.save(new_record)


def status_decider(job):
    job_end_time = job.args[2]
    if job_end_time < job.next_run_time:
        return EXPIRED
    elif job.next_run_time == datetime.now():
        return RUNNING
    else:
        return QUEUED
    # elif job_end_time > datetime.now():
    #     return 'Queued'
    # else:
    #     return 'Completed'
