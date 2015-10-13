import json
import types
from flask import Blueprint, request
from common.models.organizer import Organizer
from common.models.venue import Venue
from social_network_service.app.app_utils import authenticate, api_route, ApiResponse
from flask.ext.restful import Resource, Api
from social_network_service.meetup import Meetup

from common.models.user import UserCredentials, User
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
        This action returns a list of user social networks.

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.get(API_URL + '/venues/', headers=headers)

        .. Response::

            {
              "count": 3,
              "social_networks": [
                    {
                      "api_url": "https://api.meetup.com/2",
                      "auth_url": "https://secure.meetup.com/oauth2",
                      "client_key": "jgjvi3gsvrgjcp2mu9r6nb3kb0",
                      "id": 13,
                      "is_subscribed": true,
                      "name": "Meetup",
                      "redirect_uri": "http://127.0.0.1:8000/web/user/get_token",
                      "updated_time": "",
                      "url": "www.meetup.com/"
                    },
                    {
                      "api_url": "https://www.eventbriteapi.com/v3",
                      "auth_url": "https://www.eventbrite.com/oauth",
                      "client_key": "MSF5F2NUE35NQTLRLB",
                      "id": 18,
                      "is_subscribed": true,
                      "name": "Eventbrite",
                      "redirect_uri": "http://127.0.0.1:8000/web/user/get_token",
                      "updated_time": "",
                      "url": "www.eventbrite.com"
                    },
                    {
                      "api_url": "https://graph.facebook.com/v2.4",
                      "auth_url": "https://graph.facebook.com/oauth",
                      "client_key": "1709873329233611",
                      "id": 2,
                      "is_subscribed": false,
                      "name": "Facebook",
                      "redirect_uri": "",
                      "updated_time": "",
                      "url": "www.facebook.com/"
                    }
              ]
            }

        .. Status:: 200 (OK)
                    500 (Internal Server Error)
        """
        user_id = kwargs.get('user_id')
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
            [data.social_network_id for data in subscribed_data]
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
            for sn in all_networks:
                del sn['secret_key']
            return {'social_networks': all_networks,
                    'count': len(all_networks)}
        else:
            return {'social_networks': [], 'count': 0}


@api.route('/social_networks/groups/')
class MeetupGroups(Resource):
    """
        This resource returns a list of user's admin groups for Meetup
    """

    @authenticate
    def get(self, *args, **kwargs):
        """
        This action returns a list of user events.

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.get(API_URL + '/venues/', headers=headers)

        .. Response::

            {
              "count": 1,
              "groups": [
                {
                  "category": {
                    "shortname": "tech",
                    "name": "tech",
                    "id": 34
                  },
                  "city": "Lahore",
                  "utc_offset": 18000000,
                  "who": "Python Lovers",
                  "rating": 0,
                  "description": "This group is for anyone interested in computer programming. Python is one of the top ranking programming languages. All skill levels are welcome. Basic purpose is to get exposure about python from smart people all over the world. We can also meet at some restaurant for some food and drink afterward. Let's meetup and share knowledge.",
                  "created": 1439705650000,
                  "country": "PK",
                  "topics": [
                    {
                      "name": "Python",
                      "urlkey": "python",
                      "id": 1064
                    },
                    {
                      "name": "Web Development",
                      "urlkey": "web-development",
                      "id": 15582
                    },
                    {
                      "name": "Programming Languages",
                      "urlkey": "programming-languages",
                      "id": 17628
                    },
                    {
                      "name": "Computer programming",
                      "urlkey": "computer-programming",
                      "id": 48471
                    },
                    {
                      "name": "Python web development",
                      "urlkey": "python-web-development",
                      "id": 917242
                    }
                  ],
                  "join_mode": "open",
                  "lon": 74.3499984741211,
                  "visibility": "public",
                  "link": "http://www.meetup.com/QC-Python-Learning/",
                  "members": 59,
                  "urlname": "QC-Python-Learning",
                  "lat": 31.559999465942383,
                  "timezone": "Asia/Karachi",
                  "organizer": {
                    "name": "Waqas Younas",
                    "member_id": 183366764
                  },
                  "id": 18837246,
                  "name": "QC - Python Learning"
                }
              ]
            }

        .. Status:: 200 (OK)
                    500 (Internal Server Error)
        """
        user_id = kwargs['user_id']
        try:
            meetup = Meetup(user_id=user_id)
            groups = meetup.get_groups()
            resp = json.dumps(dict(groups=groups,
                                   count=len(groups)))
        except Exception as e:
            return ApiResponse(json.dumps(dict(message='APIError: Internal Server Error')), status=500)
        return ApiResponse(resp, status=200)


@api.route('/social_networks/token_validity/<int:social_network_id>')
class GetTokenValidity(Resource):
    @authenticate
    def get(self, social_network_id, **kwargs):
        """
        Get user access_token validity status for specified social network
        :param social_network_id: id for specified social network
        :type social_network_id: int
        :keyword user_id: id for current user
        :type user_id: int

        :Example:

            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.get(
                                        API_URL + /social_networks/token_validity/13,
                                        headers=headers
                                    )

        .. Response::

            {
              "status": true
            }

        .. Status:: 200 (OK)
                    461 (UserCredentials not found)
                    404 (Social Network not found)
                    500 (Internal Server Error)

        """
        user_id = kwargs['user_id']
        # Get social network specified by social_network_id
        social_network = SocialNetwork.get_by_id(social_network_id)
        if social_network:
            # Get social network specific Social Network class
            social_network_class = get_class(social_network.name, 'social_network')
            # create social network object which will validate and refresh access token (if possible)
            sn = social_network_class(user_id=user_id,
                                      social_network=social_network
                                      )
            return ApiResponse(dict(status=sn.access_token_status))
        else:
            return ApiResponse(dict(message='Invalid social network Id given'), status=404)


@api.route('/social_network/refresh_token/<int:social_network_id>')
class RefreshToken(Resource):
    """
        This resource refreshes access token for given social network for given user
    """

    @authenticate
    def get(self, social_network_id, **kwargs):
        """
        Gets a fresh token for specified user and social network
        :return:

        :Example:


            headers = {
                        'Authorization': 'Bearer <access_token>',
                       }
            response = requests.get(
                                        API_URL + '/social_network/refresh_token/13',
                                        headers=headers,
                                    )

        .. Response::

            {
                "message" : 'Access token has been refreshed'
                'status' : true
            }

        .. Status:: 201 (Resource Created)
                    403 (Failed to refresh token)
                    500 (Internal Server Error)
        """
        user_id = kwargs['user_id']
        try:
            social_network = SocialNetwork.get_by_id(social_network_id)
            # creating class object for respective social network
            social_network_class = get_class(social_network.name.lower(), 'social_network')
            sn = social_network_class(user_id=user_id)
            status = sn.refresh_access_token()
        except Exception as e:
            return ApiResponse(json.dumps(dict(messsage='APIError: Internal Server error..')), status=500)
        if status:
            return ApiResponse(json.dumps(dict(messsage='Access token has been refreshed',
                                               status=True)), status=200)
        else:
            return ApiResponse(json.dumps(dict(messsage='Unable to refresh access_token',
                                               status=False)), status=403)


@api.route('/venues/')
class Venues(Resource):
    """
        This resource returns a list of user's created venues
    """

    @authenticate
    def get(self, *args, **kwargs):
        """
        This action returns a list of user venues.
        :return: json for venues

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.get(API_URL + '/venues/', headers=headers)

        .. Response::

            {
              "count": 1,
              "venues": [
                {
                    "user_id": 1,
                    "zipcode": "95014",
                    "social_network_id": 13,
                    "address_line2": "",
                    "address_line1": "Infinite Loop",
                    "latitude": 0,
                    "longitude": 0,
                    "state": "CA",
                    "city": "Cupertino",
                    "country": "us"
                }

              ]
            }

        .. Status:: 200 (OK)
                    500 (Internal Server Error)

        """
        user_id = kwargs['user_id']
        user = User.get_by_id(user_id)
        venues = user.venues.all()
        venues = map(lambda venue: venue.to_json(), venues)
        resp = json.dumps(dict(venues=venues, count=len(venues)))
        return ApiResponse(resp, status=200)

    @authenticate
    def post(self, *args, **kwargs):
        """
        Creates a venue for this user
        :return:

        :Example:
            venue_data = {
                "zipcode": "95014",
                "social_network_id": 13,
                "address_line2": "",
                "address_line1": "Infinite Loop",
                "latitude": 0,
                "longitude": 0,
                "state": "CA",
                "city": "Cupertino",
                "country": "us"
            }


            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }
            data = json.dumps(venue_data)
            response = requests.post(
                                        API_URL + '/venues/',
                                        data=data,
                                        headers=headers,
                                    )

        .. Response::

            {
                "message" : 'Venue created successfully'
                'id' : 123
            }

        .. Status:: 201 (Resource Created)
                    500 (Internal Server Error)

        """
        user_id = kwargs['user_id']
        venue_data = request.get_json(force=True)
        venue_data['user_id'] = user_id
        venue = Venue(**venue_data)
        Venue.save(venue)
        return ApiResponse(json.dumps(dict(message='Venue created successfully', id=venue.id)), status=201)

    @authenticate
    def delete(self, **kwargs):
        """
        This endpoint deletes venues specified in list in request data

        :Example:
            venue_ids = {
                'ids': [1,2,3]
            }
            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }
            data = json.dumps(venue_ids)
            response = requests.post(
                                        API_URL + '/venues/',
                                        data=data,
                                        headers=headers,
                                    )

        .. Response::

            {
                'message': '3 Venues have been deleted successfully'
            }
        .. Status:: 200 (Resource Deleted)
                    207 (Not all deleted)
                    400 (Bad request)
                    500 (Internal Server Error)

        """
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


@api.route('/venues/<int:venue_id>')
class VenueById(Resource):
    """
        This resource handles venue CRUD operations for a single venue given by venue_id
    """

    @authenticate
    def get(self, venue_id, **kwargs):
        """
        This action returns a venue (given by id) created by current user.
        :param venue_id: id of venue to be returned
        :keyword user_id: id of venue owner (user who created venue)

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.get(
                                        API_URL + '/organizers/1',
                                        headers=headers
                                    )

        .. Response::

            {
              "organizer": {
                  "address_line2": "",
                  "city": "Cupertino",
                  "address_line1": "Infinite Loop",
                  "user_id": 1,
                  "social_network_id": 13,
                  "country": "us",
                  "zipcode": "95014",
                  "longitude": 0,
                  "social_network_venue_id": "15570022",
                  "state": "CA",
                  "latitude": 0,
                  "id": 1
                }
            }

        .. Status:: 200 (OK)
                    404 (Resource not found)
                    500 (Internal Server Error)
        """
        user_id = kwargs['user_id']
        venue = Venue.get_by_user_id_venue_id(user_id, venue_id)
        if venue:
            venue = venue.to_json()
            resp = json.dumps({'venue': venue})
            return ApiResponse(resp, status=200)
        else:
            return ApiResponse(json.dumps(dict(messsage='Venue not found')), status=404)

    @authenticate
    def post(self, venue_id, **kwargs):
        """
        Updates a venue for current user
        :param venue_id: id of the requested venue
        :return:

        :Example:
            venue_data = {
                  "address_line2": "",
                  "city": "Cupertino",
                  "address_line1": "Infinite Loop",
                  "social_network_id": 13,
                  "country": "us",
                  "zipcode": "95014",
                  "longitude": 0,
                  "social_network_venue_id": "15570022",
                  "state": "CA",
                  "latitude": 0,
                  "id": 1
                }


            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }
            data = json.dumps(venue_data)
            response = requests.post(
                                        API_URL + '/venues/1',
                                        data=data,
                                        headers=headers,
                                    )

        .. Response::

            {
                'message': 'Venue updated successfully'
            }

        .. Status:: 204 (Resource Updated)
                    500 (Internal Server Error)

        """
        user_id = kwargs['user_id']
        venue_data = request.get_json(force=True)
        venue = Venue.get_by_user_id_venue_id(user_id, venue_id)
        if venue:
            venue_data['user_id'] = user_id
            venue.update(**venue_data)
            return ApiResponse(json.dumps(dict(message='Venue updated successfully')), status=204)
        else:
            return ApiResponse(json.dumps(dict(messsage='Venue not found')), status=404)

    @authenticate
    def delete(self, venue_id, **kwargs):
        """
        This endpoint deletes one venue owned by this user
        :param venue_id: id of venue on getTalent database to be deleted
        :return:

        :Example:
            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }
            response = requests.delete(
                                        API_URL + '/venues/1',
                                        headers=headers,
                                    )

        .. Response::

            {
                'message': 'Venue has been deleted successfully'
            }
        .. Status:: 200 (Resource Deleted)
                    404 (Not found)
                    500 (Internal Server Error)

        """
        # Get user_id
        user_id = kwargs['user_id']
        venue = Venue.get_by_user_id_venue_id(user_id, venue_id)
        if venue:
            Venue.delete(venue_id)
            resp = json.dumps(dict(message='Venue has been deleted successfully'))
            return ApiResponse(resp, status=200)
        else:
            return ApiResponse(json.dumps(dict(message='Venue not found')), status=404)


@api.route('/organizers/')
class Organizers(Resource):
    """
        This resource handles organizer CRUD operations
    """

    @authenticate
    def get(self, *args, **kwargs):
        """
        This action returns a list of organizers created by current user.
        :keyword user_id: id of organizer owner (user who created organizer)

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            response = requests.get(API_URL + '/organizers/', headers=headers)

        .. Response::

            {
              "count": 1,
              "organizers": [
                {
                    "user_id": 1,
                    "name": "Zohaib Ijaz",
                    "email": "mzohaib.qc@gmail.com",
                    "about": "I am a software engineer"
                }

              ]
            }

        .. Status:: 200 (OK)
                    500 (Internal Server Error)
        """
        user_id = kwargs['user_id']
        organizers = map(lambda organizer: organizer.to_json(), Organizer.get_by_user_id(user_id))
        resp = json.dumps({'organizers': organizers, 'count': len(organizers)})
        return ApiResponse(resp, status=200)

    @authenticate
    def post(self, *args, **kwargs):
        """
        Creates a organizer for this user
        :return:

        :Example:
            organizer_data = {
                    "name": "Zohaib Ijaz",
                    "email": "mzohaib.qc@gmail.com",
                    "about": "I am a software engineer"
                }


            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }
            data = json.dumps(organizer_data)
            response = requests.post(
                                        API_URL + '/organizers/',
                                        data=data,
                                        headers=headers,
                                    )

        .. Response::

            {
                "message" : 'Organizer created successfully'
                'id' : 123
            }

        .. Status:: 201 (Resource Created)
                    500 (Internal Server Error)

        """
        user_id = kwargs['user_id']
        organizer_data = request.get_json(force=True)
        organizer_data['user_id'] = user_id
        organizer = Organizer(**organizer_data)
        Organizer.save(organizer)
        return ApiResponse(json.dumps(dict(messsage='Organizer created successfully', id=organizer.id)), status=201)

    @authenticate
    def delete(self, **kwargs):
        """
        This endpoint deletes one or more organizer owned by this user
        :param kwargs:
        :return:

        :Example:
            organizers_ids = {
                'ids': [1,2,3]
            }
            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }
            data = json.dumps(organizers_ids)
            response = requests.post(
                                        API_URL + '/organizers/',
                                        data=data,
                                        headers=headers,
                                    )

        .. Response::

            {
                'message': '3 Organizers have been deleted successfully'
            }
        .. Status:: 200 (Resource Deleted)
                    207 (Not all deleted)
                    400 (Bad request)
                    500 (Internal Server Error)

        """
        # Get user_id
        user_id = kwargs['user_id']
        deleted, not_deleted = [], []
        # Get json data from request
        req_data = request.get_json(force=True)
        organizer_ids = req_data['ids'] if 'ids' in req_data and isinstance(req_data['ids'], list) else []
        # If no organizer id is given, return 400 (Bad request)
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


@api.route('/organizers/<int:organizer_id>')
class OrganizerById(Resource):
    """
        This resource handles organizer CRUD operations for a single organizer given by organizer_id
    """

    @authenticate
    def get(self, organizer_id, **kwargs):
        """
        This action returns an organizer (given by id) created by current user.
        :param organizer_id: id of organizer to be returned
        :keyword user_id: id of organizer owner (user who created organizer)

        :Example:
            headers = {'Authorization': 'Bearer <access_token>'}
            organizer_id = 1
            response = requests.get(
                                        API_URL + '/organizers/' + str(organizer_id),
                                        headers=headers
                                    )

        .. Response::

            {
              "organizer": {
                    "id": 1
                    "user_id": 1,
                    "name": "Zohaib Ijaz",
                    "email": "mzohaib.qc@gmail.com",
                    "about": "I am a software engineer"
              }
            }

        .. Status:: 200 (OK)
                    404 (Resource not found)
                    500 (Internal Server Error)
        """
        user_id = kwargs['user_id']
        organizer = Organizer.get_by_user_id_organizer_id(user_id, organizer_id)
        if organizer:
            organizer = organizer.to_json()
            resp = json.dumps({'organizer': organizer})
            return ApiResponse(resp, status=200)
        else:
            ApiResponse(json.dumps(dict(messsage='APIError: Organizer not found')), status=404)

    @authenticate
    def post(self, organizer_id, **kwargs):
        """
        Updates an organizer for current user
        :return:

        :Example:
            organizer_data = {
                    'id': 1,
                    "name": "My Organizer",
                    "email": "organizer@gmail.com",
                    "about": "He arranges events"
                }


            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }
            data = json.dumps(organizer_data)
            response = requests.post(
                                        API_URL + '/organizers/1',
                                        data=data,
                                        headers=headers,
                                    )

        .. Response::

            {
                "message" : 'Organizer updated successfully'
            }

        .. Status:: 204 (Resource Updated)
                    500 (Internal Server Error)

        """
        user_id = kwargs['user_id']
        organizer_data = request.get_json(force=True)
        organizer = Organizer.get_by_user_id_organizer_id(user_id, organizer_id)
        if organizer:
            organizer_data['user_id'] = user_id
            organizer.update(**organizer_data)
            return ApiResponse(json.dumps(dict(message='Organizer updated successfully')), status=204)
        else:
            return ApiResponse(json.dumps(dict(messsage='Organizer not found')), status=404)

    @authenticate
    def delete(self, organizer_id, **kwargs):
        """
        This endpoint deletes one organizer owned by this user
        :param kwargs:
        :return:

        :Example:
            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }
            response = requests.delete(
                                        API_URL + '/organizers/1',
                                        headers=headers,
                                    )

        .. Response::

            {
                'message': 'Organizer has been deleted successfully'
            }
        .. Status:: 200 (Resource Deleted)
                    404 (Not found)
                    500 (Internal Server Error)

        """
        # Get user_id
        user_id = kwargs['user_id']
        organizer = Organizer.get_by_user_id_organizer_id(user_id, organizer_id)
        if organizer:
            Organizer.delete(organizer_id)
            resp = json.dumps(dict(message='Organizer has been deleted successfully'))
            return ApiResponse(resp, status=200)
        else:
            return ApiResponse(json.dumps(dict(message='Organizer not found')), status=404)


@api.route('/social_networks/process_access_token/<int:social_network_id>')
class ProcessAccessToken(Resource):
    """
    This resource adds user credentials for given user and social network
    This resource takes access token 'code' and social network id for which we
    want to add credentials.
    """
    @authenticate
    def post(self, social_network_id, **kwargs):
        """
        Adds credentials for user for given social network.
        Gets data from post request which contains 'code' and 'social_credentials'
        :param args:
        :param kwargs:
        :return:

        :Example:
            data = {
                    'code': '32432ffd2s8fd23e8saq123ds6a3da21221
                    }


            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }
            data = json.dumps(data)
            response = requests.post(
                                        API_URL + '/social_networks/process_access_token/13',
                                        data=data,
                                        headers=headers,
                                    )

        .. Response::

            {
                "message" : 'User credentials added successfully'
            }

        .. Status:: 201 (Resource Updated)
                    404 (Social Network not found)
                    500 (Internal Server Error)

        """
        user_id = kwargs['user_id']
        # Get json request data
        req_data = request.get_json(force=True)
        code = req_data['code']
        social_network = SocialNetwork.get_by_id(social_network_id)
        # if social network does not exists, send failure message
        if social_network:
            # Get social network specific Social Network class
            social_network_class = get_class(social_network.name, 'social_network')
            # call specific class method to save user credentials and webhook in case of Eventbrite
            access_token, refresh_token = social_network_class.get_access_and_refresh_token(
                user_id, social_network, code_to_get_access_token=code)
            user_credentials_dict = dict(user_id=user_id,
                                         social_network_id=social_network.id,
                                         access_token=access_token,
                                         refresh_token=refresh_token)
            social_network_class.save_user_credentials_in_db(user_credentials_dict)
            return ApiResponse(dict(message='User credentials added successfully'), status=201)
        else:
            return ApiResponse(dict(message='Social Network not found'), status=404)


