"""
This file contains API endpoint for importing Events and RSVPs from social-network websites like Meetup, Eventbrite etc.
"""

# Standard imports
import json
import types
import datetime

# 3rd party imports
import requests
from flask import Blueprint
from flask.ext.restful import Resource

# App specific imports
from social_network_service.common.error_handling import InvalidUsage
from social_network_service.common.models.user import User
from social_network_service.common.redis_cache import redis_store
from social_network_service.common.routes import SocialNetworkApi, SchedulerApiUrl, SocialNetworkApiUrl
from social_network_service.common.talent_api import TalentApi
from social_network_service.common.talent_config_manager import TalentEnvs, TalentConfigKeys
from social_network_service.common.utils.api_utils import api_route
from social_network_service.common.utils.auth_utils import require_oauth
from social_network_service.common.utils.datetime_utils import DatetimeUtils
from social_network_service.modules.constants import EVENTBRITE, EVENT
from social_network_service.common.constants import MEETUP
from social_network_service.tasks import import_meetup_events
from social_network_service.social_network_app import logger, app

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
        .. seealso:: process() method of SocialNetworkBase class inside social_network_service/base.py.

    """
    decorators = [require_oauth(allow_null_user=True)]

    def post(self, mode, social_network):
        """
        :param mode: Possible values -> rsvp, event
        :type mode: str
        :param social_network: Possible values -> eventbrite, facebook, meetup
        :type social_network: str
        """
        if mode == 'event_importer':
            import_lock_key = 'Meetup_Importer_Lock'
            if not redis_store.get(import_lock_key):
                # set lock for 5 minutes
                redis_store.set(import_lock_key, True, 5 * 60)
            else:
                raise InvalidUsage('Importer is locked at the moment. Please try again later.')
            if app.config[TalentConfigKeys.ENV_KEY] in [TalentEnvs.JENKINS]:
                raise InvalidUsage('Invalid Usage')

            if not (social_network.lower() in [MEETUP, EVENTBRITE]):
                raise InvalidUsage("No social network with name {} found.".format(social_network))
            # import_meetup_events.delay()

        return dict(message='Meetup Importer has started at : %s' % datetime.datetime.utcnow())


def schedule_importer_job():
    """
    Schedule a general job that hits Event  importer endpoint to run Event Importer long running task.
    """
    import_lock_key = 'Meetup_Event_Importer_Lock'
    if not redis_store.get(import_lock_key):
        # set lock for 5 minutes
        redis_store.set(import_lock_key, True, 5 * 60)
        task_name = 'Retrieve_{}_{}s'
        # for mode, sn in itertools.product([RSVP, EVENT], [MEETUP, EVENTBRITE]):
        url = SocialNetworkApiUrl.IMPORTER % ('event_importer', MEETUP)
        schedule_job(task_name=task_name.format(MEETUP.title(), EVENT), url=url)
    else:
        logger.info('Meetup Event Importer is already running.')
        return 'Done'


def schedule_job(url, task_name):
    """
    Schedule a general job that hits Event and RSVP importer endpoint every hour.
    :param url: URL to hit
    :type url: basestring
    :param task_name: task_name of scheduler job
    :type task_name: basestring
    """
    start_datetime = datetime.datetime.utcnow() + datetime.timedelta(seconds=30)

    access_token = User.generate_jw_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': access_token
    }

    data = {
        "url": url,
        "run_datetime": start_datetime.strftime(DatetimeUtils.ISO8601_FORMAT),
        "task_type": "one_time",
        "task_name": "Meetup_Event_Importer_Stream",
        'is_jwt_request': True

    }

    logger.info('Checking if {} task already running...'.format(task_name))
    response = requests.post(SchedulerApiUrl.TASKS, headers=headers,
                             data=json.dumps(data))
    if response.ok:
        logger.info('Meetup_Event_Importer_Stream Job scheduled successfully. {}'.format(response.text))
    else:
        logger.error(response.text)
