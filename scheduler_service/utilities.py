from scheduler_service.common.models.scheduler import SchedulerTask

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


def get_smart_list_ids():
    # TODO: get smart list ids from cloud service maybe
    return [1]


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
