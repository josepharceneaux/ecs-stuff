from datetime import datetime
from dateutil.parser import parse
from SocialNetworkService.base import SocialNetworkBase
from SocialNetworkService.custom_exections import SocialNetworkError, SocialNetworkNotImplemented, InvalidDatetime
from common.gt_models.social_network import SocialNetwork
from SocialNetworkService.utilities import get_class, get_message_to_log, log_error


def process_access_token(social_network_name, code_to_get_access_token, gt_user_id):
    message_to_log = get_message_to_log(function_name='process_access_token()',
                                        gt_user_id=gt_user_id)
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
            except  Exception as e:
                raise SocialNetworkError('Unable to determine social network. Please verify your data (socialNetworkId)')

            data['userId'] = user_id
            # converting incoming Datetime object from Form submission into the
            # required format for API call
            try:
                data['eventStartDatetime'] = parse(data['eventStartDatetime'])
                data['eventEndDatetime'] = parse(data['eventEndDatetime'])
                if data['eventStartDatetime'] < datetime.now() or data['eventEndDatetime'] < datetime.now():
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
                event_obj.save_event(data)
        else:
            error_message = 'Data not received from Event Creation/Edit FORM'
            message_to_log.update({'error': error_message})
            log_error(message_to_log)



# def event_importer():
#     member_id = get_member_id(social_network, access_token)
