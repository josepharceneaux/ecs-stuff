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
from social_network_service.tasks import rsvp_events_importer, import_meetup_events

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
        if not app.config[TalentConfigKeys.ENV_KEY] in [TalentEnvs.DEV, TalentEnvs.JENKINS]:
            raise InvalidUsage('Invalid Usage')
    
        if not (social_network.lower() in [MEETUP, EVENTBRITE]):
            raise InvalidUsage("No social network with name {} found.".format(social_network))

        if mode == 'event_importer':
            import_meetup_events.apply_async()
        return dict(message="{} are being imported.".format(mode.upper()))


def schedule_importer_job():
    """
    Schedule 4 general jobs that hits Event and RSVP importer endpoint every hour.
    """
    task_name = 'Retrieve_{}_{}s'
    # for mode, sn in itertools.product([RSVP, EVENT], [MEETUP, EVENTBRITE]):
    url = SocialNetworkApiUrl.IMPORTER % ('event_importer', MEETUP)
    schedule_job(task_name=task_name.format(MEETUP.title(), EVENT), url=url)


def schedule_job(url, task_name):
    """
    Schedule a general job that hits Event and RSVP importer endpoint every hour.
    :param url: URL to hit
    :type url: basestring
    :param task_name: task_name of scheduler job
    :type task_name: basestring
    """
    start_datetime = datetime.datetime.utcnow() + datetime.timedelta(seconds=15)

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
