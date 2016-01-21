"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This file contains pyTest fixtures for tests of SMS Campaign Service.
"""
# Standard Import
import time
from datetime import timedelta

# Third Party
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm.exc import ObjectDeletedError

# Application Specific

from sms_campaign_service.sms_campaign_app import init_sms_campaign_app_and_celery_app
app, _ = init_sms_campaign_app_and_celery_app()

# common conftest
from sms_campaign_service.common.tests.conftest import *

# Service specific
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.error_handling import ResourceNotFound
from sms_campaign_service.modules.sms_campaign_base import SmsCampaignBase
from sms_campaign_service.tests.modules.common_functions import (assert_api_send_response,
                                                                 assert_campaign_schedule,
                                                                 delete_test_scheduled_task)
from sms_campaign_service.modules.sms_campaign_app_constants import (TWILIO, MOBILE_PHONE_LABEL,
                                                                     TWILIO_TEST_NUMBER,
                                                                     TWILIO_INVALID_TEST_NUMBER,
                                                                     TWILIO_PAID_NUMBER_1)

# Database Models
from sms_campaign_service.common.models.user import UserPhone
from sms_campaign_service.common.models.misc import UrlConversion
from sms_campaign_service.common.models.candidate import (PhoneLabel, CandidatePhone)
from sms_campaign_service.common.models.smartlist import (Smartlist, SmartlistCandidate)
from sms_campaign_service.common.models.sms_campaign import (SmsCampaign, SmsCampaignSmartlist,
                                                             SmsCampaignBlast, SmsCampaignSend,
                                                             SmsCampaignSendUrlConversion)
# Common Utils
from sms_campaign_service.common.utils.handy_functions import (JSON_CONTENT_TYPE_HEADER,
                                                               to_utc_str)
from sms_campaign_service.common.campaign_services.campaign_utils import FrequencyIds

SLEEP_TIME = 10  # needed to add this because tasks run on Celery

# This is data to create/update SMS campaign
CREATE_CAMPAIGN_DATA = {"name": "TEST SMS Campaign",
                        "body_text": "Hi all, we have few openings at http://www.abc.com",
                        "smartlist_ids": ""
                        }


# This is data to schedule an SMS campaign
def generate_campaign_schedule_data():
    return {"frequency_id": FrequencyIds.ONCE,
            # TODO: remove timedelta from start_datetime after scheduler_service update
            "start_datetime": to_utc_str(datetime.utcnow() + timedelta(minutes=1)),
            "end_datetime": to_utc_str(datetime.utcnow() + relativedelta(days=+5))}


def remove_any_user_phone_record_with_twilio_test_number():
    """
    This function cleans the database tables user_phone and candidate_phone.
    If any record in these two tables has phone number value either TWILIO_TEST_NUMBER or
    TWILIO_INVALID_TEST_NUMBER, we remove all those records before running the tests.
    :return:
    """
    records = UserPhone.get_by_phone_value(TWILIO_TEST_NUMBER)
    records += UserPhone.get_by_phone_value(TWILIO_INVALID_TEST_NUMBER)
    map(UserPhone.delete, records)
    test_numbers = [TWILIO_PAID_NUMBER_1, TWILIO_PAID_NUMBER_1, TWILIO_PAID_NUMBER_1,
                    TWILIO_TEST_NUMBER, TWILIO_INVALID_TEST_NUMBER]
    candidate_phones = []
    for test_number in test_numbers:
        candidate_phones += CandidatePhone.get_by_phone_value(test_number)
    map(CandidatePhone.delete, candidate_phones)


# clean database tables user_phone and candidate_phone first
remove_any_user_phone_record_with_twilio_test_number()


@pytest.fixture()
def auth_token(user_auth, sample_user):
    """
    returns the access token using pytest fixture defined in common/tests/conftest.py
    :param user_auth: fixture in common/tests/conftest.py
    :param sample_user: fixture in common/tests/conftest.py
    """
    auth_token_obj = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    return auth_token_obj['access_token']


@pytest.fixture()
def auth_token_2(user_auth, sample_user_2):
    """
    returns the access token using pytest fixture defined in common/tests/conftest.py
    :param user_auth: fixture in common/tests/conftest.py
    :param sample_user: fixture in common/tests/conftest.py
    """
    auth_token_obj = user_auth.get_auth_token(sample_user_2, get_bearer_token=True)
    return auth_token_obj['access_token']


@pytest.fixture()
def valid_header(auth_token):
    """
    Returns the header containing access token and content-type to make POST/DELETE requests.
    :param auth_token: fixture to get access token of user
    """
    auth_header = {'Authorization': 'Bearer %s' % auth_token}
    auth_header.update(JSON_CONTENT_TYPE_HEADER)
    return auth_header


@pytest.fixture()
def valid_header_2(auth_token_2):
    """
    Returns the header containing access token and content-type to make POST/DELETE requests.
    :param auth_token: fixture to get access token of user
    """
    auth_header = {'Authorization': 'Bearer %s' % auth_token_2}
    auth_header.update(JSON_CONTENT_TYPE_HEADER)
    return auth_header


@pytest.fixture()
def user_phone_1(request, sample_user):
    """
    This creates a user_phone record for sample_user
    :param request:
    :param sample_user: fixture in common/tests/conftest.py
    :return:
    """
    user_phone = _create_user_twilio_phone(sample_user, fake.phone_number())

    def tear_down():
        UserPhone.delete(user_phone)

    request.addfinalizer(tear_down)
    return user_phone


@pytest.fixture()
def user_phone_2(request, sample_user):
    """
    This creates another user_phone record for sample_user
    :param request:
    :param sample_user: fixture in common/tests/conftest.py
    :return:
    """
    user_phone = _create_user_twilio_phone(sample_user, fake.phone_number())

    def tear_down():
        UserPhone.delete(user_phone)

    request.addfinalizer(tear_down)
    return user_phone


@pytest.fixture()
def user_phone_3(request, sample_user_2):
    """
    This creates user_phone record for sample_user_2
    :param sample_user_2:
    :return:
    """
    user_phone = _create_user_twilio_phone(sample_user_2, fake.phone_number())

    def tear_down():
        UserPhone.delete(user_phone)

    request.addfinalizer(tear_down)
    return user_phone


@pytest.fixture()
def sample_smartlist(request, sample_user):
    """
    This creates sample smartlist for sample user
    :param request:
    :param sample_user:
    :return:
    """

    smartlist = _create_smartlist(sample_user)

    def tear_down():
        Smartlist.delete(smartlist)

    request.addfinalizer(tear_down)
    return smartlist


@pytest.fixture()
def sample_sms_campaign_candidates(sample_user,
                                   sample_smartlist,
                                   candidate_first,
                                   candidate_second):
    """
    This adds two candidates to sample_smartlist.
    :param sample_smartlist:
    :param candidate_first:
    :param candidate_second:
    :return:
    """
    candidate_first.update(user_id=sample_user.id)
    candidate_second.update(user_id=sample_user.id)
    smartlist_candidate_1 = SmartlistCandidate(smartlist_id=sample_smartlist.id,
                                               candidate_id=candidate_first.id)
    SmartlistCandidate.save(smartlist_candidate_1)
    smartlist_candidate_2 = SmartlistCandidate(smartlist_id=sample_smartlist.id,
                                               candidate_id=candidate_second.id)
    SmartlistCandidate.save(smartlist_candidate_2)


@pytest.fixture()
def campaign_valid_data(sample_smartlist):
    """
    This returns the valid data to save an SMS campaign in database
    :return:
    """
    campaign_data = CREATE_CAMPAIGN_DATA.copy()
    campaign_data['smartlist_ids'] = [sample_smartlist.id]
    return campaign_data


@pytest.fixture()
def campaign_data_unknown_key_text():
    """
    This returns invalid data to save an SMS campaign. 'body_text' required field
    name is modified to be 'text' here i.e. the correct value is 'body_text'
    :return:
    """
    campaign_data = CREATE_CAMPAIGN_DATA.copy()
    campaign_data['text'] = campaign_data.pop('body_text')
    return campaign_data


@pytest.fixture()
def sms_campaign_of_current_user(campaign_valid_data, user_phone_1):
    """
    This creates the SMS campaign for sammple_user using valid data.
    :param campaign_valid_data:
    :param user_phone_1:
    :return:
    """
    return _create_sms_campaign(campaign_valid_data, user_phone_1)


@pytest.fixture(params=[FrequencyIds.ONCE, FrequencyIds.DAILY])
def one_time_and_periodic(request, valid_header):
    """
    This returns data to schedule a campaign one time and periodically.
    """
    data = generate_campaign_schedule_data()

    def fin():
        if 'task_id' in data:
            delete_test_scheduled_task(data['task_id'], valid_header)

    if request.param == FrequencyIds.ONCE:
        request.addfinalizer(fin)
        return data
    else:
        request.addfinalizer(fin)
        data['frequency_id'] = request.param
    return data


@pytest.fixture()
def scheduled_sms_campaign_of_current_user(request, sample_user, valid_header,
                                           sms_campaign_of_current_user):
    """
    This creates the SMS campaign for sample_user using valid data.
    """
    campaign = _get_scheduled_campaign(sample_user, sms_campaign_of_current_user, valid_header)

    def delete_scheduled_task():
        _unschedule_campaign(campaign, valid_header)

    request.addfinalizer(delete_scheduled_task)
    return campaign


@pytest.fixture()
def scheduled_sms_campaign_of_other_user(request, sample_user_2, valid_header_2,
                                         sms_campaign_of_other_user):
    """
    This creates the SMS campaign for sample_user_2 using valid data.
    :return:
    """
    campaign = _get_scheduled_campaign(sample_user_2, sms_campaign_of_other_user, valid_header_2)

    def delete_scheduled_task():
        _unschedule_campaign(campaign, valid_header_2)

    request.addfinalizer(delete_scheduled_task)
    return campaign


@pytest.fixture()
def sms_campaign_of_other_user(campaign_valid_data, user_phone_3):
    """
    This creates SMS campaign for some other user i.e. not sample_user rather sample_user_2
    :param campaign_valid_data:
    :param user_phone_3:
    :return:
    """
    return _create_sms_campaign(campaign_valid_data, user_phone_3)


@pytest.fixture()
def create_sms_campaign_blast(sms_campaign_of_current_user):
    """
    This creates a record in database table "sms_campaign_blast"
    :param sms_campaign_of_current_user:
    :return:
    """
    blast_obj = SmsCampaignBlast(campaign_id=sms_campaign_of_current_user.id)
    SmsCampaignBlast.save(blast_obj)
    return blast_obj.id


@pytest.fixture()
def create_campaign_sends(candidate_first, candidate_second, create_sms_campaign_blast):
    """
    This creates a record in database table "sms_campaign_send"
    :param candidate_first: fixture to create test candidate
    :param candidate_second: fixture to create another test candidate
    :return:
    """
    SmsCampaignBase.create_or_update_sms_campaign_send(create_sms_campaign_blast,
                                                       candidate_first.id,
                                                       datetime.now())
    SmsCampaignBase.create_or_update_sms_campaign_send(create_sms_campaign_blast,
                                                       candidate_second.id,
                                                       datetime.now())


@pytest.fixture()
def sample_smartlist_2(request, sample_user):
    """
    This creates sample smartlist for sample user
    :param request:
    :param sample_user:
    :return:
    """
    smartlist = _create_smartlist(sample_user)

    def tear_down():
        Smartlist.delete(smartlist)

    request.addfinalizer(tear_down)
    return smartlist


@pytest.fixture()
def sms_campaign_smartlist(scheduled_sms_campaign_of_current_user, sample_smartlist):
    """
    This associates sample_smartlist with the scheduled_sms_campaign_of_current_user
    :param sample_smartlist:
    :param scheduled_sms_campaign_of_current_user:
    :return:
    """
    return _create_sms_campaign_smartlist(scheduled_sms_campaign_of_current_user, sample_smartlist)


@pytest.fixture()
def smartlist_for_not_scheduled_campaign(sms_campaign_of_current_user, sample_smartlist):
    """
    This associates sample_smartlist with the sms_campaign_of_current_user
    :param sample_smartlist:
    :return:
    """
    return _create_sms_campaign_smartlist(sms_campaign_of_current_user, sample_smartlist)


@pytest.fixture()
def sms_campaign_smartlist_2(sample_smartlist_2, scheduled_sms_campaign_of_current_user):
    """
    This associates sample_smartlist with the scheduled_sms_campaign_of_current_user
    :param scheduled_sms_campaign_of_current_user:
    :return:
    """
    sms_campaign_smartlist = SmsCampaignSmartlist(
        smartlist_id=sample_smartlist_2.id,
        sms_campaign_id=scheduled_sms_campaign_of_current_user.id)
    SmsCampaignSmartlist.save(sms_campaign_smartlist)
    return sms_campaign_smartlist


@pytest.fixture()
def candidate_phone_1(request, candidate_first):
    """
    This associates sample_smartlist with the sms_campaign_of_current_user
    :param candidate_first:
    :return:
    """
    candidate_phone = _create_candidate_mobile_phone(candidate_first, fake.phone_number())

    def tear_down():
        CandidatePhone.delete(candidate_phone)

    request.addfinalizer(tear_down)
    return candidate_phone


@pytest.fixture()
def candidate_phone_2(request, candidate_second):
    """
    This associates sample_smartlist with the sms_campaign_of_current_user
    :param candidate_second:
    :return:
    """
    candidate_phone = _create_candidate_mobile_phone(candidate_second, fake.phone_number())

    def tear_down():
        CandidatePhone.delete(candidate_phone)

    request.addfinalizer(tear_down)
    return candidate_phone


@pytest.fixture()
def candidate_invalid_phone(request, candidate_second):
    """
    This associates sample_smartlist with the sms_campaign_of_current_user
    :param candidate_second:
    :return:
    """
    candidate_phone = _create_candidate_mobile_phone(candidate_second, TWILIO_INVALID_TEST_NUMBER)

    def tear_down():
        CandidatePhone.delete(candidate_phone)

    request.addfinalizer(tear_down)
    return candidate_phone


@pytest.fixture()
def candidates_with_same_phone(request, candidate_first, candidate_second):
    """
    This associates same number to candidate_first and candidate_second
    :param candidate_second:
    :return:
    """
    common_phone = fake.phone_number()
    cand_phone_1 = _create_candidate_mobile_phone(candidate_first, common_phone)
    cand_phone_2 = _create_candidate_mobile_phone(candidate_second, common_phone)

    def tear_down():
        CandidatePhone.delete(cand_phone_1)
        CandidatePhone.delete(cand_phone_2)

    request.addfinalizer(tear_down)
    return cand_phone_1, cand_phone_2


@pytest.fixture()
def users_with_same_phone(request, sample_user, sample_user_2):
    """
    This associates same number to sample_user and sample_user_2
    """
    common_phone = fake.phone_number()
    user_1 = _create_user_twilio_phone(sample_user, common_phone)
    user_2 = _create_user_twilio_phone(sample_user_2, common_phone)

    def tear_down():
        UserPhone.delete(user_1)
        UserPhone.delete(user_2)

    request.addfinalizer(tear_down)
    return user_1, user_2


@pytest.fixture()
def process_send_sms_campaign(sample_user, auth_token,
                              sms_campaign_of_current_user,
                              sample_sms_campaign_candidates,
                              smartlist_for_not_scheduled_campaign,
                              candidate_phone_1,
                              ):
    """
    This function serves the sending part of SMS campaign.
    This sends campaign to one candidate.
    :return:
    """
    response_post = requests.post(SmsCampaignApiUrl.SEND
                                  % sms_campaign_of_current_user.id,
                                  headers=dict(Authorization='Bearer %s' % auth_token))
    assert_api_send_response(sms_campaign_of_current_user, response_post, 200)
    time.sleep(SLEEP_TIME)  # had to add this as sending process runs on celery


@pytest.fixture()
def url_conversion_by_send_test_sms_campaign(request,
                                             sms_campaign_of_current_user,
                                             process_send_sms_campaign):
    """
    This sends SMS campaign (using process_send_sms_campaign fixture)
     and returns the source URL from url_conversion database table.
    :return:
    """
    time.sleep(SLEEP_TIME)  # had to add this as sending process runs on celery
    # Need to commit the session because Celery has its own session, and our session does not
    # know about the changes that Celery session has made.
    db.session.commit()
    # get campaign blast
    sms_campaign_blast = \
        SmsCampaignBlast.get_by_campaign_id(sms_campaign_of_current_user.id)
    # get campaign sends
    sms_campaign_sends = SmsCampaignSend.get_by_blast_id(str(sms_campaign_blast.id))
    # get if of record of sms_campaign_send_url_conversion for this campaign
    if not sms_campaign_sends:
        raise ResourceNotFound('sms_campaign_sends record is empty')
    campaign_send_url_conversions = SmsCampaignSendUrlConversion.get_by_campaign_send_id(
        sms_campaign_sends[0].id)
    # get URL conversion record from database table 'url_conversion'
    url_conversion = UrlConversion.get_by_id(campaign_send_url_conversions[0].url_conversion_id)

    def tear_down():
        UrlConversion.delete(url_conversion)

    request.addfinalizer(tear_down)
    return url_conversion


def _create_sms_campaign(campaign_data, user_phone):
    """
    This creates an SMS campaign in database table "sms_campaign"
    :param campaign_data: data to create campaign
    :param user_phone: user_phone obj
    :return:
    """
    smartlist_ids = campaign_data['smartlist_ids']
    del campaign_data['smartlist_ids']  # This is not a field of "sms_campaign" table.
    campaign_data['user_phone_id'] = user_phone.id
    sms_campaign = SmsCampaign(**campaign_data)
    SmsCampaign.save(sms_campaign)
    # We put it back again
    campaign_data['smartlist_ids'] = smartlist_ids
    return sms_campaign


def _create_user_twilio_phone(user, phone_value):
    """
    This adds user_phone record in database table "user_phone"
    :param user: user obj
    :param phone_value: value of phone number
    :return: user_phone obj
    """
    phone_label_id = PhoneLabel.phone_label_id_from_phone_label(TWILIO)
    user_phone = UserPhone(user_id=user.id,
                           phone_label_id=phone_label_id,
                           value=phone_value)
    UserPhone.save(user_phone)
    return user_phone


def _create_candidate_mobile_phone(candidate, phone_value):
    """
    This adds candidate_phone record in database table "candidate_phone"
    :param candidate: Candidate obj
    :param phone_value: value of phone number
    :type candidate: Candidate
    :type phone_value: str
    :return: candidate_phone obj
    :rtype: CandidatePhone
    """
    phone_label_id = PhoneLabel.phone_label_id_from_phone_label(MOBILE_PHONE_LABEL)
    candidate_phone = CandidatePhone(candidate_id=candidate.id,
                                     phone_label_id=phone_label_id,
                                     value=phone_value)
    CandidatePhone.save(candidate_phone)
    return candidate_phone


def _create_smartlist(test_user):
    """
    This creates Smartlist for given user
    :param test_user:
    :return:
    """
    smartlist = Smartlist(name=gen_salt(20), user_id=test_user.id)
    Smartlist.save(smartlist)
    return smartlist


def _get_scheduled_campaign(user, campaign, auth_header):
    """
    This schedules the given campaign and return it.
    :param user:
    :param campaign:
    :return:
    """
    response = requests.post(
        SmsCampaignApiUrl.SCHEDULE % campaign.id, headers=auth_header,
        data=json.dumps(generate_campaign_schedule_data()))
    assert_campaign_schedule(response, user.id, campaign.id)
    return campaign


def _unschedule_campaign(campaign, headers):
    """
    This un schedules the given campaign from scheduler_service
    :param headers:
    :return:
    """
    try:
        delete_test_scheduled_task(campaign.scheduler_task_id, headers)
    except ObjectDeletedError:  # campaign may have been deleted in case of DELETE request
        pass


def _create_sms_campaign_smartlist(campaign, smartlist):
    """
    This creates a smartlist for given campaign
    :param campaign:
    :return:
    """
    sms_campaign_smartlist = SmsCampaignSmartlist(smartlist_id=smartlist.id,
                                                  sms_campaign_id=campaign.id)
    SmsCampaignSmartlist.save(sms_campaign_smartlist)
    return sms_campaign_smartlist
