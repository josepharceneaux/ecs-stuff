import os
from apscheduler.executors.pool import ThreadPoolExecutor
from celery import Celery
import jinja2
from scheduler_service.common.models.scheduler import SchedulerTask
from  scheduler_service import tasks
from scheduler_service.tasks import send_sms_campaign, methods, celery
from scheduler_service import init_app
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
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.jobstores.memory import MemoryJobStore

from apscheduler.schedulers.background import BackgroundScheduler
job_store = RedisJobStore()
jobstores = {
    'redis': job_store
}
executors = {
    'default': ThreadPoolExecutor(20)
}
scheduler = BackgroundScheduler(jobstore=jobstores, executors=executors)
# scheduler.add_jobstore(job_store, 'redisJobStore')
scheduler.add_jobstore(job_store)


def my_listener(event):
    if event.exception:
        print('The job crashed :(\n')
        print str(event.exception.message) + '\n'
    else:
        print('The job worked :)')
        if event.job.next_run_time > event.job.kwargs['end_date']:
            stop_job(event.job)


def stop_job(job):
    scheduler.unschedule_job(job)
    print 'job(id: %s) has stopped' % job.id

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

app = init_app()

# Enable CORS
CORS(app, resources={
    r'/*': {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})


@app.route('/index')
def index():
    return 'Welcome to SMS Campaign Service'


@app.route('/tasks/')
def tasks():
    scheduled_tasks = SchedulerTask.query.all()
    tasks = [task for task in scheduled_tasks]
    return render_template('tasks.html', tasks=tasks)


@app.route('/shutdown/')
def shutdown():
    print('scheduler is going to shutdown')
    try:
        scheduler.shutdown()
    except Exception as e:
        return str(e)
    return "Scheduler shutdown successfully"


@app.route('/start/')
def start():
    print('scheduler is going to restart')
    try:
        scheduler.start()
    except Exception as e:
        return str(e)
    return "Scheduler restarted successfully"


@app.route('/schedule/', methods=['GET', 'POST'])
def task():
    """
    This is a test end point which sends sms campaign
    :return:
    """
    start_date = datetime.now()
    start_date.replace(second=(start_date.second + 15) % 60)
    end_date = start_date + timedelta(minutes=2)
    repeat_time_in_sec = int(request.args.get('frequency', 10))
    func = request.args.get('func', 'send_sms_campaign')
    arg1 = request.args.get('arg1')
    arg2 = request.args.get('arg2')
    job = scheduler.add_job(callback_function,
                            'interval',
                            seconds=repeat_time_in_sec,
                            start_date=start_date,
                            end_date=end_date,
                            args=[arg1, arg2, end_date],
                            kwargs=dict(func=func, end_date=end_date))
    print 'Task has been added and will run at %s ' % start_date
    return 'Task has been added to queue!!!'
    # response = send_sms_campaign(ids, body_text)
    if response:
        return flask.jsonify(**response), response['status_code']
    else:
        raise InternalServerError


def callback_function(*args, **kwargs):
    print('args', args)
    if kwargs['func'] in methods:
        methods[kwargs['func']].apply_async(args, kwargs)
    else:
        send_sms_campaign.apply_async(args, kwargs)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
my_loader = jinja2.ChoiceLoader([
    app.jinja_loader,
    jinja2.FileSystemLoader(os.path.join(BASE_DIR, 'templates')),
])
app.jinja_loader = my_loader


@app.errorhandler(Exception)
def error_handler(e):
    return str(e)

if __name__ == '__main__':
    app.run(port=8009)
    jobs = scheduler.get_jobs()
    pass

