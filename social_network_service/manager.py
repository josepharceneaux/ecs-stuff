# Standard Library
import sys
import argparse
import traceback

# Third Party
from gevent.pool import Pool


# App Settings
from social_network_service import init_app
init_app()

# Application Specific
from utilities import get_class, log_exception
from common.models.user import UserSocialNetworkCredential
from common.models.social_network import SocialNetwork
from social_network_service import logger
from social_network_service.custom_exections import AccessTokenHasExpired

POOL_SIZE = 5


def start():
    """
    This function is called by manager to process events or rsvps from given
    social network. It first gets the user_credentials of all the users in
    database and does the processing for each user. Then it instantiates
    respective social network class for auth process. Then we call the
    class socialNetworkBase class method process() to proceed further
    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-m",
                        action="store",
                        type=str,
                        dest="mode",
                        help="specify mode e.g. '-m rsvp' or '-m event'")
    parser.add_argument("-s",
                        action="store",
                        type=str,
                        dest="social_network",
                        help="specify social work name to process e.g. '-s facebook' or '-s meetup'")

    name_space = parser.parse_args()
    social_network_id = None
    if name_space.social_network is not None:
        social_network_name = name_space.social_network.lower()
        social_network_obj = SocialNetwork.get_by_name(social_network_name)
        social_network_id = social_network_obj.id
    all_user_credentials = UserSocialNetworkCredential.get_all_credentials(social_network_id)
    job_pool = Pool(POOL_SIZE)
    if all_user_credentials:
        for user_credentials in all_user_credentials:
            try:
                social_network = SocialNetwork.get_by_name(user_credentials.social_network.name)
                social_network_class = get_class(social_network.name.lower(), 'social_network',
                                                 user_credentials=user_credentials)
                # we call social network class here for auth purpose, If token is expired
                # access token is refreshed and we use fresh token
                sn = social_network_class(user_id=user_credentials.user_id)
                if sn.access_token_status:
                    logger.debug('%s Importer has started for %s(UserId: %s).'
                                 ' Social Network is %s.'
                                 % (name_space.mode.title(), sn.user.name, sn.user.id,
                                    social_network.name))
                    job_pool.spawn(sn.process, name_space.mode,
                                   user_credentials=user_credentials)
                else:
                    raise AccessTokenHasExpired('Access token has expired')
            except Exception as error:
                log_exception({'user_id': user_credentials.user_id,
                               'error': error.message})
        job_pool.join()
    else:
        logger.error('There is no User in db for social network %s' % name_space.social_network)
        
if __name__ == '__main__':
    try:
        start()
    except TypeError:
        logger.error('Please provide required parameters to run manager')
    except Exception:
        logger.error(traceback.format_exc())
        sys.exit(1)
