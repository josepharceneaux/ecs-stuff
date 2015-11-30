# """
# This module consists pyTests for URL conversion API.
# """
#
# # Third Party Imports
# import requests
#
# # Application Specific
# from sms_campaign_service import flask_app as app
#
# APP_URL = app.config['APP_URL']
# URL_CONVERSION_API_URL = APP_URL + '/url_conversion'
#
#
# def test_get_with_invalid_token():
#     response = requests.get(URL_CONVERSION_API_URL,
#                             headers=dict(Authorization='Bearer %s' % 'invalid_token'))
#     assert response.status_code == 401, 'It should be unauthorized (401)'
#     assert 'short_url' not in response.json()
#
#
# def test_get_with_valid_token_and_no_data(auth_token):
#     response = requests.get(URL_CONVERSION_API_URL,
#                             headers=dict(Authorization='Bearer %s' % auth_token))
#     assert response.status_code == 400, 'Status should be Bad request (400)'
#
#
# def test_get_with_valid_token_and_valid_data(auth_token):
#     response = requests.get(URL_CONVERSION_API_URL,
#                             headers=dict(Authorization='Bearer %s' % auth_token),
#                             data={"long_url": 'https://webdev.gettalent.com/web/default/angular#!/'}
#                             )
#     assert response.status_code == 200, 'Status should be Bad request (400)'
#     assert 'short_url' in response.json()
#
#
# def test_get_with_valid_token_and_invalid_data(auth_token):
#     response = requests.get(URL_CONVERSION_API_URL,
#                             headers=dict(Authorization='Bearer %s' % auth_token),
#                             data={"long_url": APP_URL}
#                             )
#     assert response.status_code == 500, 'Status should be (500)'
#     assert response.json()['error']['code'] == 5004  # custom exception for Google API Error
#
#
# def test_for_post_request(auth_token):
#     response = requests.post(URL_CONVERSION_API_URL,
#                              headers=dict(Authorization='Bearer %s' % auth_token))
#     assert response.status_code == 405, 'POST method should not be allowed (405)'
#
#
# def test_for_delete_request(auth_token):
#     response = requests.delete(URL_CONVERSION_API_URL,
#                                headers=dict(Authorization='Bearer %s' % auth_token))
#     assert response.status_code == 405, 'DELETE method should not be allowed (405)'
