from celery import Celery
from flask import Flask
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.background import BackgroundScheduler as Scheduler
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.events import EVENT_JOB_EXECUTED

app = Flask('scheduler_service')
celery = Celery(app.import_name, broker='redis://localhost:6379', backend='redis://localhost:6379')

scheduler = Scheduler()
scheduler.add_jobstore(RedisJobStore(), 'shelve')
# scheduler.add_jobstore(SQLAlchemyJobStore(url='sqlite:///job_store_new.sqlite'), 'shelve')



def my_listener(event):
    if event.exception:
        print('The job crashed :(\n')
        print str(event.exception.message) + '\n'
    else:
        print('The job worked :)')
        print 'Event'
        print dir(event)
        print '----------'
        print dir(event.job)
        print 'End date', event.job.kwargs['end_date']
        if event.job.next_run_time > event.job.kwargs['end_date']:
            print 'Stopping job'
            # stop_job(event.job)
scheduler.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
scheduler.start()
app.aps_scheduler = scheduler

@celery.task(name='send_sms_campaign')
def send_sms_campaign(*args, **kwargs):
    print('Sending SMS campaign')
    # time.sleep(5)
    return 'SMS Campaign sent successfully'


@celery.task(name='send_email_campaign')
def send_email_campaign(*args, **kwargs):
    print('Sending Email campaign')
    # time.sleep(5)
    return 'Email Campaign sent successfully'
    #  # current_job = args[2]
    # status = True
    # for job in sched.get_jobs():
    #     if job.args[2] == end_date:
    #         if all([datetime.now().date() == end_date.date(),
    #                 datetime.now().hour == end_date.hour,
    #                 datetime.now().minute == end_date.minute]) \
    #                 or end_date < datetime.now():
    #             # job_status = 'Completed'
    #             stop_job(job)
    #             status = False
    #             # if status:
    #             # eval(func).delay(args[0], args[1])
    # if status:
    #     # job_status = 'Running'
    #     func_1(args[0], args[1])
    #     # add_or_update_job_in_db(current_job, status=job_status)


@celery.task(name='raise_exception')
def raise_exception(*args, **kwargs):
    print('raise_exception')
    # time.sleep(5)
    raise Exception('Intentional exception raised')

methods = {
    'send_sms_campaign': send_sms_campaign,
    'send_email_campaign': send_email_campaign,
    'raise_exception': raise_exception
}
