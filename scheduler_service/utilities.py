__author__ = 'basit'

# Standard Library
import re
import json
from datetime import datetime

# Third Party Imports
import twilio
import twilio.rest
from twilio.rest import TwilioRestClient

# Application Specific
from social_network_service.utilities import http_request
from scheduler_service.app import celery
from scheduler_service.app import scheduler


def get_smart_list_ids():
    # TODO: get smart list ids from cloud service maybe
    return [1]


# def run_func(arg1, arg2, end_date):
#     if datetime.now().hour == end_date.hour \
#             and datetime.now().minute == end_date.minute:
#         stop_job(scheduler.get_jobs()[0])
#     else:
#         send_sms_campaign.delay(arg1, arg2)


# @celery.task()
def run_func_1(func, args, end_date):
    # current_job = args[2]
    status = True
    for job in scheduler.get_jobs():
        if job.args[2] == end_date:
            if all([datetime.now().date() == end_date.date(),
                    datetime.now().hour == end_date.hour,
                    datetime.now().minute == end_date.minute]) \
                    or end_date < datetime.now():
                # job_status = 'Completed'
                stop_job(job)
                status = False
                # if status:
                # eval(func).delay(args[0], args[1])
    if status:
        # job_status = 'Running'
        func_1(args[0], args[1])
        # add_or_update_job_in_db(current_job, status=job_status)


def stop_job(job):
    scheduler.unschedule_job(job)
    print 'job(id: %s) has stopped' % job.id


def get_all_tasks():
    tasks = SchedulerTask.query.all()
    return [task.to_json() for task in tasks]


# @celery.task()
# /sms_camp_service/scheduled_camp_process/
def func_1(a, b):
    print a, '\n', b


# @celery.task()
def func_2(a, b):
    print 'func_2'
