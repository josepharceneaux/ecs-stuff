import types
from app.app_utils import api_route, authenticate
from gt_models.event import Event
from flask import Blueprint
from flask.ext.restful import Api, Resource

events_blueprint = Blueprint('events_api', __name__)
api = Api()
api.init_app(events_blueprint)


api.route = types.MethodType(api_route, api)


class Resource(Resource):
    method_decorators = [authenticate]


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
        events = map(lambda event: event.to_json(), Event.query.filter_by(userId=kwargs['user_id']).all())
        if events:
            return {'events': events}, 200
        else:
            return {'events': []}, 200

    @authenticate
    def post(self, **kwargs):
        """
        This method takes data to create event in local database as well as on corresponding social network.
        :return: id of created event
        """
        # data = request.values
        return dict(id=1), 201


@api.route('/events/<int:event_id>')
class EventById(Resource):

    @authenticate
    def get(self, event_id, **kwargs):
        """
        Returns event object with required id
        :param id: integer, unique id representing event in GT database
        :return: json for required event
        """
        return dict(event={}), 200

    @authenticate
    def post(self, **kwargs):
        """
        Updates event in GT database and on corresponding social network
        :param id:
        """
        return None, 204

    @authenticate
    def delete(self, **kwargs):
        """
        Removes event from GT database and from social network as well.
        :param id: (Integer) unique id in Event table on GT database.
        """
        return None, 200


