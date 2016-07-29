"""
This module contains tests code that is common across campaign-services. e.g SMS and Push campaign.
"""

__author__ = 'basit'

# Standard Imports
import sys
import time
import json
import copy
from datetime import datetime, timedelta

# Third Party
import pytz
import requests
from redo import retry
from contracts import contract

# Application Specific
from ..models.db import db
from ..tests.conftest import fake
from campaign_utils import get_model
from ..models.smartlist import Smartlist
from ..routes import CandidatePoolApiUrl
from custom_errors import CampaignException
from ..utils.test_utils import get_fake_dict
from ..models.misc import (Frequency, Activity)
from ..utils.datetime_utils import DatetimeUtils
from ..custom_contracts import define_custom_contracts
from ..utils.handy_functions import JSON_CONTENT_TYPE_HEADER
from ..tests.fake_testing_data_generator import FakeCandidatesData
from ..error_handling import (ForbiddenError, InvalidUsage, UnauthorizedError,
                              ResourceNotFound, UnprocessableEntity)
from ..inter_service_calls.candidate_pool_service_calls import (create_smartlist_from_api,
                                                                assert_smartlist_candidates)
from ..inter_service_calls.candidate_service_calls import create_candidates_from_candidate_api

define_custom_contracts()


class CampaignsTestsHelpers(object):
    """
    This class contains common helper methods for tests of sms_campaign_service and push_campaign_service etc.
    """
    # This list is used to update/delete a campaign, e.g. sms-campaign with invalid id
    INVALID_ID = [fake.word(), 0, None, dict(), list(), '', '      ']
    # This list is used to create/update a campaign, e.g. sms-campaign with invalid name and body_text.
    INVALID_STRING = INVALID_ID[1:]
    # This list is used to schedule/reschedule a campaign e.g. sms-campaign with invalid frequency Id.
    INVALID_FREQUENCY_IDS = copy.copy(INVALID_ID)
    # Remove 0 from list as it is valid frequency_id and replace it with three digit frequency_id
    INVALID_FREQUENCY_IDS[1] = int(fake.numerify())

    @classmethod
    @contract
    def request_for_forbidden_error(cls, method, url, access_token,data=None):
        """
        This should get forbidden error because requested campaign does not belong to logged-in user's domain.
        :param http_method method: Name of HTTP method
        :param string url: URL to to make HTTP request
        :param string access_token: access access_token of user
        :param dict|None data: Data to be send in HTTP request
        """
        response = send_request(method, url, access_token, data=data)
        cls.assert_non_ok_response(response, expected_status_code=ForbiddenError.http_status_code())

    @classmethod
    @contract
    def request_for_resource_not_found_error(cls, method, url, access_token, data=None):
        """
        This should get Resource not found error because requested resource has been deleted.
        :param http_method method: Name of HTTP method
        :param string url: URL to to make HTTP request
        :param string access_token: access access_token of user
        :param dict|None data: Data to be posted
        """
        response = send_request(method, url, access_token, data=data)
        cls.assert_non_ok_response(response, expected_status_code=ResourceNotFound.http_status_code())

    @classmethod
    @contract
    def request_after_deleting_campaign(cls, campaign, url_to_delete_campaign, url_after_delete,
                                        method_after_delete, access_token, data=None):
        """
        This is a helper function to request the given URL after deleting the given resource.
        It should result in ResourceNotFound error.
        :param dict campaign: dict of campaign object
        :param string url_to_delete_campaign: URL to delete given campaign
        :param string url_after_delete: URL to be requested after deleting the campaign
        :param string method_after_delete: Name of method to be requested after deleting campaign
        :param string access_token: access access_token of logged-in user
        :param dict|None data: Data to be sent in request after deleting campaign
        """
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
        :param http_method method: Name of HTTP method
        :param string url: URL to to make HTTP request
        :param string access_token: access access_token of user
        :param dict|None data: Data to be posted
        """
        response = send_request(method, url, access_token, data)
        assert response.ok

    @classmethod
    @contract
    def assert_campaign_schedule_or_reschedule(cls, method, url, access_token, user_id, campaign_id,
                                               url_to_get_campaign,
                                               data):
        """
        This function is expected to schedule a campaign with all valid parameters.
        It then gets the campaign and validates that requested fields have been saved in database.
        :param string method: Name of HTTP method
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
    def request_with_past_start_and_end_datetime(method, url, access_token, data):
        """
        Here we pass start_datetime and end_datetime with invalid value i.e. in past, to schedule
        a campaign. Then we assert that we get InvalidUsage error in response.
        :param http_method method: Name of HTTP method
        :param string url: URL to to make HTTP request
        :param string access_token: access access_token of user
        :param dict data: Data to be posted
        """
        _assert_invalid_datetime(method, url, access_token, data, 'start_datetime')
        if not data['frequency_id'] or not data['frequency_id'] == Frequency.ONCE:
            _assert_invalid_datetime(method, url, access_token, data, 'end_datetime')

    @staticmethod
    @contract
    def missing_fields_in_schedule_data(method, url, access_token, data):
        """
        Here we try to schedule a campaign with missing required fields and assert that we get
        InvalidUsage error in response.
        :param http_method method: Name of HTTP method
        :param string url: URL to to make HTTP request
        :param string access_token: access access_token of user
        :param dict data: Data to be posted
        """
        # Test missing start_datetime field which is mandatory to schedule a campaign
        _assert_api_response_for_missing_field(method, url, access_token, data, 'start_datetime')
        # If periodic job, need to test for end_datetime as well
        if not data['frequency_id'] or not data['frequency_id'] == Frequency.ONCE:
            _assert_api_response_for_missing_field(method, url, access_token, data, 'end_datetime')

    @staticmethod
    @contract
    def invalid_datetime_format(method, url, access_token, data):
        """
        Here we pass start_datetime and end_datetime in invalid format to schedule a campaign.
        :param http_method method: Name of HTTP method
        :param string url: URL to to make HTTP request
        :param string access_token: access access_token of user
        :param dict data: Data to be posted
        """
        _assert_invalid_datetime_format(method, url, access_token, data, 'start_datetime')
        if not data['frequency_id'] or not data['frequency_id'] == Frequency.ONCE:
            _assert_invalid_datetime_format(method, url, access_token, data, 'end_datetime')

    @staticmethod
    @contract
    def request_with_invalid_token(method, url, data=None):
        """
        This is used in tests where we want to make HTTP request on given URL with invalid
        access access_token. It assert that we get ForbiddenError as a result.
        :param http_method method: Name of HTTP method
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
    def request_with_invalid_resource_id(cls, model, method, url, access_token, data=None):
        """
        This makes HTTP request (as specified by method) on given URL.
        It creates two invalid ids for requested resource, 0 and some large number(non-existing id)
        that does not exist in database for given model. It then asserts to check we get status
        code 400 in case of id 0 and status code 404 in case of non-existing id.
        :param model_class model: SQLAlchemy model
        :param http_method method: Name of HTTP method
        :param string url: URL to to make HTTP request
        :param string access_token: access access_token of user
        :param dict|None data: Data to be posted
        """
        invalid_ids = (0, cls.get_non_existing_id(model))
        invalid_id_and_status_code = _get_invalid_id_and_status_code_pair(invalid_ids)
        for _id, status_code in invalid_id_and_status_code:
            response = send_request(method, url % _id, access_token, data)
            assert response.status_code == status_code

    @staticmethod
    @contract
    def get_last_id(model):
        """
        This methods returns the id of last record in given database table.
        If there is no record found, it returns None.
        :param model_class model: SQLAlchemy model
        """
        last_obj = model.query.order_by(model.id.desc()).first()
        return last_obj.id if last_obj else None

    @classmethod
    @contract
    def get_non_existing_id(cls, model):
        """
        This methods returns the non-existing id for given db Model.
        If last record is found, it adds 1000 in its id and return it.
        Otherwise it returns sys.maxint which ensures that returned number is a non-existing id for
        given model.
        :param model_class model: SQLAlchemy model
        """
        last_id = cls.get_last_id(model)
        return last_id + 1000 if last_id else sys.maxint

    @classmethod
    @contract
    def get_non_existing_ids(cls, model):
        """
        This methods returns a tuple of non-existing ids for given db Model.
        :param model_class model: SQLAlchemy model
        """
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
    def campaign_send_with_no_smartlist(url, access_token):
        """
        This is the test to send a campaign which has no smartlist associated  with it.
        It should get Invalid usage error. Custom error should be
        NoSmartlistAssociatedWithCampaign.
        :param string url: URL to to make HTTP request
        :param string access_token: access access_token of user
        """
        response = send_request('post', url, access_token, None)
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be invalid usage error(400)'
        error_resp = response.json()['error']
        assert error_resp['code'] == CampaignException.NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN
        assert 'No Smartlist'.lower() in error_resp['message'].lower()

    @classmethod
    @contract
    def campaign_send_with_no_smartlist_candidate(cls, url, access_token, campaign, talent_pipeline_id):
        """
        User auth access_token is valid, campaign has one smart list associated. But smartlist has
        no candidate associated with it. The function tries to send the email campaign and resturns the
        response to calling function.
        :param string url: URL to to make HTTP request
        :param string access_token: access access_token of user
        :param campaign_models campaign: Campaign object
        :param positive talent_pipeline_id: Id of talent_pipeline
        """
        smartlist_id = FixtureHelpers.create_smartlist_with_search_params(access_token,
                                                                          talent_pipeline_id)
        campaign_type = campaign.__tablename__
        #  Need to do this because cannot make changes until prod is stable
        campaign_smartlist_model = get_model(campaign_type,
                                             campaign_type + '_smartlist')
        campaign_smartlist_obj = campaign_smartlist_model(campaign_id=campaign.id,
                                                          smartlist_id=smartlist_id)
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
        :param campaign_models campaign: Campaigns' model object
        :param int expected_status: Expected status code
        """
        assert response.status_code == expected_status
        assert response.json()
        db.session.commit()
        blasts = campaign.blasts.all()
        assert not blasts, 'Email campaign blasts found for campaign (id:%d)' % campaign.id
        assert len(blasts) == 0

    @classmethod
    @contract
    def campaign_test_with_no_valid_candidate(cls, url, access_token, campaign_id):
        """
        This is the test to send campaign to candidate(s) who do not have valid
        data for the campaign to be sent to them. e.g. in case of email_campaign, candidate
        will have no email or for SMS campaign, candidate will not have any mobile number
        associated. This should assert custom error NO_VALID_CANDIDATE_FOUND in response.
        :param string url: URL to to make HTTP request
        :param string access_token: access access_token of user
        :param positive campaign_id: Id of campaign
        """
        response_post = send_request('post', url, access_token)
        error_resp = cls.assert_non_ok_response(response_post)
        assert error_resp['code'] == CampaignException.NO_VALID_CANDIDATE_FOUND
        assert str(campaign_id) in error_resp['message']

    @staticmethod
    @contract
    def assert_for_activity(user_id, _type, source_id):
        """
        This verifies that activity has been created for given action
        :param positive user_id: Id of user
        :param positive _type: Type number of activity
        :param positive source_id: Id of activity source
        """
        retry(_assert_activity, args=(user_id, _type, source_id), sleeptime=3, attempts=20, sleepscale=1,
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
        assert response.status_code == requests.codes.OK, 'Response should be "OK" (200)'
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
        :param campaign_models|dict campaign: Campaign object
        :param string access_token: Auth access_token to make HTTP request
        :param string|None blasts_url: URL to get blasts of given campaign
        """
        # send campaign
        campaign_id = campaign.id if hasattr(campaign, 'id') else campaign['id']
        send_url = url % campaign_id
        response = send_request('post', send_url, access_token)
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
    def get_blasts(campaign, access_token=None, blasts_url=None):
        """
        This returns all the blasts associated with given campaign
        :param campaign_models|dict campaign: Campaign object
        :param string|None access_token: Access token of user
        :param string|None blasts_url: URL to get blasts of campaign
        """
        if not blasts_url:
            db.session.commit()
            blasts = campaign.blasts.all()
        else:
            blasts_get_response = send_request('get', blasts_url, access_token)
            blasts = blasts_get_response.json()['blasts'] if blasts_get_response.ok else []
        assert blasts
        return blasts

    @staticmethod
    @contract
    def get_blasts_with_polling(campaign, access_token=None, blasts_url=None, timeout=300):
        """
        This polls the result of blasts of a campaign for given timeout (default 300s).
        :param campaign_models|dict campaign: Campaign object
        :param string|None access_token: Access token of user
        :param string|None blasts_url: URL to get blasts of campaign
        :param positive timeout: No of seconds for retry function
        """
        attempts = timeout / 3 + 1
        return retry(CampaignsTestsHelpers.get_blasts, sleeptime=3, attempts=attempts, sleepscale=1,
                     args=(campaign, access_token, blasts_url), retry_exceptions=(AssertionError,))

    @staticmethod
    @contract
    def get_blast_by_index_with_polling(campaign, blast_index=0, access_token=None, blasts_url=None, timeout=20):
        """
        This polls the result of get_blasts_with_index() for given timeout (default 10s).
        :param campaign_models|dict campaign: Campaign object
        :param int blast_index: index of campaign's blast
        :param string|None access_token: Access token of user
        :param string|None blasts_url: URL to get blasts of campaign
        :param positive timeout: No of seconds for retry function
        """
        attempts = timeout / 3 + 1
        return retry(CampaignsTestsHelpers.get_blast_with_index, sleeptime=3, attempts=attempts, sleepscale=1,
                     args=(campaign, blast_index, access_token, blasts_url), retry_exceptions=(AssertionError,))

    @staticmethod
    @contract
    def get_blast_with_index(campaign, blast_index=0, access_token=None, blasts_url=None):
        """
        This returns one particular blast associated with given campaign as specified by index.
        :param campaign_models|dict campaign: Campaign object
        :param int blast_index: index of campaign's blast
        :param string|None access_token: Access token of user
        :param string|None blasts_url: URL to get blasts of campaign
        """
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
        :param campaign_models|dict campaign: Campaign object
        :param int expected_count: Expected number of count
        :param int blast_index: index of campaign's blast
        :param string|None blast_url: URL to get blasts of campaign
        :param string|None access_token: Access token of user
        """
        db.session.commit()
        if not blast_url:
            assert campaign.blasts[blast_index].sends == expected_count
        else:
            response = send_request('get', blast_url, access_token)
            if response.ok:
                assert response.json()['blast']['sends'] == expected_count

    @staticmethod
    @contract
    def assert_blast_sends(campaign, expected_count, blast_index=0, abort_time_for_sends=300,
                           blast_url=None, access_token=None):
        """
        This function asserts that particular blast of given campaign has expected number of sends
        :param campaign_models|dict campaign: Campaign object
        :param int expected_count: Expected number of count
        :param int blast_index: index of campaign's blast
        :param int abort_time_for_sends: timeout for retry function
        :param string|None blast_url: URL to get blasts of campaign
        :param string|None access_token: Access token of user
        """
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
        :param campaign_models|dict campaign: Campaign object
        :param int expected_count: Expected number of blasts of campaign
        :param string|None access_token: Access token of user
        :param string|None blasts_url: URL to get blasts of campaign
        """
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
        :param campaign_models|dict campaign: Campaign object
        :param int expected_count: Expected number of count
        :param string|None access_token: Access token of user
        :param string|None blasts_url: URL to get blasts of campaign
        :param int timeout: timeout for retry function
        """
        attempts = timeout / 3 + 1
        retry(CampaignsTestsHelpers.verify_blasts, sleeptime=3, attempts=attempts, sleepscale=1,
              args=(campaign, expected_count, access_token, blasts_url),
              retry_exceptions=(AssertionError,))

    @staticmethod
    @contract
    def create_smartlist_with_candidate(access_token, talent_pipeline, count=1, data=None,
                                        emails_list=False, create_phone=False,
                                        assert_candidates=True, smartlist_name=fake.word(),
                                        candidate_ids=(), timeout=300):
        """
        This creates candidate(s) as specified by the count and assign it to a smartlist.
        Finally it returns smartlist_id and candidate_ids.
        :param string access_token: Access token of user
        :param model talent_pipeline: Talent Pipeline object
        :param int count: Expected number of candidates
        :param dict|None data: Dictionary to create candidates
        :param bool emails_list: If True will create email for candidates
        :param bool create_phone: If True will create phone for candidates
        :param bool assert_candidates: If True will assert that candidates have been uploaded on cloud
        :param string smartlist_name: Name of smartlist
        :param list|tuple candidate_ids: List of candidate ids
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
                time.sleep(30)  # TODO: Need to remove this and use polling instead
        smartlist_data = {'name': smartlist_name,
                          'candidate_ids': candidate_ids,
                          'talent_pipeline_id': talent_pipeline.id}

        smartlists = create_smartlist_from_api(data=smartlist_data, access_token=access_token)
        smartlist_id = smartlists['smartlist']['id']
        if assert_candidates:
            attempts = timeout / 3 + 1
            retry(assert_smartlist_candidates, sleeptime=3, attempts=attempts, sleepscale=1,
                  args=(smartlist_id, len(candidate_ids), access_token), retry_exceptions=(AssertionError,))
            print '%s candidate(s) found for smartlist(id:%s)' % (len(candidate_ids), smartlist_id)
        return smartlist_id, candidate_ids

    @staticmethod
    @contract
    def get_two_smartlists_with_same_candidate(talent_pipeline, access_token, count=1, create_phone=False,
                                               email_list=False):
        """
        Create two smartlists with same candidate in both of them and returns smartlist ids in list format.
        :param model talent_pipeline: Talent pipeline object of user
        :param string access_token: Access token of user
        :param int count: Number of candidates in first smartlist
        :param bool create_phone: True if need to create candidate's phone
        :param bool email_list: True if need to create candidate's email
        :rtype: list
        """
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
        :param http_method method: Name of HTTP method
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
    def campaign_create_or_update_with_invalid_string(method, url, access_token, campaign_data, field):
        """
        This creates or updates a campaign with unexpected fields present in the data and
        asserts that we get invalid usage error from respective API. Data passed should be a dictionary
        here.
        :param str method: Name of HTTP method
        :param str url: URL on which we are supposed to make HTTP request
        :param str access_token: Access token of user
        :param dict campaign_data: Data to be passed in HTTP request
        :param str field: Field in campaign data
        """
        for invalid_campaign_name in CampaignsTestsHelpers.INVALID_STRING:
            print "Iterating %s as campaign name/body_text" % invalid_campaign_name
            campaign_data[field] = invalid_campaign_name
            response = send_request(method, url, access_token, data=campaign_data)
            CampaignsTestsHelpers.assert_non_ok_response(response)

    @staticmethod
    def campaign_create_or_update_with_invalid_smartlist(method, url, access_token, campaign_data):
        """
        This creates or updates a campaign with invalid lists and asserts that we get invalid usage error from
        respective API. Data passed should be a dictionary.
        Invalid smartlist ids include Non-existing id, non-integer id, empty list, duplicate items in list etc.
        :param str method: Name of HTTP method
        :param str url: URL on which we are supposed to make HTTP request
        :param str access_token: Access token of user
        :param dict campaign_data: Data to be passed in HTTP request
        """
        # This list is used to create/update a campaign, e.g. sms-campaign with invalid smartlist ids.
        invalid_lists = [[item] for item in CampaignsTestsHelpers.INVALID_ID]
        non_existing_smartlist_id = CampaignsTestsHelpers.get_non_existing_id(Smartlist)
        invalid_lists.extend([non_existing_smartlist_id, non_existing_smartlist_id])  # Test for unique items
        for invalid_list in invalid_lists:
            print "Iterating %s" % invalid_list
            campaign_data['smartlist_ids'] = invalid_list
            response = send_request(method, url, access_token, data=campaign_data)
            CampaignsTestsHelpers.assert_non_ok_response(response)

    @staticmethod
    def campaign_schedule_or_reschedule_with_invalid_frequency_id(method, url, access_token, scheduler_data):
        """
        This creates or updates a campaign with unexpected fields present in the data and
        asserts that we get invalid usage error from respective API. Data passed should be a dictionary
        here.
        :param str method: Name of HTTP method
        :param str url: URL on which we are supposed to make HTTP request
        :param str access_token: Access token of user
        :param dict scheduler_data: Data to be passed in HTTP request to schedule/reschedule given campaign
        """
        for invalid_frequency_id in CampaignsTestsHelpers.INVALID_FREQUENCY_IDS:
            print "Iterating %s as frequency_id" % invalid_frequency_id
            scheduler_data['frequency_id'] = invalid_frequency_id
            response = send_request(method, url, access_token, data=scheduler_data)
            CampaignsTestsHelpers.assert_non_ok_response(response)

    @staticmethod
    def campaigns_delete_with_invalid_data(url, access_token, campaign_model):
        """
        This tests the campaigns' endpoint to delete multiple campaigns with invalid data (non-int ids,
        duplicate ids etc). It should result in Bad Request Error and campaigns should not be removed.
        :param str url: URL on which we are supposed to make HTTP request
        :param str access_token: Access token of user
        :param (db.Model) campaign_model: SQLAlchemy model
        """
        invalid_data = [[item] for item in CampaignsTestsHelpers.INVALID_ID]
        non_existing_campaign_id = CampaignsTestsHelpers.get_non_existing_id(campaign_model)
        invalid_data.extend([[non_existing_campaign_id, non_existing_campaign_id]])  # Test for unique items
        for invalid_item in invalid_data:
            print "Iterating %s." % invalid_item
            response = send_request('delete', url, access_token, data={'ids': invalid_item})
            CampaignsTestsHelpers.assert_non_ok_response(response)


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
    :param http_method method: Name of HTTP method
    :param string url: URL to to make HTTP request
    :param string access_token: access access_token of user
    :param dict|None data: Data to be posted
    :param bool is_json: If True it means data is already in JSON form
    :param bool data_dumps: If True, will take dumps of data
    """
    # This method is being used for test cases, so it is sure that method has
    #  a valid value like 'get', 'post' etc.test_reschedule_with_invalid_token
    request_method = getattr(requests, method)
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
def _assert_api_response_for_missing_field(method, url, access_token, data, field_to_remove):
    """
    This function removes the field from data as specified by field_to_remove, and
    then POSTs data on given URL. It then asserts that removed filed is in error_message.
    :param http_method method: Name of HTTP method
    :param string url: URL to to make HTTP request
    :param string access_token: access access_token of user
    :param dict data: Data to be posted
    :param string field_to_remove: Name of field we want to remove from given data
    """
    removed_value = data[field_to_remove]
    del data[field_to_remove]
    response = send_request(method, url, access_token, data)
    error = CampaignsTestsHelpers.assert_non_ok_response(response)
    assert field_to_remove in error['message'], '%s should be in error_message' % field_to_remove
    # assign removed field again
    data[field_to_remove] = removed_value


@contract
def _assert_invalid_datetime_format(method, url, access_token, data, key):
    """
    Here we modify field of data as specified by param 'key' and then assert the invalid usage
    error in response of HTTP request.
    :param http_method method: Name of HTTP method
    :param string url: URL to to make HTTP request
    :param string access_token: access access_token of user
    :param dict data: Data to be posted
    :param string key: Name of field we want to make invalidly formatted
    """
    str_datetime = str(datetime.utcnow())
    old_value = data[key]
    data[key] = str_datetime  # Invalid datetime format
    response = send_request(method, url, access_token, data)
    CampaignsTestsHelpers.assert_non_ok_response(response)
    data[key] = old_value


@contract
def _assert_invalid_datetime(method, url, access_token, data, key):
    """
    Here we set datetime field of data to as specified by param 'key' to past and then assert
    the invalid usage error in response of HTTP request.
    :param http_method method: Name of HTTP method
    :param string url: URL to to make HTTP request
    :param string access_token: access access_token of user
    :param dict data: Data to be posted
    :param string key: Name of field we want to assert invalidity on
    """
    old_value = data[key]
    data[key] = DatetimeUtils.to_utc_str(datetime.utcnow() - timedelta(hours=10))  # Past datetime
    response = send_request(method, url, access_token, data)
    CampaignsTestsHelpers.assert_non_ok_response(response)
    data[key] = old_value


@contract
def _assert_unauthorized(method, url, access_token, data=None):
    """
    For a given URL, here we request with invalid access_token and assert that we get Unauthorized error.
    :param http_method method: Name of HTTP method
    :param string url: URL to to make HTTP request
    :param string access_token: access access_token of user
    :param dict|None data: Data to be posted
    """
    response = send_request(method, url, access_token, data)
    assert response.status_code == UnauthorizedError.http_status_code(), \
        'It should not be authorized (401)'


@contract
def _invalid_data_test(method, url, access_token):
    """
    This is used to make HTTP request as specified by 'method' on given URL and assert invalid
    usage error in response.
    :param http_method method: Name of HTTP method
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
