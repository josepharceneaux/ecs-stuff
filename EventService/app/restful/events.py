from app.app import api
from gt_models.event import Event
from flask.ext.restful import Resource


@api.route('/events/')
class EventList(Resource):
    """
        This resource returns a list of events or it can be used to create event using POST
    """

    def get(self):
        """
        This action returns a list of user events.
        """
        events = Event.query.filter_by(userId=1).all()
        if events:
            return {'events': events.to_json()}
        else:
            return {'events': []}

