"""
    This module contains all test for Event related code.
"""
import requests
import json
from gt_models.social_network import SocialNetwork
from gt_models.user import UserCredentials


def test_subscribed_social_network(user, client, base_url, auth_data):
    """
    Input: We have a user which is subscribed to Facebook and Eventbrite
    Social networks.
    Output: Once we call the /social_networks/ for that user we get a list
    of all social networks and for Facebook and Eventbrite it has
    'is_subscribed' set to 'true'.
    :param user:
    :return:
    """
    # Create Facebook and Eventbrite Social Networks if not already there.
    # Make sure the user has credentials in the user_credentials table for these two.
    
    facebook = SocialNetwork.get_by_name('Facebook')
    eventbrite = SocialNetwork.get_by_name('Eventbrite')
    if not facebook:
        facebook = SocialNetwork(name='Facebook', url='www.facebook.com/')
        SocialNetwork.save(facebook)
    if not eventbrite:
        eventbrite = SocialNetwork(name='Eventbrite', url='www.eventbrite.com/',
                                   apiUrl='https://www.eventbriteapi.com/')
        SocialNetwork.save(eventbrite)

    facebook_creds = UserCredentials.get_by_user_and_social_network(user.id, facebook.id)
    if not facebook_creds:
        facebook_credentials = UserCredentials(userId=user.id, socialNetworkId=facebook.id,
                            accessToken='lorel ipsum', refreshToken='lorel ipsum')
        UserCredentials.save(facebook_credentials)

    eventbrite_creds = UserCredentials.get_by_user_and_social_network(user.id, eventbrite.id)
    if not eventbrite_creds:
        eventbrite_credentials = UserCredentials(userId=user.id, socialNetworkId=eventbrite.id,
                            accessToken='lorel ipsum', refreshToken='lorel ipsum')
        UserCredentials.save(eventbrite_credentials)

    response = requests.get(base_url + 'social_networks/',
                            headers={'Authorization': auth_data['access_token']})

    data = json.loads(response.text)['social_networks']
    assert all([item.has_key('is_subscribed') for item in data])
    assert len(filter(lambda data: data['is_subscribed'] == True, data)) == 2
    UserCredentials.delete(facebook_credentials.id)
    UserCredentials.delete(eventbrite_credentials.id)


def test_no_subscribed_social_network(base_url, auth_data):
    """
    Input: We have a user which is subscribed to Facebook and Eventbrite
    Social networks.
    Output: Once we call the /social_networks/ for that user we get a list
    of all social networks and for Facebook and Eventbrite it has
    'is_subscribed' set to 'true'.
    :param user:
    :return:
    """

    response = requests.get(base_url + 'social_networks/',
                            headers={'Authorization': auth_data['access_token']})

    data = json.loads(response.text)['social_networks']
    assert all([item.has_key('is_subscribed') for item in data])

    assert len(filter(lambda data: data['is_subscribed'] == True, data)) == 0
