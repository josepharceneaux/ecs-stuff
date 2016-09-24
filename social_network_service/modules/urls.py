"""
get_url method returns vendor specific absolute url.

Example url: http://localhost:8016/v1/api/self/member

"""

# App specific imports
from social_network_service.common.constants import API, AUTH
from social_network_service.common.vendor_urls.sn_relative_urls import SocialNetworkUrls
from social_network_service.common.routes import MockServiceApiUrl
from social_network_service.common.error_handling import InternalServerError
from social_network_service.common.talent_config_manager import TalentConfigKeys, TalentEnvs
from social_network_service.modules.constants import MOCK_VENDORS
from social_network_service.modules.event.base import EventBase
from social_network_service.social_network_app import app, logger


def get_url(class_object, key, custom_url=None, is_auth=None):
    """
    This returns the required URL to make HTTP request on some social-network website
    :param EventBase|SocialNetworkBase class_object: SocialNetwork class object
    :param string key: Requested Key
    :param custom_url: Custom API URL different from class_object.api_url
    :param bool is_auth: if is_auth is true then use vendor auth url, otherwise use api url
    :rtype: string
    """
    social_network_name = class_object.social_network.name
    social_network_urls = getattr(SocialNetworkUrls, social_network_name.upper())
    if app.config[TalentConfigKeys.ENV_KEY] in [TalentEnvs.JENKINS] \
            and social_network_name.lower() in MOCK_VENDORS:
        # There are currently two types of URLs. i.e Auth and API url.
        auth_part = AUTH if is_auth else API
        api_url = MockServiceApiUrl.MOCK_SERVICE % (auth_part, social_network_name.lower())
    else:
        api_url = (class_object.auth_url if is_auth else class_object.api_url) if not custom_url else custom_url

    try:
        relative_url = social_network_urls[key.lower()]
    except KeyError as error:
        logger.error(error.message)
        raise InternalServerError('Error occurred while getting URL for %s. (SocialNetwork:%s)'
                                  % (key, social_network_name))

    return relative_url.format(api_url, '{}')
