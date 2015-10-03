import json
import types
from flask import Blueprint, request
from common.models.organizer import Organizer
from common.models.venue import Venue
from social_network_service.app.app_utils import authenticate, api_route, ApiResponse
from flask.ext.restful import Resource, Api
from social_network_service.meetup import Meetup

from common.models.user import UserCredentials
from common.models.social_network import SocialNetwork
from social_network_service.utilities import get_class

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
                [data.social_network_id for data in subscribed_data]
            )
            # Convert it to JSON
            subscribed_networks = map(lambda sn: sn.to_json(), subscribed_networks)
            # Add 'is_subscribed' key in each object and set it to True because
            # these are the social networks user is subscribed to
            subscribed_networks = self.set_is_subscribed(subscribed_networks, value=True)
        # Get list of social networks user is not subscribed to
        unsubscribed_networks = SocialNetwork.get_all_except_ids(
            [data.social_network_id for data in subscribed_data ]
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
            return ApiResponse(json.dumps(dict(message='APIError: Internal Server Error')), status=500)
        return ApiResponse(resp, status=200)


@api.route('/social_network/refresh_token/')
class RefreshToken(Resource):
    """
        This resource refreshes access token for given social network for given user
    """

    @authenticate
    def post(self, *args, **kwargs):
        """
        Creates a venue for this user
        :return:
        """
        user_id = kwargs['user_id']
        try:
            data = request.get_json(force=True)
            data['user_id'] = user_id
            social_network_id = data['social_network_id']
            social_network = SocialNetwork.get_by_id(social_network_id)
            # creating class object for respective social network
            social_network_class = get_class(social_network.name.lower(), 'social_network')
            sn = social_network_class(user_id=user_id, social_network_id=social_network.id)
            status = sn.refresh_access_token()
        except Exception as e:
            return ApiResponse(json.dumps(dict(messsage='APIError: Internal Server error..')), status=500)
        if status:
            return ApiResponse(json.dumps(dict(messsage='Access token has been refreshed',
                                               status=True)), status=200)
        else:
            return ApiResponse(json.dumps(dict(messsage='Unable to refresh access_token',
                                               status=False)), status=200)


# @api.route('/social_networks/authInfo')
# class SocialNetworkGroups(Resource):
#     """
#         This resource returns a list of user admin group list on Meetup.com
#     """
#
#     @authenticate
#     def get(self, *args, **kwargs):
#         """
#         This action returns a list of user groups.
#         """
#         user_id = kwargs['user_id']
#         try:
#             meetup_db = SocialNetwork.get_by_name('Meetup')
#             meetup = Meetup(user_id=user_id, social_network_id=meetup_db.id)
#             groups = meetup.get_groups()
#         except Exception as e:
#             return ApiResponse(json.dums(dict(message='APIError: Internal Server Error')), status=500)
#         return ApiResponse(json.dumps(dict(groups=groups)), status=200)


@api.route('/venues/')
class Venues(Resource):
    """
        This resource returns a list of user's created venues
    """

    @authenticate
    def get(self, *args, **kwargs):
        """
        This action returns a list of user venues.
        """
        user_id = kwargs['user_id']
        try:
            venues = map(lambda venue: venue.to_json(), Venue.get_by_user_id(user_id=user_id))
            resp = json.dumps({'venues': venues, 'count': len(venues)})
        except Exception as e:
            return ApiResponse(json.dumps(dict(messsage='APIError: Internal Server error..')), status=500)
        return ApiResponse(resp, status=200)

    @authenticate
    def post(self, *args, **kwargs):
        """
        Creates a venue for this user
        :return:
        """
        user_id = kwargs['user_id']
        try:
            venue_data = request.get_json(force=True)
            venue_data['user_id'] = user_id
            venue = Venue(**venue_data)
            Venue.save(venue)
        except Exception as e:
            return ApiResponse(json.dumps(dict(messsage='APIError: Internal Server error..')), status=500)
        return ApiResponse(json.dumps(dict(messsage='Venue created successfully', id=venue.id)), status=201)

    @authenticate
    def delete(self, **kwargs):
        user_id = kwargs['user_id']
        deleted, not_deleted = [], []
        req_data = request.get_json(force=True)
        venue_ids = req_data['ids'] if 'ids' in req_data and isinstance(req_data['ids'], list) else []
        if venue_ids:
            for _id in venue_ids:
                venue = Venue.get_by_user_id_venue_id(user_id, _id)
                if venue:
                    Venue.delete(_id)
                    deleted.append(_id)
                else:
                    not_deleted.append(_id)

                if len(not_deleted) == 0:
                    return ApiResponse(json.dumps(dict(
                        message='%s Venue/s deleted successfully' % len(deleted))),
                        status=200)

                return ApiResponse(json.dumps(dict(message='Unable to delete %s venue/s' % len(not_deleted),
                                                   deleted=deleted,
                                                   not_deleted=not_deleted)), status=207)
        else:
            return ApiResponse(json.dumps(dict(message='Bad request, include ids as list data')), status=400)


@api.route('/organizers/')
class Organizers(Resource):
    """
        This resource handles organizer CRUD operations
    """

    @authenticate
    def get(self, *args, **kwargs):
        """
        This action returns a list of user organizer.
        """
        user_id = kwargs['user_id']
        try:
            organizers = map(lambda organizer: organizer.to_json(), Organizer.get_by_user_id(user_id))
            resp = json.dumps({'organizers': organizers, 'count': len(organizers)})
        except Exception as e:
            return ApiResponse(json.dumps(dict(messsage='APIError: Internal Server error..')), status=500)
        return ApiResponse(resp, status=200)

    @authenticate
    def post(self, *args, **kwargs):
        """
        Creates a organizer for this user
        :return:
        """
        user_id = kwargs['user_id']
        try:
            organizer_data = request.get_json(force=True)
            organizer_data['user_id'] = user_id
            organizer = Organizer(**organizer_data)
            Organizer.save(organizer)
        except Exception as e:
            return ApiResponse(json.dumps(dict(messsage='APIError: Internal Server error..')), status=500)
        return ApiResponse(json.dumps(dict(messsage='Organizer created successfully', id=organizer.id)), status=201)

    @authenticate
    def delete(self, **kwargs):
        user_id = kwargs['user_id']
        deleted, not_deleted = [], []
        req_data = request.get_json(force=True)
        organizer_ids = req_data['ids'] if 'ids' in req_data and isinstance(req_data['ids'], list) else []
        if organizer_ids:
            for _id in organizer_ids:
                organizer = Organizer.get_by_user_id_organizer_id(user_id, _id)
                if organizer:
                    Organizer.delete(_id)
                    deleted.append(_id)
                else:
                    not_deleted.append(_id)

                if len(not_deleted) == 0:
                    return ApiResponse(json.dumps(dict(
                        message='%s Organizer/s deleted successfully' % len(deleted))),
                        status=200)

                return ApiResponse(json.dumps(dict(message='Unable to delete %s organizer/s' % len(not_deleted),
                                                   deleted=deleted,
                                                   not_deleted=not_deleted)), status=207)
        else:
            return ApiResponse(json.dumps(dict(message='Bad request, include ids as list data')), status=400)
