import json
import types
from flask import Blueprint, request
from flask.ext.restful import Api, Resource
from SocialNetworkService.app.app_utils import api_route, authenticate, ApiResponse
from SocialNetworkService.custom_exections import ApiException
from SocialNetworkService.manager import process_event, delete_events
from SocialNetworkService.utilities import convert_keys_to_camel_case
from common.gt_models.event import Event

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
        This action returns a list of user events.
        """
        # raise InvalidUsage('Not authorized', status_code=401)
        events = map(lambda event: event.to_json_(), Event.query.filter_by(userId=kwargs['user_id']).all())
        if events:
            return {'events': events, 'events_cont': len(events)}, 200
        else:
            return {'events': [], 'events_cont': 0}, 200

    @authenticate
    def post(self, **kwargs):
        """
        This method takes data to create event in local database as well as on corresponding social network.
        :return: id of created event
        """
        event_data = request.get_json(force=True)
        event_data = convert_keys_to_camel_case(event_data)
        try:
            gt_event_id = process_event(event_data, kwargs['user_id'])
        except ApiException as err:
            raise
        except Exception as err:
            raise ApiException('APIError: Internal Server error occurred!', status_code=500)
        headers = {'Location': '/events/%s' % gt_event_id}
        resp = ApiResponse(json.dumps(dict(id=gt_event_id)), status=201, headers=headers)
        return resp

    @authenticate
    def delete(self, **kwargs):
        user_id = kwargs['user_id']
        req_data = request.get_json(force=True)
        event_ids = req_data['event_ids'] if 'event_ids' in req_data and isinstance(req_data['event_ids'], list) else []
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

    @authenticate
    def get(self, event_id, **kwargs):
        """
        Returns event object with required id
        :param id: integer, unique id representing event in GT database
        :return: json for required event
        """
        user_id = kwargs['user_id']
        event = Event.get_by_user_and_event_id(user_id, event_id)
        if event:
            try:
                event = event.to_json_()
            except Exception as e:
                raise ApiException('Unable to serialize event data', status_code=500)
            return dict(event=event), 200
        raise ApiException('Event does not exist with id %s' % event_id, status_code=400)

    @authenticate
    def post(self, event_id, **kwargs):
        """
        Updates event in GT database and on corresponding social network
        :param id:
        """
        user_id = kwargs['user_id']
        event_data = request.get_json(force=True)
        # check whether given event_id exists for this user
        event = Event.get_by_user_and_event_id(user_id, event_id)
        if event:
            try:
                process_event(event_data, user_id)
            except ApiException as err:
                raise
            except Exception as err:
                raise ApiException('APIError: Internal Server error!', status_code=500)
            return ApiResponse(json.dumps(message='Event updated successfully'), status=204)
        return ApiResponse(json.dumps(dict(message='Forbidden: You can not edit event for given event_id')),
                           status=403)

    @authenticate
    def delete(self, event_id, **kwargs):
        """
        Removes a single event from GT database and from social network as well.
        :param id: (Integer) unique id in Event table on GT database.
        """
        user_id = kwargs['user_id']
        deleted, not_deleted = delete_events(user_id, [event_id])
        if len(deleted) == 1:
            return ApiResponse(json.dumps(dict(message='Event deleted successfully')), status=200)
        return ApiResponse(json.dumps(dict(message='Forbidden: Unable to delete event')), status=403)


