from celery import Celery
from flask import Flask
import time

app = Flask('scheduler_service')
celery = Celery(app.import_name, broker='redis://localhost:6379', backend='redis://localhost:6379')


# @celery.task(name='send_sms_campaign')
def send_sms_campaign(*args, **kwargs):
    print('Sending SMS campaign')
    # time.sleep(5)
    return 'SMS Campaign sent successfully'


# @celery.task(name='send_email_campaign')
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





# @celery.task(name='raise_exception')
def raise_exception(*args, **kwargs):
    print('raise_exception')
    # time.sleep(5)
    raise Exception('Intentional exception raised')

methods = {
    'send_sms_campaign': send_sms_campaign,
    'send_email_campaign': send_email_campaign,
    'raise_exception': raise_exception
}
