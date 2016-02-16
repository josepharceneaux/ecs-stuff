"""
    This module contains all test for Event related code.
"""
# TODO: add comment and docstring
import requests
import json


from social_network_service.social_network_app import logger
from social_network_service.common.routes import SocialNetworkApiUrl


# TODO: error code inherit from class

def test_subscribed_social_network(token, sample_user, is_subscribed_test_data):
    """
    Input: We created two test social networks with name SN1 and SN2 and added credentials for SN1
    in UserSocialNetworkCredential Table in is_subscribed_test_data fixture.

    Output: Once we call the /social_networks/ for that user we get a list
    of all social networks and for Now in social_networks API data, these two social networks
    should be according to our expectations.
    'is_subscribed' set to 'true' for SN1 and 'false' for SN2
    :param user:
    :return:
    """

    response = requests.get(SocialNetworkApiUrl.SOCIAL_NETWORKS,
                            headers={'Authorization': 'Bearer %s' %token})
    logger.info(response.text)
    assert response.status_code == 200
    social_networks = json.loads(response.text)['social_networks']
    assert all(['is_subscribed' in sn for sn in social_networks])
    add_social_networks = filter(lambda sn: sn['name'] in ['SN1', 'SN2'], social_networks)
    assert len(add_social_networks) >= 2, 'There should be two items after filter that we added now'
    subscribed_social_network = filter(lambda sn: sn['name'] in ['SN1'], add_social_networks)
    assert len(subscribed_social_network) == 1, 'Only one added social network is subscribed'
    assert subscribed_social_network[0]['is_subscribed'] == True, 'SN1 must be subscribed'

    not_subscribed_social_network = filter(lambda sn: sn['name'] in ['SN2'], add_social_networks)
    assert len(not_subscribed_social_network) == 1, 'Only one added social network is subscribed'
    assert not_subscribed_social_network[0]['is_subscribed'] == False, 'SN2 must be not subscribed'


def test_social_network_no_auth():
    """
    Send request with invalid token and response should be 401 (Unauthorized)
    :return:
    """
    response = requests.get(SocialNetworkApiUrl.SOCIAL_NETWORKS,
                            headers={'Authorization': 'some random'})
    logger.info(response.text)
    assert response.status_code == 401
