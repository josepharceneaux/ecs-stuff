from app.app import api, api_route
from gt_models.social_network import SocialNetwork
from flask.ext.restful import Resource


@api.route('/social_networks/')
class SocialNetwork(Resource):
    """
        This resource returns a list of events or it can be used to create event using POST
    """

    def get(self):
        """
        This action returns a list of user events.
        """
        social_networks = map(lambda sn: sn.to_json(), SocialNetwork.query.filter_by(userId=1).all())
        if social_networks:
            return {'social_networks': social_networks}
        else:
            return {'social_networks': []}

