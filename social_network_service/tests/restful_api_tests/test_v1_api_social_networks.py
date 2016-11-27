"""
Test that the user is subscribed to a social network or not
For that, first create an two social network and subscribe to only one of them and then get them to check
if social network is subscribed or not
Also check that the endpoint should not be accessible with invalid token
"""
import json

import requests

from social_network_service.common.routes import SocialNetworkApiUrl
from social_network_service.common.tests.api_conftest import token_first, user_first
from social_network_service.social_network_app import logger


def test_subscribed_social_network(token_first, user_first, test_eventbrite_credentials, test_meetup_credentials):
    """
    Input: We created two test social networks with name SN1 and SN2 and added credentials for SN1
    in UserSocialNetworkCredential Table in is_subscribed_test_data fixture.

    Output: Once we call the /social_networks/ for that user we get a list
    of all social networks and for Now in social_networks API data, these two social networks
    should be according to our expectations.
    'is_subscribed' set to 'true' for SN1 and 'false' for SN2
    """

    response = requests.get(SocialNetworkApiUrl.SOCIAL_NETWORKS,
                            headers={'Authorization': 'Bearer %s' % token_first})
    logger.info(response.text)
    assert response.status_code == 200
    social_networks = json.loads(response.text)['social_networks']
    assert all(['is_subscribed' in sn for sn in social_networks])
    subscribed_social_networks = filter(lambda sn: sn['is_subscribed'], social_networks)
    assert len(subscribed_social_networks) == 2
    subscribed_social_network = filter(lambda sn: sn['name'] in ['Eventbrite', 'Meetup'], subscribed_social_networks)
    assert len(subscribed_social_network) == 2, 'Subscribed social networks must be Meetup and Eventbrite'


def test_social_network_no_auth():
    """
    Send request with invalid token and response should be 401 (Unauthorized)
    """
    response = requests.get(SocialNetworkApiUrl.SOCIAL_NETWORKS,
                            headers={'Authorization': 'some random'})
    logger.info(response.text)
    assert response.status_code == 401
