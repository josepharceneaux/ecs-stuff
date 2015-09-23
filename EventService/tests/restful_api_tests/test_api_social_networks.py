"""
    This module contains all test for Event related code.
"""
import requests
import json
from gt_models.social_network import SocialNetwork
from gt_models.user import UserCredentials

def test_subscribed_social_network(user, client, base_url, auth_data):
    """
    Input: We have a user who has subscribed to Facebook and Eventbrite
    Social networks.
    Output: Once we call the /social_networks/ for that user we get a list
    of all social networks and for Facebook and Eventbrite it has
    'is_subscribed' set to 'true'.
    :param user: User is a valid user in gettTalent's database
    :param base_url: Base URL of the app
    :param auth_data: Contains auth info as given in response from AuthService,
    it contains a refresh token, and access token.
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
    Input: We have a user who hasn't subscribed to any social network.
    Output: Once we call the /social_networks/ for that user we get a list
    of all social networks and for Facebook and Eventbrite it has
    'is_subscribed' set to 'true'.
    :param base_url: Base URL of the app.
    :param auth_data: Contains auth info as given in response from AuthService,
    it contains a refresh token, and access token.
    :return:
    """

    response = requests.get(base_url + 'social_networks/',
                            headers={'Authorization': auth_data['access_token']})

    data = json.loads(response.text)['social_networks']
    assert all([item.has_key('is_subscribed') for item in data])

    assert len(filter(lambda data: data['is_subscribed'] == True, data)) == 0

def test_social_network_with_invalid_token(base_url):
    """
    Input: We try to talk to the API with an invalid token and it
    shouldn't let us.
    Output: It should send us status code of 401.
    'is_subscribed' set to 'true'.
    :param base_url: Base URL of the app.
    :return:
    """

    response = requests.get(base_url + 'social_networks/',
                            headers={'Authorization': 'bad token'})

    assert response.status_code == 401


# -------------------------------------------------------------------
# Following tests are related to /social_networks/auth_info endpoint |
# -------------------------------------------------------------------

def test_user_auth_info_with_valid_user(user, auth_data, base_url):
    """
    We create the Eventbrite social network if it's not there. Then
    we create user's credentials in user_credentials table which are
    valid and we call the end point and it should smoothly.
    :param user: Valid user as given in gT's database.
    :param auth_data: Contains auth info as given in response from AuthService,
    it contains a refresh token, and access token.
    :param base_url: Base URL of the app.
    :return:
    """
    eb_auth_token = '37SUXFOPQJGF3O4LJHZD'
    eventbrite = SocialNetwork.get_by_name('Eventbrite')
    if not eventbrite:
        eventbrite = SocialNetwork(name='Eventbrite', url='www.eventbrite.com/',
                                   apiUrl='https://www.eventbriteapi.com/v3/')
        SocialNetwork.save(eventbrite)

    eventbrite_creds = UserCredentials.get_by_user_and_social_network(user.id, eventbrite.id)
    if not eventbrite_creds:
        eventbrite_credentials = UserCredentials(userId=user.id, socialNetworkId=eventbrite.id,
                            accessToken=eb_auth_token, refreshToken=None)
        UserCredentials.save(eventbrite_credentials)


    response = requests.get(base_url + 'social_networks/auth_info',
                            headers={'Authorization': auth_data['access_token']})
    assert response.status_code == 200
    assert response.json().has_key('auth_info')
    result = response.json()['auth_info'][0]
    assert result['name'] == 'Eventbrite'
    assert result['auth_status'] == True

def test_user_auth_info_with_expired_token(user, auth_data, base_url):
    """
    We create the Eventbrite social network if it's not there. Then
    we create user's credentials in user_credentials table which are
    invalid and we call the end point and it should smoothly return
    us a response saying the auth_info is invalid (because token
    was not valid).
    :param user: Valid user as given in getTalent's database
   :param auth_data: Contains auth info as given in response from AuthService,
    it contains a refresh token, and access token.
    :return:
    """
    eb_auth_token = '37SUXFOPQJGF3O' # Invalid token
    client_secret = 'FMCZZVWG6LDMMX36DRIONOCNVSWRZ6LQNST3AHLQRVY5X4CMP7'
    application_key = '3CU4XVANDI7CMHGDLO'
    eventbrite = SocialNetwork.get_by_name('Eventbrite')
    if not eventbrite:
        eventbrite = SocialNetwork(name='Eventbrite', url='www.eventbrite.com/',
                                   apiUrl='https://www.eventbriteapi.com/')
        SocialNetwork.save(eventbrite)

    eventbrite_creds = UserCredentials.get_by_user_and_social_network(user.id, eventbrite.id)
    if not eventbrite_creds:
        eventbrite_credentials = UserCredentials(userId=user.id, socialNetworkId=eventbrite.id,
                            accessToken=eb_auth_token, refreshToken=None)
        UserCredentials.save(eventbrite_credentials)

    # Thought it's an invalid token but it should refresh the token itself
    # and get a new token
    response = requests.get(base_url + 'social_networks/auth_info',
                            headers={'Authorization': auth_data['access_token']})
    assert response.status_code == 200
    assert response.json().has_key('auth_info')
    result = response.json()['auth_info'][0]
    assert result['name'] == 'Eventbrite'
    assert result['auth_status'] == False

def test_user_auth_info_with_no_social_network(auth_data, base_url):
    """
    We create the Eventbrite social network if it's not there. We don't
     create any credentials for the user in user_credentials table. So
     when we hit the endpoint we shouldn't get any results back because
     user isn't connected to any social network.
    :param auth_data: Contains auth info as given in response from AuthService,
    it contains a refresh token, and access token.:
    :param base_url: Base URL of the app.
    :return:
    """
    eventbrite = SocialNetwork.get_by_name('Eventbrite')
    if not eventbrite:
        eventbrite = SocialNetwork(name='Eventbrite', url='www.eventbrite.com/',
                                   apiUrl='https://www.eventbriteapi.com/')
        SocialNetwork.save(eventbrite)

    response = requests.get(base_url + 'social_networks/auth_info',
                            headers={'Authorization': auth_data['access_token']})

    assert response.status_code == 200
    assert response.json().has_key('auth_info')
    result = response.json()['auth_info']
    assert len(result) == 0
