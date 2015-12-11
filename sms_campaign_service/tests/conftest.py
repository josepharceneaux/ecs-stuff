"""
Author: Hafiz Muhammad Basit, QC-Technologies,
        Lahore, Punjab, Pakistan <basit.gettalent@gmail.com>

    This file contains pyTest fixtures for tests of SMS Campaign Service.
"""
# App Settings
from sms_campaign_service import init_sms_campaign_app
app = init_sms_campaign_app()

# Application Specific
# common conftest
from sms_campaign_service.common.tests.conftest import *


# App specific
from sms_campaign_service.common.models.user import UserPhone
from sms_campaign_service.sms_campaign_base import SmsCampaignBase
from sms_campaign_service.common.models.misc import (UrlConversion, Activity)
from sms_campaign_service.sms_campaign_app_constants import (TWILIO, CANDIDATE_PHONE_LABEL)
from sms_campaign_service.common.models.candidate import (PhoneLabel, CandidatePhone)
from sms_campaign_service.common.models.smart_list import (SmartList, SmartListCandidate)
from sms_campaign_service.common.models.sms_campaign import (SmsCampaign, SmsCampaignSmartlist,
                                                             SmsCampaignBlast, SmsCampaignSend,
                                                             SmsCampaignSendUrlConversion)


@pytest.fixture()
def auth_token(user_auth, sample_user):
    """
    returns the access token using pytest fixture defined in common/tests/conftest.py
    :param user_auth: fixture in common/tests/conftest.py
    :param sample_user: fixture in common/tests/conftest.py
    """
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    return auth_token_row['access_token']


@pytest.fixture()
def valid_header(auth_token):
    """
    Returns the header containing access token and content-type to make POST/DELETE requests.
    :param auth_token: fixture to get access token of user
    """
    return {'Authorization': 'Bearer %s' % auth_token,
            'content-type': 'application/json'}


@pytest.fixture()
def user_phone_1(request, sample_user):
    """
    This creates a user_phone record for sample_user
    :param request:
    :param sample_user: fixture in common/tests/conftest.py
    :return:
    """
    user_phone = _create_user_twilio_phone(sample_user, gen_salt(15))

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
    user_phone = _create_user_twilio_phone(sample_user, gen_salt(15))

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
    user_phone = _create_user_twilio_phone(sample_user_2, gen_salt(15))

    def tear_down():
        UserPhone.delete(user_phone)

    request.addfinalizer(tear_down)
    return user_phone


@pytest.fixture()
def campaign_valid_data():
    """
    This returns the valid data to save an SMS campaign in database
    :return:
    """
    return {"name": "TEST SMS Campaign",
            "sms_body_text": "HI all, we have few openings at http://www.abc.com",
            "frequency_id": 2,
            "added_time": "2015-11-24T08:00:00",
            "send_time": "2015-11-26T08:00:00",
            "stop_time": "2015-11-30T08:00:00",
            }


@pytest.fixture()
def campaign_invalid_data():
    """
    This returns invalid data to save an SMS campaign. 'sms_body_text' required field
    name is modified to 'text' here.
    :return:
    """
    return {"name": "TEST SMS Campaign",
            "text": "HI all, we have few openings at http://www.abc.com",  # invalid key
            "frequency_id": 2,
            "added_time": "2015-11-24T08:00:00",
            "send_time": "2015-11-26T08:00:00",
            "stop_time": "2015-11-30T08:00:00",
            }


@pytest.fixture()
def sms_campaign_of_current_user(campaign_valid_data, user_phone_1):
    return _create_sms_campaign(campaign_valid_data, user_phone_1)


@pytest.fixture()
def sms_campaign_of_current_user_with_no_link(campaign_valid_data, user_phone_1):
    campaign_valid_data['sms_body_text'] = 'HI all'
    return _create_sms_campaign(campaign_valid_data, user_phone_1)


@pytest.fixture()
def sms_campaign_of_other_user(campaign_valid_data, user_phone_3):
    return _create_sms_campaign(campaign_valid_data, user_phone_3)


@pytest.fixture()
def create_sms_campaign_blast(sms_campaign_of_current_user):
    """
    This creates a record in database table "sms_campaign_blast"
    :param sms_campaign_of_current_user:
    :return:
    """
    return SmsCampaignBase.create_or_update_sms_campaign_blast(sms_campaign_of_current_user.id)


@pytest.fixture()
def create_campaign_sends(candidate_first, candidate_second, create_sms_campaign_blast):
    """
    This creates a record in database table "sms_campaign_send"
    :param candidate_first: fixture to create test candidate
    :param candidate_second: fixture to create another test candidate
    :return:
    """
    campaign_send_1 = SmsCampaignBase.create_or_update_sms_campaign_send(create_sms_campaign_blast,
                                                                         candidate_first.id,
                                                                         datetime.now())
    campaign_send_2 = SmsCampaignBase.create_or_update_sms_campaign_send(create_sms_campaign_blast,
                                                                         candidate_second.id,
                                                                         datetime.now())


@pytest.fixture()
def sample_smartlist(request, sample_user):
    """
    This creates sample smartlist for sample user
    :param request:
    :param sample_user:
    :return:
    """

    smart_list = _create_smart_list(sample_user)

    def tear_down():
        SmartList.delete(smart_list)

    request.addfinalizer(tear_down)
    return smart_list


@pytest.fixture()
def sample_smartlist_2(request, sample_user):
    """
    This creates sample smartlist for sample user
    :param request:
    :param sample_user:
    :return:
    """
    smart_list = _create_smart_list(sample_user)

    def tear_down():
        SmartList.delete(smart_list)

    request.addfinalizer(tear_down)
    return smart_list


@pytest.fixture()
def sample_sms_campaign_candidates(sample_user,
                                   sample_smartlist,
                                   candidate_first,
                                   candidate_second):
    """
    This adds two candidates to sample_smartlist
    :param sample_smartlist:
    :param candidate_first:
    :param candidate_second:
    :return:
    """
    candidate_first.update(user_id=sample_user.id)
    candidate_second.update(user_id=sample_user.id)
    smart_list_candidate_1 = SmartListCandidate(smart_list_id=sample_smartlist.id,
                                                candidate_id=candidate_first.id)
    SmartListCandidate.save(smart_list_candidate_1)
    smart_list_candidate_2 = SmartListCandidate(smart_list_id=sample_smartlist.id,
                                                candidate_id=candidate_second.id)
    SmartListCandidate.save(smart_list_candidate_2)


@pytest.fixture()
def sms_campaign_smartlist(sample_smartlist, sms_campaign_of_current_user):
    """
    This associates sample_smartlist with the sms_campaign_of_current_user
    :param sample_smartlist:
    :param sms_campaign_of_current_user:
    :return:
    """
    sms_campaign_smart_list = SmsCampaignSmartlist(smart_list_id=sample_smartlist.id,
                                                   sms_campaign_id=sms_campaign_of_current_user.id)
    SmsCampaignSmartlist.save(sms_campaign_smart_list)
    return sms_campaign_smart_list


@pytest.fixture()
def sms_campaign_smartlist_2(sample_smartlist_2, sms_campaign_of_current_user):
    """
    This associates sample_smartlist with the sms_campaign_of_current_user
    :param sample_smartlist:
    :param sms_campaign_of_current_user:
    :return:
    """
    sms_campaign_smart_list = SmsCampaignSmartlist(smart_list_id=sample_smartlist_2.id,
                                                   sms_campaign_id=sms_campaign_of_current_user.id)
    SmsCampaignSmartlist.save(sms_campaign_smart_list)
    return sms_campaign_smart_list


@pytest.fixture()
def candidate_phone_1(request, candidate_first):
    """
    This associates sample_smartlist with the sms_campaign_of_current_user
    :param candidate_first:
    :return:
    """
    candidate_phone = _create_candidate_mobile_phone(candidate_first, gen_salt(15))

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
    candidate_phone = _create_candidate_mobile_phone(candidate_second, gen_salt(15))

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
    test_number = gen_salt(15)
    cand_phone_1 = _create_candidate_mobile_phone(candidate_first, test_number)
    cand_phone_2 = _create_candidate_mobile_phone(candidate_second, test_number)

    def tear_down():
        CandidatePhone.delete(cand_phone_1)
        CandidatePhone.delete(cand_phone_2)

    request.addfinalizer(tear_down)
    return cand_phone_1, cand_phone_2


@pytest.fixture()
def process_send_sms_campaign(sample_user, auth_token,
                              sms_campaign_of_current_user,
                              sample_sms_campaign_candidates,
                              sms_campaign_smartlist,
                              candidate_phone_1,
                              ):
    """
    This function serves the sending part of SMS campaign
    :return:
    """
    campaign_obj = SmsCampaignBase(sample_user.id)
    # send campaign to candidates
    campaign_obj.process_send(sms_campaign_of_current_user)


@pytest.fixture()
def url_conversion_by_send_test_sms_campaign(request,
                                             sms_campaign_of_current_user,
                                             process_send_sms_campaign):
    """
    This sends SMS campaign and returns the source URL from url_conversion database table.
    :return:
    """
    # get campaign blast
    sms_campaign_blast = SmsCampaignBlast.get_by_campaign_id(sms_campaign_of_current_user.id)
    # get campaign sends
    sms_campaign_sends = SmsCampaignSend.get_by_blast_id(str(sms_campaign_blast.id))
    # get if of record of sms_campaign_send_url_conversion for this campaign
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
    :param user_phone: user_phone row
    :return:
    """
    campaign_data['user_phone_id'] = user_phone.id
    sms_campaign = SmsCampaign(**campaign_data)
    SmsCampaign.save(sms_campaign)
    return sms_campaign


def _create_user_twilio_phone(user, phone_value):
    """
    This adds user_phone record in database table "user_phone"
    :param user: user row
    :param phone_value: value of phone number
    :return: user_phone row
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
    :param candidate: Candidate row
    :param phone_value: value of phone number
    :return: user_phone row
    """
    phone_label_id = PhoneLabel.phone_label_id_from_phone_label(CANDIDATE_PHONE_LABEL)
    candidate_phone = CandidatePhone(candidate_id=candidate.id,
                                     phone_label_id=phone_label_id,
                                     value=phone_value)
    CandidatePhone.save(candidate_phone)
    return candidate_phone


def _create_smart_list(test_user):
    """
    This creates Smartlist for given user
    :param test_user:
    :return:
    """
    smart_list = SmartList(name=gen_salt(20), user_id=test_user.id)
    SmartList.save(smart_list)
    return smart_list


def assert_for_activity(user_id, type_, source_id):
    """
    This verifies that activity has been created for given action
    :param user_id:
    :param type_:
    :param source_id:
    :return:
    """
    db.session.commit()
    assert Activity.get_by_user_id_type_source_id(user_id, type_, source_id)
