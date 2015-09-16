import json
from dateutil.parser import parse
import requests
from event_manager import logger

from gt_models.social_network import SocialNetwork

EVENTBRITE = SocialNetwork.get_by_name('Eventbrite')
MEETUP = SocialNetwork.get_by_name('Meetup')
FACEBOOK = SocialNetwork.get_by_name('Facebook')


class EventInputMissing(Exception):
    pass


class EventNotSaved(Exception):
    pass


class EventNotCreated(Exception):
    pass


class EventNotPublished(Exception):
    pass


class EventNotUnpublished(Exception):
    pass


class EventLocationNotCreated(Exception):
    pass


class TicketsNotCreated(Exception):
    pass


class EventNotSaveInDb(Exception):
    pass


class UserCredentialsNotFound(Exception):
    pass


class SocialNetworkNotImplemented(Exception):
    pass


class InvalidAccessToken(Exception):
    pass


def _get_message_to_log(function_name='', error='', class_name=''):
    """
    Here we define descriptive message to be used for logging purposes
    :param function_name:
    :param error:
    :param class_name:
    :return:
    """
    message_to_log = {
        'user': '',  # TODO: replace it with actual user name
        'class': class_name,
        'fileName': 'TalentEventsAPI.py',
        'functionName': function_name,
        'error': error}
    return message_to_log


def _log_exception(message_dict):
    """
    This function logs exception when it is called inside a catch block
    where ever it is called using message_dict as descriptive message to log.
    :param message_dict:
    :return:
    """
    message_to_log = ("Reason: %(error)s \n"
                      "functionName: %(functionName)s, "
                      "fileName: %(fileName)s, "
                      "User: %(user)s" % message_dict)
    if message_dict.get('class'):
        message_to_log += ", class: %(class)s" % message_dict
    logger.exception(message_to_log)


def _log_error(message_dict):
    """
    This function logs error using message_dict as descriptive message to log.
    :param message_dict:
    :return:
    """
    message_to_log = ("Reason: %(error)s \n"
                      "functionName: %(functionName)s, "
                      "fileName: %(fileName)s, "
                      "User: %(user)s" % message_dict)
    if message_dict.get('class'):
        message_to_log += ", class: %(class)s" % message_dict
    logger.error(message_to_log)


def http_request(method_type, url, params=None, headers=None, data=None, message_to_log=None):
    """
    This is common function to make HTTP Requests. It takes method_type (GET or POST)
    and makes call on given URL. It also handles/logs exception.
    :param method_type: GET or POST.
    :param url: resource URL.
    :param params: params to be sent in URL.
    :param headers: headers for Authorization.
    :param data: data to be sent.
    :param message_to_log: descriptive message to log when exception occurs.
    :return:
    """
    if method_type in ['GET', 'POST']:
        method = getattr(requests, method_type.lower())
        error_message = None
        if url:
            try:
                response = method(url, params=params, headers=headers, data=data)
                # If we made a bad request (a 4XX client error or 5XX server error response),
                # we can raise it with Response.raise_for_status():"""
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if 'errors' in e.response.json():
                    error_message = e.message + ' , Details: ' \
                                    + json.dumps(e.response.json().get('errors'))
                else:
                    error_message = e.message
            except requests.RequestException as e:
                error_message = e.message
            if error_message and message_to_log:
                message_to_log.update({'error': error_message})
                _log_exception(message_to_log)
            return response
        else:
            error_message = 'URL is None. Unable to make %s Call' % method_type
            logger.error(error_message)
    else:
        logger.error('Unknown Method type %s ' % method_type)


def process_event(data, user_id):
    """
    This functions is called from restful POST service (which gets data from
    Event Create Form submission).
    It creates event on vendor as well as saves in database.
    Data in the arguments is the Data coming from Event creation form submission
    user_id is the id of current logged in user (which we get from session).
    """
    function_name = 'process_event()'
    message_to_log = _get_message_to_log(function_name=function_name)
    if data:
        vendor_id = data['socialNetworkId']
        social_network = SocialNetwork.get_by_id(vendor_id)
        data['user_id'] = user_id
        # converting incoming Datetime object from Form submission into the
        # required format for API call
        data['eventStartDatetime'] = parse(data['eventStartDatetime'])
        data['eventEndDatetime'] = parse(data['eventEndDatetime'])
        # creating class object for respective social network
        if social_network.name == EVENTBRITE.name:
            from event_exporter.eventbrite import Eventbrite
            class_object = Eventbrite()
        elif social_network.name == MEETUP.name:
            from event_exporter.meetup import Meetup
            class_object = Meetup()
        else:
            error_message = 'Social Network "%s" is not allowed for now, ' \
                            'please implement code for this social network.' \
                            % social_network.name
            message_to_log.update({'error': error_message})
            _log_error(message_to_log)
            raise SocialNetworkNotImplemented
        # posting event on social network
        class_object.get_mapped_data(data)
        event_id, tickets_id = class_object.create_event()
        data['ticketsId'] = tickets_id
        if event_id:  # Event has been successfully published on vendor
            # save event in database
            save_event(event_id, data)
    else:
        error_message = 'Data not received from Event Creation/Edit FORM'
        message_to_log.update({'error': error_message})
        _log_error(message_to_log)


def save_event(event_id, data):
    """
    This function serves the storage of event in database after it is
    successfully published.
    :param event_id:
    :param data:
    :return:
    """
    function_name = 'save_event()'
    message_to_log = _get_message_to_log(function_name=function_name)
    db_data = data
    # try:
    #     inserted_record_id = db.event.update_or_insert(
    #         ((db.event.vendorEventId == event_id) &
    #          (db.event.socialNetworkId == db_data['socialNetworkId'])),
    #         eventTitle=db_data['eventTitle'],
    #         eventDescription=db_data['eventDescription'],
    #         socialNetworkId=db_data['socialNetworkId'],
    #         userId=db_data['user_id'],
    #         eventStartDatetime=db_data['eventStartDatetime'],
    #         eventEndDatetime=db_data['eventEndDatetime'],
    #         vendorEventId=event_id,
    #         groupId=db_data['groupId'],
    #         groupUrlName=db_data['groupUrlName'],
    #         ticketsId=db_data['ticketsId'],
    #         eventAddressLine1=db_data['eventAddressLine1'],
    #         eventAddressLine2=db_data['eventAddressLine2'],
    #         eventState=db_data['eventState'],
    #         eventCity=db_data['eventCity'],
    #         eventZipCode=db_data['eventZipCode'],
    #         eventCountry=db_data['eventCountry'],
    #         organizerName=db_data['organizerName'],
    #         organizerEmail=db_data['organizerEmail'],
    #         aboutEventOrganizer=db_data['aboutEventOrganizer'],
    #         registrationInstruction=db_data['registrationInstruction'],
    #         eventCost=db_data['eventCost'],
    #         maxAttendees=db_data['maxAttendees'],
    #         eventLongitude=db_data['eventLongitude'],
    #         eventLatitude=db_data['eventLatitude'],
    #         eventCurrency=db_data['eventCurrency'],
    #         eventTimeZone=db_data['eventTimeZone'],
    #     )
    #     db.commit()
    #     logger.info('|  Event has been saved in Database  |')
    # except Exception as e:
    #     error_message = 'Event was not saved in Database\nError: %s' % str(e)
    #     message_to_log.update({'error': error_message})
    #     _log_error(message_to_log)
    #     raise EventNotSaveInDb
    # return inserted_record_id
