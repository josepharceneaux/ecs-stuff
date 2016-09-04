# Standard imports
import json
import os
import types
import datetime

import itertools
import requests

# 3rd party imports
from flask import Blueprint
from flask.ext.restful import Resource

# App specific imports
from social_network_service.common.error_handling import InvalidUsage, InternalServerError
from social_network_service.common.models.candidate import SocialNetwork
from social_network_service.common.models.user import UserSocialNetworkCredential, User
from social_network_service.common.redis_cache import redis_store
from social_network_service.common.routes import SocialNetworkApi, SchedulerApiUrl, SocialNetworkApiUrl
from social_network_service.common.talent_api import TalentApi
from social_network_service.common.talent_config_manager import TalentEnvs, TalentConfigKeys
from social_network_service.common.utils.api_utils import api_route
from social_network_service.common.utils.auth_utils import require_oauth
from social_network_service.common.utils.datetime_utils import DatetimeUtils
from social_network_service.modules.constants import EVENTBRITE, TASK_ALREADY_SCHEDULED, RSVP, EVENT
from social_network_service.common.constants import MEETUP
from social_network_service.social_network_app import logger, app
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
        """
        :param mode: Possible values -> rsvp, event
        :type mode: str
        :param social_network: Possible values -> eventbrite, facebook, meetup
        :type social_network: str
        """
        # Lock the importer for 3500 seconds. So that someone doesn't make multiple requests to this endpoint
        import_lock_key = 'Importer_Lock'
        if not redis_store.get(import_lock_key):
            redis_store.set(import_lock_key, True, 3500)
        elif not app.config[TalentConfigKeys.ENV_KEY] in [TalentEnvs.DEV, TalentEnvs.JENKINS]:
            raise InvalidUsage('Importer is locked at the moment. Please try again later.')
        # Start celery rsvp importer method here.
        if mode.lower() not in [EVENT, RSVP]:
            raise InvalidUsage("There is no mode with name {} found".format(mode))

        if not (social_network.lower() in [MEETUP, EVENTBRITE]):
            raise InvalidUsage("No social network with name {} found.".format(social_network))

        social_network_name = social_network.lower()
        social_network_obj = SocialNetwork.get_by_name(social_network_name)
        if not social_network_obj:
            raise InvalidUsage('Social Network with name {} doesn\'t exist.'.format(social_network))
        social_network_id = social_network_obj.id

        all_user_credentials = UserSocialNetworkCredential.get_all_credentials(social_network_id)

        if all_user_credentials:
            logger.info('Got {} users for {}'.format(len(all_user_credentials), social_network))
            for user_credentials in all_user_credentials:
                datetime_range = {}
                if mode == EVENT:
                    # Get last updated time of current user_credentials if NULL, then run event importer for that user
                    # first time and get all events otherwise get events from last_updated date
                    if user_credentials.updated_datetime:
                        last_updated = user_credentials.updated_datetime
                    else:
                        last_updated = datetime.datetime(2000, 1, 1)
                    datetime_range.update({
                        'date_range_start': DatetimeUtils.get_utc_datetime(last_updated, 'utc'),
                        'date_range_end': DatetimeUtils.get_utc_datetime(datetime.datetime.utcnow(), 'utc')
                    })
                rsvp_events_importer.apply_async([social_network, mode, user_credentials.id, datetime_range])
        else:
            logger.error('User Credentials not found for social network {}'
                         .format(social_network))

        return dict(message="{} are being imported.".format(mode.upper()))


def schedule_importer_job():
    """
    Schedule 4 general jobs that hits Event and RSVP importer endpoint every hour.
    """
    task_name = 'Retrieve_{}_{}s'
    for mode, sn in itertools.product([RSVP, EVENT], [MEETUP, EVENTBRITE]):
        url = SocialNetworkApiUrl.IMPORTER % (mode, sn)
        schedule_job(task_name=task_name.format(sn.title(), mode), url=url)


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
    frequency = 3600

    secret_key_id, access_token = User.generate_jw_token()
    headers = {
        'Content-Type': 'application/json',
        'X-Talent-Secret-Key-ID': secret_key_id,
        'Authorization': access_token
    }
    data = {
        'start_datetime': start_datetime.strftime(DatetimeUtils.ISO8601_FORMAT),
        'end_datetime': end_datetime.strftime(DatetimeUtils.ISO8601_FORMAT),
        'frequency': frequency,
        'is_jwt_request': True
    }

    logger.info('Checking if {} task already running...'.format(task_name))
    response = requests.get(SchedulerApiUrl.TASK_NAME % task_name, headers=headers)
    # If job is not scheduled then schedule it
    if response.status_code == requests.codes.not_found:
        logger.info('Task {} not scheduled. Scheduling {} task.'.format(task_name, task_name))
        data.update({'url': url})
        data.update({'task_name': task_name, 'task_type': 'periodic'})

        response = requests.post(SchedulerApiUrl.TASKS, headers=headers,
                                 data=json.dumps(data))

        is_already_created = \
            response.status_code == requests.codes.created or response.json()['error']['code'] == TASK_ALREADY_SCHEDULED
        if not is_already_created:
            logger.error(response.text)
            raise InternalServerError(error_message='Unable to schedule Meetup importer job')
    elif response.status_code == requests.codes.ok:
        logger.info('Job already scheduled. {}'.format(response.text))
    else:
        logger.error(response.text)
