# Standard Library
import sys
import argparse
import traceback

# Third Party
import gevent
from gevent import monkey
gevent.monkey.patch_all()
from gevent.pool import Pool

# App Settings
from social_network_service.app.app import init_app
init_app()

# Application Specific
from utilities import get_class
from social_network_service import logger
from social_network_service.common.models.user import UserSocialNetworkCredential
from social_network_service.common.models.candidate import SocialNetwork

POOL_SIZE = 5


def start():
    """
    This function is called when we run manager to import events or rsvps from
    social network website.

    "manager" takes "-m mode -s social_network" as arguments to run.
        - "mode" will be either "event" or "rsvp".
        - "source" will be from following (for now)
            1- meetup
            2- eventbrite
            3- facebook.

    ** Working **
    What this method does, is explained in following steps:

    1- It creates a job_pool to process multiple user_credentials in parallel.
    2- It gets the user_social_network_credentials of all the users related
        to given social network (social_network provided in arguments) from
        getTalent database in variable all_user_credentials.
    3- It picks one user_credential from all_user_credentials and instantiates
        respective social network class for auth process.
    4- If access token is not valid, we raise
        AccessTokenHasExpired exception and move on to next user_credential.
    5- If access token is valid, we spawn the job pool by calling the
        SocialNetworkBase class method process() and by passing "mode" and
        "user_credential" as arguments.
    6- Once all user_credential have been traversed, we call job_pool.join()
        to execute all the tasks in job_pool.

    **See Also**
    .. seealso:: process() method of SocialNetworkBase class inside
                social_network_service/base.py.
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
                        help="specify social work name to process e.g. "
                             "'-s facebook' or '-s meetup'")

    name_space = parser.parse_args()
    social_network_id = None
    if name_space.social_network is not None:
        social_network_name = name_space.social_network.lower()
        try:
            social_network_obj = SocialNetwork.get_by_name(social_network_name)
            social_network_id = social_network_obj.id
        except:
            raise NotImplementedError('Social Network "%s" is not allowed for now, '
                                      'please implement code for this social network.'
                                      % social_network_name)
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

                logger.debug('%s Importer has started for %s(UserId: %s).'
                             ' Social Network is %s.'
                             % (name_space.mode.title(), sn.user.name, sn.user.id,
                                social_network.name))
                job_pool.spawn(sn.process, name_space.mode,
                               user_credentials=user_credentials)
            except KeyError:
                raise
            except:
                logger.exception('start: running %s importer, user_id: %s',
                                 name_space.mode, user_credentials.user_id)
        job_pool.join()
    else:
        logger.error('There is no User in db for social network %s'
                     % name_space.social_network)
        
if __name__ == '__main__':
    try:
        start()
    except TypeError as e:
        logger.error('Please provide required parameters to run manager')
    except:
        logger.error(traceback.format_exc())
        sys.exit(1)
