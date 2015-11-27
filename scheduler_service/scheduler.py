import pytz
from dateutil.parser import parse
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.events import EVENT_JOB_EXECUTED
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.redis import RedisJobStore

from apscheduler.schedulers.background import BackgroundScheduler
from scheduler_service.tasks import send_request

job_store = RedisJobStore()
jobstores = {
    'redis': job_store
}
executors = {
    'default': ThreadPoolExecutor(20)
}
scheduler = BackgroundScheduler(jobstore=jobstores, executors=executors)
scheduler.add_jobstore(job_store)


def my_listener(event):
    if event.exception:
        print('The job crashed :(\n')
        print str(event.exception.message) + '\n'
    else:
        print('The job worked :)')
        job = scheduler.get_job(event.job_id)
        if job.next_run_time > job.trigger.end_date:
            print 'Stopping job'
            try:
                scheduler.remove_job(job_id=job.id)
            except Exception as e:
                print(e)
            else:
                print("Job removed successfully")


scheduler.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)


def schedule_job(data, user_id):
    """
    This is a test end point which sends sms campaign
    :return:
    """
    start_date = data['start_date']
    end_date = data['end_date']
    frequency = data['frequency']
    post_data = data['post_data']
    url = data['url']
    timezone = data.get('timezone', 'Asia/Karachi')
    try:
        job = scheduler.add_job(run_job,
                                'interval',
                                seconds=frequency.get('seconds', 0),
                                minutes=frequency.get('minutes', 0),
                                hours=frequency.get('hours', 0),
                                days=frequency.get('days', 0),
                                weeks=frequency.get('weeks', 0),
                                start_date=start_date,
                                end_date=end_date,
                                timezone=timezone,
                                args=[user_id, url],
                                kwargs=post_data)
    except Exception as e:
        print e
        return e
    print 'Task has been added and will run at %s ' % start_date
    return job.id


def run_job(user_id, url, **kwargs):
    print('User ID: %s, Url: %s' % (user_id, url))
    send_request.apply_async([user_id, url, kwargs])


def remove_tasks(ids, user_id):
    jobs = scheduler.get_jobs()
    jobs = filter(lambda job: job.args[0] == user_id and job.id in ids, jobs)
    removed = map(lambda job: (scheduler.remove_job(job.id), job.id), jobs)
    return removed


def serialize_task(task):
    task_dict = dict(
        id=task.id,
        url=task.args[1],
        start_date=str(task.trigger.start_date),
        end_date=str(task.trigger.end_date),
        next_run_time=str(task.next_run_time),
        timezone=task.trigger.timezone.zone,
        frequency=dict(days=task.trigger.interval.days, seconds=task.trigger.interval.seconds),
        post_data=task.kwargs,
        pending=task.pending
    )
    return task_dict
