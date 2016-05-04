"""
This module contains tests code that is common across services. e.g SMS and Push campaign.
"""
__author__ = 'basit'

# Standard Imports
import time
import json
from datetime import datetime, timedelta

# Third Party
import requests
from polling import poll, TimeoutException

# Application Specific
from ..models.db import db
from ..tests.conftest import fake
from campaign_utils import get_model
from ..routes import CandidatePoolApiUrl
from custom_errors import CampaignException
from ..models.user import (DomainRole, User)
from ..models.sms_campaign import SmsCampaign
from ..models.misc import (Frequency, Activity)
from ..models.push_campaign import PushCampaign
from ..utils.datetime_utils import DatetimeUtils
from ..models.email_campaign import EmailCampaign
from ..utils.validators import raise_if_not_instance_of
from ..utils.handy_functions import (JSON_CONTENT_TYPE_HEADER,
                                     add_role_to_test_user)
from ..tests.fake_testing_data_generator import FakeCandidatesData
from ..error_handling import (ForbiddenError, InvalidUsage,
                              UnauthorizedError, ResourceNotFound, UnprocessableEntity,
                              InternalServerError)
from ..inter_service_calls.candidate_pool_service_calls import create_smartlist_from_api, \
    assert_smartlist_candidates
from ..inter_service_calls.candidate_service_calls import create_candidates_from_candidate_api


class CampaignsTestsHelpers(object):
    """
    This class contains common tests for sms_campaign_service and push_campaign_service.
    """
    @classmethod
    def request_for_forbidden_error(cls, method, url, token):
        """
        This should get forbidden error because requested campaign does not belong to
        logged-in user's domain.
        """
        response = send_request(method, url, token, None)
        cls.assert_api_response(response, expected_status_code=ForbiddenError.http_status_code())

    @classmethod
    def request_for_resource_not_found_error(cls, method, url, token, data):
        """
        This should get Resource not found error because requested resource has been deleted.
        """
        response = send_request(method, url, token, data=data)
        cls.assert_api_response(response, expected_status_code=ResourceNotFound.http_status_code())

    @classmethod
    def request_after_deleting_campaign(cls, campaign, url_to_delete_campaign, url_after_delete,
                                        method_after_delete, token, data=None):
        """
        This is a helper function to request the given URL after deleting the given resource.
        It should result in ResourceNotFound error.
        :param (SmsCampaign | EmailCampaign | PushCampaign) campaign: Campaign object
        :param (str) url_to_delete_campaign: URL to delete given campaign
        :param (str) url_after_delete: URL to be requested after deleting the campaign
        :param (str) method_after_delete: Name of method to be requested after deleting campaign
        :param (str) token: access token of logged-in user
        :param data: Data to be sent in request after deleting campaign
        """
        campaign_id = campaign.id if hasattr(campaign, 'id') else campaign['id']
        # Delete the campaign first
        CampaignsTestsHelpers.request_for_ok_response('delete', url_to_delete_campaign % campaign_id,
                                                      token, None)
        CampaignsTestsHelpers.request_for_resource_not_found_error(
            method_after_delete, url_after_delete % campaign_id, token, data)

    @classmethod
    def request_for_ok_response(cls, method, url, token, data):
        """
        This function is expected to schedule a campaign
        :param url:
        :param token:
        :param data:
        :return:
        """
        response = send_request(method, url, token, data)
        assert response.ok
        json_response = response.json()
        assert json_response
        if method.lower() != 'delete':
            assert json_response['task_id']
            return json_response['task_id']

    @classmethod
    def request_with_past_start_and_end_datetime(cls, method, url, token, data):
        """
        Here we pass start_datetime and end_datetime in invalid format
        :param url:
        :param token:
        :param data:
        :return:
        """
        _assert_invalid_datetime(method, url, token, data, 'start_datetime')
        if not data['frequency_id'] or not data['frequency_id'] == Frequency.ONCE:
            _assert_invalid_datetime(method, url, token, data, 'end_datetime')

    @classmethod
    def missing_fields_in_schedule_data(cls, method, url, token, data):
        # Test missing start_datetime field which is mandatory to schedule a campaign
        _assert_api_response_for_missing_field(method, url, token, data, 'start_datetime')
        # if periodic job, need to test for end_datetime as well
        if not data['frequency_id'] or not data['frequency_id'] == Frequency.ONCE:
            _assert_api_response_for_missing_field(method, url, token, data, 'end_datetime')

    @classmethod
    def invalid_datetime_format(cls, method, url, token, data):
        """
        Here we pass start_datetime and end_datetime in invalid format
        :param url:
        :param token:
        :param data:
        :return:
        """
        _assert_invalid_datetime_format(method, url, token, data, 'start_datetime')
        if not data['frequency_id'] or not data['frequency_id'] == Frequency.ONCE:
            _assert_invalid_datetime_format(method, url, token, data, 'end_datetime')

    @classmethod
    def request_with_invalid_token(cls, method, url, data=None):
        _assert_unauthorized(method, url, 'invalid_token', data)

    @classmethod
    def reschedule_with_invalid_data(cls, url, token):
        _invalid_data_test('put', url, token)

    @classmethod
    def request_with_invalid_resource_id(cls, model, method, url, token, data):
        """
        This makes HTTP request (as specified by method) on given URL.
        It creates two invalid ids for requested resource, 0 and some large number(non-existing id)
        that does not exist in database for given model. It then asserts to check we get status
        code 400 in case of id 0 and status code 404 in case of non-existing id.
        """
        assert db.Model in model.__mro__, '`model` should be instance of db.Model'
        raise_if_not_instance_of(method, basestring)
        raise_if_not_instance_of(url, basestring)
        raise_if_not_instance_of(token, basestring)
        last_campaign_id_in_db = cls.get_last_id(model)
        invalid_ids = get_invalid_ids(last_campaign_id_in_db)
        invalid_id_and_status_code = _get_invalid_id_and_status_code_pair(invalid_ids)
        for _id, status_code in invalid_id_and_status_code:
            response = send_request(method, url % _id, token, data)
            assert response.status_code == status_code

    @classmethod
    def get_last_id(cls, model):
        last_obj = model.query.order_by(model.id.desc()).first()
        if last_obj:
            return last_obj.id
        else:
            return 1000

    @classmethod
    def reschedule_with_post_method(cls, url, token, data):
        # Test forbidden error. To schedule a task first time, we have to send POST,
        # but we will send request using PUT which is for update and will validate error
        response = send_request('post', url, token, data)
        cls.assert_api_response(response, expected_status_code=ForbiddenError.http_status_code())

    @classmethod
    def assert_api_response(cls, response, expected_status_code=InvalidUsage.http_status_code()):
        """
        This method is used to assert Invalid usage error in given response
        :param response:
        :return:
        """
        assert response.status_code == expected_status_code
        error = response.json()['error']
        assert error, 'error key is missing from response'
        assert error['message']
        return error

    @classmethod
    def campaign_send_with_no_smartlist(cls, url, access_token):
        """
        This is the test to send a campaign which has no smartlist associated  with it.
        It should get Invalid usage error. Custom error should be
        NoSmartlistAssociatedWithCampaign.
        """
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
        User auth token is valid, campaign has one smart list associated. But smartlist has
        no candidate associated with it. It should get invalid usage error.
        Custom error should be NoCandidateAssociatedWithSmartlist.
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
        error_resp = cls.assert_api_response(response_post,
                                             expected_status_code=InvalidUsage.http_status_code())
        assert error_resp['code'] == CampaignException.NO_CANDIDATE_ASSOCIATED_WITH_SMARTLIST
        assert error_resp['message']

    @classmethod
    def campaign_test_with_no_valid_candidate(cls, url, token, campaign_id):
        """
        This is the test to send campaign to candidate(s) who do not have valid
        data for the campaign to be sent to them. e.g. in case of email_campaign, candidate
        will have no email or for SMS campaign, candidate will not have any mobile number
        associated. This should assert custom error NO_VALID_CANDIDATE_FOUND in response.
        """
        response_post = send_request('post', url,  token)
        error_resp = cls.assert_api_response(response_post,
                                             expected_status_code=InvalidUsage.http_status_code())
        assert error_resp['code'] == CampaignException.NO_VALID_CANDIDATE_FOUND
        assert str(campaign_id) in error_resp['message']

    @classmethod
    def assert_for_activity(cls, user_id, type_, source_id):
        """
        This verifies that activity has been created for given action
        :param (int, long) user_id: Id of user
        :param (int, long) type_: Type number of activity
        :param (int, long) source_id: Id of activity source
        """
        # Need to commit the session because Celery has its own session, and our session does not
        # know about the changes that Celery session has made.
        db.session.commit()
        activity = poll(_get_activity, args=(user_id, type_, source_id), step=3, timeout=60)
        assert activity

    @classmethod
    def assert_ok_response_and_counts(cls, response, count=0, entity='sends', check_count=True):
        """
        This is the common function to assert that response is returning valid 'count'
        and 'sends' or 'replies' for a particular campaign.
        :param response:
        :param count:
        :return:
        """
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
        :param url: URL to hit for sending given campaign
        :param campaign: Email or SMS campaign obj
        :param access_token: Auth token to make HTTP request
        :param blasts_url: URL to get blasts of given campaign
        """
        raise_if_not_instance_of(access_token, basestring)
        raise_if_not_instance_of(url, basestring)
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
        # TODO--kindly validate campaign here and in followoing relevant methods
        db.session.commit()
        if not blasts_url:
            return campaign.blasts.all()
        blasts_get_response = send_request('get', blasts_url, access_token)
        if blasts_get_response.ok:
            return blasts_get_response.json()['blasts']

    @staticmethod
    def get_blasts_with_polling(campaign, access_token=None, blasts_url=None, timeout=10):
        """
        This polls the result of blasts of a campaign for given timeout (default 10s).
        """
        return poll(CampaignsTestsHelpers.get_blasts, step=3,
                    args=(campaign, access_token, blasts_url), timeout=timeout)

    @staticmethod
    def get_blast_by_index_with_polling(campaign, blast_index=0, access_token=None,
                                        blasts_url=None, timeout=10):
        """
        This polls the result of get_blasts_with_index() for given timeout (default 10s).
        """
        return poll(CampaignsTestsHelpers.get_blast_with_index, step=3,
                    args=(campaign, blast_index, access_token, blasts_url), timeout=timeout)

    @staticmethod
    def get_blast_with_index(campaign, blast_index=0, access_token=None, blasts_url=None):
        """
        This returns one particular blast associated with given campaign as specified by index.
        """
        db.session.commit()
        if not blasts_url:
            try:
                return campaign.blasts[blast_index]
            except IndexError:
                return []
        blasts_get_response = send_request('get', blasts_url, access_token)
        if blasts_get_response.ok:
            return blasts_get_response.json()['blast']

    @staticmethod
    def verify_sends(campaign, expected_count, blast_index, blast_url=None, access_token=None):
        """
        This returns all number of sends associated with given blast index of a campaign
        """
        db.session.commit()
        if not blast_url:
            return campaign.blasts[blast_index].sends
        response = send_request('get', blast_url, access_token)
        if response.ok:
            return response.json()['blast']['sends'] == expected_count

    @staticmethod
    def assert_blast_sends(campaign, expected_count, blast_index=0, abort_time_for_sends=20,
                           blast_url=None, access_token=None):
        """
        This function asserts the particular blast of given campaign has expected number of sends
        """
        sends_verified = poll(CampaignsTestsHelpers.verify_sends, step=3,
                              args=(campaign, expected_count, blast_index, blast_url, access_token),
                              timeout=abort_time_for_sends)
        assert sends_verified

    @staticmethod
    def assert_campaign_blasts(campaign, access_token, blasts_url, expected_count, timeout=10):
        """
        This function asserts the particular blast of given campaign has expected number of sends
        """
        blasts = poll(CampaignsTestsHelpers.get_blasts, step=3,
                      args=(campaign, access_token, blasts_url), timeout=timeout)
        return len(blasts) == expected_count

    @staticmethod
    def create_smartlist_with_candidate(access_token, talent_pipeline, count=1,
                                        data=None, emails_list=False, create_phone=False,
                                        assign_role=False, assert_candidates=True,
                                        smartlist_name=fake.word(), timeout=70):
        """
        This creates candidate(s) as specified by the count and assign it to a smartlist.
        Finally it returns smartlist_id and candidate_ids.
        """
        # TODO kindly validate mandatory params
        if assign_role:
            CampaignsTestsHelpers.assign_roles(talent_pipeline.user)
        if not data:
            # create candidate
            data = FakeCandidatesData.create(talent_pool=talent_pipeline.talent_pool,
                                             emails_list=emails_list, create_phone=create_phone,
                                             count=count)

        candidate_ids = create_candidates_from_candidate_api(access_token, data,
                                                             return_candidate_ids_only=True)
        # TODO can we rmeove the following todo or in future?
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

            # TODO may be we can remove the print or instead log
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
        name = fake.word()
        search_params = {"maximum_years_experience": "5", "location": "San Jose, CA",
                         "minimum_years_experience": "2"}
        data = {'name': name, 'search_params': search_params,
                'talent_pipeline_id': talent_pipeline_id}
        response = send_request('post', CandidatePoolApiUrl.SMARTLISTS, access_token, data)
        assert response.status_code == 201  # Successfully created
        json_resp = response.json()
        assert 'smartlist' in json_resp
        assert 'id' in json_resp['smartlist']
        return json_resp['smartlist']['id']


def send_request(method, url, access_token, data=None, is_json=True, data_dumps=True):
    # This method is being used for test cases, so it is sure that method has
    #  a valid value like 'get', 'post' etc.test_reschedule_with_invalid_token
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


def _assert_api_response_for_missing_field(method, url, token, data, field_to_remove):
    """
    This function removes the field from data as specified by field_to_remove, and
    then POSTs data on given URL. It then asserts that removed filed is in error_message.
    :param method:
    :param url:
    :param token:
    :param data:
    :param field_to_remove:
    :return:
    """
    removed_value = data[field_to_remove]
    del data[field_to_remove]
    response = send_request(method, url, token, data)
    error = CampaignsTestsHelpers.assert_api_response(response)
    assert field_to_remove in error['message'], '%s should be in error_message' % field_to_remove
    # assign removed field again
    data[field_to_remove] = removed_value


def _assert_invalid_datetime_format(method, url, token, data, key):
    """
    Here we modify field of data as specified by param 'key' and then assert the invalid usage
    error in response of HTTP request.
    :param method:
    :param url:
    :param token:
    :param data:
    :param key:
    :return:
    """
    str_datetime = str(datetime.utcnow())
    old_value = data[key]
    data[key] = str_datetime  # Invalid datetime format
    response = send_request(method, url, token, data)
    CampaignsTestsHelpers.assert_api_response(response)
    data[key] = old_value


def _assert_invalid_datetime(method, url, token, data, key):
    """
    Here we set datetime field of data to as specified by param 'key' to past and then assert
    the invalid usage error in response of HTTP request.
    :param method:
    :param url:
    :param token:
    :param data:
    :param key:
    :return:
    """
    old_value = data[key]
    data[key] = DatetimeUtils.to_utc_str(datetime.utcnow() - timedelta(hours=10))  # Past datetime
    response = send_request(method, url, token, data)
    CampaignsTestsHelpers.assert_api_response(response)
    data[key] = old_value


def _assert_unauthorized(method, url, access_token, data=None):
    """
    For a given URL, here we request with invalid token and assert that we get Unauthorized error.
    :param method:
    :param url:
    :param access_token:
    :param data:
    :return:
    """
    response = send_request(method, url, access_token, data)
    assert response.status_code == UnauthorizedError.http_status_code(), \
        'It should not be authorized (401)'


def _invalid_data_test(method, url, token):
    """
    This is used to make HTTP request as specified by 'method' on given URL and assert invalid
    usage error in response.
    :param method:
    :param url:
    :param token:
    :return:
    """
    # test with None Data
    data = None
    response = send_request(method, url, token, data)
    CampaignsTestsHelpers.assert_api_response(response)
    # Test with empty dict
    data = {}
    CampaignsTestsHelpers.assert_api_response(response)
    response = send_request(method, url, token, data)
    CampaignsTestsHelpers.assert_api_response(response)
    # Test with valid data and invalid header
    data = get_fake_dict()
    response = send_request(method, url, token, data, is_json=False)
    CampaignsTestsHelpers.assert_api_response(response)
    # Test with Non JSON data and valid header
    data = get_invalid_fake_dict()
    response = send_request(method, url, token, data, data_dumps=False)
    CampaignsTestsHelpers.assert_api_response(response)


def get_invalid_ids(last_id_of_obj_in_db):
    """
    Given a database model object, here we create a list of two invalid ids. One of them
    is 0 and other one is 1000 plus the id of last record.
    """
    # TODO--one line validation would be awesome
    return 0, last_id_of_obj_in_db + 1000


def _get_invalid_id_and_status_code_pair(invalid_ids):
    """
    This associates expected status code with given invalid_ids.
    :param invalid_ids:
    :return:
    """
    # TODO a none invalid_ids will breka things here, kindly validate
    return [(invalid_ids[0], InvalidUsage.http_status_code()),
            (invalid_ids[1], ResourceNotFound.http_status_code())]


def _get_activity(user_id, _type, source_id):
    """
    This gets that activity from database table Activity for given params
    :param (int, long) user_id: Id of user
    :param (int, long) _type: Type number of activity
    :param (int, long) source_id: Id of activity source
    """
    # TODO--kindly validate
    return Activity.get_by_user_id_type_source_id(user_id, _type, source_id)
