"""
A manager that will help us run the Event's code, be it importing events
or handling RSVPs, from command line and etc. There is one important thing
to note. So when we add a code for a social network we should try to name
that module (and the class inside it) same as the value of that social network's
name in the social network table. So if the name in social network table is 'meetup'
we should try to add  amodule named 'meetup' and a class named "Meetup". This will help
us in keeping things consistent and also help us import things in a clean way on the fly.
We had to make an exception, in terms of this suggested naming scheme, for facebook's
case because facebook-sdk gets into a name conflict if we try naming the module
'facebook'.
"""
import argparse
import logging
import importlib
import sys
import traceback
from gevent.pool import Pool
from gt_models.config import init_db
from gt_models.user import UserCredentials
from gt_models.social_network import SocialNetwork
init_db()


logger = logging.getLogger('event_service.app')

POOL_SIZE = 5


def start():
    parser = argparse.ArgumentParser()
    logger.debug("Hey world...")
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
        social_network = name_space.social_network.lower()
        social_network_obj = SocialNetwork.get_by_name(social_network)
        social_network_id = social_network_obj.id
    all_user_credentials = UserCredentials.get_all_credentials(social_network_id)
    job_pool = Pool(POOL_SIZE)

    for user_credential in all_user_credentials:
        social_network = SocialNetwork.get_by_name(user_credential.social_network.name)
        # Unfortunately, the library facebook-sdk gets in a conflict
        # if you name your module 'facebook.py' so we had to make an exception
        # for Facebook
        social_network_name = social_network.name.lower()
        if social_network_name == 'facebook':
            module_name = 'event_importer.' + social_network_name + "_ev"
        else:
            module_name = 'event_importer.' + social_network_name
        try:
            module = importlib.import_module(module_name)
        except ImportError as ie:
            logger.exception("Event service manager cannot import module,"
                             " details: %s" % ie.message)
        else:
            vendor_class = getattr(module, social_network_name.title())
            obj = vendor_class()
            obj.set_user_credential(user_credential)
            if name_space.mode == 'event':
                job_pool.spawn(obj._process_events)
            elif name_space.mode == 'rsvp':
                job_pool.spawn(obj._process_rsvps)
    job_pool.join()

if __name__ == '__main__':
    try:
        start()
    except Exception:
        logger.error(traceback.format_exc())
        sys.exit(1)
