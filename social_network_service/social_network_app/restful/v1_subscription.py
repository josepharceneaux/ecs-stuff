"""
This file contains endpoint(s) for getTalent users to connect/authenticate with their social networks accounts.
Currently it contains only endpoint for Twitter.
"""

__author__ = 'basit'

# Standard imports
import types

# 3rd party imports
from flask import Blueprint, request
from flask.ext.restful import Resource

# Application specific imports
from social_network_service.common.talent_api import TalentApi
from social_network_service.common.routes import SocialNetworkApi
from social_network_service.common.utils.api_utils import api_route
from social_network_service.common.utils.auth_utils import require_oauth
from social_network_service.modules.social_network.twitter import Twitter


subscription_blueprint = Blueprint('subscription_api', __name__)
api = TalentApi()
api.init_app(subscription_blueprint)
api.route = types.MethodType(api_route, api)


@api.route(SocialNetworkApi.TWITTER_AUTH)
class TwitterSubscription(Resource):
    """
        This resource connects getTalent users with their Twitter accounts.
    """
    decorators = [require_oauth()]

    def get(self):
        """
        This endpoint is hit when user clicks on profile page to connect with Twitter account.
        Here we create object of Twitter class defined in social_network/twitter.py and call its method authenticate().
        This redirects the user to Twitter website to enter credentials and grant access to getTalent app.

        **See Also**
            .. seealso:: authenticate() method defined in Twitter class inside social_network/twitter.py.

        """
        user_id = request.user.id
        twitter_obj = Twitter(user_id=user_id, validate_credentials=False)
        return twitter_obj.authenticate()
