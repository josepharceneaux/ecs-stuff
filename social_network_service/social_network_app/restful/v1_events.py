"""
This file contains list of all API endpoints related to events.
"""
# Standard imports
import types

# 3rd party imports
from flask.ext.cors import CORS
from flask import Blueprint, request
from flask.ext.restful import Resource

# Application specific imports
from social_network_service.common.error_handling import *
from social_network_service.common.models.event import Event
from social_network_service.common.talent_api import TalentApi
from social_network_service.common.routes import SocialNetworkApi
from social_network_service.modules.utilities import add_organizer_venue_data
from social_network_service.common.utils.auth_utils import require_oauth
from social_network_service.modules.utilities import process_event, delete_events
from social_network_service.common.utils.api_utils import api_route, ApiResponse
from social_network_service.common.utils.handy_functions import get_valid_json_data


events_blueprint = Blueprint('events_api', __name__)
api = TalentApi()
api.init_app(events_blueprint)
api.route = types.MethodType(api_route, api)


@api.route(SocialNetworkApi.EVENTS)
class Events(Resource):
    """
        This resource returns a list of events or it can be used to create event using POST.
    """
    decorators = [require_oauth()]

    def get(self):
        """
        This action returns a list of user events and their count
        :return events_data: a dictionary containing list of events and their count
        :rtype json

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.get(API_URL + '/events/', headers=headers)

        .. Response::

            {
              "count": 1,
              "events": [
                {
                  "cost": 0,
                  "currency": "USD",
                  "description": "Test Event Description",
                  "end_datetime": "2015-10-30 16:51:00",
                  "social_network_group_id": "18837246",
                  "group_url_name": "QC-Python-Learning",
                  "id": 189,
                  "max_attendees": 10,
                  "organizer_id": 1,
                  "registration_instruction": "Just Come",
                  "social_network_event_id": "18970807195",
                  "social_network_id": 18,
                  "start_datetime": "2015-10-25 16:50:00",
                  "tickets_id": "39836307",
                  "timezone": "Asia/Karachi",
                  "title": "Test Event",
                  "url": "",
                  "user_id": 1,
                  "venue_id": 2
                }
              ]
            }

        .. Status:: 200 (OK)
                    500 (Internal Server Error)

        """
        data = request.values
        limit = data.get('limit', 30)
        offset = data.get('offset', 0)
        events = request.user.events.order_by(Event.start_datetime.desc())\
            .limit(limit).offset(offset).all()
        events = map(add_organizer_venue_data, events)
        if events:
            return dict(events=events, count=len(events)), 200
        else:
            return dict(events=[], count=0), 200

    def post(self):
        """
        This method takes data to create event in local database as well as on corresponding social network.

        :Example:
            event_data = {
                    "organizer_id": 1,
                    "venue_id": 2,
                    "title": "Test Event",
                    "description": "Test Event Description",
                    "registration_instruction": "Just Come",
                    "end_datetime": "30 Oct, 2015 04:51 pm",
                    "group_url_name": "QC-Python-Learning",
                    "social_network_id": 18,
                    "timezone": "Asia/Karachi",
                    "cost": 0,
                    "start_datetime": "25 Oct, 2015 04:50 pm",
                    "currency": "USD",
                    "social_network_group_id": 18837246,
                    "max_attendees": 10
            }

            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }
            data = json.dumps(event_data)
            response = requests.post(
                                        API_URL + '/events/',
                                        data=data,
                                        headers=headers,
                                    )

        .. Response::

            {
                id: 123232
            }
        .. Status:: 201 (Resource Created)
                    500 (Internal Server Error)
                    401 (Unauthorized to access getTalent)

        .. Error codes:
                    In case of internal server error, response contains error code which can be
                    4052 (Unable to determine Social Network)
                    4053 (Some required event fields are missing)
                    4055 (Event not created)
                    4056 (Event not Published on Social Network)
                    4058 (Event venue not created on Social Network)
                    4059 (Tickets for event not created)
                    4060 (Event was not saved in getTalent database)
                    4061 (User credentials of user for Social Network not found)
                    4062 (No implementation for specified Social Network)
                    4064 (Invalid datetime for event)
                    4065 (Specified Venue not found in database)
                    4066 (Access token for Social Network has expired)


        :return: id of created event
        """
        # get json post request data
        event_data = get_valid_json_data(request)
        gt_event_id = process_event(event_data, request.user.id)
        headers = {'Location': '/%s/events/%s' % (SocialNetworkApi.VERSION, gt_event_id)}
        return ApiResponse(dict(id=gt_event_id), status=201, headers=headers)

    def delete(self):
        """
        Deletes multiple event whose ids are given in list in request data.
        :return:

        :Example:
            event_ids = {
                'ids': [1,2,3]
            }
            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }
            data = json.dumps(event_ids)
            response = requests.post(
                                        API_URL + '/events/',
                                        data=data,
                                        headers=headers,
                                    )

        .. Response::

            {
                'message': '3 Events have been deleted successfully'
            }
        .. Status:: 200 (Resource deleted)
                    207 (Not all deleted)
                    400 (Bad request)
                    500 (Internal Server Error)

        """
        # get event_ids for events to be deleted
        req_data = get_valid_json_data(request)
        event_ids = req_data['ids'] if 'ids' in req_data and isinstance(req_data['ids'], list) else []
        # check if event_ids list is not empty
        if event_ids:
            deleted, not_deleted = delete_events(request.user.id, event_ids)
            if len(not_deleted) == 0:
                return dict(message='%s Events deleted successfully' % len(deleted)), 200

            return dict(message='Unable to delete %s events' % len(not_deleted),
                        deleted=deleted,
                        not_deleted=not_deleted), 207
        raise InvalidUsage('Bad request, include event_ids as list data')


@api.route(SocialNetworkApi.EVENT)
class EventById(Resource):
    """
    This resource handles event related task for a specific event specified by id
    """
    decorators = [require_oauth()]

    def get(self, id):
        """
        Returns event object with required id
        :param id: (Integer) unique id in Event table on GT database.

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            event_id = 1
            response = requests.get(API_URL + '/events/' + str(event_id), headers=headers)

        .. Response::

            {
              "event": {
                          "cost": 0,
                          "currency": "USD",
                          "description": "Test Event Description",
                          "end_datetime": "2015-10-30 16:51:00",
                          "social_network_group_id": "18837246",
                          "group_url_name": "QC-Python-Learning",
                          "id": 1,
                          "max_attendees": 10,
                          "organizer_id": 1,
                          "registration_instruction": "Just Come",
                          "social_network_event_id": "18970807195",
                          "social_network_id": 18,
                          "start_datetime": "2015-10-25 16:50:00",
                          "tickets_id": "39836307",
                          "timezone": "Asia/Karachi",
                          "title": "Test Event",
                          "url": "",
                          "user_id": 1,
                          "venue_id": 2
                        }

            }

        .. Status:: 200 (OK)
                    404 (Event not found)
                    500 (Internal Server Error)
        :param id: integer, unique id representing event in GT database
        :return: json for required event
        """
        event = Event.get_by_user_and_event_id(request.user.id, id)
        if event:
            event_data = add_organizer_venue_data(event)
            return dict(event=event_data), 200
        raise ResourceNotFound('Event does not exist with id %s' % id)

    def put(self, id):
        """
        Updates event in getTalent's database and on corresponding social network.
        :param id: id of event on getTalent database

        :Example:

            event_data = {
                    "organizer_id": 1,
                    "venue_id": 2,
                    "title": "Test Event",
                    "description": "Test Event Description",
                    "registration_instruction": "Just Come",
                    "end_datetime": "30 Oct, 2015 04:51 pm",
                    "group_url_name": "QC-Python-Learning",
                    "social_network_id": 18,
                    "timezone": "Asia/Karachi",
                    "cost": 0,
                    "start_datetime": "25 Oct, 2015 04:50 pm",
                    "currency": "USD",
                    "social_network_group_id": 18837246,
                    "max_attendees": 10
            }

            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }
            data = json.dumps(event_data)
            event_id = event_data['id']
            response = requests.post(
                                        API_URL + '/events/' + str(event_id)',
                                        data=data,
                                        headers=headers,
                                    )

        .. Response::

            No Content

        .. Status:: 200 (Resource Modified)
                    500 (Internal Server Error)
                    401 (Unauthorized to access getTalent)
                    403 (Forbidden: Can not update specified event)

        .. Error codes (returned in response's body):
                    In case of internal server error, response contains error code which can be

                    4052 (Unable to determine Social Network)
                    4053 (Some Required event fields are missing)
                    4055 (Event not created)
                    4056 (Event not Published on Social Network)
                    4058 (Event venue not created on Social Network)
                    4059 (Tickets for event not created)
                    4060 (Event was not save in getTalent database)
                    4061 (User credentials of user for Social Network not found)
                    4062 (No implementation for specified Social Network)
                    4064 (Invalid datetime for event)
                    4065 (Specified Venue not found in database)
                    4066 (Access token for Social Network has expired)

        """
        event_data = get_valid_json_data(request)
        # check whether given event_id exists for this user
        event = Event.get_by_user_id_event_id_social_network_event_id(
            request.user.id, id, event_data['social_network_event_id'])
        if event:
            process_event(event_data, request.user.id, method='Update')
            return dict(message='Event updated successfully'), 200
        raise ResourceNotFound('Event not found')

    def delete(self, id):
        """
        Removes a single event from getTalent's database and from social network as well.
        :param id: (Integer) unique id in Event table on GT database.

        :Example:
            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }
            event_id = 1
            response = requests.post(
                                        API_URL + '/events/' + str(event_id),
                                        headers=headers,
                                    )

        .. Response::

            {
                'message': 'Event has been deleted successfully'
            }
        .. Status:: 200 (Resource Deleted)
                    403 (Forbidden: event not found for this user)
                    500 (Internal Server Error)
        """
        deleted, not_deleted = delete_events(request.user.id, [id])
        if len(deleted) == 1:
            return dict(message='Event deleted successfully'), 200
        raise ForbiddenError('Forbidden: Unable to delete event')

