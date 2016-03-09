# Standard imports
import json
import types

# 3rd party imports
import flask
from flask import Blueprint, request
from flask.ext.restful import Resource

from social_network_service.common.error_handling import InvalidUsage
from social_network_service.common.models.candidate import SocialNetwork
from social_network_service.common.models.user import UserSocialNetworkCredential
from social_network_service.common.routes import SocialNetworkApi
from social_network_service.common.talent_api import TalentApi
from social_network_service.common.utils.api_utils import api_route
from social_network_service.common.utils.auth_utils import require_oauth
from social_network_service.modules.utilities import get_class
from social_network_service.social_network_app import logger
from social_network_service.tasks import rsvp_events_importer
from social_network_service.modules.rsvp.eventbrite import Eventbrite as EventbriteRsvp

rsvp_blueprint = Blueprint('importer', __name__)
api = TalentApi()
api.init_app(rsvp_blueprint)
api.route = types.MethodType(api_route, api)


@api.route(SocialNetworkApi.IMPORTER)
class RsvpEventImporter(Resource):
    """
        This resource get all RSVPs or events.

        This function is called when we run celery to import events or rsvps from
        social network website.

        1- meetup
        2- facebook.

        ** Working **
        What this method does, is explained in following steps:
        1- Call celery importer task depending on mode value

        2- It gets the user_social_network_credentials of all the users related
            to given social network (social_network provided in arguments) from
            getTalent database in variable all_user_credentials.
        3- It picks one user_credential from all_user_credentials and instantiates
            respective social network class for auth process.
        4- If access token is not valid, we raise
            AccessTokenHasExpired exception in celery task and move on to next user_credential.

        **See Also**
        .. seealso:: process() method of SocialNetworkBase class inside
                    social_network_service/base.py.

    """
    decorators = [require_oauth()]

    def get(self, mode, social_network):

        # Start celery rsvp importer method here.
        if mode.lower() not in ["event", "rsvp"]:
            raise InvalidUsage("No mode of value %s found" % mode)

        if social_network.lower() not in ["meetup", "facebook"]:
            raise InvalidUsage("No social network with name %s found." % social_network)

        social_network_id = None
        if social_network is not None:
            social_network_name = social_network.lower()
            try:
                social_network_obj = SocialNetwork.get_by_name(social_network_name)
                social_network_id = social_network_obj.id
            except Exception:
                raise NotImplementedError('Social Network "%s" is not allowed for now, '
                                          'please implement code for this social network.'
                                          % social_network_name)

        all_user_credentials = UserSocialNetworkCredential.get_all_credentials(social_network_id)
        if all_user_credentials:
            for user_credentials in all_user_credentials:
                rsvp_events_importer.apply_async([social_network, mode, user_credentials])
        else:
            logger.error('There is no User in db for social network %s'
                         % social_network)

        return dict(message="%s are being imported." % mode.upper())


@api.route(SocialNetworkApi.EVENTBRITE_IMPORTER)
class RsvpEventImporterEventbrite(Resource):
    """
        This resource get all RSVPs or events. This callback method will be called when someone hit register
        on an eventbrite event.

        ** Working **
        What this method does, is explained in following steps:
        1- Call celery importer task depending on mode value

        2- It gets the user_social_network_credentials of all the users related
            to given social network (social_network provided in arguments) from
            getTalent database in variable all_user_credentials.
        3- It picks one user_credential from all_user_credentials and instantiates
            respective social network class for auth process.
        4- If access token is not valid, we raise
            AccessTokenHasExpired exception in celery task and move on to next user_credential.

        **See Also**
        .. seealso:: process() method of SocialNetworkBase class inside
                    social_network_service/base.py.

    """

    def post(self, **kwargs):
        """
    This function only receives data when a candidate rsvp to some event.
    It first finds the getTalent user having incoming webhook id.
    Then it creates the candidate in candidate table by getting information
    of attendee. Then it inserts in rsvp table the required information.
    It will also insert an entry in DB table activity
    """
        user_id = ''
        if request.data:
            try:
                data = json.loads(request.data)
                action = data['config']['action']
                if action == 'order.placed':
                    webhook_id = data['config']['webhook_id']
                    user_credentials = \
                        EventbriteRsvp.get_user_credentials_by_webhook(webhook_id)
                    logger.debug('Got an RSVP on %s Event via webhook.'
                                 % user_credentials.social_network.name)
                    user_id = user_credentials.user_id
                    social_network_class = \
                        get_class(user_credentials.social_network.name.lower(),
                                  'social_network')
                    # we make social network object here to check the validity of
                    # access token. If access token is valid, we proceed to do the
                    # processing to save in getTalent db tables otherwise we raise
                    # exception AccessTokenHasExpired.
                    sn_obj = social_network_class(user_id=user_credentials.user_id)
                    sn_obj.process('rsvp', user_credentials=user_credentials,
                                   rsvp_data=data)
                elif action == 'test':
                    logger.debug('Successful webhook connection')

            except Exception as error:
                logger.exception('handle_rsvp: Request data: %s, user_id: %s',
                                 request.data, user_id)
                data = {'message': error.message,
                        'status_code': 500}
                return flask.jsonify(**data), 500

            data = {'message': 'RSVP Saved',
                    'status_code': 200}
            return flask.jsonify(**data)

        else:
            error_message = 'No RSVP data received.'
            data = {'message': error_message,
                    'status_code': 200}
            return flask.jsonify(**data)
