import os
from apscheduler.executors.pool import ThreadPoolExecutor
import jinja2
from scheduler_service.common.models.scheduler import SchedulerTask
from scheduler_service.tasks import methods, raise_exception
from scheduler_service import init_app
from scheduler_service.utils import jsonify

__author__ = 'zohaib'

"""
    This module contains flask app startup.
    We register blueprints for different APIs with this app.
    Error handlers are added at the end of file.
"""
# Standard  Library imports
from datetime import datetime

# Initializing App. This line should come before any imports from models


# Run Celery from terminal as
# celery -A scheduler_service.app.app.celery worker

# start the scheduler
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.events import EVENT_JOB_EXECUTED
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.background import BackgroundScheduler

"""
add Redis job store and listener to scheduler
"""
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
        if event.job.next_run_time > event.job.kwargs['end_date']:
            print 'Stopping job'


scheduler.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)


# Third party imports
from flask import request
from flask import render_template
from flask.ext.cors import CORS

app = init_app()

# Enable CORS
CORS(app, resources={
    r'/*': {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})

"""
Scheduling service endpoints
"""


@app.route('/index')
def index():
    return 'Welcome to SMS Campaign Service'


@app.route('/resume/<job_id>', methods=['POST'])
def job_resume(job_id):
    """
    Resume already stopped job
    :param job_id: job id to resume job
    :return:
    """
    try:
        scheduler.resume_job(job_id=job_id)
    except Exception as e:
        return str(e)
    msg = {
        'message': "Job resumed successfully"
    }
    return jsonify(msg)


@app.route('/stop/<job_id>', methods = ['POST'])
def job_stop(job_id):
    """
    Stops a scheduled running job
    :param job_id:
    :return:
    """
    try:
        scheduler.pause_job(job_id=job_id)
    except Exception as e:
        return str(e)
    msg = {
        'message': "Job stopped successfully"
    }
    return jsonify(msg)


@app.route('/unschedule/<job_id>', methods=['POST'])
def unschedule(job_id):
    """
    Unschedule already scheduled job
    :param job_id:
    :return:
    """
    try:
        scheduler.remove_job(job_id=job_id)
    except Exception as e:
        return str(e)
    msg = {
        'message': "Job removed successfully"
    }
    return jsonify(msg)


@app.route('/unschedule-jobs/', methods=['POST'])
def unschedule_jobs():
    """
    Unschedule all jobs
    :return:
    """
    try:
        scheduler.remove_all_jobs()
    except Exception as e:
        return str(e)
    msg = {
        'message': "Jobs removed successfully"
    }
    return jsonify(msg)


@app.route('/schedule/', methods=['POST'])
def schedule_job():
    """
    This is a test end point which schedule task
    :return:
    """
    job_data = request.get_json(force=True)
    start_date = datetime.strptime(job_data['start_date'], '%Y-%m-%d %H:%M:%S')
    end_date = datetime.strptime(job_data['end_date'], '%Y-%m-%d %H:%M:%S')
    repeat_time_in_sec = job_data['seconds']
    func = job_data['func']
    trigger = job_data['trigger']
    try:
        job = scheduler.add_job(on_task_added,
                                trigger=trigger,
                                seconds=repeat_time_in_sec,
                                start_date=start_date,
                                end_date=end_date,
                                #args=[arg1, arg2, end_date],
                                kwargs=dict(func=func, end_date=end_date)
                                )
        job_dict = {
            'id': job.id
        }
    except Exception as e:
        print e
        return e
    print 'Task has been added and will run at %s ' % start_date
    return jsonify(job_dict)


@app.route('/get-job/<job_id>', methods=['GET'])
def get_job(job_id):
    try:
        job_obj = scheduler.get_job(job_id=job_id)
    except Exception as e:
        return str(e)
    job = {
        'id': job_obj.id,
        'next_run_time': str(job_obj.next_run_time),
        'func': str(job_obj.func)
    }
    return jsonify(job)


@app.route('/get-jobs/', methods=['GET'])
def get_jobs():
    try:
        job_objs = scheduler.get_jobs()
    except Exception as e:
        return str(e)
    jobs = []
    for job_obj in job_objs:
        job = {
            'id': job_obj.id,
            'next_run_time': str(job_obj.next_run_time),
            'func': str(job_obj.func)
        }
        jobs.append(job)
    return jsonify(jobs)


@app.route("/get-task/<job_id>")
def get_tasks(job_id):
    task = scheduler.get_job(job_id=job_id)
    return task


def on_task_added(*args, **kwargs):
    if kwargs['func'] in methods:
        methods[kwargs['func']].apply_async(args, kwargs)
    else:
        raise_exception.apply_async(args, kwargs)


@app.errorhandler(Exception)
def error_handler(e):
    return str(e)


scheduler.start()


if __name__ == '__main__':
    app.run(port=8009)


