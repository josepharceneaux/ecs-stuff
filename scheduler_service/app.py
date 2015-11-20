from celery import Celery
from scheduler_service.tasks import app, celery, send_campaign
from scheduler_service.utilities import get_all_tasks

__author__ = 'zohaib'

"""
    This module contains flask app startup.
    We register blueprints for different APIs with this app.
    Error handlers are added at the end of file.
"""
# Standard  Library imports
import json
import time
import traceback
from datetime import datetime, timedelta

# Initializing App. This line should come before any imports from models


# Run Celery from terminal as
# celery -A scheduler_service.app.app.celery worker

# start the scheduler
# from sms_campaign_service.gt_scheduler import GTScheduler
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.events import EVENT_JOB_EXECUTED
from apscheduler.jobstores.redis_store import RedisJobStore

from apscheduler.scheduler import Scheduler
scheduler = Scheduler()
scheduler.add_jobstore(RedisJobStore(), 'redisJobStore')


def my_listener(event):
    if event.exception:
        print('The job crashed :(\n')
        print str(event.exception.message) + '\n'
    else:
        print('The job worked :)')


scheduler.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
scheduler.start()


# Third party imports
import flask
from flask import request, Flask
from flask import render_template
from flask.ext.cors import CORS
from flask.ext.restful import Api
from werkzeug.utils import redirect

# Application specific imports
# from utilities import get_all_tasks
# from utilities import http_request
# from scheduler_service.utilities import get_smart_list_ids



# Enable CORS
CORS(app, resources={
    r'/*': {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})

@app.route('/')
def hello_world():
    return 'Welcome to SMS Campaign Service'


@app.route('/tasks')
def tasks():
    data = get_all_tasks()
    return render_template('tasks.html', tasks=data)


@app.route('/schedule/', methods=['GET', 'POST'])
def sms():
    """
    This is a test end point which sends sms campaign
    :return:
    """
    # if request.args.has_key('text'):
    #     body_text = request.args['text']
    #     body_text = process_link_in_body_text(body_text)
    # else:
    #     body_text = 'Welcome to getTalent'
    # ids = get_smart_list_ids()
    # start_min = request.args.get('start')
    # end_min = request.args.get('end')
    start_date = datetime.now()
    start_date.replace(minute=(start_date.minute + 1))
    end_date = start_date + timedelta(minutes=5)
    repeat_time_in_sec = int(request.args.get('frequency', 10))
    func = request.args.get('func')
    arg1 = request.args.get('arg1')
    arg2 = request.args.get('arg2')
    # for x in range (1,50):
    # send_campaign()
    # return 'Jon ran'
    job = scheduler.add_interval_job(callback,
                                 seconds=repeat_time_in_sec,
                                 start_date=start_date,
                                 args=[func, [arg1, arg2], end_date],
                                 jobstore='redisJobStore')
    print 'Task has been added and will run at %s ' % start_date
    return 'Task has been added to queue!!!'
    # response = send_sms_campaign(ids, body_text)
    if response:
        return flask.jsonify(**response), response['status_code']
    else:
        raise InternalServerError


def callback(*args, **kwargs):
    print('asas')
    send_campaign.apply_async()


@app.errorhandler(Exception)
def error_handler(e):
    return str(e)

if __name__ == '__main__':
    app.run(port=8009)

