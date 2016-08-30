"""
This file contains URLs of different vendors e.g. Meetup, Eventbrite for social-network-service
"""

__author__ = 'basit'

# Application Specific
from social_network_service.social_network_app import logger, app
from social_network_service.modules.constants import MOCK_VENDORS
from social_network_service.common.routes import SocialNetworkApiUrl
from social_network_service.common.error_handling import InternalServerError
from social_network_service.common.talent_config_manager import TalentConfigKeys, TalentEnvs


class SocialNetworkUrls(object):
    """
    Here we have URLs for different vendors used in social-network-service
    """
    IS_DEV = app.config[TalentConfigKeys.ENV_KEY] in [TalentEnvs.DEV, TalentEnvs.JENKINS]
    VALIDATE_TOKEN = 'validate_token'
    GROUPS = 'groups'
    VENUES = 'venues'
    EVENTS = 'events'
    ORGANIZERS = 'organizers'

    """ Social-Networks """
    MEETUP = {VALIDATE_TOKEN: '{}/member/self',
              GROUPS: '{}/groups',
              VENUES: '{}/venues',
              EVENTS: '{}/event',  # This is singular on Meetup website,
              }

    EVENTBRITE = {
        VALIDATE_TOKEN: '{}/users/me/',
        VENUES: '{}/venues/',
        EVENTS: '{}/events/',
        ORGANIZERS: '{}/organizers/'
    }

    @classmethod
    def get_url(cls, class_object, key, custom_url=None):
        """
        This returns the required URL to make HTTP request on some social-network website
        :param class_object: SocialNetwork class object
        :param string key: Requested Key
        :param custom_url: Custom API URL different from class_object.api_url
        :rtype: string
        """
        social_network_name = class_object.social_network.name
        social_network_urls = getattr(cls, social_network_name.upper())
        if app.config[TalentConfigKeys.ENV_KEY] in [TalentEnvs.DEV, TalentEnvs.JENKINS] \
                and social_network_name.lower() in MOCK_VENDORS:
            api_url = SocialNetworkApiUrl.MOCK_SERVICE % social_network_name.lower()
        else:
            api_url = class_object.api_url if not custom_url else custom_url
        try:
            relative_url = social_network_urls[key.lower()]
        except AttributeError as error:
            logger.error(error.message)
            raise InternalServerError('Error occurred while getting URL for required action')

        return relative_url.format(api_url)
