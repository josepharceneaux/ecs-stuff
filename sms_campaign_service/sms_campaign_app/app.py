"""
    This module contains flask app startup.
    We register blueprints for different APIs with this app.
    Error handlers are added at the end of file.
"""
# Standard  Library imports
import json
import traceback
from datetime import datetime

# Initializing App. This line should come before any imports from models
from sms_campaign_service import init_app
app = init_app()

# # create celery object
# from sms_campaign_service.celery_config import make_celery
# celery = make_celery(app)

# Run Celery from terminal as
# celery -A sms_campaign_service.app.app.celery worker

# start the scheduler
from sms_campaign_service.gt_scheduler import GTScheduler
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.events import EVENT_JOB_EXECUTED
from apscheduler.jobstores.redis_store import RedisJobStore

sched = GTScheduler()
sched.add_jobstore(RedisJobStore(), 'redisJobStore')

# from apscheduler.jobstores.shelve_store import ShelveJobStore
# from apscheduler.scheduler import Scheduler
# from common.utils.apscheduler.jobstores.redis_store import RedisJobStore
# from common.utils.apscheduler.scheduler import Scheduler
# config = {'apscheduler.jobstores.file.class': 'apscheduler.jobstores.shelve_store:ShelveJobStore',
#           'apscheduler.jobstores.file.path': '/tmp/dbfile'}
# sched = Scheduler(config)
# sched.add_jobstore(ShelveJobStore('/tmp/dbfile'), 'file')
# jobstore = RedisJobStore(jobs_key='example.jobs', run_times_key='example.run_times')
# sched.add_jobstore(jobstore)


# def my_listener(event):
#     if event.exception:
#         print('The job crashed :(\n')
#         print str(event.exception.message) + '\n'
#     else:
#         print('The job worked :)')
#
# sched.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
# sched.start()

# Third party imports
import json
import flask
import twilio.twiml
from flask import request
from flask import render_template
from flask.ext.cors import CORS
from werkzeug.utils import redirect

# Application specific imports
from sms_campaign_service import logger
from sms_campaign_service.utilities import run_func, run_func_1
from sms_campaign_service.sms_campaign_base import SmsCampaignBase
from sms_campaign_service.common.error_handling import InternalServerError, ResourceNotFound
from sms_campaign_service.sms_campaign_app.restful_API.sms_campaign_api import sms_campaign_blueprint
from sms_campaign_service.sms_campaign_app.restful_API.url_conversion_api import url_conversion_blueprint

# Register Blueprints for different APIs
app.register_blueprint(sms_campaign_blueprint)
app.register_blueprint(url_conversion_blueprint)

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


@app.route('/sms_campaign/<int:campaign_id>/url_redirection/<int:url_conversion_id>/', methods=['GET'])
def sms_campaign_url_redirection(campaign_id=None, url_conversion_id=None):
    try:
        user_id = request.args.get('user_id')
        candidate_id = request.args.get('candidate_id')
        if all([user_id and campaign_id and url_conversion_id and candidate_id]):
            camp_obj = SmsCampaignBase(user_id=user_id, buy_new_number=False)
            redirection_url = camp_obj.process_url_redirect(campaign_id=campaign_id,
                                                            url_conversion_id=url_conversion_id,
                                                            candidate_id=candidate_id)
            return redirect(redirection_url)
        else:
            logger.error("Required field is missing from requested URL. "
                         "user_id:%s, campaign_id:%s, url_conversion_id:%s, candidate_id:%s"
                         % (user_id, campaign_id, url_conversion_id, candidate_id))
            raise InternalServerError
    except:
        logger.exception("Error occurred while URL redirection for SMS campaign.")
        data = {'message': 'Internal Server Error'}
        return flask.jsonify(**data), 500


@app.route("/sms_receive/", methods=['POST'])
def sms_receive():
    """
    This is a test end point to receive sms
    :return:
    """
    if request.values:
        logger.debug('SMS received from %(From)s on %(To)s.\n '
                     'Body text is "%(Body)s"' % request.values)
        SmsCampaignBase.process_candidate_reply(request.values)
    return """
        <?xml version="1.0" encoding="UTF-8"?>
            <Response>
            </Response>
            """


@app.route('/sms', methods=['GET', 'POST'])
def sms():
    """
    This is a test end point which sends sms campaign
    :return:
    """
    # if request.args.has_key('text'):
    #     body_text = request.args['text']
    #     body_text = process_urls_in_sms_body_text(body_text)
    # else:
    #     body_text = 'Welcome to getTalent'
    # ids = get_smart_list_ids()
    start_min = request.args.get('start')
    end_min = request.args.get('end')
    start_date = datetime(2015, 11, 13, 17, int(start_min), 50)
    end_date = datetime(2015, 11, 13, 17, int(end_min), 36)
    repeat_time_in_sec = int(request.args.get('frequency'))
    func = request.args.get('func')
    arg1 = request.args.get('arg1')
    arg2 = request.args.get('arg2')
    # for x in range (1,50):
    job = sched.add_interval_job(run_func_1,
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

# resp = twilio.twiml.Response()
# resp.message("Thank you for your response")
# return str(resp)
# <Message> Hello </Message>

