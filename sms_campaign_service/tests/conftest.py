"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This file contains pyTest fixtures for tests of SMS Campaign Service.
"""
# Standard Import
import json
import time
from datetime import (datetime, timedelta)

# Third Party
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm.exc import ObjectDeletedError

# Application Specific
# common conftest
from sms_campaign_service.common.tests.conftest import \
    (db, pytest, fake, requests, gen_salt, user_auth, access_token_first,
     sample_client, test_domain, first_group, domain_first, user_first, candidate_first,
     test_domain_2, second_group, domain_second, candidate_second, user_from_diff_domain,
     user_same_domain, user_second, access_token_second)

# Service specific
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.modules.sms_campaign_base import SmsCampaignBase
from sms_campaign_service.tests.modules.common_functions import (assert_api_send_response,
                                                                 assert_campaign_schedule,
                                                                 delete_test_scheduled_task)
from sms_campaign_service.modules.sms_campaign_app_constants import (TWILIO, MOBILE_PHONE_LABEL,
                                                                     TWILIO_TEST_NUMBER,
                                                                     TWILIO_INVALID_TEST_NUMBER)

# Database Models
from sms_campaign_service.common.models.user import UserPhone
from sms_campaign_service.common.models.misc import (UrlConversion, Frequency)
from sms_campaign_service.common.models.candidate import (PhoneLabel, CandidatePhone, Candidate)
from sms_campaign_service.common.models.smartlist import (Smartlist, SmartlistCandidate)
from sms_campaign_service.common.models.sms_campaign import (SmsCampaign, SmsCampaignSmartlist,
                                                             SmsCampaignBlast, SmsCampaignSend)
# Common Utils
from sms_campaign_service.common.datetime_utils import DatetimeUtils
from sms_campaign_service.common.utils.handy_functions import JSON_CONTENT_TYPE_HEADER


SLEEP_TIME = 20  # needed to add this because tasks run on Celery

# This is data to create/update SMS campaign
CREATE_CAMPAIGN_DATA = {"name": "TEST SMS Campaign",
                        "body_text": "Hi all, we have few openings at https://www.gettalent.com",
                        "smartlist_ids": ""
                        }


# This is data to schedule an SMS campaign
def generate_campaign_schedule_data():
    return {"frequency_id": Frequency.ONCE,
            "start_datetime": DatetimeUtils.to_utc_str(datetime.utcnow() + timedelta(minutes=1)),
            "end_datetime": DatetimeUtils.to_utc_str(datetime.utcnow() + relativedelta(days=+5))}


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


# clean database tables user_phone and candidate_phone first
remove_any_user_phone_record_with_twilio_test_number()


@pytest.fixture()
def valid_header(access_token_first):
    """
    Returns the header containing access token and content-type to make POST/DELETE requests.
    :param access_token_first: fixture to get access token of user
    """
    return _get_auth_header(access_token_first)


@pytest.fixture()
def valid_header_2(access_token_second):
    """
    Returns the header containing access token and content-type to make POST/DELETE requests.
    """
    return _get_auth_header(access_token_second)


@pytest.fixture()
def user_phone_1(request, user_first):
    """
    This creates a user_phone record for user_first
    :param request:
    :param user_first: fixture in common/tests/conftest.py
    :return:
    """
    user_phone = _create_user_twilio_phone(user_first, fake.phone_number())

    def tear_down():
        _delete_user_phone(user_phone)

    request.addfinalizer(tear_down)
    return user_phone


@pytest.fixture()
def user_phone_2(request, user_first):
    """
    This creates another user_phone record for user_first
    :param request:
    :param user_first: fixture in common/tests/conftest.py
    :return:
    """
    user_phone = _create_user_twilio_phone(user_first, fake.phone_number())

    def tear_down():
        _delete_user_phone(user_phone)

    request.addfinalizer(tear_down)
    return user_phone


@pytest.fixture()
def user_phone_3(request, user_second):
    """
    This creates user_phone record for user_from_diff_domain
    :return:
    """
    user_phone = _create_user_twilio_phone(user_second, fake.phone_number())

    def tear_down():
        _delete_user_phone(user_phone)

    request.addfinalizer(tear_down)
    return user_phone


@pytest.fixture()
def user_phone_4(request, user_same_domain):
    """
    This creates user_phone record for user_same_domain
    :param request:
    :param user_first: fixture in common/tests/conftest.py
    :return:
    """
    user_phone = _create_user_twilio_phone(user_same_domain, fake.phone_number())

    def tear_down():
        _delete_user_phone(user_phone)

    request.addfinalizer(tear_down)
    return user_phone


@pytest.fixture()
def sample_smartlist(request, user_first):
    """
    This creates sample smartlist for sample user
    :param request:
    :param user_first:
    :return:
    """

    smartlist = _create_smartlist(user_first)

    def tear_down():
        _delete_smartlist(smartlist)

    request.addfinalizer(tear_down)
    return smartlist


@pytest.fixture()
def smartlist_of_other_domain(request, user_from_diff_domain):
    """
    This creates sample smartlist for sample user
    :param request:
    :param user_first:
    :return:
    """

    smartlist = _create_smartlist(user_from_diff_domain)

    def tear_down():
        _delete_smartlist(smartlist)

    request.addfinalizer(tear_down)
    return smartlist


@pytest.fixture()
def sample_sms_campaign_candidates(user_first,
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
    candidate_first.update(user_id=user_first.id)
    candidate_second.update(user_id=user_first.id)
    smartlist_candidate_1 = SmartlistCandidate(smartlist_id=sample_smartlist.id,
                                               candidate_id=candidate_first.id)
    SmartlistCandidate.save(smartlist_candidate_1)
    smartlist_candidate_2 = SmartlistCandidate(smartlist_id=sample_smartlist.id,
                                               candidate_id=candidate_second.id)
    SmartlistCandidate.save(smartlist_candidate_2)


@pytest.fixture()
def sample_campaign_candidate_of_other_domain(sample_smartlist, candidate_in_other_domain):
    """
    This adds candidate of other domain to sample_smartlist.
    :param sample_smartlist:
    :return:
    """
    smartlist_candidate_1 = SmartlistCandidate(smartlist_id=sample_smartlist.id,
                                               candidate_id=candidate_in_other_domain.id)
    SmartlistCandidate.save(smartlist_candidate_1)


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
def sms_campaign_of_current_user(request, campaign_valid_data, user_phone_1):
    """
    This creates the SMS campaign for sammple_user using valid data.
    :param campaign_valid_data:
    :param user_phone_1:
    :return:
    """
    test_sms_campaign = _create_sms_campaign(campaign_valid_data, user_phone_1)

    def fin():
        _delete_campaign(test_sms_campaign)

    request.addfinalizer(fin)
    return test_sms_campaign


@pytest.fixture()
def sms_campaign_of_other_user_in_same_domain(request, campaign_valid_data,
                                              user_phone_4):
    """
    This creates the SMS campaign for sample_user using valid data.
    :param campaign_valid_data:
    """
    test_sms_campaign = _create_sms_campaign(campaign_valid_data, user_phone_4)

    def fin():
        _delete_campaign(test_sms_campaign)

    request.addfinalizer(fin)
    return test_sms_campaign


@pytest.fixture()
def sms_campaign_in_other_domain(request, campaign_valid_data, user_phone_3):
    """
    This creates SMS campaign for some other user in different domain.
    :param campaign_valid_data:
    :param user_phone_3:
    :return:
    """
    test_sms_campaign_of_other_user = _create_sms_campaign(campaign_valid_data, user_phone_3)

    def fin():
        _delete_campaign(test_sms_campaign_of_other_user)

    request.addfinalizer(fin)
    return test_sms_campaign_of_other_user


@pytest.fixture(params=[Frequency.ONCE, Frequency.DAILY])
def one_time_and_periodic(request, valid_header):
    """
    This returns data to schedule a campaign one time and periodically.
    """
    data = generate_campaign_schedule_data()

    def fin():
        if 'task_id' in data:
            delete_test_scheduled_task(data['task_id'], valid_header)

    if request.param == Frequency.ONCE:
        request.addfinalizer(fin)
        return data
    else:
        request.addfinalizer(fin)
        data['frequency_id'] = request.param
    return data


@pytest.fixture()
def scheduled_sms_campaign_of_current_user(request, user_first, valid_header,
                                           sms_campaign_of_current_user):
    """
    This creates the SMS campaign for user_first using valid data.
    """
    campaign = _get_scheduled_campaign(user_first, sms_campaign_of_current_user, valid_header)

    def delete_scheduled_task():
        _unschedule_campaign(campaign, valid_header)

    request.addfinalizer(delete_scheduled_task)
    return campaign


@pytest.fixture()
def scheduled_sms_campaign_of_other_domain(request, user_second,
                                         valid_header_2, sms_campaign_in_other_domain):
    """
    This creates the SMS campaign for user_from_diff_domain using valid data.
    :return:
    """
    campaign = _get_scheduled_campaign(user_second,
                                       sms_campaign_in_other_domain,
                                       valid_header_2)

    def delete_scheduled_task():
        _unschedule_campaign(campaign, valid_header_2)

    request.addfinalizer(delete_scheduled_task)
    return campaign


@pytest.fixture()
def create_sms_campaign_blast(request, sms_campaign_of_current_user):
    """
    This creates a record in database table "sms_campaign_blast" for
    campaign owned by logged-in user.
    :param sms_campaign_of_current_user:
    :return:
    """
    blast_obj = _create_blast(sms_campaign_of_current_user.id)

    def fin():
        _delete_blast(blast_obj)

    request.addfinalizer(fin)
    return blast_obj


@pytest.fixture()
def create_blast_for_not_owned_campaign(request, sms_campaign_in_other_domain):
    """
    This creates a record in database table "sms_campaign_blast" for
    a campaign which does not belongs to domain of logged-in user.
    :param sms_campaign_in_other_domain:
    :return:
    """
    blast_obj = _create_blast(sms_campaign_in_other_domain.id)

    def fin():
        _delete_blast(blast_obj)

    request.addfinalizer(fin)
    return blast_obj


@pytest.fixture()
def create_campaign_sends(user_first, candidate_first, candidate_second,
                          create_sms_campaign_blast):
    """
    This creates a record in database table "sms_campaign_send"
    :param candidate_first: fixture to create test candidate
    :param candidate_second: fixture to create another test candidate
    :return:
    """
    camp_obj = SmsCampaignBase(user_first.id)

    camp_obj.create_or_update_campaign_send(create_sms_campaign_blast.id, candidate_first.id,
                                            datetime.now(), SmsCampaignSend)
    SmsCampaignBase.update_campaign_blast(create_sms_campaign_blast, sends=True)
    camp_obj.create_or_update_campaign_send(create_sms_campaign_blast.id, candidate_second.id,
                                            datetime.now(), SmsCampaignSend)
    SmsCampaignBase.update_campaign_blast(create_sms_campaign_blast, sends=True)


@pytest.fixture()
def create_campaign_replies(candidate_phone_1, create_sms_campaign_blast):
    """
    This creates a record in database table "sms_campaign_reply"
    """
    SmsCampaignBase.save_candidate_reply(create_sms_campaign_blast.id,
                                         candidate_phone_1.id, 'Got it')
    SmsCampaignBase.update_campaign_blast(create_sms_campaign_blast, replies=True)


@pytest.fixture()
def sample_smartlist_2(request, user_first):
    """
    This creates sample smartlist for sample user
    :param request:
    :param user_first:
    :return:
    """
    smartlist = _create_smartlist(user_first)

    def tear_down():
        _delete_smartlist(smartlist)

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
        campaign_id=scheduled_sms_campaign_of_current_user.id)
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
        _delete_candidate_phone(candidate_phone)

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
        _delete_candidate_phone(candidate_phone)

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
        _delete_candidate_phone(candidate_phone)

    request.addfinalizer(tear_down)
    return candidate_phone


@pytest.fixture()
def candidate_in_other_domain(request, user_from_diff_domain):
    candidate = Candidate(last_name=gen_salt(20), first_name=gen_salt(20),
                          user_id=user_from_diff_domain.id)
    db.session.add(candidate)
    db.session.commit()

    def tear_down():
        try:
            db.session.delete(candidate)
            db.session.commit()
        except Exception:
            db.session.rollback()

    request.addfinalizer(tear_down)
    return candidate


@pytest.fixture()
def candidate_phone_in_other_domain(request, candidate_in_other_domain):
    """
    This associates sample_smartlist with the sms_campaign_of_current_user
    """
    candidate_phone = _create_candidate_mobile_phone(candidate_in_other_domain, fake.phone_number())

    def tear_down():
        _delete_candidate_phone(candidate_phone)

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
        _delete_candidate_phone(cand_phone_1)
        _delete_candidate_phone(cand_phone_2)

    request.addfinalizer(tear_down)
    return candidate_first, candidate_second


@pytest.fixture()
def candidates_with_same_phone_in_diff_domains(request, candidate_first,
                                               candidate_phone_1,
                                               candidate_in_other_domain):
    """
    This associates same number to candidate_first and candidate_in_other_domain
    :return:
    """
    cand_phone_2 = _create_candidate_mobile_phone(candidate_in_other_domain,
                                                  candidate_phone_1.value)

    def tear_down():
        _delete_candidate_phone(cand_phone_2)

    request.addfinalizer(tear_down)
    return candidate_first, candidate_in_other_domain


@pytest.fixture()
def users_with_same_phone(request, user_first, user_same_domain):
    """
    This associates same number to user_first and user_same_domain
    """
    common_phone = fake.phone_number()
    user_1 = _create_user_twilio_phone(user_first, common_phone)
    user_2 = _create_user_twilio_phone(user_same_domain, common_phone)

    def tear_down():
        _delete_user_phone(user_1)
        _delete_user_phone(user_2)

    request.addfinalizer(tear_down)
    return user_1, user_2


@pytest.fixture()
def process_send_sms_campaign(user_first, access_token_first,
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
                                  headers=dict(Authorization='Bearer %s' % access_token_first))
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
    # time.sleep(SLEEP_TIME)  # had to add this as sending process runs on celery
    # Need to commit the session because Celery has its own session, and our session does not
    # know about the changes that Celery session has made.
    db.session.commit()
    # get campaign blast
    sms_campaign_blast = sms_campaign_of_current_user.blasts[0]
    # get URL conversion record from relationship
    url_conversion = \
        sms_campaign_blast.blast_sends[0].url_conversions[0].url_conversion

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


def _delete_campaign(campaign_obj):
    """
    This deletes the given campaign from database
    :param campaign_obj:
    :return:
    """
    try:
        SmsCampaign.delete(campaign_obj)
    except Exception:  # campaign may have been deleted in case of DELETE request
        pass


def _delete_candidate_phone(candidate_phone_obj):
    """
    This deletes the given candidate_phone record from database
    :param campaign:
    :return:
    """
    try:
        CandidatePhone.delete(candidate_phone_obj)
    except Exception:  # resource may have been deleted in case of DELETE request
        pass


def _delete_user_phone(user_phone_obj):
    """
    This deletes the given user_phone record from database
    :return:
    """
    try:
        UserPhone.delete(user_phone_obj)
    except Exception:  # resource may have been deleted in case of DELETE request
        pass


def _delete_smartlist(smartlist_obj):
    """
    This un deletes the given smartlist record from database
    :param campaign:
    :return:
    """
    try:
        Smartlist.delete(smartlist_obj)
    except Exception:  # resource may have been deleted in case of DELETE request
        pass


def _create_sms_campaign_smartlist(campaign, smartlist):
    """
    This creates a smartlist for given campaign
    :param campaign:
    :return:
    """
    sms_campaign_smartlist = SmsCampaignSmartlist(smartlist_id=smartlist.id,
                                                  campaign_id=campaign.id)
    SmsCampaignSmartlist.save(sms_campaign_smartlist)
    return sms_campaign_smartlist


def _create_blast(campaign_id):
    """
    This creates campaign blast object for given campaign id
    :param campaign_id:
    :return:
    """
    blast_obj = SmsCampaignBlast(campaign_id=campaign_id)
    SmsCampaignBlast.save(blast_obj)
    return blast_obj


def _delete_blast(blast_obj):
    """
    This deletes the campaign blast obj from database.
    :param blast_obj:
    :return:
    """
    try:
        SmsCampaignBlast.delete(blast_obj)
    except Exception:  # resource may have been deleted in case of DELETE request
        pass


def _get_auth_header(access_token):
    """
    This returns auth header dict.
    :param access_token:
    :return:
    """
    auth_header = {'Authorization': 'Bearer %s' % access_token}
    auth_header.update(JSON_CONTENT_TYPE_HEADER)
    return auth_header
