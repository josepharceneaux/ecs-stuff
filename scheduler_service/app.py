from apscheduler.executors.pool import ThreadPoolExecutor
from celery import Celery
from scheduler_service.common.models.scheduler import SchedulerTask
from  scheduler_service import tasks
from scheduler_service.tasks import app, send_sms_campaign, methods

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




# Third party imports
import flask
from flask import request, Flask
from flask import render_template



@app.route('/index')
def index():
    return 'Welcome to SMS Campaign Service'


@app.route('/tasks/')
def tasks():
    tasks = SchedulerTask.query.all()
    tasks = [task.to_json() for task in tasks]
    return render_template('tasks.html', tasks=tasks)

@app.route('/jobs/', methods=['GET'])
def get_jobs():

    jobs = app.aps_scheduler.get_jobs(jobstore='shelve')
    print 'Jobs'
    print jobs
    if jobs:
        print dir(jobs[0])
    data = []
    for job in jobs:
        job_data = {}
        job_data['job_id'] = job.id
        job_data['job_name'] = job.name
        # job_data['next_run_time'] = job.next_run_time
        data.append(job_data)
    return json.dumps(data)

@app.route('/shutdown/')
def shutdown():
    print('scheduler is going to shutdown')
    try:
        app.aps_scheduler.shutdown()
    except Exception as e:
        return str(e)
    return "Scheduler shutdown successfully"


@app.route('/start/')
def start():
    print('scheduler is going to restart')
    try:
        app.aps_scheduler.start()
    except Exception as e:
        return str(e)
    return "Scheduler restarted successfully"


@app.route('/stop/job/', methods=['GET'])
def stop_job():
    job_id = request.args.get('job_id')
    app.aps_scheduler.remove_job(job_id, 'shelve')
    print 'It seems job is stopped'
    return "It seems job is stopped"

@app.route('/pause/job/', methods=['GET'])
def pause_job():
    job_id = request.args.get('job_id')
    app.aps_scheduler.pause_job(job_id, 'shelve')
    print 'It seems job is paused'
    return "It seems job is paused"

@app.route('/resume/job/', methods=['GET'])
def resume_job():
    job_id = request.args.get('job_id')
    app.aps_scheduler.resume_job(job_id, 'shelve')
    print 'It seems job is resumed'
    return "It seems job is resumed"

@app.route('/schedule/', methods=['GET', 'POST'])
def task():
    """
    This is a test end point which sends sms campaign
    :return:
    """
    start_date = datetime.now()
    start_date.replace(minute=(start_date.minute + 1))
    end_date = start_date + timedelta(minutes=5)
    repeat_time_in_sec = int(request.args.get('frequency', 20))
    func = request.args.get('func', 'send_sms_campaign')
    arg1 = request.args.get('arg1')
    arg2 = request.args.get('arg2')
    job = app.aps_scheduler.add_job(callback, 'interval', jobstore='shelve', kwargs={'func': func}, minutes=1,
                            start_date=start_date.strftime("%Y-%m-%d %H:%M:%S"), end_date=end_date.strftime("%Y-%m-%d %H:%M:%S"))
                            # misfire_grace_time=10)
    # job = scheduler.add_interval_job(callback,
    #                                  seconds=repeat_time_in_sec,
    #                                  start_date=start_date,
    #                                  args=[arg1, arg2, end_date],
    #                                  kwargs=dict(func=func, end_date=end_date),
    #                                  misfire_grace_time=60,
    #                                  jobstore='shelve')

    print 'Task has been added and will run at %s ' % start_date
    return 'Task has been added to queue!!!'
    # response = send_sms_campaign(ids, body_text)
    if response:
        return flask.jsonify(**response), response['status_code']
    else:
        raise InternalServerError

@app.route('/schedulenew/', methods=['GET', 'POST'])
def tasknew():
    """
    This is a test end point which sends sms campaign
    :return:
    """
    start_date = datetime.now()
    start_date.replace(minute=(start_date.minute + 1))
    end_date = start_date + timedelta(minutes=5)
    repeat_time_in_sec = int(request.args.get('frequency', 20))
    func = request.args.get('func', 'send_sms_campaign')
    arg1 = request.args.get('arg1')
    arg2 = request.args.get('arg2')
    job = app.aps_scheduler.add_job(callback, 'interval', jobstore='shelve', kwargs={'func': func}, minutes=2, misfire_grace_time=60)
    # job = scheduler.add_interval_job(callback,
    #                                  seconds=repeat_time_in_sec,
    #                                  start_date=start_date,
    #                                  args=[arg1, arg2, end_date],
    #                                  kwargs=dict(func=func, end_date=end_date),
    #                                  misfire_grace_time=60,
    #                                  jobstore='shelve')

    print 'Task has been added and will run at %s ' % start_date
    return 'Task has been added to queue!!!'
    # response = send_sms_campaign(ids, body_text)
    if response:
        return flask.jsonify(**response), response['status_code']
    else:
        raise InternalServerError

def callback(*args, **kwargs):
    print('args', args)
    if kwargs['func'] in methods:
        methods[kwargs['func']].apply_async(args, kwargs)
    else:
        send_sms_campaign.apply_async(args, kwargs)


@app.errorhandler(Exception)
def error_handler(e):
    return str(e)


if __name__ == '__main__':
    app.debug = True
    app.run(port=8009, use_reloader=False)
