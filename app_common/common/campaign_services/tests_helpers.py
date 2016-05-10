"""
This module contains tests code that is common across campaign-services. e.g SMS and Push campaign.
"""

__author__ = 'basit'

# Standard Imports
import sys
import time
import json
from datetime import datetime, timedelta

# Third Party
import requests
from requests import Response
from polling import poll, TimeoutException

# Application Specific
from ..models.db import db
from ..tests.conftest import fake
from ..routes import CandidatePoolApiUrl
from custom_errors import CampaignException
from ..models.user import (DomainRole, User)
from ..models.sms_campaign import SmsCampaign
from ..models.misc import (Frequency, Activity)
from ..models.push_campaign import PushCampaign
from ..utils.datetime_utils import DatetimeUtils
from ..models.email_campaign import EmailCampaign
from campaign_utils import get_model, CampaignUtils
from ..utils.validators import raise_if_not_instance_of
from ..models.talent_pools_pipelines import TalentPipeline
from ..utils.handy_functions import (JSON_CONTENT_TYPE_HEADER,
                                     add_role_to_test_user)
from ..tests.fake_testing_data_generator import FakeCandidatesData
from ..error_handling import (ForbiddenError, InvalidUsage, UnauthorizedError,
                              ResourceNotFound, UnprocessableEntity, InternalServerError)
from ..inter_service_calls.candidate_pool_service_calls import create_smartlist_from_api, \
    assert_smartlist_candidates
from ..inter_service_calls.candidate_service_calls import create_candidates_from_candidate_api


class CampaignsTestsHelpers(object):
    """
    This class contains common helper methods for tests of sms_campaign_service and
    push_campaign_service etc.
    """
    @classmethod
    def request_for_forbidden_error(cls, method, url, access_token):
        """
        This should get forbidden error because requested campaign does not belong to
        logged-in user's domain.
        :param (str) method: Name of HTTP method
        :param (str) url: URL to to make HTTP request
        :param (str) access_token: access access_token of user
        """
        raise_if_not_instance_of(method, basestring)
        raise_if_not_instance_of(url, basestring)
        raise_if_not_instance_of(access_token, basestring)
        response = send_request(method, url, access_token, None)
        cls.assert_api_response(response, expected_status_code=ForbiddenError.http_status_code())

    @classmethod
    def request_for_resource_not_found_error(cls, method, url, access_token, data=None):
        """
        This should get Resource not found error because requested resource has been deleted.
        :param (str) method: Name of HTTP method
        :param (str) url: URL to to make HTTP request
        :param (str) access_token: access access_token of user
        :param (dict | None) data: Data to be posted
        """
        raise_if_not_instance_of(method, basestring)
        raise_if_not_instance_of(url, basestring)
        raise_if_not_instance_of(access_token, basestring)
        raise_if_not_instance_of(data, dict) if data else None
        response = send_request(method, url, access_token, data=data)
        cls.assert_api_response(response, expected_status_code=ResourceNotFound.http_status_code())

    @classmethod
    def request_after_deleting_campaign(cls, campaign, url_to_delete_campaign, url_after_delete,
                                        method_after_delete, access_token, data=None):
        """
        This is a helper function to request the given URL after deleting the given resource.
        It should result in ResourceNotFound error.
        :param (dict | SmsCampaign | EmailCampaign | PushCampaign) campaign: Campaign object
        :param (str) url_to_delete_campaign: URL to delete given campaign
        :param (str) url_after_delete: URL to be requested after deleting the campaign
        :param (str) method_after_delete: Name of method to be requested after deleting campaign
        :param (str) access_token: access access_token of logged-in user
        :param (dict | None) data: Data to be sent in request after deleting campaign
        """
        raise_if_not_instance_of(campaign, (dict, CampaignUtils.MODELS))
        raise_if_not_instance_of(url_to_delete_campaign, basestring)
        raise_if_not_instance_of(url_after_delete, basestring)
        raise_if_not_instance_of(method_after_delete, basestring)
        raise_if_not_instance_of(access_token, basestring)
        raise_if_not_instance_of(data, dict) if data else None
        campaign_id = campaign.id if hasattr(campaign, 'id') else campaign['id']
        # Delete the campaign first
        cls.request_for_ok_response('delete', url_to_delete_campaign % campaign_id, access_token)
        cls.request_for_resource_not_found_error(
            method_after_delete, url_after_delete % campaign_id, access_token, data)

    @staticmethod
    def request_for_ok_response(method, url, access_token, data=None):
        """
        This function is expected to schedule a campaign with all valid parameters.
        :param (str) method: Name of HTTP method
        :param (str) url: URL to to make HTTP request
        :param (str) access_token: access access_token of user
        :param (dict | None) data: Data to be posted
        """
        raise_if_not_instance_of(method, basestring)
        raise_if_not_instance_of(url, basestring)
        raise_if_not_instance_of(access_token, basestring)
        raise_if_not_instance_of(data, dict) if data else None
        response = send_request(method, url, access_token, data)
        assert response.ok
        json_response = response.json()
        assert json_response
        if method.lower() != 'delete':
            assert json_response['task_id']
            return json_response['task_id']

    @staticmethod
    def request_with_past_start_and_end_datetime(method, url, access_token, data):
        """
        Here we pass start_datetime and end_datetime with invalid value i.e. in past, to schedule
        a campaign. Then we assert that we get InvalidUsage error in response.
        :param (str) method: Name of HTTP method
        :param (str) url: URL to to make HTTP request
        :param (str) access_token: access access_token of user
        :param (dict) data: Data to be posted
        """
        raise_if_not_instance_of(method, basestring)
        raise_if_not_instance_of(url, basestring)
        raise_if_not_instance_of(access_token, basestring)
        raise_if_not_instance_of(data, dict) if data else None
        _assert_invalid_datetime(method, url, access_token, data, 'start_datetime')
        if not data['frequency_id'] or not data['frequency_id'] == Frequency.ONCE:
            _assert_invalid_datetime(method, url, access_token, data, 'end_datetime')

    @staticmethod
    def missing_fields_in_schedule_data(method, url, access_token, data):
        """
        Here we try to schedule a campaign with missing required fields and assert that we get
        InvalidUsage error in response.
        :param (str) method: Name of HTTP method
        :param (str) url: URL to to make HTTP request
        :param (str) access_token: access access_token of user
        :param (dict) data: Data to be posted
        """
        # Test missing start_datetime field which is mandatory to schedule a campaign
        raise_if_not_instance_of(method, basestring)
        raise_if_not_instance_of(url, basestring)
        raise_if_not_instance_of(access_token, basestring)
        raise_if_not_instance_of(data, dict)
        _assert_api_response_for_missing_field(method, url, access_token, data, 'start_datetime')
        # If periodic job, need to test for end_datetime as well
        if not data['frequency_id'] or not data['frequency_id'] == Frequency.ONCE:
            _assert_api_response_for_missing_field(method, url, access_token, data, 'end_datetime')

    @staticmethod
    def invalid_datetime_format(method, url, access_token, data):
        """
        Here we pass start_datetime and end_datetime in invalid format to schedule a campaign.
        :param (str) method: Name of HTTP method
        :param (str) url: URL to to make HTTP request
        :param (str) access_token: access access_token of user
        :param (dict) data: Data to be posted
        """
        raise_if_not_instance_of(method, basestring)
        raise_if_not_instance_of(url, basestring)
        raise_if_not_instance_of(access_token, basestring)
        raise_if_not_instance_of(data, dict)
        _assert_invalid_datetime_format(method, url, access_token, data, 'start_datetime')
        if not data['frequency_id'] or not data['frequency_id'] == Frequency.ONCE:
            _assert_invalid_datetime_format(method, url, access_token, data, 'end_datetime')

    @staticmethod
    def request_with_invalid_token(method, url, data=None):
        """
        This is used in tests where we want to make HTTP request on given URL with invalid
        access access_token. It assert that we get ForbiddenError as a result.
        :param (str) method: Name of HTTP method
        :param (str) url: URL to to make HTTP request
        :param (dict | None) data: Data to be posted
        """
        raise_if_not_instance_of(method, basestring)
        raise_if_not_instance_of(url, basestring)
        raise_if_not_instance_of(data, dict) if data else None
        _assert_unauthorized(method, url, 'invalid_token', data)

    @staticmethod
    def reschedule_with_invalid_data(url, access_token):
        """
        This is used in campaign tests where we want to re-schedule a campaign with invalid data.
        This asserts that we get BadRequest error for every bad data we pass.
        :param (str) url: URL to to make HTTP request
        :param (str) access_token: access access_token of user
        """
        raise_if_not_instance_of(url, basestring)
        raise_if_not_instance_of(access_token, basestring)
        _invalid_data_test('put', url, access_token)

    @classmethod
    def request_with_invalid_resource_id(cls, model, method, url, access_token, data=None):
        """
        This makes HTTP request (as specified by method) on given URL.
        It creates two invalid ids for requested resource, 0 and some large number(non-existing id)
        that does not exist in database for given model. It then asserts to check we get status
        code 400 in case of id 0 and status code 404 in case of non-existing id.
        :param (db.Model) model: SQLAlchemy model
        :param (str) method: Name of HTTP method
        :param (str) url: URL to to make HTTP request
        :param (str) access_token: access access_token of user
        :param (dict | None) data: Data to be posted
        """
        assert db.Model in model.__mro__, '`model` should be instance of db.Model'
        raise_if_not_instance_of(method, basestring)
        raise_if_not_instance_of(url, basestring)
        raise_if_not_instance_of(access_token, basestring)
        raise_if_not_instance_of(data, dict) if data else None
        invalid_ids = (0, cls.get_non_existing_id(model))
        invalid_id_and_status_code = _get_invalid_id_and_status_code_pair(invalid_ids)
        for _id, status_code in invalid_id_and_status_code:
            response = send_request(method, url % _id, access_token, data)
            assert response.status_code == status_code

    @staticmethod
    def get_last_id(model):
        """
        This methods returns the id of last record in given database table.
        If there is no record found, it returns None.
        :param (db.Model) model: SQLAlchemy model
        """
        assert db.Model in model.__mro__, '`model` should be instance of db.Model'
        last_obj = model.query.order_by(model.id.desc()).first()
        return last_obj.id if last_obj else None

    @classmethod
    def get_non_existing_id(cls, model):
        """
        This methods returns the non-existing id for given db Model.
        If last record is found, it adds 1000 in its id and return it.
        Otherwise it returns sys.maxint which ensures that returned number is a non-existing id for
        given model.
        :param (db.Model) model: SQLAlchemy model
        """
        assert db.Model in model.__mro__, '`model` should be instance of db.Model'
        last_id = cls.get_last_id(model)
        return last_id + 1000 if last_id else sys.maxint

    @classmethod
    def get_non_existing_ids(cls, model):
        """
        This methods returns a tuple of non-existing ids for given db Model.
        :param (db.Model) model: SQLAlchemy model
        """
        assert db.Model in model.__mro__, '`model` should be instance of db.Model'
        return get_invalid_ids(cls.get_non_existing_id(model))

    @classmethod
    def reschedule_with_post_method(cls, url, access_token, data):
        """
        Test forbidden error. To schedule a task first time, we have to send POST,
        but we will send request using PUT which is for update and will validate error
        :param (str) url: URL to to make HTTP request
        :param (str) access_token: access access_token of user
        :param (dict) data: Data to be posted
        """
        raise_if_not_instance_of(url, basestring)
        raise_if_not_instance_of(access_token, basestring)
        raise_if_not_instance_of(data, dict)
        response = send_request('post', url, access_token, data)
        cls.assert_api_response(response, expected_status_code=ForbiddenError.http_status_code())

    @staticmethod
    def assert_api_response(response, expected_status_code=InvalidUsage.http_status_code()):
        """
        This method is used to assert Invalid usage error in given response
        :param (Response) response: HTTP response
        :return: error dict
        """
        raise_if_not_instance_of(response, Response)
        raise_if_not_instance_of(expected_status_code, int)
        assert response.status_code == expected_status_code
        error = response.json()['error']
        assert error, 'error key is missing from response'
        assert error['message']
        return error

    @staticmethod
    def campaign_send_with_no_smartlist(url, access_token):
        """
        This is the test to send a campaign which has no smartlist associated  with it.
        It should get Invalid usage error. Custom error should be
        NoSmartlistAssociatedWithCampaign.
        :param (str) url: URL to to make HTTP request
        :param (str) access_token: access access_token of user
        """
        raise_if_not_instance_of(url, basestring)
        raise_if_not_instance_of(access_token, basestring)
        response = send_request('post', url, access_token, None)
        assert response.status_code == InvalidUsage.http_status_code(), \
            'It should be invalid usage error(400)'
        error_resp = response.json()['error']
        assert error_resp['code'] == CampaignException.NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN
        assert 'No Smartlist'.lower() in error_resp['message'].lower()

    @classmethod
    def campaign_send_with_no_smartlist_candidate(cls, url, access_token, campaign,
                                                  talent_pipeline_id):
        """
        User auth access_token is valid, campaign has one smart list associated. But smartlist has
        no candidate associated with it. It should get invalid usage error.
        Custom error should be NoCandidateAssociatedWithSmartlist.
        :param (SmsCampaign | EmailCampaign | PushCampaign) campaign: Campaign object
        :param (str) url: URL to to make HTTP request
        :param (str) access_token: access access_token of user
        :param (int, long) talent_pipeline_id: Id of talent_pipeline
        """
        raise_if_not_instance_of(url, basestring)
        raise_if_not_instance_of(access_token, basestring)
        raise_if_not_instance_of(campaign, CampaignUtils.MODELS)
        raise_if_not_instance_of(talent_pipeline_id, (int, long))
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
        error_resp = cls.assert_api_response(response_post,
                                             expected_status_code=InvalidUsage.http_status_code())
        assert error_resp['code'] == CampaignException.NO_CANDIDATE_ASSOCIATED_WITH_SMARTLIST
        assert error_resp['message']

    @classmethod
    def campaign_test_with_no_valid_candidate(cls, url, access_token, campaign_id):
        """
        This is the test to send campaign to candidate(s) who do not have valid
        data for the campaign to be sent to them. e.g. in case of email_campaign, candidate
        will have no email or for SMS campaign, candidate will not have any mobile number
        associated. This should assert custom error NO_VALID_CANDIDATE_FOUND in response.
        :param (str) url: URL to to make HTTP request
        :param (str) access_token: access access_token of user
        :param (int, long) campaign_id: Id of campaign
        """
        raise_if_not_instance_of(url, basestring)
        raise_if_not_instance_of(access_token, basestring)
        raise_if_not_instance_of(campaign_id, (int, long))
        response_post = send_request('post', url,  access_token)
        error_resp = cls.assert_api_response(response_post,
                                             expected_status_code=InvalidUsage.http_status_code())
        assert error_resp['code'] == CampaignException.NO_VALID_CANDIDATE_FOUND
        assert str(campaign_id) in error_resp['message']

    @staticmethod
    def assert_for_activity(user_id, _type, source_id):
        """
        This verifies that activity has been created for given action
        :param (int, long) user_id: Id of user
        :param (int, long) _type: Type number of activity
        :param (int, long) source_id: Id of activity source
        """
        raise_if_not_instance_of(user_id, (int, long))
        raise_if_not_instance_of(_type, (int, long))
        raise_if_not_instance_of(source_id, (int, long))
        # Need to commit the session because Celery has its own session, and our session does not
        # know about the changes that Celery session has made.
        activity = poll(_get_activity, args=(user_id, _type, source_id), step=3, timeout=60)
        assert activity

    @staticmethod
    def assert_ok_response_and_counts(response, count=0, entity='sends', check_count=True):
        """
        This is the common function to assert that response is returning valid 'count'
        and 'sends' or 'replies' for a particular campaign.
        :param (Response) response: Response object of HTTP request
        :param (int) count: Number of expected objects
        :param (str) entity: Name of expected entity
        :param (bool) check_count: If True, will check number of objects
        """
        raise_if_not_instance_of(response, Response)
        raise_if_not_instance_of(count, int)
        raise_if_not_instance_of(entity, basestring)
        raise_if_not_instance_of(check_count, bool)
        assert response.status_code == 200, 'Response should be "OK" (200)'
        assert response.json()
        json_response = response.json()
        assert entity in json_response
        if check_count:
            assert len(json_response[entity]) == count
            if not count:  # if count is 0, campaign_sends should be []
                assert not json_response[entity]
            else:
                assert json_response[entity]

    @staticmethod
    def send_campaign(url, campaign, access_token, blasts_url=None):
        """
        This function sends the campaign via /v1/email-campaigns/:id/send or
        /v1/sms-campaigns/:id/send depending on campaign type.
        sleep_time is set to be 20s here. One can modify this by passing required value.
        :param (str) url: URL to hit for sending given campaign
        :param (dict | SmsCampaign | EmailCampaign | PushCampaign) campaign: Campaign object
        :param (str) access_token: Auth access_token to make HTTP request
        :param (str | None) blasts_url: URL to get blasts of given campaign
        """
        raise_if_not_instance_of(url, basestring)
        raise_if_not_instance_of(campaign, (dict, CampaignUtils.MODELS))
        raise_if_not_instance_of(access_token, basestring)
        raise_if_not_instance_of(blasts_url, basestring) if blasts_url else None
        # send campaign
        campaign_id = campaign.id if hasattr(campaign, 'id') else campaign['id']
        send_url = url % campaign_id
        response = send_request('post', send_url, access_token)
        assert response.ok
        if blasts_url:
            blasts_url = blasts_url % campaign_id
        blasts = CampaignsTestsHelpers.get_blasts_with_polling(campaign, access_token,
                                                               blasts_url=blasts_url)
        if not blasts:
            raise UnprocessableEntity('blasts not found in given time range.')
        return response

    @staticmethod
    def get_blasts(campaign, access_token=None, blasts_url=None):
        """
        This returns all the blasts associated with given campaign
        """
        if not blasts_url:
            raise_if_not_instance_of(campaign, CampaignUtils.MODELS)
            db.session.commit()
            return campaign.blasts.all()
        raise_if_not_instance_of(access_token, basestring)
        raise_if_not_instance_of(blasts_url, basestring)
        blasts_get_response = send_request('get', blasts_url, access_token)
        return blasts_get_response.json()['blasts'] if blasts_get_response.ok else []

    @staticmethod
    def get_blasts_with_polling(campaign, access_token=None, blasts_url=None, timeout=10):
        """
        This polls the result of blasts of a campaign for given timeout (default 10s).
        """
        raise_if_not_instance_of(campaign, (dict, CampaignUtils.MODELS))
        raise_if_not_instance_of(access_token, basestring) if access_token else None
        raise_if_not_instance_of(blasts_url, basestring) if blasts_url else None
        raise_if_not_instance_of(timeout, int)
        return poll(CampaignsTestsHelpers.get_blasts, step=3,
                    args=(campaign, access_token, blasts_url), timeout=timeout)

    @staticmethod
    def get_blast_by_index_with_polling(campaign, blast_index=0, access_token=None,
                                        blasts_url=None, timeout=10):
        """
        This polls the result of get_blasts_with_index() for given timeout (default 10s).
        """
        raise_if_not_instance_of(campaign, (dict, CampaignUtils.MODELS))
        raise_if_not_instance_of(blast_index, int)
        raise_if_not_instance_of(access_token, basestring) if access_token else None
        raise_if_not_instance_of(blasts_url, basestring) if blasts_url else None
        raise_if_not_instance_of(timeout, int)
        return poll(CampaignsTestsHelpers.get_blast_with_index, step=3,
                    args=(campaign, blast_index, access_token, blasts_url), timeout=timeout)

    @staticmethod
    def get_blast_with_index(campaign, blast_index=0, access_token=None, blasts_url=None):
        """
        This returns one particular blast associated with given campaign as specified by index.
        """
        raise_if_not_instance_of(campaign, (dict, CampaignUtils.MODELS))
        raise_if_not_instance_of(blast_index, int)
        raise_if_not_instance_of(access_token, basestring) if access_token else None
        raise_if_not_instance_of(blasts_url, basestring) if blasts_url else None
        if not blasts_url:
            try:
                raise_if_not_instance_of(campaign, CampaignUtils.MODELS)
                db.session.commit()
                return campaign.blasts[blast_index]
            except IndexError:
                return []
        raise_if_not_instance_of(access_token, basestring)
        raise_if_not_instance_of(blasts_url, basestring)
        blasts_get_response = send_request('get', blasts_url, access_token)
        if blasts_get_response.ok:
            return blasts_get_response.json()['blast']

    @staticmethod
    def verify_sends(campaign, expected_count, blast_index, blast_url=None, access_token=None):
        """
        This returns all number of sends associated with given blast index of a campaign
        """
        raise_if_not_instance_of(campaign, (dict, CampaignUtils.MODELS))
        raise_if_not_instance_of(expected_count, int)
        raise_if_not_instance_of(blast_index, int)
        if not blast_url:
            raise_if_not_instance_of(campaign, CampaignUtils.MODELS)
            db.session.commit()
            return campaign.blasts[blast_index].sends == expected_count
        raise_if_not_instance_of(access_token, basestring)
        raise_if_not_instance_of(blast_url, basestring)
        response = send_request('get', blast_url, access_token)
        if response.ok:
            return response.json()['blast']['sends'] == expected_count

    @staticmethod
    def assert_blast_sends(campaign, expected_count, blast_index=0, abort_time_for_sends=30,
                           blast_url=None, access_token=None):
        """
        This function asserts that particular blast of given campaign has expected number of sends
        """
        raise_if_not_instance_of(campaign, (dict, CampaignUtils.MODELS))
        raise_if_not_instance_of(expected_count, int)
        raise_if_not_instance_of(blast_index, int)
        raise_if_not_instance_of(abort_time_for_sends, int)
        raise_if_not_instance_of(access_token, basestring) if access_token else None
        raise_if_not_instance_of(blast_url, basestring) if blast_url else None
        sends_verified = poll(CampaignsTestsHelpers.verify_sends, step=3,
                              args=(campaign, expected_count, blast_index, blast_url, access_token),
                              timeout=abort_time_for_sends)
        assert sends_verified

    @staticmethod
    def verify_blasts(campaign, access_token, blasts_url, expected_count):
        """
        This function asserts that given campaign has expected number of blast objects
        """
        raise_if_not_instance_of(campaign, (dict, CampaignUtils.MODELS))
        raise_if_not_instance_of(expected_count, int)
        raise_if_not_instance_of(access_token, basestring) if access_token else None
        raise_if_not_instance_of(blasts_url, basestring) if blasts_url else None
        received_blasts_count = len(CampaignsTestsHelpers.get_blasts(campaign, access_token,
                                                                     blasts_url))
        if received_blasts_count == expected_count:
            return True
        else:
            print 'Expected Blasts:%s' % expected_count
            print 'Received Blasts:%s' % received_blasts_count
            return False

    @staticmethod
    def assert_campaign_blasts(campaign, expected_count, access_token=None, blasts_url=None, timeout=10):
        """
        This function polls verify_blasts() to assert that given campaign has expected number
        of blast objects.
        """
        raise_if_not_instance_of(campaign, (dict, CampaignUtils.MODELS))
        raise_if_not_instance_of(expected_count, int)
        raise_if_not_instance_of(access_token, basestring) if access_token else None
        raise_if_not_instance_of(blasts_url, basestring) if blasts_url else None
        raise_if_not_instance_of(timeout, int)
        poll(CampaignsTestsHelpers.verify_blasts, args=(campaign, access_token, blasts_url, expected_count),
             step=3, timeout=timeout)

    @staticmethod
    def create_smartlist_with_candidate(access_token, talent_pipeline, count=1,
                                        data=None, emails_list=False, create_phone=False,
                                        assign_role=False, assert_candidates=True,
                                        smartlist_name=fake.word(), timeout=120):
        """
        This creates candidate(s) as specified by the count and assign it to a smartlist.
        Finally it returns smartlist_id and candidate_ids.
        """
        raise_if_not_instance_of(access_token, basestring)
        raise_if_not_instance_of(talent_pipeline, TalentPipeline)
        raise_if_not_instance_of(count, int)
        raise_if_not_instance_of(data, dict) if data else None
        raise_if_not_instance_of(emails_list, bool)
        raise_if_not_instance_of(create_phone, bool)
        raise_if_not_instance_of(assign_role, bool)
        raise_if_not_instance_of(assert_candidates, bool)
        raise_if_not_instance_of(smartlist_name, basestring)
        raise_if_not_instance_of(timeout, int)
        if assign_role:
            CampaignsTestsHelpers.assign_roles(talent_pipeline.user)
        if not data:
            # create candidate
            data = FakeCandidatesData.create(talent_pool=talent_pipeline.talent_pool,
                                             emails_list=emails_list, create_phone=create_phone,
                                             count=count)

        candidate_ids = create_candidates_from_candidate_api(access_token, data,
                                                             return_candidate_ids_only=True)
        if assert_candidates:
            time.sleep(10)  # TODO: Need to remove this and use polling instead
        smartlist_data = {'name': smartlist_name,
                          'candidate_ids': candidate_ids,
                          'talent_pipeline_id': talent_pipeline.id}

        smartlists = create_smartlist_from_api(data=smartlist_data, access_token=access_token)
        smartlist_id = smartlists['smartlist']['id']
        if assert_candidates:
            try:
                poll(assert_smartlist_candidates, step=3,
                     args=(smartlist_id, len(candidate_ids), access_token), timeout=timeout)
            except TimeoutException:
                raise InternalServerError('Candidates not found for smartlist(id:%s) '
                                          'within given time range' % smartlist_id)
            print '%s candidate(s) found for smartlist(id:%s)' % (len(candidate_ids), smartlist_id)
        return smartlist_id, candidate_ids

    @staticmethod
    def assign_roles(user, roles=(DomainRole.Roles.CAN_ADD_CANDIDATES,
                                  DomainRole.Roles.CAN_GET_CANDIDATES)):
        """
        This assign required permission to given user.
        Default roles are CAN_ADD_CANDIDATES and CAN_GET_CANDIDATES.
        """
        raise_if_not_instance_of(user, User)
        raise_if_not_instance_of(roles, (list, tuple))
        add_role_to_test_user(user, roles)


class FixtureHelpers(object):
    """
    This contains the functions which will be useful for similar fixtures across campaigns
    """
    @classmethod
    def create_smartlist_with_search_params(cls, access_token, talent_pipeline_id):
        """
        This creates a smartlist with search params and returns the id of smartlist
        """
        raise_if_not_instance_of(access_token, basestring)
        raise_if_not_instance_of(talent_pipeline_id, (int, long))
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


def send_request(method, url, access_token, data=None, is_json=True, data_dumps=True):
    # This method is being used for test cases, so it is sure that method has
    #  a valid value like 'get', 'post' etc.test_reschedule_with_invalid_token
    raise_if_not_instance_of(method, basestring)
    raise_if_not_instance_of(url, basestring)
    raise_if_not_instance_of(access_token, basestring)
    raise_if_not_instance_of(is_json, bool)
    raise_if_not_instance_of(data_dumps, bool)
    request_method = getattr(requests, method)
    headers = dict(Authorization='Bearer %s' % access_token)
    if is_json:
        headers['Content-Type'] = JSON_CONTENT_TYPE_HEADER['content-type']
    if data_dumps:
        data = json.dumps(data)
    return request_method(url, data=data, headers=headers)


def get_fake_dict():
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
    data = dict()
    for _ in range(3):
        data[fake.word()] = fake.word()
    return data


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
    fake_dict[len(fake_dict.keys())-1] = [fake.word]
    return fake_dict


def _assert_api_response_for_missing_field(method, url, access_token, data, field_to_remove):
    """
    This function removes the field from data as specified by field_to_remove, and
    then POSTs data on given URL. It then asserts that removed filed is in error_message.
    :param (str) method: Name of HTTP method
    :param (str) url: URL to to make HTTP request
    :param (str) access_token: access access_token of user
    :param (dict) data: Data to be posted
    :param (str) field_to_remove: Name of field we want to remove from given data
    """
    raise_if_not_instance_of(method, basestring)
    raise_if_not_instance_of(url, basestring)
    raise_if_not_instance_of(access_token, basestring)
    raise_if_not_instance_of(data, dict)
    raise_if_not_instance_of(field_to_remove, basestring)
    removed_value = data[field_to_remove]
    del data[field_to_remove]
    response = send_request(method, url, access_token, data)
    error = CampaignsTestsHelpers.assert_api_response(response)
    assert field_to_remove in error['message'], '%s should be in error_message' % field_to_remove
    # assign removed field again
    data[field_to_remove] = removed_value


def _assert_invalid_datetime_format(method, url, access_token, data, key):
    """
    Here we modify field of data as specified by param 'key' and then assert the invalid usage
    error in response of HTTP request.
    :param (str) method: Name of HTTP method
    :param (str) url: URL to to make HTTP request
    :param (str) access_token: access access_token of user
    :param (dict) data: Data to be posted
    :param (str) key: Name of field we want to make invalidly formatted
    """
    raise_if_not_instance_of(method, basestring)
    raise_if_not_instance_of(url, basestring)
    raise_if_not_instance_of(access_token, basestring)
    raise_if_not_instance_of(data, dict)
    raise_if_not_instance_of(key, basestring)
    str_datetime = str(datetime.utcnow())
    old_value = data[key]
    data[key] = str_datetime  # Invalid datetime format
    response = send_request(method, url, access_token, data)
    CampaignsTestsHelpers.assert_api_response(response)
    data[key] = old_value


def _assert_invalid_datetime(method, url, access_token, data, key):
    """
    Here we set datetime field of data to as specified by param 'key' to past and then assert
    the invalid usage error in response of HTTP request.
    :param (str) method: Name of HTTP method
    :param (str) url: URL to to make HTTP request
    :param (str) access_token: access access_token of user
    :param (dict) data: Data to be posted
    :param (str) key: Name of field we want to assert invalidity on
    """
    raise_if_not_instance_of(method, basestring)
    raise_if_not_instance_of(url, basestring)
    raise_if_not_instance_of(access_token, basestring)
    raise_if_not_instance_of(data, dict)
    raise_if_not_instance_of(key, basestring)
    old_value = data[key]
    data[key] = DatetimeUtils.to_utc_str(datetime.utcnow() - timedelta(hours=10))  # Past datetime
    response = send_request(method, url, access_token, data)
    CampaignsTestsHelpers.assert_api_response(response)
    data[key] = old_value


def _assert_unauthorized(method, url, access_token, data=None):
    """
    For a given URL, here we request with invalid access_token and assert that we get Unauthorized error.
    :param (str) method: Name of HTTP method
    :param (str) url: URL to to make HTTP request
    :param (str) access_token: access access_token of user
    :param (dict | None) data: Data to be posted
    """
    raise_if_not_instance_of(method, basestring)
    raise_if_not_instance_of(url, basestring)
    raise_if_not_instance_of(access_token, basestring)
    raise_if_not_instance_of(data, dict) if data else None
    response = send_request(method, url, access_token, data)
    assert response.status_code == UnauthorizedError.http_status_code(), \
        'It should not be authorized (401)'


def _invalid_data_test(method, url, access_token):
    """
    This is used to make HTTP request as specified by 'method' on given URL and assert invalid
    usage error in response.
    :param (str) method: Name of HTTP method
    :param (str) url: URL to to make HTTP request
    :param (str) access_token: access access_token of user
    """
    raise_if_not_instance_of(method, basestring)
    raise_if_not_instance_of(url, basestring)
    raise_if_not_instance_of(access_token, basestring)
    # test with None Data
    data = None
    response = send_request(method, url, access_token, data)
    CampaignsTestsHelpers.assert_api_response(response)
    # Test with empty dict
    data = {}
    CampaignsTestsHelpers.assert_api_response(response)
    response = send_request(method, url, access_token, data)
    CampaignsTestsHelpers.assert_api_response(response)
    # Test with valid data and invalid header
    data = get_fake_dict()
    response = send_request(method, url, access_token, data, is_json=False)
    CampaignsTestsHelpers.assert_api_response(response)
    # Test with Non JSON data and valid header
    data = get_invalid_fake_dict()
    response = send_request(method, url, access_token, data, data_dumps=False)
    CampaignsTestsHelpers.assert_api_response(response)


def get_invalid_ids(non_existing_id):
    """
    Given a database model object, here we create a list of two invalid ids. One of them
    is 0 and other one is non-existing id for a particular model.
    """
    raise_if_not_instance_of(non_existing_id, (int, long))
    return 0, non_existing_id


def _get_invalid_id_and_status_code_pair(invalid_ids):
    """
    This associates expected status code with given list of invalid_ids.
    i.e. 400 for invalid id e.g. 0 and 404 for non-existing record
    """
    raise_if_not_instance_of(invalid_ids, (list, tuple))
    return [(invalid_ids[0], InvalidUsage.http_status_code()),
            (invalid_ids[1], ResourceNotFound.http_status_code())]


def _get_activity(user_id, _type, source_id):
    """
    This gets that activity from database table Activity for given params
    :param (int, long) user_id: Id of user
    :param (int, long) _type: Type number of activity
    :param (int, long) source_id: Id of activity source
    """
    raise_if_not_instance_of(user_id, (int, long))
    raise_if_not_instance_of(_type, (int, long))
    raise_if_not_instance_of(source_id, (int, long))
    # Need to commit the session because Celery has its own session, and our session does not
    # know about the changes that Celery session has made.
    db.session.commit()
    return Activity.get_by_user_id_type_source_id(user_id, _type, source_id)
