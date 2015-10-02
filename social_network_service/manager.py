import os
import sys
from gt_common.models.config import GTSQLAlchemy
if not GTSQLAlchemy.db_session:
    app_cfg = os.path.abspath('app.cfg')
    logging_cfg = os.path.abspath('logging.conf')

    GTSQLAlchemy(app_config_path=app_cfg,
                 logging_config_path=logging_cfg)
import logging
import argparse
import traceback

from gevent.pool import Pool
from datetime import datetime
from dateutil.parser import parse
from gt_common.models.event import Event
from gt_common.models.user import UserCredentials, User
from gt_common.models.social_network import SocialNetwork
from utilities import get_class, get_message_to_log, log_error
from social_network_service.custom_exections import SocialNetworkError, \
    SocialNetworkNotImplemented, InvalidDatetime, EventInputMissing
logger = logging.getLogger('event_service.app')

POOL_SIZE = 5


def process_access_token(social_network_name, code_to_get_access_token, gt_user_id):
    message_to_log = get_message_to_log(
        function_name='process_access_token()',
        gt_user=User.get_by_id(gt_user_id).name)
    social_network = SocialNetwork.get_by_name(social_network_name)
    social_network_class = get_class(social_network_name, 'social_network')
    access_token, refresh_token = social_network_class.get_access_token(
        social_network,
        code_to_get_access_token)
    if access_token:
        user_credentials = dict(user_id=gt_user_id,
                                social_network_id=social_network.id,
                                access_token=access_token,
                                refresh_token=refresh_token,
                                member_id=None)
        # we have access token, lets save in db
        social_network_class.save_token_in_db(user_credentials)
    else:
        error_message = "Couldn't get access token for %s " % social_network_name
        message_to_log.update({'error': error_message})
        log_error(message_to_log)


def process_event(data, user_id):
        """
        This functions is called from restful POST service (which gets data from
        Event Create Form submission).
        It creates event on vendor as well as saves in database.
        Data in the arguments is the Data coming from Event creation form submission
        user_id is the id of current logged in user (which we get from session).
        """
        function_name = 'process_event()'
        message_to_log = get_message_to_log(function_name=function_name)
        # data = convert_keys_to_camel_case(data)
        if data:
            try:
                social_network_id = data['social_network_id']
                social_network = SocialNetwork.get_by_id(social_network_id)
                # creating class object for respective social network
                social_network_class = get_class(social_network.name.lower(), 'social_network')
                event_class = get_class(social_network.name.lower(), 'event')
                sn = social_network_class(user_id=user_id, social_network_id=social_network.id)
                event_obj = event_class(user=sn.user,
                                        headers=sn.headers,
                                        social_network=social_network)
            except SocialNetworkNotImplemented as e:
                raise
            except Exception as e:
                raise SocialNetworkError('Unable to determine social network. '
                                         'Please verify your data (socialNetworkId)')

            data['user_id'] = user_id
            # converting incoming Datetime object from Form submission into the
            # required format for API call
            try:
                start = data['start_datetime']
                end = data['end_datetime']
                if not all([start, end]):
                    raise
            except Exception as e:
                raise EventInputMissing("DateTimeError: Unable to find datetime inputs")
            try:
                data['start_datetime'] = parse(start)
                data['end_datetime'] = parse(end)
                if data['start_datetime'] < datetime.now() or data['end_datetime'] < datetime.now():
                    raise InvalidDatetime('Invalid DateTime')
            except InvalidDatetime as e:
                raise InvalidDatetime('Invalid DateTime: start_datetime and end_datetime should '
                                      'be in future.')
            except Exception as e:
                raise InvalidDatetime('Invalid DateTime: Kindly specify datetime in ISO format')
            # posting event on social network
            event_obj.gt_to_sn_fields_mappings(data)
            event_id, tickets_id = event_obj.create_event()
            data['tickets_id'] = tickets_id
            if event_id:  # Event has been successfully published on vendor
                # save event in database
                data['social_network_event_id'] = event_id
                gt_event_id = event_obj.save_event(data)
                return gt_event_id
        else:
            error_message = 'Data not received from Event Creation/Edit FORM'
            message_to_log.update({'error': error_message})
            log_error(message_to_log)


def delete_events(user_id, event_ids):
    if event_ids:
        social_networks = {}
        deleted, not_deleted = [], []
        for event_id in event_ids:
            event = Event.get_by_user_and_event_id(user_id, event_id)
            if event:
                social_network = event.socialNetwork
                if social_network.id not in social_networks:
                    social_network_class = get_class(social_network.name.lower(), 'social_network')
                    event_class = get_class(social_network.name.lower(), 'event')
                    sn = social_network_class(user_id=user_id, social_network_id=social_network.id)
                    event_obj = event_class(user_id=user_id,
                                            api_url=social_network.apiUrl,
                                            headers=sn.headers)
                    social_networks[social_network.id] = dict(event_obj=event_obj,
                                                              event_ids=[event_id])
                else:
                    social_networks[social_network.id]['event_ids'].append(event_id)
            else:
                not_deleted.append(event_id)
        for _, social_network in social_networks.items():
            event_obj = social_network['event_obj']
            dltd, nt_dltd = event_obj.delete_events(social_network['event_ids'])
            deleted.extend(dltd)
            not_deleted.extend(nt_dltd)
        return deleted, not_deleted
    else:
        error_message = 'event_ids should contain at least one event id'
        log_error(
            dict(
                functionName='delete_events()',
                error=error_message,
                user=User.get_by_id(user_id).name,
                fileName=__file__
            )
        )


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
    for user_credentials in all_user_credentials:
        social_network = SocialNetwork.get_by_name(user_credentials.social_network.name)
        social_network_class = get_class(social_network.name.lower(), 'social_network')
        # we call social network class here for auth purpose, If token is expired
        # access token is refreshed and we use fresh token
        sn = social_network_class(user_id=user_credentials.user_id,
                                  social_network_id=social_network.id)
        if not user_credentials.member_id:
            # gets an save the member Id of gt-user
            sn.get_member_id(dict())
        job_pool.spawn(sn.process(name_space.mode,
                                  user_credentials=user_credentials))
    job_pool.join()

if __name__ == '__main__':
    try:
        start()
    except TypeError:
        logger.error('Please provide required parameters to run manager')
    except Exception:
        logger.error(traceback.format_exc())
        sys.exit(1)
