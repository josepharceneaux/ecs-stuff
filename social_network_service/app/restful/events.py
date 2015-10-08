import json
import traceback
import types
from flask import Blueprint, request
from flask.ext.restful import Api, Resource
from social_network_service.app.app_utils import api_route, authenticate, ApiResponse
from social_network_service.custom_exections import ApiException
from social_network_service.manager import process_event, delete_events
from common.models.event import Event

events_blueprint = Blueprint('events_api', __name__)
api = Api()
api.init_app(events_blueprint)
api.route = types.MethodType(api_route, api)


@api.route('/events/')
class Events(Resource):
    """
        This resource returns a list of events or it can be used to create event using POST
    """
    @authenticate
    def get(self, **kwargs):
        """
        This action returns a list of user events and their count
        :keyword user_id: user_id of events owner
        :type user_id: int
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
                  "group_id": "18837246",
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
        try:
            # Refresh Session before fetching events from db
            events = map(lambda event: event.to_json(), Event.query.filter_by(user_id=kwargs['user_id']).all())
        except Exception as e:
            return ApiResponse(json.dumps(dict(messsage='APIError: Internal Server error while retrieving records')), status=500)
        if events:
            return {'events': events, 'count': len(events)}, 200
        else:
            return {'events': [], 'count': 0}, 200

    @authenticate
    def post(self, **kwargs):
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
                    "group_id": 18837246,
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
                    452 (Unable to determine Social Network)
                    453 (Some Required event fields are missing)
                    455 (Event not created)
                    456 (Event not Published on Social Network)
                    458 (Event venue not created on Social Network)
                    459 (Tickets for event not created)
                    460 (Event was not save in getTalent database)
                    461 (User credentials of user for Social Network not found)
                    462 (No implementation for specified Social Network)
                    464 (Invalid datetime for event)
                    465 (Specified Venue not found in database)
                    466 (Access token for Social Network has expired)


        :return: id of created event
        """
        # get json post request data
        event_data = request.get_json(force=True)
        try:
            # create event on social network and local database
            gt_event_id = process_event(event_data, kwargs['user_id'])
        except ApiException as err:
            raise
        except Exception as err:
            raise ApiException('APIError: Internal Server error occurred!')
        headers = {'Location': '/events/%s' % gt_event_id}
        resp = ApiResponse(json.dumps(dict(id=gt_event_id)), status=201, headers=headers)
        return resp

    @authenticate
    def delete(self, **kwargs):
        """
        Deletes multiple event whose ids are given in list in request data
        :param kwargs:
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
        .. Status:: 200 (Resource Deleted)
                    207 (Not all deleted)
                    400 (Bad request)
                    500 (Internal Server Error)

        """
        user_id = kwargs['user_id']
        # get event_ids for events to be deleted
        req_data = request.get_json(force=True)
        event_ids = req_data['event_ids'] if 'event_ids' in req_data and isinstance(req_data['event_ids'], list) else []
        # check if event_ids list is not empty
        if event_ids:
            deleted, not_deleted = delete_events(user_id, event_ids)
            if len(not_deleted) == 0:
                return ApiResponse(json.dumps(dict(
                    message='%s Events deleted successfully' % len(deleted))),
                    status=200)

            return ApiResponse(json.dumps(dict(message='Unable to delete %s events' % len(not_deleted),
                                               deleted=deleted,
                                               not_deleted=not_deleted)), status=207)
        return ApiResponse(json.dumps(dict(message='Bad request, include event_ids as list data')), status=400)


@api.route('/events/<int:event_id>')
class EventById(Resource):
    """
    This resource handles event related task for a specific event specified by id
    """

    @authenticate
    def get(self, event_id, **kwargs):
        """
        Returns event object with required id


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
                          "group_id": "18837246",
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
                    400 (Event not found)
                    500 (Internal Server Error)
        :param id: integer, unique id representing event in GT database
        :return: json for required event
        """

        user_id = kwargs['user_id']
        event = Event.get_by_user_and_event_id(user_id, event_id)
        if event:
            try:
                event = event.to_json()
            except Exception as e:
                raise ApiException('Unable to serialize event data')
            return dict(event=event), 200
        raise ApiException('Event does not exist with id %s' % event_id, error_code=400)

    @authenticate
    def post(self, event_id, **kwargs):
        """
        Updates event in GT database and on corresponding social network
        :param event_id: id of event on getTalent database

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
                    "group_id": 18837246,
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

        .. Status:: 204 (Resource Modified)
                    500 (Internal Server Error)
                    401 (Unauthorized to access getTalent)
                    403 (Forbidden: Can not update specified event)
                    452 (Unable to determine Social Network)
                    453 (Some Required event fields are missing)
                    455 (Event not created)
                    456 (Event not Published on Social Network)
                    458 (Event venue not created on Social Network)
                    459 (Tickets for event not created)
                    460 (Event was not save in getTalent database)
                    461 (User credentials of user for Social Network not found)
                    462 (No implementation for specified Social Network)
                    464 (Invalid datetime for event)
                    465 (Specified Venue not found in database)
                    466 (Access token for Social Network has expired)

        """
        user_id = kwargs['user_id']
        event_data = request.get_json(force=True)
        # check whether given event_id exists for this user
        event = Event.get_by_user_id_event_id_social_network_event_id(
            user_id, event_id, event_data['social_network_event_id'])
        if event:
            try:
                process_event(event_data, user_id, method='Update')
            except ApiException as err:
                raise
            except Exception as err:
                print(traceback.format_exc())
                raise ApiException('APIError: Internal Server error!')
            return ApiResponse(json.dumps(dict(message='Event updated successfully')), status=204)
        return ApiResponse(json.dumps(dict(message='Forbidden: You can not edit event for given event_id')),
                           status=403)

    @authenticate
    def delete(self, event_id, **kwargs):
        """
        Removes a single event from GT database and from social network as well.
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
        user_id = kwargs['user_id']
        deleted, not_deleted = delete_events(user_id, [event_id])
        if len(deleted) == 1:
            return ApiResponse(json.dumps(dict(message='Event deleted successfully')), status=200)
        return ApiResponse(json.dumps(dict(message='Forbidden: Unable to delete event')), status=403)


