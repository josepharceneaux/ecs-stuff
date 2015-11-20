__author__ = 'zohaib'

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


def my_listener(event):
    if event.exception:
        print('The job crashed :(\n')
        print str(event.exception.message) + '\n'
    else:
        print('The job worked :)')

sched.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
sched.start()

# Third party imports
import flask
from flask import request
from flask import render_template
from flask.ext.cors import CORS
from flask.ext.restful import Api
from werkzeug.utils import redirect

# Application specific imports
from utilities import get_all_tasks
from utilities import http_request
from sms_campaign_service.utilities import send_sms_campaign
from sms_campaign_service.utilities import get_smart_list_ids
from sms_campaign_service.utilities import process_redirection
from sms_campaign_service.utilities import process_link_in_body_text
from sms_campaign_service.app.app_utils import ApiResponse
from sms_campaign_service.custom_exceptions import ApiException
from sms_campaign_service.common.error_handling import InternalServerError

# Register Blueprints for different APIs
app.register_blueprint(sms_campaign_blueprint)
api = Api(app)

LONG_URL = 'https://webdev.gettalent.com/web/user/login?_next=/web/default/angular#!/'

# Enable CORS
CORS(app, resources={
    r'/*': {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})


@app.route('/')
def hello_world():

    from sms_campaign_service.common.models.sms_campaign import SmsCampaign, \
        SmsCampaignBlast, SmsCampaignSend, SmsCampaignReply
    from sms_campaign_service.common.models.misc import Frequency
    from sms_campaign_service.common.models.user import UserPhone
    print SmsCampaign.query.all()
    print SmsCampaignBlast.query.all()
    print SmsCampaignSend.query.all()
    print SmsCampaignReply.query.all()
    print Frequency.query.all()
    print UserPhone.query.all()
    # from sms_campaign_service.common.models.candidate import Candidate
    # candidate = Candidate.query.get(1)
    # social_networks = candidate.candidate_social_network
    # data = [{
    #             'name': social_network.social_network.name,
    #             'url': social_network.social_profile_url
    #         } for social_network in social_networks]
    return 'Welcome to SMS Campaign Service'


@app.route('/tasks')
def tasks():
    data = get_all_tasks()
    return render_template('tasks.html', tasks=data)


@app.route('/url_conversion', methods=['GET', 'POST'])
# @app.route('/url_conversion/<url>', methods=['GET', 'POST'])
def short_url_test(url=None):
    """
    This is a test end point which converts given URL to short URL
    :return:
    """
    url = 'http://127.0.0.1:8007/convert_url'
    response = http_request('GET', url, params={'url': LONG_URL})
    if response.ok:
        short_url, long_url = url_conversion(url)
        return redirect(short_url)
    else:
        data = {'message': 'No URL given in request',
                'status_code': 200}
    return flask.jsonify(**data), 200


@app.route('/sms', methods=['GET', 'POST'])
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


@app.route("/sms_receive", methods=['GET', 'POST'])
def sms_receive():
    """
    This is a test end point to receive sms
    :return:
    """
    if request.values:
        response = 'SMS received from %(From)s on %(To)s.\n' \
                   'Body text is "%(Body)s"' \
                   % request.values
        print response
    return """
        <?xml version="1.0" encoding="UTF-8"?>
            <Response>
            </Response>
            """

# resp = twilio.twiml.Response()
# resp.message("Thank you for your response")
# return str(resp)
# <Message> Hello </Message>


@app.route('/redirect', methods=['GET', 'POST'])
def redirect_to_long_url():
    """
    This is a test end point which redirects to Long URL
    :return:
    """
    if request.args.get('url_id'):
        url_conversion = process_redirection(request.args['url_id'])
        return redirect(url_conversion.destination_url)
    else:
        return ''


@app.errorhandler(ApiException)
def handle_api_exception(error):
    """
    This handler handles ApiException error
    :param error: exception object containing error info
    :type error:  ApiException
    :return: json response
    """
    logger.debug('Error: %s\nTraceback: %s' % (error, traceback.format_exc()))
    response = json.dumps(error.to_dict())
    return ApiResponse(response, status=error.status_code)


@app.errorhandler(Exception)
def handle_any_errors(error):
    """
    This handler handles any kind of error in app.
    :param error: exception object containing error info
    :type error:  Exception
    :return: json response
    """
    logger.debug('Error: %s\nTraceback: %s' % (error, traceback.format_exc()))
    response = json.dumps(dict(message='Ooops! Internal server error occurred..' + str(error.message)))
    return ApiResponse(response, status=500)


