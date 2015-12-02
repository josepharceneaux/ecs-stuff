"""
This module consists pyTests for SMS Campaign API.
"""

# Third Party Imports
import json
import requests

# Application Specific
from sms_campaign_service import flask_app as app

APP_URL = app.config['APP_URL']
SMS_CAMPAIGN_API_URL = APP_URL + '/campaigns/'


class TestSmsCampaign:
    """
    This class contains tests for endpoint /campaigns/.
    """

    def test_get_with_invalid_token(self):
        """
        User auth token is invalid. It should get Unauthorized error.
        :return:
        """
        response = requests.get(SMS_CAMPAIGN_API_URL,
                                headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_get_with_valid_token_and_no_user_phone(self, auth_token):
        """
        User has no phone value. It should get forbidden error.
        :param auth_token: access token of user
        :return:
        """
        response = requests.get(SMS_CAMPAIGN_API_URL,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 403, 'Should get forbidden error (403)'

    def test_get_with_valid_token_and_one_user_phone(self, auth_token, user_phone_1):
        """
        User has one phone value of type Twilio, it should get ok response.
        :param auth_token: access token of user
        :param user_phone_1: user_phone fixture to assign a test phone number to user
        :return:
        """
        response = requests.get(SMS_CAMPAIGN_API_URL,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 200, 'Status should be Ok (200)'
        assert 'count' in response.json()
        assert 'campaigns' in response.json()
        assert response.json()['count'] == 0
        assert response.json()['campaigns'] == []

    def test_get_with_valid_token_and_multiple_user_phone(self, auth_token,
                                                          user_phone_1,
                                                          user_phone_2):
        """
        User has multiple phone value of type Twilio, it should get internal server error.
        Error code should be 5002 (MultipleTwilioNumbers)
        :param auth_token: access token of user
        :param user_phone_1: fixture to assign one test phone number to user
        :param user_phone_2: fixture to assign another test phone number to user
        :return:
        """
        response = requests.get(SMS_CAMPAIGN_API_URL,
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 500, 'Internal Server Error should occur (500)'
        assert response.json()['error']['code'] == 5002

    def test_post_with_invalid_token(self):
        """
        User auth token is invalid, it should get Unauthorized.
        :return:
        """
        response = requests.post(SMS_CAMPAIGN_API_URL,
                                 headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_post_with_valid_token_and_no_user_phone_and_valid_data(self, auth_token,
                                                                    campaign_valid_data):
        """
        User has no phone value. It should get forbidden error.
        :param auth_token: access token of user
        :return:
        """
        response = requests.post(SMS_CAMPAIGN_API_URL,
                                 headers=dict(Authorization='Bearer %s' % auth_token),
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == 403, 'It should get forbidden error (403)'

    def test_post_with_valid_token_and_requesting_new_twilio_number_and_valid_data(
            self, auth_token, campaign_valid_data):
        """
        User has no phone value. It should get forbidden error.
        :param auth_token: access token of user
        :return:
        """
        campaign_valid_data['buy_new_number'] = True
        response = requests.post(SMS_CAMPAIGN_API_URL,
                                 headers=dict(Authorization='Bearer %s' % auth_token),
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == 201, 'It should create sms campaign (201)'
        assert 'location' in response.headers
        assert 'id' in response.json()

    def test_post_with_valid_token_and_one_user_phone_and_no_data(self,
                                                                  auth_token,
                                                                  user_phone_1):
        """
        User has one phone value, but no data. It should get bad request error.
        :param auth_token: access token of user
        :return:
        """
        response = requests.post(SMS_CAMPAIGN_API_URL,
                                 headers={'Authorization': 'Bearer %s' % auth_token})
        assert response.status_code == 400, 'Should be a bad request (400)'

    def test_post_with_valid_token_and_one_user_phone_and_invalid_data_type(self, auth_token,
                                                                       campaign_valid_data,
                                                                       user_phone_1):
        """
        User has one phone value, valid header and invalid data type (not json).
        It should get bad request error.
        :param auth_token: access token of user
        :param user_phone_1: fixture to create user_phone
        :return:
        """
        response = requests.post(SMS_CAMPAIGN_API_URL,
                                 headers={'Authorization': 'Bearer %s' % auth_token},
                                 data=campaign_valid_data)
        assert response.status_code == 400, 'Should be a bad request (400)'

    def test_post_with_valid_token_and_one_user_phone_and_invalid_data(self, auth_token,
                                                                       campaign_invalid_data,
                                                                       user_phone_1):
        """
        User has one phone value, valid header and invalid data (unknown key_value).
        It should get internal server error. Error code should be 5006.
        :param auth_token: access token of user
        :param user_phone_1: fixture to create user_phone
        :return:
        """
        response = requests.post(SMS_CAMPAIGN_API_URL,
                                 headers={'Authorization': 'Bearer %s' % auth_token},
                                 data=json.dumps(campaign_invalid_data))
        assert response.status_code == 500, 'Internal server error should occur (500)'
        assert response.json()['error']['code'] == 5006

    def test_post_with_valid_token_and_one_user_phone_and_valid_data(self, auth_token,
                                                                     campaign_valid_data,
                                                                     user_phone_1):
        """
        User has one phone value, valid header and valid data.
        It should get ok response (201 status code)
        :param auth_token: access token of user
        :return:
        """
        response = requests.post(SMS_CAMPAIGN_API_URL,
                                 headers={'Authorization': 'Bearer %s' % auth_token},
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == 201, 'Should create campaign (201)'
        assert 'location' in response.headers
        assert 'id' in response.json()

    def test_post_with_valid_token_and_multiple_user_phone_and_valid_data(self, auth_token,
                                                                          campaign_valid_data,
                                                                          user_phone_1,
                                                                          user_phone_2):
        """
        User has multiple phone values, and valid data. It should get internal server error.
        Error code should be 5002 (MultipleTwilioNumbers)
        :param auth_token: access token of user
        :return:
        """
        response = requests.post(SMS_CAMPAIGN_API_URL,
                                 headers={'Authorization': 'Bearer %s' % auth_token},
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == 500, 'Internal Server Error should occur (500)'
        assert response.json()['error']['code'] == 5002

    def test_delete_with_invalid_token(self):
        """
        User auth token is invalid, it should get Unauthorized.
        :return:
        """
        response = requests.delete(SMS_CAMPAIGN_API_URL,
                                   headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_delete_with_valid_token_and_no_data(self, auth_token):
        """
        User auth token is valid, but no data provided. It should get bad request error.
        :return:
        """
        response = requests.delete(SMS_CAMPAIGN_API_URL,
                                   headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 400, 'It should be a bad request (400)'

    def test_delete_with_valid_token_and_not_json_data_type(self, auth_token):
        """
        User auth token is valid, but invalid data type provided.
        It should get bad request error.
        :return:
        """
        response = requests.delete(SMS_CAMPAIGN_API_URL,
                                   headers=dict(Authorization='Bearer %s' % auth_token),
                                   data={
                                       'ids': [1, 2, 3]
                                   })
        assert response.status_code == 400, 'It should be a bad request (400)'

    def test_delete_with_valid_token_and_invalid_data_type(self, auth_token):
        """
        User auth token is valid, but invalid data provided(other than list).
        It should get bad request error.
        :return:
        """
        response = requests.delete(SMS_CAMPAIGN_API_URL,
                                   headers=dict(Authorization='Bearer %s' % auth_token),
                                   data=json.dumps({
                                       'ids': 1
                                   }))
        assert response.status_code == 400, 'It should be a bad request (400)'

    def test_delete_with_valid_token_valid_data_type_invalid_ids(self, auth_token):
        """
        User auth token is valid, but invalid data provided(id other than int).
        It should get bad request error.
        :return:
        """
        response = requests.delete(SMS_CAMPAIGN_API_URL,
                                   headers=dict(Authorization='Bearer %s' % auth_token),
                                   data=json.dumps({
                                       'ids': ['a', 'b', 1]
                                   }))
        assert response.status_code == 400, 'It should be a bad request (400)'

    def test_delete_with_valid_token_valid_data_type_and_valid_ids(self, auth_token,
                                                                   sms_campaign_of_current_user):
        """
        User auth token is valid, data type is valid and ids are valid
        (campaign corresponds to user). Response should be ok.
        :return:
        """
        response = requests.delete(SMS_CAMPAIGN_API_URL,
                                   headers=dict(Authorization='Bearer %s' % auth_token),
                                   data=json.dumps({
                                       'ids': [sms_campaign_of_current_user.id]
                                   }))
        assert response.status_code == 200, 'Response should be ok (200)'

    def test_delete_with_valid_token_valid_data_type_and_unauthorized_ids(self, auth_token,
                                                                          sms_campaign_of_other_user):
        """
        User auth token is valid, data type is valid and ids are of those sms campaigns that
        belong to some other user. It should get unauthorized error.
        :return:
        """
        response = requests.delete(SMS_CAMPAIGN_API_URL,
                                   headers=dict(Authorization='Bearer %s' % auth_token),
                                   data=json.dumps({
                                       'ids': [sms_campaign_of_other_user.id]
                                   }))
        assert response.status_code == 403, 'It should get forbidden error (403)'


class TestSmsCampaignWithId:
    """
    This class contains tests for endpoint /campaigns/:id
    """

    def test_get_with_valid_token_and_valid_id(self, auth_token, sms_campaign_of_current_user):
        """
        User auth token is valid. It uses 'sms_campaign_of_current_user' fixture
        to create an SMS campaign in database. It gets that record from GET HTTP request
        Response should be ok. It then assert all fields of record got from GET call with the
        original field values(provided at time of creation of campaign.
        :return:
        """
        response = requests.get(SMS_CAMPAIGN_API_URL + str(sms_campaign_of_current_user.id),
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 200, 'Response should be ok (200)'
        # verify all the field values
        assert response.json()['campaign']['name'] == sms_campaign_of_current_user.name
        assert response.json()['campaign'][
                   'sms_body_text'] == sms_campaign_of_current_user.sms_body_text
        assert response.json()['campaign'][
                   'frequency_id'] == sms_campaign_of_current_user.frequency_id
        assert response.json()['campaign']['added_time'] == str(
            sms_campaign_of_current_user.added_time)
        assert response.json()['campaign']['send_time'] == str(
            sms_campaign_of_current_user.send_time)
        assert response.json()['campaign']['stop_time'] == str(
            sms_campaign_of_current_user.stop_time)

    def test_get_with_invalid_token(self, sms_campaign_of_current_user):
        """
        User auth token is invalid. It should get Unauthorized error.
        :return:
        """
        response = requests.get(SMS_CAMPAIGN_API_URL + str(sms_campaign_of_current_user.id),
                                headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_get_with_valid_token_and_id_of_deleted_record(self, auth_token,
                                                           sms_campaign_of_current_user):
        """
        User auth token is valid. It deletes the campaign and then GETs the record from db.
        It should get Not Found error.
        :return:
        """
        response = requests.delete(SMS_CAMPAIGN_API_URL + str(sms_campaign_of_current_user.id),
                                   headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 200, 'should get ok response (200)'
        response = requests.get(SMS_CAMPAIGN_API_URL + str(sms_campaign_of_current_user.id),
                                headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 404, 'Record should not be found (404)'

    def test_delete_with_invalid_token(self, sms_campaign_of_current_user):
        """
        User auth token is invalid. It should get Unauthorized error.
        :return:
        """
        response = requests.delete(SMS_CAMPAIGN_API_URL + str(sms_campaign_of_current_user.id),
                                   headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_delete_with_valid_token_and_owned_sms_campaign(self, auth_token,
                                                            sms_campaign_of_current_user):
        """
        User auth token is valid. It deletes the campaign from database.
        It should get ok response.
        :return:
        """
        response = requests.delete(SMS_CAMPAIGN_API_URL + str(sms_campaign_of_current_user.id),
                                   headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 200, 'should get ok response (200)'

    def test_delete_with_valid_token_and_not_owned_sms_campaign(self, auth_token,
                                                                sms_campaign_of_other_user):
        """
        User auth token is valid. It tries to delete the campaign of some other user
        from database. It should get not authorized error.
        :return:
        """
        response = requests.delete(SMS_CAMPAIGN_API_URL + str(sms_campaign_of_other_user.id),
                                   headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 403, 'should not be authorized (403)'

    def test_post_with_valid_token_and_valid_data(self, auth_token, campaign_valid_data,
                                                  sms_campaign_of_current_user):
        """
        This uses fixture to create an sms_campaign record in db. It then makes a POST
        call to update that record with name modification. If status code is 200, it then
        gets the record from database and assert the 'name' of modified record.
        :param auth_token: access token of user
        :return:
        """
        modified_name = 'Modified Name'
        campaign_valid_data.update({'name': modified_name})
        response_post = requests.post(SMS_CAMPAIGN_API_URL + str(sms_campaign_of_current_user.id),
                                      headers=dict(Authorization='Bearer %s' % auth_token),
                                      data=json.dumps(campaign_valid_data))
        assert response_post.status_code == 200, 'Response should be ok (200)'

        # get updated record to verify the change we made in name
        response_get = requests.get(SMS_CAMPAIGN_API_URL + str(sms_campaign_of_current_user.id),
                                    headers=dict(Authorization='Bearer %s' % auth_token),
                                    data=json.dumps(campaign_valid_data))
        assert response_get.status_code == 200, 'Response should be ok (200)'
        assert response_get.json()['campaign']['name'] == modified_name

    def test_post_with_valid_token_and_id_of_deleted_record(self, auth_token,
                                                            sms_campaign_of_current_user,
                                                            campaign_valid_data):
        """
        User auth token is valid. It deletes the campaign from database and then tries
        to update the record. It should get Not Found error.
        :return:
        """
        response = requests.delete(SMS_CAMPAIGN_API_URL + str(sms_campaign_of_current_user.id),
                                   headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 200, 'should get ok response (200)'
        response = requests.post(SMS_CAMPAIGN_API_URL + str(sms_campaign_of_current_user.id),
                                 headers=dict(Authorization='Bearer %s' % auth_token),
                                 data=json.dumps(campaign_valid_data))
        assert response.status_code == 404, 'Record should not be found (404)'

    def test_post_with_invalid_token(self, sms_campaign_of_current_user):
        """
        User auth token is invalid. It should get Unauthorized error.
        :return:
        """
        response = requests.post(SMS_CAMPAIGN_API_URL + str(sms_campaign_of_current_user.id),
                                 headers=dict(Authorization='Bearer %s' % 'invalid_token'))
        assert response.status_code == 401, 'It should be unauthorized (401)'

    def test_post_with_valid_token_and_no_data(self, auth_token, sms_campaign_of_current_user):
        """
        User auth token is valid but no data is provided. It should get bad request error.
        :return:
        """
        response = requests.post(SMS_CAMPAIGN_API_URL + str(sms_campaign_of_current_user.id),
                                 headers=dict(Authorization='Bearer %s' % auth_token))
        assert response.status_code == 400, 'It should get bad request error (400)'

    def test_post_with_valid_token_and_invalid_data_type(self, auth_token,
                                                         campaign_valid_data,
                                                         sms_campaign_of_current_user):
        """
        This tries to update sms_campaign record providing invalid data.
        It should get internal server error.
        Error code should be 5006 (MissingRequiredField)
        """
        response = requests.post(SMS_CAMPAIGN_API_URL + str(sms_campaign_of_current_user.id),
                                 headers={'Authorization': 'Bearer %s' % auth_token},
                                 data=campaign_valid_data)
        assert response.status_code == 400, 'Should be a bad request (400)'

    def test_post_with_valid_token_and_invalid_data(self, auth_token,
                                                    campaign_invalid_data,
                                                    sms_campaign_of_current_user):
        """
        It tries to update the already present sms_campaign record with invalid_data.
        It should get internal server error. Error code should be 5006.
        :param auth_token: access token of user
        :param campaign_invalid_data: fixture to get invalid data to update old record
        :param sms_campaign_of_current_user: fixture to create sms_campaign record in database
                                            fo current user.
        :return:
        """
        response = requests.post(SMS_CAMPAIGN_API_URL + str(sms_campaign_of_current_user.id),
                                 headers={'Authorization': 'Bearer %s' % auth_token},
                                 data=json.dumps(campaign_invalid_data))
        assert response.status_code == 500, 'Internal server error should occur (500)'
        assert response.json()['error']['code'] == 5006
