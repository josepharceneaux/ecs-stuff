import types
from flask import Blueprint
from app.app_utils import authenticate, api_route
from gt_models.social_network import SocialNetwork
from flask.ext.restful import Resource, Api
from gt_models.user import UserCredentials
from event_importer.eventbrite import Eventbrite
from event_importer.meetup import Meetup
from event_importer.facebook_ev import Facebook
from gt_models.event import Event

social_network_blueprint = Blueprint('social_networks_api', __name__)
api = Api()
api.init_app(social_network_blueprint)


api.route = types.MethodType(api_route, api)


@api.route('/social_networks/auth_info')
class SocialNetworksAuthInfo(Resource):
    """
    This resource returns a list of social networks user is subscribed to.
    """


    @authenticate
    def get(self, *args, **kwargs):
        user_id = kwargs.get('user_id') or None
        assert user_id
        # Get list of networks user is subscribed to from UserCredentials table
        subscribed_networks = None
        subscribed_data = UserCredentials.get_by_user_id(user_id=user_id)
        if subscribed_data:
            # Get list of social networks user is subscribed to
            subscribed_networks = SocialNetwork.get_by_ids(
                [data.socialNetworkId for data in subscribed_data]
            )
            # Convert it to JSON
            subscribed_networks = map(lambda sn: sn.to_json(), subscribed_networks)
            for social_network in subscribed_networks:
                user_credential = UserCredentials.get_by_user_and_social_network(
                    user_id, social_network['id']
                )
                if social_network['name'].lower() == 'eventbrite':
                    eb = Eventbrite()
                    eb.user_credential = user_credential
                    if eb.validate_token():
                        social_network['auth_status'] = True
                    else:
                        social_network['auth_status'] = False

                elif social_network['name'].lower() == 'meetup':
                    meetup = Meetup()
                    meetup.user_credential = user_credential
                    if meetup.validate_token():
                        social_network['auth_status'] = True
                    else:
                        social_network['auth_status'] = False

                elif social_network['name'].lower() == 'facebook':
                    facebook = Facebook()
                    facebook.user_credential = user_credential
                    if facebook.validate_token():
                        social_network['auth_status'] = True
                    else:
                        social_network['auth_status'] = False
        subscribed_networks = subscribed_networks or []
        return {
                'auth_info': subscribed_networks
            }



@api.route('/social_networks/')
class SocialNetworks(Resource):
    """
        This resource returns a list of events or it can be used to create event using POST
    """

    def set_is_subscribed(self, dicts, value=False):
        for dict in dicts:
            dict['is_subscribed'] = value
        return dicts

    @authenticate
    def get(self, *args, **kwargs):
        """
        This action returns a list of user events.
        """
        user_id = kwargs.get('user_id') or None
        assert user_id
        # Get list of networks user is subscribed to from UserCredentials table
        subscribed_networks = None
        subscribed_data = UserCredentials.get_by_user_id(user_id=user_id)
        if subscribed_data:
            # Get list of social networks user is subscribed to
            subscribed_networks = SocialNetwork.get_by_ids(
                [data.socialNetworkId for data in subscribed_data]
            )
            # Convert it to JSON
            subscribed_networks = map(lambda sn: sn.to_json(), subscribed_networks)
            # Add 'is_subscribed' key in each object and set it to True because
            # these are the social networks user is subscribed to
            subscribed_networks = self.set_is_subscribed(subscribed_networks, value=True)
        # Get list of social networks user is not subscribed to
        unsubscribed_networks = SocialNetwork.get_all_except_ids(
            [data.socialNetworkId for data in subscribed_data ]
        )
        if unsubscribed_networks:
            unsubscribed_networks = map(lambda sn: sn.to_json(), unsubscribed_networks)
            # Add 'is_subscribed' key in each object and set it to False
            unsubscribed_networks = self.set_is_subscribed(unsubscribed_networks, value=False)
        # Now merge both subscribed and unsubscribed networks
        all_networks = []
        if subscribed_networks:
            all_networks.extend(subscribed_networks)
        if unsubscribed_networks:
            all_networks.extend(unsubscribed_networks)
        if all_networks:
            return {'social_networks': all_networks}
        else:
            return {'social_networks': []}
