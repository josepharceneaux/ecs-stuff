import json
import types
from flask import Blueprint
from SocialNetworkService.app.app_utils import authenticate, api_route, ApiResponse
from flask.ext.restful import Resource, Api
from SocialNetworkService.meetup import Meetup

from common.gt_models.user import UserCredentials
from common.gt_models.social_network import SocialNetwork

social_network_blueprint = Blueprint('social_network_api', __name__)
api = Api()
api.init_app(social_network_blueprint)
api.route = types.MethodType(api_route, api)


@api.route('/social_networks/')
class SocialNetworks(Resource):
    """
        This resource returns a list of social networks
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
        print args, kwargs
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


@api.route('/social_networks/groups/')
class MeetupGroups(Resource):
    """
        This resource returns a list of user's admin groups for Meetup
    """

    @authenticate
    def get(self, *args, **kwargs):
        """
        This action returns a list of user events.
        """
        user_id = kwargs['user_id']
        try:
            meetup_db = SocialNetwork.get_by_name('Meetup')
            meetup = Meetup(user_id=user_id, social_network_id=meetup_db.id)
            groups = meetup.get_groups()
            resp = json.dumps(dict(groups=groups))
        except Exception as e:
            return ApiResponse(json.dums(dict(message='APIError: Internal Server Error')), status=500)
        return ApiResponse(resp, status=200)


# @api.route('/social_networks/authInfo')
# class SocialNetworkGroups(Resource):
#     """
#         This resource returns a list of user auth info (validity of token)
#     """
#
#     @authenticate
#     def get(self, *args, **kwargs):
#         """
#         This action returns a list of user events.
#         """
#         user_id = kwargs['user_id']
#         try:
#             meetup_db = SocialNetwork.get_by_name('Meetup')
#             meetup = Meetup(user_id=user_id, social_network_id=meetup_db.id)
#             groups = meetup.get_groups()
#         except Exception as e:
#             return ApiResponse(json.dums(dict(message='APIError: Internal Server Error')), status=500)
#         return ApiResponse(json.dums(dict(groups=groups)), status=200)