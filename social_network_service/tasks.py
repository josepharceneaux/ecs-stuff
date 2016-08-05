"""
Celery tasks are defined here. It will be a separate celery process.
These methods are called by run_job method asynchronously

- Running celery using commandline (social_network_service directory) =>

    celery -A social_network_service.social_network_app.celery_app worker  worker --concurrency=4 --loglevel=info

"""
# Application imports
import datetime

from social_network_service.common.models.candidate import SocialNetwork
from social_network_service.common.models.user import UserSocialNetworkCredential
from social_network_service.common.talent_config_manager import TalentConfigKeys
from social_network_service.modules.utilities import get_class
from social_network_service.social_network_app import celery_app as celery, app


@celery.task(name="events_and_rsvps_importer")
def rsvp_events_importer(social_network_name, mode, user_credentials_id, datetime_range):
    """
    Imports RSVPs or events of a user, create candidates store them in db and also upload them on Cloud search
    :param social_network_name: Facebook, Eventbrite, Meetup
    :type social_network_name: str
    :param mode: rsvp or event
    :type mode: str
    :param user_credentials_id: user credentials entry
    :type user_credentials_id: id
    :param datetime_range:
    :type datetime_range: dict
    :return:
    """
    with app.app_context():
        logger = app.config[TalentConfigKeys.LOGGER]
        user_credentials = UserSocialNetworkCredential.get_by_id(user_credentials_id)
        user_id = user_credentials.user_id
        try:
            social_network = SocialNetwork.get_by_name(social_network_name.lower())
            social_network_class = get_class(social_network.name.lower(), 'social_network',
                                             user_credentials=user_credentials)
            # we call social network class here for auth purpose, If token is expired
            # access token is refreshed and we use fresh token8
            sn = social_network_class(user_id)

            logger.debug('%s Importer has started for %s(UserId: %s).'
                         ' Social Network is %s.'
                         % (mode.title(), sn.user.name, sn.user.id,
                            social_network.name))
            sn.process(mode, user_credentials=user_credentials, **datetime_range)
            # Update last_updated of each user_credentials.
            user_credentials.update(updated_datetime=datetime.datetime.utcnow())
        except Exception as e:
            logger.exception('start: running %s importer, user_id: %s failed. %s',
                             mode, user_id, e.message)
