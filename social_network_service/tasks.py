"""
Celery tasks are defined here. It will be a separate celery process.
These methods are called by run_job method asynchronously

- Running celery using commandline (social_network_service directory) =>

    celery -A social_network_service.run.celery  worker --concurrency=4 --loglevel=info

"""

# Application imports
from social_network_service.common.models.candidate import SocialNetwork
from social_network_service.common.models.user import UserSocialNetworkCredential
from social_network_service.common.talent_config_manager import TalentConfigKeys
from social_network_service.modules.utilities import get_class
from social_network_service.social_network_app import celery_app as celery, app


@celery.task(name="rsvp_events_importer")
def rsvp_events_importer(social_network_name, mode, user_credentials):
    """
    Imports RSVPs or events of a user, create canidates store them in db and also upload them on Cloud search
    :param social_network_name: facebook, eventbrite, meetup
    :param mode: rsvp or event
    :param app: Flask app
    :return:
    """
    with app.app_context():
        logger = app.config[TalentConfigKeys.LOGGER]

        try:
            social_network = SocialNetwork.get_by_name(social_network_name.lower())
            social_network_class = get_class(social_network.name.lower(), 'social_network',
                                             user_credentials=user_credentials)
            # we call social network class here for auth purpose, If token is expired
            # access token is refreshed and we use fresh token
            sn = social_network_class(user_id=user_credentials.user_id)

            logger.debug('%s Importer has started for %s(UserId: %s).'
                         ' Social Network is %s.'
                         % (mode.title(), sn.user.name, sn.user.id,
                            social_network.name))
            sn.process(mode, user_credentials=user_credentials)
        except KeyError:
            logger.exception("Key error while running importer for user %s" % user_credentials.user_id)
        except Exception:
            logger.exception('start: running %s importer, user_id: %s',
                             mode, user_credentials.user_id)
