"""
    This module contains flask app startup.
    We register blueprints for different APIs with this app.
    Error handlers are added at the end of file.
"""
# Standard  Library imports
import os
from datetime import datetime, timedelta

# 3rd party imports
from flask import request
from flask import render_template
from flask.ext.cors import CORS

# Initializing App. This line should come before any imports from models
from scheduler_service import init_app
app = init_app()

from scheduler_service.common.models.scheduler import SchedulerTask
from scheduler_service.api.scheduler_api import scheduler_blueprint
from scheduler_service.scheduler import scheduler
from scheduler_service.tasks import send_sms_campaign, methods


# Run Celery from terminal as
# celery -A scheduler_service.app.app.celery worker

# Third party imports


app.register_blueprint(scheduler_blueprint)
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


# @app.route('/tasks/')
# def tasks():
#     scheduled_tasks = SchedulerTask.query.all()
#     tasks = [task for task in scheduled_tasks]
#     return render_template('tasks.html', tasks=tasks)


@app.route('/resume/<job_id>')
def job_resume(job_id):
    try:
        scheduler.resume_job(job_id=job_id)
    except Exception as e:
        return str(e)
    return "Job resumed successfully"


@app.route('/stop/<job_id>')
def job_stop(job_id):
    try:
        scheduler.pause_job(job_id=job_id)
    except Exception as e:
        return str(e)
    return "Job stopped successfully"


@app.route('/unschedule/<job_id>')
def unschedule(job_id):
    try:
        scheduler.remove_job(job_id=job_id)
    except Exception as e:
        return str(e)
    return "Job removed successfully"


@app.route('/schedule/', methods=['GET', 'POST'])
def schedule_job():
    """
    This is a test end point which sends sms campaign
    :return:
    """
    start_date = datetime.now()
    start_date.replace(second=(start_date.second + 15) % 60)
    end_date = start_date + timedelta(hours=2)
    repeat_time_in_sec = int(request.args.get('frequency', 10))
    func = request.args.get('func', 'send_sms_campaign')
    arg1 = request.args.get('arg1')
    arg2 = request.args.get('arg2')
    try:
        scheduler.add_job(on_task_added,
                            'interval',
                            seconds=repeat_time_in_sec,
                            start_date=start_date,
                            end_date=end_date,
                            args=[arg1, arg2, end_date],
                            kwargs=dict(func=func, end_date=end_date))
    except Exception as e:
        print e
        return e
    print 'Task has been added and will run at %s ' % start_date
    return 'Task has been added to queue!!!'


@app.route("/get-task/<job_id>")
def get_tasks(job_id):
    task = scheduler.get_job(job_id=job_id)
    return task





# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# my_loader = jinja2.ChoiceLoader([
#     app.jinja_loader,
#     jinja2.FileSystemLoader(os.path.join(BASE_DIR, 'templates')),
# ])
# app.jinja_loader = my_loader


@app.errorhandler(Exception)
def error_handler(e):
    return str(e)


scheduler.start()

if __name__ == '__main__':
    app.run(port=8000)


