"""
This module contains tests code that is common across campaign-services. e.g SMS and Push campaign.
"""

# Standard Imports
import sys
import time
import json
import copy
from datetime import (datetime, timedelta)

# Third Party
import pytz
import requests
from redo import retry
from contracts import contract

# Application Specific
from ..models.db import db
from ..models.smartlist import Smartlist
from custom_errors import CampaignException
from ..models.misc import (Frequency, Activity)
from ..utils.datetime_utils import DatetimeUtils
from campaign_utils import get_model, CampaignUtils
from ..utils.validators import raise_if_not_instance_of
from ..custom_errors.campaign import NOT_NON_ZERO_NUMBER
from ..models.talent_pools_pipelines import TalentPipeline
from ..utils.handy_functions import JSON_CONTENT_TYPE_HEADER
from ..tests.fake_testing_data_generator import FakeCandidatesData
from ..utils.test_utils import (get_fake_dict, get_and_assert_zero,
                                delete_smartlist, fake, search_candidates)
from ..routes import (CandidatePoolApiUrl, PushCampaignApiUrl, SmsCampaignApiUrl,
                      EmailCampaignApiUrl)
from ..error_handling import (ForbiddenError, InvalidUsage, UnauthorizedError,
                              ResourceNotFound, UnprocessableEntity, InternalServerError)
from ..inter_service_calls.candidate_pool_service_calls import (create_smartlist_from_api,
                                                                assert_smartlist_candidates)
from ..inter_service_calls.candidate_service_calls import create_candidates_from_candidate_api

__author__ = 'basit'


class CampaignsTestsHelpers(object):
    """
    This class contains common helper methods for tests of sms_campaign_service and push_campaign_service etc.
    """
    # This list is used to update/delete a campaign, e.g. sms-campaign with invalid id
    INVALID_IDS = [fake.word(), 0, None, dict(), list(), '', '        ']
    # This list is used to create/update a campaign, e.g. sms-campaign with invalid name and body_text.
    INVALID_STRINGS = INVALID_IDS[1:]
    # This list is used to schedule/reschedule a campaign e.g. sms-campaign with invalid frequency Id.
    INVALID_FREQUENCY_IDS = copy.copy(INVALID_IDS)
    # Remove 0 from list as it is valid frequency_id and replace it with sys.maxint
    INVALID_FREQUENCY_IDS[1] = sys.maxint
    # Invalid values for required text field
    INVALID_TEXT_VALUES = ['', '  ', 0, {}, [], None, True]
    # Invalid values for boolean field
    INVALID_BOOLEANS = (fake.word(), None, dict(), list(), '', '        ')
    # Invalid values for integers
    INVALID_INTEGERS = (fake.word(), -99, 0, None, dict(), list(), '', '        ')

    @classmethod
    @contract
    def request_for_forbidden_error(cls, method, url, access_token, data=None, expected_error_code=None):
        """
        This should get forbidden error because requested campaign does not belong to logged-in user's domain.
        :param http_method method: Name of HTTP method. e.g. 'get', 'post' etc
        :param string url: URL to to make HTTP request
        :param string access_token: access access_token of user
        :param dict|None data: Data to be send in HTTP request
        :param int|None expected_error_code: Expected error code
        """
        response = send_request(method, url, access_token, data=data)
        error = cls.assert_non_ok_response(response, expected_status_code=ForbiddenError.http_status_code())
        assert error['code'] == expected_error_code, 'Expecting error_code:{}, found:{}'.format(expected_error_code,
                                                                                                error['code'])

    @classmethod
    @contract
    def request_for_resource_not_found_error(cls, method, url, access_token, data=None, expected_error_code=None):
        """
        This should get Resource not found error because requested resource has been deleted.
        :param http_method method: Name of HTTP method. e.g. 'get', 'post' etc
        :param string url: URL to to make HTTP request
        :param string access_token: access access_token of user
        :param dict|None data: Data to be posted
        :param int|None expected_error_code: Expected error code
        """
        response = send_request(method, url, access_token, data=data)
        error = cls.assert_non_ok_response(response, expected_status_code=ResourceNotFound.http_status_code())
        assert error['code'] == expected_error_code, 'Expecting error_code:{}, found:{}'.format(expected_error_code,
                                                                                                error['code'])

    @classmethod
    @contract
    def request_with_invalid_input(cls, method, url, access_token, data=None, is_json=True,
                                   expected_status_code=InvalidUsage.http_status_code(), expected_error_code=None):
        """
        This should get Invalid Usage error because we are requesting with invalid input.
        :param http_method method: Name of HTTP method. e.g. 'get', 'post' etc
        :param string url: URL to make HTTP request
        :param string access_token: access token of user
        :param dict|None data: Data to be posted
        :param bool is_json: If True it means data is already in JSON form
        :param int expected_status_code: Expected status code
        :param int|None expected_error_code: Expected error code
        """
        response = send_request(method, url, access_token, is_json=is_json, data=data)
        error = cls.assert_non_ok_response(response, expected_status_code=expected_status_code)
        assert error['code'] == expected_error_code, 'Expecting error_code:{}, found:{}'.format(expected_error_code,
                                                                                                error['code'])
        return response

    @staticmethod
    @contract
    def request_with_invalid_string(method, url, access_token, data, field, expected_error_code=None):
        """
        This creates or updates a resource with unexpected fields present in the data and
        asserts that we get invalid usage error from respective API. Data passed should be a dictionary
        here.
        :param string method: Name of HTTP method. e.g. 'get', 'post' etc
        :param string url: URL on which we are supposed to make HTTP request
        :param string access_token: Access token of user
        :param dict data: Data to be passed in HTTP request
        :param string field: Field in campaign data
        :param int|None expected_error_code: Expected error code
        """
        CampaignsTestsHelpers._validate_invalid_usage(method, url, access_token, expected_error_code,
                                                      CampaignsTestsHelpers.INVALID_STRINGS, data.copy(), field)

    @staticmethod
    @contract
    def request_with_invalid_integer(method, url, access_token, data, field, expected_error_code=None):
        """
        This creates or updates a resource with invalid integer value of given field in the data and
        asserts that we get invalid usage error from respective API. Data passed should be a dictionary
        here.
        :param string method: Name of HTTP method. e.g. 'get', 'post' etc
        :param string url: URL on which we are supposed to make HTTP request
        :param string access_token: Access token of user
        :param dict data: Data to be passed in HTTP request
        :param string field: Field in campaign data
        :param int|None expected_error_code: Expected error code
        """
        CampaignsTestsHelpers._validate_invalid_usage(method, url, access_token, expected_error_code,
                                                      CampaignsTestsHelpers.INVALID_INTEGERS, data.copy(), field)

    @staticmethod
    @contract
    def request_with_invalid_boolean(method, url, access_token, data, field, expected_error_code=None):
        """
        This creates or updates a resource with invalid value of boolean field present in data.
        It then asserts that we get invalid usage error from respective API.
        :param string method: Name of HTTP method. e.g. 'get', 'post' etc
        :param string url: URL on which we are supposed to make HTTP request
        :param string access_token: Access token of user
        :param dict data: Data to be passed in HTTP request
        :param string field: Field in campaign data
        :param int|None expected_error_code: Expected error code
        """
        CampaignsTestsHelpers._validate_invalid_usage(method, url, access_token, expected_error_code,
                                                      CampaignsTestsHelpers.INVALID_BOOLEANS, data.copy(), field)

    @staticmethod
    @contract
    def _validate_invalid_usage(method, url, access_token, expected_error_code, invalid_items_list, data, field):
        """
        :param string method: Name of HTTP method. e.g. 'get', 'post' etc
        :param string url: URL on which we are supposed to make HTTP request
        :param string access_token: Access token of user
        :param dict data: Data to be passed in HTTP request
        :param string field: Field in campaign data
        :param int|None expected_error_code: Expected error code
        :param list|tuple invalid_items_list: List of invalid items
        :param dict data: Dictionary of data
        :param string field: Some key name in the data
        """
        for invalid_value in invalid_items_list:
            print "Iterating {} as {}".format(invalid_value, field)
            data[field] = invalid_value
            CampaignsTestsHelpers.request_with_invalid_input(method, url, access_token, data,
                                                             expected_error_code=expected_error_code)

    @classmethod
    @contract
    def request_after_deleting_campaign(cls, campaign, url_to_delete_campaign, url_after_delete,
                                        method_after_delete, access_token, data=None):
        """
        This is a helper function to request the given URL after deleting the given resource.
        It should result in ResourceNotFound error.
        :param type(t) campaign: Campaign object
        :param string url_to_delete_campaign: URL to delete given campaign
        :param string url_after_delete: URL to be requested after deleting the campaign
        :param string method_after_delete: Name of method to be requested after deleting campaign
        :param string access_token: access access_token of logged-in user
        :param dict|None data: Data to be sent in request after deleting campaign
        """
        raise_if_not_instance_of(campaign, (dict, CampaignUtils.MODELS))
        campaign_id = campaign.id if hasattr(campaign, 'id') else campaign['id']
        # Delete the campaign first
        response = send_request('delete', url_to_delete_campaign % campaign_id, access_token)
        assert response.ok
        cls.request_for_resource_not_found_error(
            method_after_delete, url_after_delete % campaign_id, access_token, data)

    @staticmethod
    @contract
    def request_for_ok_response(method, url, access_token, data=None):
        """
        This function is expected to schedule a campaign with all valid parameters.
        :param http_method method: Name of HTTP method. e.g. 'get', 'post' etc
        :param string url: URL to to make HTTP request
        :param string access_token: access access_token of user
        :param dict|None data: Data to be posted
        """
        response = send_request(method, url, access_token, data)
        assert response.ok, response.text

    @classmethod
    @contract
    def assert_campaign_schedule_or_reschedule(cls, method, url, access_token, user_id, campaign_id,
                                               url_to_get_campaign, data):
        """
        This function is expected to schedule a campaign with all valid parameters.
        It then gets the campaign and validates that requested fields have been saved in database.
        :param string method: Name of HTTP method. e.g. 'get', 'post' etc
        :param string url: URL to to make HTTP request to schedule/re-schedule campaign
        :param string access_token: access access_token of user
        :param int|long user_id: Id of user
        :param int|long campaign_id: Id of requested campaign
        :param string url_to_get_campaign: URL to get campaign once campaign is scheduled
        :param dict|None data: Data to be posted
        """
        response = send_request(method, url % campaign_id, access_token, data)
        assert response.status_code == requests.codes.OK, response.text
        json_response = response.json()
        assert json_response
        assert 'task_id' in response.json()
        CampaignsTestsHelpers.assert_for_activity(user_id, Activity.MessageIds.CAMPAIGN_SCHEDULE, campaign_id)
        # get updated record to verify the changes we made
        response_get = send_request('get', url_to_get_campaign % campaign_id, access_token)
        assert response_get.status_code == requests.codes.OK, 'Response should be ok (200)'
        resp = response_get.json()['campaign']
        assert resp['frequency'].lower() in Frequency.standard_frequencies()
        assert resp['start_datetime']
        assert resp['end_datetime']
        return json_response['task_id']

    @staticmethod
    @contract
    def request_with_past_start_and_end_datetime(method, url, access_token, data, expected_status_code=None,
                                                 expected_error_code=None):
        """
        Here we pass start_datetime and end_datetime with invalid value i.e. in past, to schedule
        a campaign. Then we assert that we get InvalidUsage error in response.
        :param http_method method: Name of HTTP method. e.g. 'get', 'post' etc
        :param string url: URL to to make HTTP request
        :param string access_token: access access_token of user
        :param dict data: Data to be posted
        :param int|None expected_status_code: Expected status code
        :param int|None expected_error_code: Expected error code
        """
        _assert_invalid_datetime(method, url, access_token, data.copy(), 'start_datetime',
                                 expected_status_code=expected_status_code,
                                 expected_error_code=expected_error_code)
        if 'end_datetime' in data:
            _assert_invalid_datetime(method, url, access_token, data.copy(), 'end_datetime',
                                     expected_status_code=expected_status_code,
                                     expected_error_code=expected_error_code)

    @staticmethod
    @contract
    def missing_fields_in_schedule_data(method, url, access_token, data, expected_status_code=None,
                                        expected_error_code=None):
        """
        Here we try to schedule a campaign with missing required fields and assert that we get
        InvalidUsage error in response.
        :param http_method method: Name of HTTP method. e.g. 'get', 'post' etc
        :param string url: URL to to make HTTP request
        :param string access_token: access access_token of user
        :param dict data: Data to be posted
        :param int|None expected_status_code: Expected status code
        :param int|None expected_error_code: Expected error code
        """
        # Test missing start_datetime field which is mandatory to schedule a campaign
        _assert_api_response_for_missing_field(method, url, access_token, data, 'start_datetime',
                                               expected_status_code=expected_status_code,
                                               expected_error_code=expected_error_code)
        # If periodic job, need to test for end_datetime as well
        if not data['frequency_id'] or not data['frequency_id'] == Frequency.ONCE:
            _assert_api_response_for_missing_field(method, url, access_token, data, 'end_datetime',
                                                   expected_status_code=expected_status_code,
                                                   expected_error_code=expected_error_code)

    @staticmethod
    @contract
    def invalid_datetime_format(method, url, access_token, data, expected_error_code=None):
        """
        Here we pass start_datetime and end_datetime in invalid format to schedule a campaign.
        :param http_method method: Name of HTTP method. e.g. 'get', 'post' etc
        :param string url: URL to to make HTTP request
        :param string access_token: access access_token of user
        :param dict data: Data to be posted
        :param int|None expected_error_code: Expected error code
        """
        assert_invalid_datetime_format(method, url, access_token, data.copy(), 'start_datetime',
                                       expected_error_code=expected_error_code)
        if 'end_datetime' in data:
            assert_invalid_datetime_format(method, url, access_token, data.copy(), 'end_datetime',
                                           expected_error_code=expected_error_code)

    @staticmethod
    @contract
    def request_with_invalid_token(method, url, data=None):
        """
        This is used in tests where we want to make HTTP request on given URL with invalid
        access access_token. It assert that we get ForbiddenError as a result.
        :param http_method method: Name of HTTP method. e.g. 'get', 'post' etc
        :param string url: URL to to make HTTP request
        :param dict|None data: Data to be posted
        """
        _assert_unauthorized(method, url, 'invalid_token', data)

    @staticmethod
    @contract
    def reschedule_with_invalid_data(url, access_token):
        """
        This is used in campaign tests where we want to re-schedule a campaign with invalid data.
        This asserts that we get BadRequest error for every bad data we pass.
        :param string url: URL to to make HTTP request
        :param string access_token: access access_token of user
        """
        _invalid_data_test('put', url, access_token)

    @classmethod
    @contract
    def request_with_invalid_resource_id(cls, model, method, url, access_token, expected_error_code=None, data=None):
        """
        This makes HTTP request (as specified by method) on given URL.
        It creates two invalid ids for requested resource, 0 and some large number(non-existing id)
        that does not exist in database for given model. It then asserts to check we get status
        code 400 in case of id 0 and status code 404 in case of non-existing id.
        :param type(t) model: SQLAlchemy model
        :param http_method method: Name of HTTP method. e.g. 'get', 'post' etc
        :param string url: URL to to make HTTP request
        :param string access_token: access access_token of user
        :param positive|None expected_error_code: Expected custom error code
        :param dict|None data: Data to be posted
        """
        assert db.Model in model.__mro__
        invalid_ids = (0, cls.get_non_existing_id(model))
        invalid_id_and_status_code = _get_invalid_id_and_status_code_pair(invalid_ids)
        for _id, status_code in invalid_id_and_status_code:
            response = send_request(method, url % _id, access_token, data)
            cls.assert_non_ok_response(response, expected_status_code=status_code)
            error_resp = response.json()['error']
            if status_code == ResourceNotFound.http_status_code():
                assert error_resp['code'] == expected_error_code, \
                    "Expecting error_code:{}, Found:{}".format(expected_error_code, error_resp['code'])
            elif status_code == InvalidUsage.http_status_code():
                assert error_resp['code'] == NOT_NON_ZERO_NUMBER[1], \
                    "Expecting error_code:{}, Found:{}".format(NOT_NON_ZERO_NUMBER[1], error_resp['code'])

    @staticmethod
    def get_last_id(model):
        """
        This methods returns the id of last record in given database table.
        If there is no record found, it returns None.
        """
        assert db.Model in model.__mro__
        last_obj = model.query.order_by(model.id.desc()).first()
        return last_obj.id if last_obj else None

    # TODO: Move to common/utils/test_utils.py
    @classmethod
    def get_non_existing_id(cls, model):
        """
        This methods returns the non-existing id for given db Model.
        If last record is found, it adds 1000 in its id and return it.
        Otherwise it returns 100000 which ensures that returned number is a non-existing id for
        given model.
        """
        assert db.Model in model.__mro__
        last_id = cls.get_last_id(model)
        return last_id + 1000 if last_id else 100000

    @classmethod
    def get_non_existing_ids(cls, model):
        """
        This methods returns a tuple of non-existing ids for given db Model.
        """
        assert db.Model in model.__mro__
        return get_invalid_ids(cls.get_non_existing_id(model))

    @classmethod
    @contract
    def reschedule_with_post_method(cls, url, access_token, data):
        """
        To re-schedule a campaign, we have to use PUT HTTP method. But here we will make a
        POST HTTP request which is for first time scheduling and will validate that we get
        forbidden error.
        :param string url: URL to to make HTTP request
        :param string access_token: access access_token of user
        :param dict data: Data to be posted
        """
        response = send_request('post', url, access_token, data)
        cls.assert_non_ok_response(response, expected_status_code=ForbiddenError.http_status_code())

    @staticmethod
    @contract
    def assert_non_ok_response(response, expected_status_code=InvalidUsage.http_status_code()):
        """
        This method is used to assert Invalid usage error in given response
        :param Response response: HTTP response
        :param int expected_status_code: Expected status code
        :return: error dict
        """
        assert response.status_code == expected_status_code, \
            'Expected status code:%s. Got:%s' % (expected_status_code, response.status_code)
        error = response.json()['error']
        assert error, 'error key is missing from response'
        assert error['message']
        return error

    @staticmethod
    @contract
    def campaign_send_with_no_smartlist(url, access_token, campaign_id, expected_error_code):
        """
        This is the test to send a campaign which has no smartlist associated  with it.
        It should get Invalid usage error. Custom error should be NoSmartlistAssociatedWithCampaign.
        :param string url: URL to to make HTTP request
        :param string access_token: access access_token of user
        :param positive campaign_id: Id of campaign
        :param int expected_error_code: Expected error code
        """
        response = send_request('post', url % campaign_id, access_token)
        assert response.status_code == InvalidUsage.http_status_code(), 'It should be invalid usage error(400)'
        error_resp = response.json()['error']
        assert error_resp['code'] == expected_error_code, "Expecting:{}, Found:{}".format(expected_error_code,
                                                                                          error_resp['code'])

    @classmethod
    @contract
    def campaign_send_with_no_smartlist_candidate(cls, url, access_token, campaign, talent_pipeline_id):
        """
        User auth access_token is valid, campaign has one smart list associated. But smartlist has
        no candidate associated with it. The function tries to send the email campaign and resturns the
        response to calling function.
        :param string url: URL to to make HTTP request
        :param string access_token: access access_token of user
        :param type(t) campaign: Campaign object
        :param positive talent_pipeline_id: Id of talent_pipeline
        """
        raise_if_not_instance_of(campaign, CampaignUtils.MODELS)
        smartlist_id = FixtureHelpers.create_smartlist_with_search_params(access_token, talent_pipeline_id)
        campaign_type = campaign.__tablename__
        campaign_smartlist_model = get_model(campaign_type, campaign_type + '_smartlist')
        campaign_smartlist_obj = campaign_smartlist_model(campaign_id=campaign.id, smartlist_id=smartlist_id)
        campaign_smartlist_model.save(campaign_smartlist_obj)
        response_post = send_request('post', url, access_token)
        return response_post

    @classmethod
    @contract
    def assert_campaign_failure(cls, response, campaign, expected_status=200):
        """
        If we try to send a campaign with invalid data, e.g. a campaign with no smartlist associated
        or with 0 candidates, the campaign sending will fail. This method asserts that the specified
        campaign sending failed and no blasts have been created.
        :param Response response: HTTP response object
        :param type(t) campaign: Campaign object
        :param int expected_status: Expected status code
        """
        raise_if_not_instance_of(campaign, CampaignUtils.MODELS)
        assert response.status_code == expected_status, response.text
        assert response.json()
        db.session.commit()
        blasts = campaign.blasts.all()
        assert not blasts, 'Email campaign blasts found for campaign (id:%d)' % campaign.id
        assert len(blasts) == 0

    @classmethod
    @contract
    def campaign_test_with_no_valid_candidate(cls, url, access_token, campaign_id, campaign_service_urls=None):
        """
        This is the test to send campaign to candidate(s) which does not have valid
        data for the campaign to be sent to them. e.g. in case of email_campaign, candidate
        will have no email or for SMS campaign, candidate will not have any mobile number
        associated. We will get 200 response but campaign will not be sent over celery due to invalid data.
        :param string url: URL to to make HTTP request
        :param string access_token: access access_token of user
        :param positive campaign_id: Id of campaign
        :param type(t) campaign_service_urls: routes url class. e.g PushCampaignApiUrl or SmsCampaignApiUrl
        """
        if campaign_service_urls and campaign_service_urls not in (PushCampaignApiUrl, SmsCampaignApiUrl,
                                                                   EmailCampaignApiUrl):
            raise InternalServerError('see docs for valid value of campaign_service_urls')
        response_post = send_request('post', url % campaign_id, access_token)
        assert response_post.status_code == requests.codes.OK, response_post.text
        assert getattr(campaign_service_urls, 'SENDS')
        get_and_assert_zero(getattr(campaign_service_urls, 'SENDS') % campaign_id, 'sends', access_token)
        return response_post

    @staticmethod
    @contract
    def assert_for_activity(user_id, _type, source_id, timeout=80):
        """
        This verifies that activity has been created for given action
        :param positive user_id: Id of user
        :param positive _type: Type number of activity
        :param positive source_id: Id of activity source
        """
        attempts = timeout / 3 + 1
        retry(_assert_activity, args=(user_id, _type, source_id), sleeptime=3, attempts=attempts, sleepscale=1,
              retry_exceptions=(AssertionError,))

    @staticmethod
    @contract
    def assert_ok_response_and_counts(response, count=0, entity='sends', check_count=True):
        """
        This is the common function to assert that response is returning valid 'count'
        and 'sends' or 'replies' for a particular campaign.
        :param Response response: Response object of HTTP request
        :param int count: Number of expected objects
        :param string entity: Name of expected entity
        :param bool check_count: If True, will check number of objects
        """
        assert response.status_code == requests.codes.OK, 'Expecting:200, Found:{}'.format(response.status_code)
        json_response = response.json()
        assert entity in json_response
        if check_count:
            assert len(json_response[entity]) == count
            if not count:  # if count is 0, campaign_sends should be []
                assert not json_response[entity]
            else:
                assert json_response[entity]

    @staticmethod
    @contract
    def send_campaign(url, campaign, access_token, blasts_url=None):
        """
        This function sends the campaign via /v1/email-campaigns/:id/send or
        /v1/sms-campaigns/:id/send depending on campaign type.
        sleep_time is set to be 20s here. One can modify this by passing required value.
        :param string url: URL to hit for sending given campaign
        :param type(t) campaign: Campaign object
        :param string access_token: Auth access_token to make HTTP request
        :param string|None blasts_url: URL to get blasts of given campaign
        """
        raise_if_not_instance_of(campaign, (dict, CampaignUtils.MODELS))
        # send campaign
        campaign_id = campaign.id if hasattr(campaign, 'id') else campaign['id']
        send_url = url % campaign_id
        response = send_request('post', send_url, access_token)
        print 'Campaign object:%s' % campaign.to_dict() if hasattr(campaign, 'to_dict') else campaign
        assert response.ok, response.text
        if blasts_url:
            blasts_url = blasts_url % campaign_id
        blasts = CampaignsTestsHelpers.get_blasts_with_polling(campaign, access_token,
                                                               blasts_url=blasts_url)
        if not blasts:
            raise UnprocessableEntity('blasts not found in given time range.')
        return response

    @staticmethod
    @contract
    def get_blasts(campaign, access_token=None, blasts_url=None, count=None):
        """
        This returns all the blasts associated with given campaign
        :param type(t) campaign: Campaign object
        :param string|None access_token: Access token of user
        :param string|None blasts_url: URL to get blasts of campaign
        :param int|None count: Expected number of blasts
        """
        raise_if_not_instance_of(campaign, (dict, CampaignUtils.MODELS))
        if not blasts_url:
            db.session.commit()
            blasts = campaign.blasts.all()
        else:
            blasts_get_response = send_request('get', blasts_url, access_token)
            blasts = blasts_get_response.json()['blasts'] if blasts_get_response.ok else []
        assert blasts
        if count and isinstance(count, int):
            assert len(blasts) == count, "Expecting blasts count:{}, Found:{}".format(count, len(blasts))
        return blasts

    @staticmethod
    @contract
    def get_blasts_with_polling(campaign, access_token=None, blasts_url=None, timeout=300, count=None):
        """
        This polls the result of blasts of a campaign for given timeout (default 300s).
        :param type(t) campaign: Campaign object
        :param string|None access_token: Access token of user
        :param string|None blasts_url: URL to get blasts of campaign
        :param int|None count: Expected number of blasts
        :param positive timeout: No of seconds for retry function
        """
        raise_if_not_instance_of(campaign, (dict, CampaignUtils.MODELS))
        attempts = timeout / 3 + 1
        return retry(CampaignsTestsHelpers.get_blasts, sleeptime=3, attempts=attempts, sleepscale=1,
                     args=(campaign, access_token, blasts_url, count), retry_exceptions=(AssertionError,))

    @staticmethod
    @contract
    def get_blast_by_index_with_polling(campaign, blast_index=0, access_token=None, blasts_url=None, timeout=20):
        """
        This polls the result of get_blasts_with_index() for given timeout (default 20s).
        :param type(t) campaign: Campaign object
        :param int blast_index: index of campaign's blast
        :param string|None access_token: Access token of user
        :param string|None blasts_url: URL to get blasts of campaign
        :param positive timeout: No of seconds for retry function
        """
        raise_if_not_instance_of(campaign, (dict, CampaignUtils.MODELS))
        attempts = timeout / 3 + 1
        return retry(CampaignsTestsHelpers.get_blast_with_index, sleeptime=3, attempts=attempts, sleepscale=1,
                     args=(campaign, blast_index, access_token, blasts_url), retry_exceptions=(AssertionError,))

    @staticmethod
    @contract
    def get_blast_with_index(campaign, blast_index=0, access_token=None, blasts_url=None):
        """
        This returns one particular blast associated with given campaign as specified by index.
        :param type(t) campaign: Campaign object
        :param int blast_index: index of campaign's blast
        :param string|None access_token: Access token of user
        :param string|None blasts_url: URL to get blasts of campaign
        """
        raise_if_not_instance_of(campaign, (dict, CampaignUtils.MODELS))
        if not blasts_url:
            db.session.commit()
            assert len(campaign.blasts.all()) > blast_index
            blasts = campaign.blasts[blast_index]
        else:
            blasts_get_response = send_request('get', blasts_url, access_token)
            assert blasts_get_response.ok
            blasts = blasts_get_response.json()['blast']
        assert blasts
        return blasts

    @staticmethod
    @contract
    def verify_sends(campaign, expected_count, blast_index, blast_url=None, access_token=None):
        """
        This verifies that we get expected number of sends associated with given blast index of
        given campaign.
        :param type(t) campaign: Campaign object
        :param int expected_count: Expected number of count
        :param int blast_index: index of campaign's blast
        :param string|None blast_url: URL to get blasts of campaign
        :param string|None access_token: Access token of user
        """
        raise_if_not_instance_of(campaign, (dict, CampaignUtils.MODELS))
        db.session.commit()
        if not blast_url:
            blast_sends = campaign.blasts[blast_index].sends
        else:
            response = send_request('get', blast_url, access_token)
            blast_sends = response.json()['blast']['sends']
        assert blast_sends == expected_count, "Expecting sends count:{}, Found:{}".format(expected_count, blast_sends)

    @staticmethod
    @contract
    def assert_blast_sends(campaign, expected_count, blast_index=0, abort_time_for_sends=300,
                           blast_url=None, access_token=None):
        """
        This function asserts that particular blast of given campaign has expected number of sends
        :param type(t) campaign: Campaign object
        :param int expected_count: Expected number of count
        :param int blast_index: index of campaign's blast
        :param int abort_time_for_sends: timeout for retry function
        :param string|None blast_url: URL to get blasts of campaign
        :param string|None access_token: Access token of user
        """
        raise_if_not_instance_of(campaign, (dict, CampaignUtils.MODELS))
        attempts = abort_time_for_sends / 3 + 1
        retry(CampaignsTestsHelpers.verify_sends, sleeptime=5, attempts=attempts, sleepscale=1,
              args=(campaign, expected_count, blast_index, blast_url, access_token),
              retry_exceptions=(AssertionError, IndexError,))

    @staticmethod
    @contract
    def verify_blasts(campaign, expected_count, access_token=None, blasts_url=None):
        """
        This function verifies that given campaign has expected number of blast objects.
        If they are, it returns True, otherwise returns False.
        :param type(t) campaign: Campaign object
        :param int expected_count: Expected number of blasts of campaign
        :param string|None access_token: Access token of user
        :param string|None blasts_url: URL to get blasts of campaign
        """
        raise_if_not_instance_of(campaign, (dict, CampaignUtils.MODELS))
        received_blasts_count = len(CampaignsTestsHelpers.get_blasts(campaign, access_token, blasts_url))
        print 'Expected Blasts:%s' % expected_count
        print 'Received Blasts:%s' % received_blasts_count
        assert received_blasts_count == expected_count

    @staticmethod
    @contract
    def assert_campaign_blasts(campaign, expected_count, access_token=None, blasts_url=None, timeout=10):
        """
        This function polls verify_blasts() to assert that given campaign has expected number
        of blast objects.
        :param type(t) campaign: Campaign object
        :param int expected_count: Expected number of count
        :param string|None access_token: Access token of user
        :param string|None blasts_url: URL to get blasts of campaign
        :param int timeout: timeout for retry function
        """
        raise_if_not_instance_of(campaign, (dict, CampaignUtils.MODELS))
        attempts = timeout / 3 + 1
        retry(CampaignsTestsHelpers.verify_blasts, sleeptime=3, attempts=attempts, sleepscale=1,
              args=(campaign, expected_count, access_token, blasts_url),
              retry_exceptions=(AssertionError,))

    @staticmethod
    @contract(talent_pipeline=TalentPipeline)
    def create_smartlist_with_candidate(access_token, talent_pipeline, count=1, data=None, emails_list=False,
                                        create_phone=False, assert_candidates=True, smartlist_name=fake.word(),
                                        candidate_ids=None, timeout=600):
        """
        This creates candidate(s) as specified by the count and assign it to a smartlist.
        Finally it returns smartlist_id and candidate_ids.
        :param string access_token: Access token of user
        :param int count: Expected number of candidates
        :param dict|None data: Dictionary to create candidates
        :param bool emails_list: If True will create email for candidates
        :param bool create_phone: If True will create phone for candidates
        :param bool assert_candidates: If True will assert that candidates have been uploaded on cloud
        :param string smartlist_name: Name of smartlist
        :param list|tuple|None candidate_ids: List of candidate ids
        :param int timeout: timeout for retry function
        """
        if not data:
            # create candidate
            data = FakeCandidatesData.create(talent_pool=talent_pipeline.talent_pool,
                                             emails_list=emails_list, create_phone=create_phone,
                                             count=count)
        if not candidate_ids:
            candidate_ids = create_candidates_from_candidate_api(access_token, data,
                                                                 return_candidate_ids_only=True)
            if assert_candidates:
                retry(search_candidates, max_sleeptime=60, retry_exceptions=(AssertionError,),
                      args=(candidate_ids, access_token))
        time.sleep(10)
        smartlist_data = {'name': smartlist_name,
                          'candidate_ids': candidate_ids,
                          'talent_pipeline_id': talent_pipeline.id}

        smartlists = create_smartlist_from_api(data=smartlist_data, access_token=access_token)
        smartlist_id = smartlists['smartlist']['id']
        if assert_candidates:
            attempts = timeout / 3 + 1
            retry(assert_smartlist_candidates, sleeptime=3, attempts=attempts, sleepscale=1,
                  retry_exceptions=(AssertionError,), args=(smartlist_id, len(candidate_ids), access_token))
            print '%s candidate(s) found for smartlist(id:%s)' % (len(candidate_ids), smartlist_id)
        return smartlist_id, candidate_ids

    @staticmethod
    @contract(talent_pipeline=TalentPipeline)
    def get_two_smartlists_with_same_candidate(talent_pipeline, access_token, count=1, create_phone=False,
                                               email_list=False, smartlist_and_candidate_ids=None):
        """
        Create two smartlists with same candidate in both of them and returns smartlist ids in list format.
        :param string access_token: Access token of user
        :param int count: Number of candidates in first smartlist
        :param bool create_phone: True if need to create candidate's phone
        :param bool email_list: True if need to create candidate's email
        :param tuple|None smartlist_and_candidate_ids: Tuple contianing smartlist id and associated candidate ids
        :rtype: list
        """
        if smartlist_and_candidate_ids:
            smartlist_1_id, candidate_ids = smartlist_and_candidate_ids
        else:
            smartlist_1_id, candidate_ids = CampaignsTestsHelpers.create_smartlist_with_candidate(
                access_token, talent_pipeline, count=count, create_phone=create_phone, emails_list=email_list)
        # Going to assign candidate belonging to smartlist_1 to smartlist_2 so both will have same candidate
        candidate_ids_for_smartlist_2 = [candidate_ids[0]]
        smartlist_2_id, _ = CampaignsTestsHelpers.create_smartlist_with_candidate(
            access_token, talent_pipeline, candidate_ids=candidate_ids_for_smartlist_2)
        smartlist_ids = [smartlist_1_id, smartlist_2_id]
        return smartlist_ids

    @staticmethod
    @contract
    def assert_valid_datetime_range(datetime_str, minutes=2):
        """
        This asserts that given datetime is in valid range i.e. in neighboured of current datetime.
        1) It should be greater than current datetime - minutes (default=2)
        2) It should be less than current datetime + minutes (default=2)
        :param string datetime_str: Datetime str
        :param int minutes: minutes
        """
        current_datetime = datetime.utcnow().replace(tzinfo=pytz.utc)
        assert DatetimeUtils.utc_isoformat_to_datetime(datetime_str) > current_datetime - timedelta(minutes=minutes)
        assert DatetimeUtils.utc_isoformat_to_datetime(datetime_str) < current_datetime + timedelta(minutes=minutes)

    @staticmethod
    @contract
    def test_api_with_with_unexpected_field_in_data(method, url, access_token, campaign_data):
        """
        This creates or updates a campaign with unexpected fields present in the data and
        asserts that we get invalid usage error from respective API. Data passed should be a dictionary
        here.
        :param http_method method: Name of HTTP method. e.g. 'get', 'post' etc
        :param string url: URL on which we are supposed to make HTTP request
        :param string access_token: Access token of user
        :param dict campaign_data: Data to be passed in HTTP request
        """
        campaign_data['unexpected_key'] = fake.word()
        response = send_request(method, url, access_token, data=campaign_data)
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should result in bad request error because unexpected data was given.'
        assert 'unexpected_key' in response.json()['error']['message']

    @staticmethod
    @contract
    def campaign_create_or_update_with_invalid_smartlist(method, url, access_token, campaign_data,
                                                         field='smartlist_ids', expected_error_code=None):
        """
        This creates or updates a campaign with invalid lists and asserts that we get invalid usage error from
        respective API. Data passed should be a dictionary.
        Invalid smartlist ids include Non-existing id, non-integer id, empty list, duplicate items in list etc.
        :param string method: Name of HTTP method. e.g. 'get', 'post' etc
        :param string url: URL on which we are supposed to make HTTP request
        :param string access_token: Access token of user
        :param string field: Name of key in the data
        :param dict campaign_data: Data to be passed in HTTP request
        :param int|None expected_error_code: Expected error code
        """
        # This list is used to create/update a campaign, e.g. sms-campaign with invalid smartlist ids.
        invalid_lists = [[item] for item in CampaignsTestsHelpers.INVALID_IDS]
        non_existing_smartlist_id = CampaignsTestsHelpers.get_non_existing_id(Smartlist)
        invalid_lists.extend([[non_existing_smartlist_id, non_existing_smartlist_id]])  # Test for unique items
        CampaignsTestsHelpers._validate_invalid_usage(method, url, access_token, expected_error_code, invalid_lists,
                                                      campaign_data.copy(), field)

    @staticmethod
    @contract
    def campaign_schedule_or_reschedule_with_invalid_frequency_id(method, url, access_token, scheduler_data,
                                                                  expected_error_code):
        """
        This creates or updates a campaign with unexpected fields present in the data and
        asserts that we get invalid usage error from respective API. Data passed should be a dictionary
        here.
        :param string method: Name of HTTP method. e.g. 'get', 'post' etc
        :param string url: URL on which we are supposed to make HTTP request
        :param string access_token: Access token of user
        :param dict scheduler_data: Data to be passed in HTTP request to schedule/reschedule given campaign
        :param int expected_error_code: Expected error code
        """
        CampaignsTestsHelpers._validate_invalid_usage(method, url, access_token, expected_error_code,
                                                      CampaignsTestsHelpers.INVALID_FREQUENCY_IDS,
                                                      scheduler_data.copy(), field='frequency_id')

    @staticmethod
    @contract
    def campaigns_delete_with_invalid_data(url, access_token, campaign_model):
        """
        This tests the campaigns' endpoint to delete multiple campaigns with invalid data (non-int ids,
        duplicate ids etc). It should result in Bad Request Error and campaigns should not be removed.
        :param string url: URL on which we are supposed to make HTTP request
        :param string access_token: Access token of user
        :param type(t) campaign_model: Campaign object
        """
        assert db.Model in campaign_model.__mro__
        invalid_data = [[item] for item in CampaignsTestsHelpers.INVALID_IDS]
        non_existing_campaign_id = CampaignsTestsHelpers.get_non_existing_id(campaign_model)
        invalid_data.extend([[non_existing_campaign_id, non_existing_campaign_id]])  # Test for unique items
        for invalid_item in invalid_data:
            print "Iterating %s." % invalid_item
            response = send_request('delete', url, access_token, data={'ids': invalid_item})
            CampaignsTestsHelpers.assert_non_ok_response(response)

    @classmethod
    @contract
    def send_request_with_deleted_smartlist(cls, method, url, token, smartlist_id, expected_error_code, data=None):
        """
        This helper method sends HTTP request to given url and verifies that API raised InvalidUsage 400 error.
        :param http_method method: POST or PUT
        :param string url: target api url
        :param string token: access token
        :param int | long smartlist_id: smartlist id
        :param int expected_error_code: Expected error code
        :param dict|None data: request body
        """
        delete_smartlist(smartlist_id, token)
        response = send_request(method, url, token, data=data)
        error = cls.assert_non_ok_response(response)
        assert error['code'] == expected_error_code, \
            'Expecting error_code:{}, found:{}'.format(expected_error_code, error['code'])

    @staticmethod
    @contract
    def start_datetime_greater_than_end_datetime(method, url, access_token, data={}, expected_status_code=None,
                                                 expected_error_code=None):
        """
        Here we pass start_datetime greater than end_datetime to schedule a campaign. API raised InvalidUsage 400 error.
        :param http_method method: Name of HTTP method: GET or POST
        :param string url: URL to to make HTTP request
        :param string access_token: access access_token of user
        :param dict data: Data to be sent in the request
        :param int|None expected_status_code: Expected status code
        :param int|None expected_error_code: Expected error code
        """
        start_datetime = datetime.utcnow() + timedelta(minutes=50)
        end_datetime = datetime.utcnow() + timedelta(minutes=40)
        data['start_datetime'] = DatetimeUtils.to_utc_str(start_datetime)
        data['end_datetime'] = DatetimeUtils.to_utc_str(end_datetime)
        data['frequency_id'] = Frequency.DAILY
        response = send_request(method, url, access_token, data=data)
        error = CampaignsTestsHelpers.assert_non_ok_response(response, expected_status_code=expected_status_code)
        assert error['code'] == expected_error_code, 'Expecting error_code:{}, found:{}'.format(expected_error_code,
                                                                                                error['code'])

    @staticmethod
    def base_campaign_data():
        """
        This returns data to create base-campaign.
        """
        return {
            'name': fake.name(),
            'description': fake.sentence()
        }


class FixtureHelpers(object):
    """
    This contains the functions which will be useful for similar fixtures across campaigns
    """

    @classmethod
    @contract
    def create_smartlist_with_search_params(cls, access_token, talent_pipeline_id):
        """
        This creates a smartlist with search params and returns the id of smartlist
        :param string access_token: Access token of user
        :param positive talent_pipeline_id: Id of talent_pipeline
        """
        name = fake.word()
        search_params = {"maximum_years_experience": "5", "location": "San Jose, CA",
                         "minimum_years_experience": "2"}
        data = {'name': name, 'search_params': search_params,
                'talent_pipeline_id': talent_pipeline_id}
        response = send_request('post', CandidatePoolApiUrl.SMARTLISTS, access_token, data)
        assert response.status_code == requests.codes.CREATED  # Successfully created
        json_resp = response.json()
        assert 'smartlist' in json_resp
        assert 'id' in json_resp['smartlist']
        return json_resp['smartlist']['id']


@contract
def send_request(method, url, access_token, data=None, is_json=True, data_dumps=True):
    """
    :param http_method method: Name of HTTP method. e.g. 'get', 'post' etc
    :param string url: URL to to make HTTP request
    :param string access_token: access access_token of user
    :param dict|None data: Data to be posted
    :param bool is_json: If True it means data is already in JSON form
    :param bool data_dumps: If True, will take dumps of data
    """
    # This method is being used for test cases, so it is sure that method has
    #  a valid value like 'get', 'post' etc.test_reschedule_with_invalid_token
    request_method = getattr(requests, method.lower())
    headers = dict(Authorization='Bearer %s' % access_token)
    if is_json:
        headers['Content-Type'] = JSON_CONTENT_TYPE_HEADER['content-type']
    if data_dumps:
        data = json.dumps(data)
    return request_method(url, data=data, headers=headers)


def get_invalid_fake_dict():
    """
    This method just creates a dictionary with 3 random keys and values

    : Example:

        data = {
                    'excepturi': 'qui',
                    'unde': 'ipsam',
                    'magni': 'voluptate'
                }
    :return: data
    :rtype dict
    """
    fake_dict = get_fake_dict()
    fake_dict[len(fake_dict.keys()) - 1] = [fake.word]
    return fake_dict


@contract
def _assert_api_response_for_missing_field(method, url, access_token, data, field_to_remove,
                                           expected_status_code=None, expected_error_code=None):
    """
    This function removes the field from data as specified by field_to_remove, and
    then POSTs data on given URL. It then asserts that removed filed is in error_message.
    :param http_method method: Name of HTTP method. e.g. 'get', 'post' etc
    :param string url: URL to to make HTTP request
    :param string access_token: access access_token of user
    :param dict data: Data to be posted
    :param string field_to_remove: Name of field we want to remove from given data
    :param int|None expected_status_code: Expected status code
    :param int|None expected_error_code: Expected error code
    """
    removed_value = data[field_to_remove]
    del data[field_to_remove]
    response = send_request(method, url, access_token, data)
    error = CampaignsTestsHelpers.assert_non_ok_response(response, expected_status_code=expected_status_code)
    assert error['code'] == expected_error_code, 'Expecting error_code:{}, found:{}'.format(expected_error_code,
                                                                                            error['code'])
    assert field_to_remove in error['message'], '%s should be in error_message' % field_to_remove
    # assign removed field again
    data[field_to_remove] = removed_value


# TODO: Move to common/utils/test_utils.py
@contract
def assert_invalid_datetime_format(method, url, access_token, data, key, expected_error_code=None):
    """
    Here we modify field of data as specified by param 'key' and then assert the invalid usage
    error in response of HTTP request.
    :param http_method method: Name of HTTP method. e.g. 'get', 'post' etc
    :param string url: URL to to make HTTP request
    :param string access_token: access access_token of user
    :param dict data: Data to be posted
    :param string key: Name of field we want to make invalidly formatted
    :param int|None expected_error_code: Expected error code
    """
    str_datetime = str(datetime.utcnow())
    data[key] = str_datetime  # Invalid datetime format
    response = send_request(method, url, access_token, data)
    error = CampaignsTestsHelpers.assert_non_ok_response(response)
    assert error['code'] == expected_error_code, 'Expecting error_code:{}, found:{}'.format(expected_error_code,
                                                                                            error['code'])


@contract
def _assert_invalid_datetime(method, url, access_token, data, key, expected_status_code=None,
                             expected_error_code=None):
    """
    Here we set datetime field of data to as specified by param 'key' to past and then assert
    the invalid usage error in response of HTTP request.
    :param http_method method: Name of HTTP method. e.g. 'get', 'post' etc
    :param string url: URL to make HTTP request
    :param string access_token: access_token of user
    :param dict data: Data to be posted
    :param string key: Name of field we want to assert invalidity on
    :param int|None expected_status_code: Expected status code
    :param int|None expected_error_code: Expected error code
    """
    data[key] = DatetimeUtils.to_utc_str(datetime.utcnow() - timedelta(hours=10))  # Past datetime
    response = send_request(method, url, access_token, data)
    error = CampaignsTestsHelpers.assert_non_ok_response(response, expected_status_code=expected_status_code)
    assert error['code'] == expected_error_code, 'Expecting error_code:{}, found:{}'.format(expected_error_code,
                                                                                            error['code'])


@contract
def _assert_unauthorized(method, url, access_token, data=None):
    """
    For a given URL, here we request with invalid access_token and assert that we get Unauthorized error.
    :param http_method method: Name of HTTP method. e.g. 'get', 'post' etc
    :param string url: URL to to make HTTP request
    :param string access_token: access access_token of user
    :param dict|None data: Data to be posted
     """
    response = send_request(method, url, access_token, data)
    assert response.status_code == UnauthorizedError.http_status_code(), \
        'Expecting:401, Found:{}'.format(response.status_code)
    assert response.json()['error']['code'] == 11, \
        'Expecting error_code:11, Found:{}'.format(response.json()['error']['code'])


@contract
def _invalid_data_test(method, url, access_token):
    """
    This is used to make HTTP request as specified by 'method' on given URL and assert invalid
    usage error in response.
    :param http_method method: Name of HTTP method. e.g. 'get', 'post' etc
    :param string url: URL to to make HTTP request
    :param string access_token: access access_token of user
    """
    # test with None Data
    data = None
    response = send_request(method, url, access_token, data)
    CampaignsTestsHelpers.assert_non_ok_response(response)
    # Test with empty dict
    data = {}
    CampaignsTestsHelpers.assert_non_ok_response(response)
    response = send_request(method, url, access_token, data)
    CampaignsTestsHelpers.assert_non_ok_response(response)
    # Test with valid data and invalid header
    data = get_fake_dict()
    response = send_request(method, url, access_token, data, is_json=False)
    CampaignsTestsHelpers.assert_non_ok_response(response)
    # Test with Non JSON data and valid header
    data = get_invalid_fake_dict()
    response = send_request(method, url, access_token, data, data_dumps=False)
    CampaignsTestsHelpers.assert_non_ok_response(response)


@contract
def get_invalid_ids(non_existing_id):
    """
    Given a database model object, here we create a list of two invalid ids. One of them
    is 0 and other one is non-existing id for a particular model.
    :param positive non_existing_id: Id that does not exist in database for a particular model.
    """
    return 0, non_existing_id


@contract
def _get_invalid_id_and_status_code_pair(invalid_ids):
    """
    This associates expected status code with given list of invalid_ids.
    i.e. 400 for invalid id e.g. 0 and 404 for non-existing record
    :param list|tuple invalid_ids: List or tuple of invalid ids
    """
    return [(invalid_ids[0], InvalidUsage.http_status_code()),
            (invalid_ids[1], ResourceNotFound.http_status_code())]


@contract
def _assert_activity(user_id, _type, source_id):
    """
    This gets that activity from database table Activity for given params
    :param positive user_id: Id of user
    :param positive _type: Type number of activity
    :param positive source_id: Id of activity source
    """
    # Need to commit the session because Celery has its own session, and our session does not
    # know about the changes that Celery session has made.
    db.session.commit()
    activity = Activity.get_by_user_id_type_source_id(user_id, _type, source_id)
    assert activity
