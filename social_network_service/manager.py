import sys
import os
from gt_common.models.config import GTSQLAlchemy
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
from gt_common.models.user import UserCredentials
from gt_common.models.social_network import SocialNetwork
from utilities import get_class, get_message_to_log, log_error, convert_keys_to_camel_case
from social_network_service.custom_exections import SocialNetworkError, \
    SocialNetworkNotImplemented, InvalidDatetime, EventInputMissing
logger = logging.getLogger('event_service.app')

POOL_SIZE = 5


def process_access_token(social_network_name, code_to_get_access_token, gt_user_id):
    social_network = SocialNetwork.get_by_name(social_network_name)
    user_credentials = UserCredentials.get_by_user_and_social_network_id(
        gt_user_id, social_network.id)
    message_to_log = get_message_to_log(
        function_name='process_access_token()',
        gt_user=user_credentials.user.firstName + ' ' + user_credentials.user.lastName)
    social_network = SocialNetwork.get_by_name(social_network_name)
    social_network_class = get_class(social_network_name, 'social_network')
    access_token, refresh_token = social_network_class.get_access_token(
        social_network,
        code_to_get_access_token)
    if access_token:
        user_credentials = dict(userId=gt_user_id,
                                socialNetworkId=social_network.id,
                                accessToken=access_token,
                                refreshToken=refresh_token,
                                memberId=None)
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
        data = convert_keys_to_camel_case(data)
        if data:
            try:
                vendor_id = data['socialNetworkId']
                social_network = SocialNetwork.get_by_id(vendor_id)
                # creating class object for respective social network
                social_network_class = get_class(social_network.name.lower(), 'social_network')
                event_class = get_class(social_network.name.lower(), 'event')
                sn = social_network_class(user_id=user_id, social_network_id=social_network.id)
                event_obj = event_class(user_id=user_id,
                                        api_url=social_network.apiUrl,
                                        headers=sn.headers)
            except SocialNetworkNotImplemented as e:
                raise
            except Exception as e:
                raise SocialNetworkError('Unable to determine social network. '
                                         'Please verify your data (socialNetworkId)')

            data['userId'] = user_id
            # converting incoming Datetime object from Form submission into the
            # required format for API call
            try:
                start = data['eventStartDatetime']
                end = data['eventEndDatetime']
                if not all([start, end]):
                    raise
            except Exception as e:
                raise EventInputMissing("DateTimeError: Unable to find datetime inputs")
            try:
                data['eventStartDatetime'] = parse(start)
                data['eventEndDatetime'] = parse(end)
                if data['eventStartDatetime'] < datetime.now() or data['eventEndDatetime'] < datetime.now():
                    raise InvalidDatetime('Invalid DateTime')
            except InvalidDatetime as e:
                raise InvalidDatetime('Invalid DateTime: eventStartDatetime and eventEndDatetime should '
                                      'be in future.')
            except Exception as e:
                raise InvalidDatetime('Invalid DateTime: Kindly specify datetime in ISO format')
            # posting event on social network
            event_obj.gt_to_sn_fields_mappings(data)
            event_id, tickets_id = event_obj.create_event()
            data['ticketsId'] = tickets_id
            if event_id:  # Event has been successfully published on vendor
                # save event in database
                data['vendorEventId'] = event_id
                gt_event_id = event_obj.save_event(data)
                return gt_event_id
        else:
            error_message = 'Data not received from Event Creation/Edit FORM'
            message_to_log.update({'error': error_message})
            log_error(message_to_log)


def delete_events(user_id, event_ids):
    assert len(event_ids) > 0, 'event_ids should contain at least one event id'
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
    for user_credentials in all_user_credentials:
        social_network = SocialNetwork.get_by_name(user_credentials.social_network.name)
        social_network_class = get_class(social_network.name.lower(), 'social_network')
        event_or_rsvp_class = get_class(social_network.name.lower(), name_space.mode)
        # we call social network class here for auth purpose, If token is expired
        # access token is refreshed and we use fresh token
        sn = social_network_class(user_id=user_credentials.userId,
                                  social_network_id=social_network.id)
        if not user_credentials.memberId:
            # get an save the member Id of gt-user
            sn.get_member_id(dict())
        event_or_rsvp_obj = event_or_rsvp_class(user_credentials=user_credentials,
                                                social_network=social_network,
                                                headers=sn.headers)
        if name_space.mode == 'event':
            job_pool.spawn(event_or_rsvp_obj._process_events)
        elif name_space.mode == 'rsvp':
            job_pool.spawn(event_or_rsvp_obj._process_rsvps)
    job_pool.join()

if __name__ == '__main__':
    try:
        start()
    except TypeError:
        logger.error('Please provide required parameters to run manager')
    except Exception:
        logger.error(traceback.format_exc())
        sys.exit(1)
