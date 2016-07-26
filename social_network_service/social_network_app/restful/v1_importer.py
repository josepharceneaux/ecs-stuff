# Standard imports
import json
import os
import types

# 3rd party imports
import datetime
import requests
from flask import Blueprint
from flask.ext.restful import Resource

# App specific imports
from social_network_service.common.error_handling import InvalidUsage, InternalServerError
from social_network_service.common.models.candidate import SocialNetwork
from social_network_service.common.models.user import UserSocialNetworkCredential, User
from social_network_service.common.routes import SocialNetworkApi, SchedulerApiUrl, SocialNetworkApiUrl
from social_network_service.common.talent_api import TalentApi
from social_network_service.common.talent_config_manager import TalentEnvs, TalentConfigKeys
from social_network_service.common.utils.api_utils import api_route
from social_network_service.common.utils.auth_utils import require_oauth
from social_network_service.common.utils.datetime_utils import DatetimeUtils
from social_network_service.social_network_app import logger
from social_network_service.tasks import rsvp_events_importer

rsvp_blueprint = Blueprint('importer', __name__)
api = TalentApi()
api.init_app(rsvp_blueprint)
api.route = types.MethodType(api_route, api)


@api.route(SocialNetworkApi.IMPORTER)
class RsvpEventImporter(Resource):
    """
        This resource gets all RSVPs or events.

        This function is called when we run celery to import events or RSVPs from
        social network website.

        1- Meetup
        2- Eventbrite

        ** Working **
        What this method does, is explained in following steps:
        1- Call celery importer task depending on mode and social_network value

        2- It gets the user_social_network_credentials of all the users related
            to given social network (social_network provided in arguments) from
            getTalent database in variable all_user_credentials.
        3- It picks one user_credential from all_user_credentials and instantiates
            respective social network class for auth process.
        4- If access token is not valid, we raise
            AccessTokenHasExpired exception in celery task and move on to next user_credential.

        **See Also**
        .. seealso:: process() method of SocialNetworkBase class inside
                    social_network_service/base.py.

    """
    decorators = [require_oauth(allow_null_user=True)]

    def post(self, mode, social_network):

        # Start celery rsvp importer method here.
        if mode.lower() not in ["event", "rsvp"]:
            raise InvalidUsage("No mode of value %s found" % mode)

        if not (social_network.lower() in ["meetup", "facebook", "eventbrite"]):
            raise InvalidUsage("No social network with name %s found." % social_network)

        social_network_name = social_network.lower()
        try:
            social_network_obj = SocialNetwork.get_by_name(social_network_name)
            if not social_network_obj:
                raise InvalidUsage('Social Network with name %s doesn\'t exist.' % social_network)
            social_network_id = social_network_obj.id
        except Exception:
            raise NotImplementedError('Social Network "%s" is not allowed for now, '
                                      'please implement code for this social network.'
                                      % social_network_name)

        all_user_credentials = UserSocialNetworkCredential.get_all_credentials(social_network_id)

        if all_user_credentials:
            logger.info('Got %s users for %s' % (len(all_user_credentials), social_network))
            for user_credentials in all_user_credentials:
                # Get last updated time of current user_credentials if NULL, then run event importer for that user
                # first time and get all events otherwise get events from last_updated date
                datetime_range = {}
                if mode == 'event':
                    last_updated = \
                      user_credentials.last_updated if user_credentials.last_updated else datetime.datetime(2000, 1, 1)
                    datetime_range.update({
                        'date_range_start': DatetimeUtils.to_utc_str(last_updated),
                        'date_range_end': DatetimeUtils.to_utc_str(datetime.datetime.utcnow())
                    })
                    # Update last_updated of each user_credentials.
                    user_credentials.update(last_updated=datetime.datetime.utcnow())
                rsvp_events_importer.apply_async([social_network, mode, user_credentials.id, datetime_range])
        else:
            logger.error('User Credentials not found for social network %s'
                         % social_network)

        return dict(message="%s are being imported." % mode.upper())


def schedule_importer_job():
    """
    Schedule 4 general jobs that hits Event and RSVP importer endpoint every hour.
    :return:
    """
    task_name_meetup = 'Retrieve_Meetup_%s'
    task_name_eventbrite = 'Retrieve_Eventbrite_%s'

    url = SocialNetworkApiUrl.IMPORTER % ('event', 'meetup')
    schedule_job(task_name=task_name_meetup % 'events', url=url)

    url = SocialNetworkApiUrl.IMPORTER % ('event', 'eventbrite')
    schedule_job(task_name=task_name_eventbrite % 'events', url=url)

    url = SocialNetworkApiUrl.IMPORTER % ('rsvp', 'meetup')
    schedule_job(task_name=task_name_meetup % 'rsvp', url=url)

    url = SocialNetworkApiUrl.IMPORTER % ('rsvp', 'eventbrite')
    schedule_job(task_name=task_name_eventbrite % 'rsvp', url=url)


def schedule_job(url, task_name):
    """
    Schedule a general job that hits Event and RSVP importer endpoint every hour.
    :param url: URL to hit
    :type url: basestring
    :param task_name: task_name of scheduler job
    :type task_name: basestring
    """
    start_datetime = datetime.datetime.utcnow() + datetime.timedelta(seconds=15)
    # Schedule for next 100 years
    end_datetime = datetime.datetime.utcnow() + datetime.timedelta(weeks=52 * 100)

    env = os.getenv(TalentConfigKeys.ENV_KEY) or TalentEnvs.DEV
    frequency = 120 if env in [TalentEnvs.DEV, TalentEnvs.JENKINS] else 3600

    secret_key_id, access_token = User.generate_jw_token()
    headers = {
            'Content-Type': 'application/json',
            'X-Talent-Secret-Key-ID': secret_key_id,
            'Authorization': access_token
        }
    data = {
        'start_datetime': start_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'end_datetime': end_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'frequency': frequency,
        'is_jwt_request': True
    }

    logger.info('Checking if %s task already running...' % task_name)
    response = requests.get(SchedulerApiUrl.TASK_NAME % task_name, headers=headers)
    # If job is not scheduled then schedule it
    if response.status_code == requests.codes.not_found:
        logger.info('Task %s not scheduled. Scheduling %s task.' % (task_name, task_name))
        data.update({'url': url})
        data.update({'task_name': task_name, 'task_type': 'periodic'})

        response = requests.post(SchedulerApiUrl.TASKS, headers=headers,
                                 data=json.dumps(data))

        if not (response.status_code == requests.codes.created or response.json()['error']['code'] == 6057):
            logger.error(response.text)
            raise InternalServerError(error_message='Unable to schedule meetup importer job')
    elif response.status_code == requests.codes.ok:
        logger.info('Job already scheduled. %s' % response.text)
