"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This file contains pyTest fixtures for tests of SMS Campaign Service.
"""
# Standard Import
import json
from datetime import (datetime, timedelta)

# Third Party
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm.exc import ObjectDeletedError

# Application Specific
# common conftest
from sms_campaign_service.common.tests.conftest import \
    (db, pytest, fake, requests, gen_salt, user_auth, access_token_first,
     sample_client, test_domain, first_group, domain_first, user_first, candidate_first,
     test_domain_2, second_group, domain_second, candidate_second,
     user_same_domain, user_from_diff_domain, access_token_second, talent_pipeline, talent_pool,
     access_token_other, access_token_same, talent_pool_other, talent_pipeline_other)

# Service specific
from sms_campaign_service.sms_campaign_app import app
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.common.tests.fake_testing_data_generator import FakeCandidatesData
from sms_campaign_service.tests.modules.common_functions import (assert_api_send_response,
                                                                 assert_campaign_schedule,
                                                                 delete_test_scheduled_task,
                                                                 assert_campaign_creation,
                                                                 candidate_ids_associated_with_campaign,
                                                                 reply_and_assert_response)
from sms_campaign_service.modules.sms_campaign_app_constants import (TWILIO, MOBILE_PHONE_LABEL,
                                                                     TWILIO_TEST_NUMBER,
                                                                     TWILIO_INVALID_TEST_NUMBER)

# Database Models
from sms_campaign_service.common.models.user import UserPhone
from sms_campaign_service.common.models.misc import (UrlConversion, Frequency)
from sms_campaign_service.common.models.sms_campaign import (SmsCampaign, SmsCampaignBlast)
from sms_campaign_service.common.models.candidate import (PhoneLabel, CandidatePhone, Candidate)

# Common Utils
from sms_campaign_service.common.routes import CandidateApiUrl
from sms_campaign_service.common.utils.datetime_utils import DatetimeUtils
from sms_campaign_service.common.utils.handy_functions import JSON_CONTENT_TYPE_HEADER
from sms_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers, \
    FixtureHelpers

# This is data to create/update SMS campaign
CREATE_CAMPAIGN_DATA = {"name": "TEST SMS Campaign",
                        "body_text": "Hi all, we have few openings at https://www.gettalent.com",
                        "smartlist_ids": ""
                        }


# This is data to schedule an SMS campaign
def generate_campaign_schedule_data():
    """
    This returns a dictionary to schedule an sms-campaign
    """
    return {"frequency_id": Frequency.ONCE,
            "start_datetime": DatetimeUtils.to_utc_str(datetime.utcnow() + timedelta(minutes=1)),
            "end_datetime": DatetimeUtils.to_utc_str(datetime.utcnow() + relativedelta(days=+5))}


def remove_any_user_phone_record_with_twilio_test_number():
    """
    This function cleans the database tables user_phone and candidate_phone.
    If any record in these two tables has phone number value either TWILIO_TEST_NUMBER or
    TWILIO_INVALID_TEST_NUMBER, we remove all those records before running the tests.
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
def valid_header_2(access_token_other):
    """
    Returns the header (for user of some other domain) containing access token and content-type
    to make POST/DELETE requests.
    """
    return _get_auth_header(access_token_other)


@pytest.fixture()
def valid_header_same_domain(access_token_same):
    """
    Returns the header (for other user of same domain) containing access token and content-type
    to make POST/DELETE requests.
    """
    return _get_auth_header(access_token_same)


@pytest.fixture()
def user_phone_1(request, user_first):
    """
    This creates a user_phone record for user_first
    :param user_first: fixture in common/tests/conftest.py
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
    :param user_first: fixture in common/tests/conftest.py
    """
    user_phone = _create_user_twilio_phone(user_first, fake.phone_number())

    def tear_down():
        _delete_user_phone(user_phone)

    request.addfinalizer(tear_down)
    return user_phone


@pytest.fixture()
def user_phone_3(request, user_same_domain):
    """
    This creates user_phone record for user_same_domain
    :param user_same_domain: fixture in common/tests/conftest.py
    """
    user_phone = _create_user_twilio_phone(user_same_domain, fake.phone_number())

    def tear_down():
        _delete_user_phone(user_phone)

    request.addfinalizer(tear_down)
    return user_phone


@pytest.fixture()
def campaign_valid_data(smartlist_with_two_candidates):
    """
    This returns the valid data to save an SMS campaign in database
    """
    campaign_data = CREATE_CAMPAIGN_DATA.copy()
    campaign_data['smartlist_ids'] = [smartlist_with_two_candidates[0]]
    return campaign_data


@pytest.fixture()
def campaign_data_unknown_key_text():
    """
    This returns invalid data to save an SMS campaign. 'body_text' required field
    name is modified to be 'text' here i.e. the correct value is 'body_text'
    """
    campaign_data = CREATE_CAMPAIGN_DATA.copy()
    campaign_data['text'] = campaign_data.pop('body_text')
    return campaign_data


@pytest.fixture()
def smartlist_with_two_candidates(access_token_first, talent_pipeline):
    """
    This creates a smartlist with two candidates
    """
    smartlist_id, candidate_ids = CampaignsTestsHelpers.create_smartlist_with_candidate(
        access_token_first, talent_pipeline, count=2, create_phone=True, assign_role=True)
    return smartlist_id, candidate_ids


@pytest.fixture()
def smartlist_with_two_candidates_in_other_domain(access_token_other, talent_pipeline_other):
    """
    This creates a smartlist with two candidates for user_from_diff_domain
    """
    smartlist_id, candidate_ids = CampaignsTestsHelpers.create_smartlist_with_candidate(
        access_token_other, talent_pipeline_other, count=2, create_phone=True, assign_role=True)
    return smartlist_id, candidate_ids


@pytest.fixture()
def sms_campaign_of_current_user(request, campaign_valid_data, talent_pipeline,
                                 valid_header, smartlist_with_two_candidates, user_phone_1):
    """
    This creates the SMS campaign for user_first using valid data.
    """
    smartlist_id, _ = smartlist_with_two_candidates
    campaign_valid_data['smartlist_ids'] = [smartlist_id]
    test_sms_campaign = create_sms_campaign_via_api(campaign_valid_data, valid_header,
                                                    talent_pipeline.user.id)

    def fin():
        _delete_campaign(test_sms_campaign)

    request.addfinalizer(fin)
    return test_sms_campaign


@pytest.fixture()
def sms_campaign_with_two_smartlists(request, campaign_valid_data,
                                     access_token_first, talent_pipeline,
                                     valid_header):
    """
    This creates the SMS campaign for user_first using valid data and two smartlists.
    """
    smartlist_1_id, _ = CampaignsTestsHelpers.create_smartlist_with_candidate(
        access_token_first, talent_pipeline, create_phone=True)
    smartlist_2_id, _ = CampaignsTestsHelpers.create_smartlist_with_candidate(
        access_token_first, talent_pipeline, create_phone=True)
    campaign_valid_data['smartlist_ids'] = [smartlist_1_id, smartlist_2_id]
    test_sms_campaign = create_sms_campaign_via_api(campaign_valid_data, valid_header,
                                                    talent_pipeline.user.id)

    def fin():
        _delete_campaign(test_sms_campaign)

    request.addfinalizer(fin)
    return test_sms_campaign


@pytest.fixture()
def sms_campaign_with_one_valid_candidate(request, campaign_valid_data,
                                          access_token_first, talent_pipeline,
                                          valid_header):
    """
    This fixture creates an SMS campaign with two candidates. Only one candidates has phone number
    associated with it.
    """
    # create candidate
    candidates_data = FakeCandidatesData.create(talent_pool=talent_pipeline.talent_pool)
    candidate_2_data = FakeCandidatesData.create(talent_pool=talent_pipeline.talent_pool,
                                                 create_phone=False)
    candidates_data['candidates'].append(candidate_2_data['candidates'][0])
    smartlist_id, _ = CampaignsTestsHelpers.create_smartlist_with_candidate(access_token_first,
                                                                            talent_pipeline,
                                                                            data=candidates_data)
    campaign_valid_data['smartlist_ids'] = [smartlist_id]
    test_sms_campaign = create_sms_campaign_via_api(campaign_valid_data, valid_header,
                                                    talent_pipeline.user.id)

    def fin():
        _delete_campaign(test_sms_campaign)

    request.addfinalizer(fin)
    return test_sms_campaign


@pytest.fixture()
def sms_campaign_with_no_candidate(request, campaign_valid_data,
                                   access_token_first, talent_pipeline,
                                   valid_header, user_phone_1):
    """
    This creates the SMS campaign for user_first using valid data.
    """
    smartlist_id = FixtureHelpers.create_smartlist_with_search_params(access_token_first,
                                                                      talent_pipeline.id)
    campaign_valid_data['smartlist_ids'] = [smartlist_id]
    test_sms_campaign = create_sms_campaign_via_api(campaign_valid_data, valid_header,
                                                    talent_pipeline.user.id)

    def fin():
        _delete_campaign(test_sms_campaign)

    request.addfinalizer(fin)
    return test_sms_campaign


@pytest.fixture()
def sms_campaign_of_other_user_in_same_domain(request, campaign_valid_data,
                                              user_same_domain, valid_header_same_domain,
                                              user_phone_3,
                                              smartlist_with_two_candidates):
    """
    This creates the SMS campaign for user_same_domain using valid data, so that we have
    another campaign in the user_first's domain.
    """
    smartlist_id, _ = smartlist_with_two_candidates
    campaign_valid_data['smartlist_ids'] = [smartlist_id]
    test_sms_campaign = create_sms_campaign_via_api(campaign_valid_data,
                                                    valid_header_same_domain,
                                                    user_same_domain.id)

    def fin():
        _delete_campaign(test_sms_campaign)

    request.addfinalizer(fin)
    return test_sms_campaign


@pytest.fixture()
def bulk_sms_campaigns(request, campaign_valid_data, talent_pipeline,
                       valid_header, smartlist_with_two_candidates, user_phone_1):
    """
    This creates the 10 SMS campaign for user_first using valid data.
    """
    smartlist_id, _ = smartlist_with_two_candidates
    campaign_valid_data['smartlist_ids'] = [smartlist_id]
    test_campaigns = []
    for _ in xrange(1, 11):
        campaign_valid_data['name'] = 'bulk_campaigns: %s' % fake.name()
        test_campaigns.append(create_sms_campaign_via_api(campaign_valid_data, valid_header,
                                                          talent_pipeline.user.id))

    def fin():
        for test_sms_campaign in test_campaigns:
            _delete_campaign(test_sms_campaign)

    request.addfinalizer(fin)
    return test_campaigns


@pytest.fixture()
def invalid_sms_campaign(request, campaign_valid_data, user_phone_1):
    """
    This creates the SMS campaign for sample_user using valid data.
    """
    test_sms_campaign = _create_sms_campaign(campaign_valid_data, user_phone_1)

    def fin():
        _delete_campaign(test_sms_campaign)

    request.addfinalizer(fin)
    return test_sms_campaign


@pytest.fixture()
def sms_campaign_with_no_valid_candidate(request, campaign_valid_data,
                                         access_token_first, talent_pipeline,
                                         valid_header):
    """
    This creates the SMS campaign for user_first using valid data. Candidates associated
    with this campaign have no phone number saved in database.
    """
    smartlist_id, _ = CampaignsTestsHelpers.create_smartlist_with_candidate(
        access_token_first, talent_pipeline, count=2)
    campaign_valid_data['smartlist_ids'] = [smartlist_id]
    test_sms_campaign = create_sms_campaign_via_api(campaign_valid_data, valid_header,
                                                    talent_pipeline.user.id)

    def fin():
        _delete_campaign(test_sms_campaign)

    request.addfinalizer(fin)
    return test_sms_campaign


@pytest.fixture()
def sms_campaign_in_other_domain(request, campaign_valid_data, valid_header_2,
                                 talent_pipeline_other,
                                 smartlist_with_two_candidates_in_other_domain):
    """
    This creates SMS campaign for some other user in different domain.
    """
    smartlist_id, _ = smartlist_with_two_candidates_in_other_domain
    campaign_valid_data['smartlist_ids'] = [smartlist_id]
    test_sms_campaign = create_sms_campaign_via_api(campaign_valid_data,
                                                    valid_header_2,
                                                    talent_pipeline_other.user.id)

    def fin():
        _delete_campaign(test_sms_campaign)

    request.addfinalizer(fin)
    return test_sms_campaign


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
def scheduled_sms_campaign_of_other_domain(request, user_from_diff_domain,
                                           valid_header_2, sms_campaign_in_other_domain):
    """
    This creates the SMS campaign for user_from_diff_domain using valid data.
    """
    campaign = _get_scheduled_campaign(user_from_diff_domain,
                                       sms_campaign_in_other_domain,
                                       valid_header_2)

    def delete_scheduled_task():
        _unschedule_campaign(campaign, valid_header_2)

    request.addfinalizer(delete_scheduled_task)
    return campaign


@pytest.fixture()
def create_campaign_replies(candidate_and_phone_1, sent_campaign, access_token_first,
                            user_phone_1):
    """
    This hits the endpoint /v1/receive where we add an entry in database
    table "sms_campaign_reply" for first candidate associated with campaign.
    """
    reply_and_assert_response(sent_campaign, user_phone_1, candidate_and_phone_1[1],
                              access_token_first)


@pytest.fixture()
def create_bulk_replies(candidate_and_phone_1, candidate_and_phone_2, sent_campaign,
                        access_token_first, user_phone_1):
    """
    Here we create 10 replies to an sms-campaign.
    This hits the endpoint /v1/receive where we add an entry in database
    table "sms_campaign_reply" for first candidate associated with campaign.
    We use 2 candidates and create 5 replies from each candidate
    """
    for count in xrange(1, 6):
        reply_and_assert_response(sent_campaign, user_phone_1,
                                  candidate_and_phone_1[1], access_token_first,
                                  count_of_replies=count)

    for count in xrange(1, 6):
        reply_and_assert_response(sent_campaign, user_phone_1,
                                  candidate_and_phone_2[1], access_token_first,
                                  count_of_replies=count)


@pytest.fixture()
def candidate_and_phone_1(request, sent_campaign_and_blast_ids, access_token_first, valid_header):
    """
    This returns the candidate object and candidate_phone for first candidate associated with
    the sms-campaign in a tuple. Here we assume campaign has been sent to candidate.
    """
    candidate, candidate_phone = _get_candidate_and_phone_tuple(request,
                                                                sent_campaign_and_blast_ids,
                                                                access_token_first,
                                                                valid_header, candidate_index=0)
    return candidate, candidate_phone


@pytest.fixture()
def candidate_and_phone_2(request, sent_campaign_and_blast_ids, access_token_first, valid_header):
    """
    This returns the candidate object and candidate_phone for first candidate associated with
    the sms-campaign in a tuple. Here we assume campaign has been sent to candidate.
    """
    candidate, candidate_phone = _get_candidate_and_phone_tuple(request,
                                                                sent_campaign_and_blast_ids,
                                                                access_token_first,
                                                                valid_header, candidate_index=1)
    return candidate, candidate_phone


@pytest.fixture()
def candidate_phone_2(request, candidate_second):
    """
    This associates sample_smartlist with the sms_campaign_of_current_user
    :param candidate_second: fixture to create candidate
    """
    candidate_phone = _create_candidate_mobile_phone(candidate_second, fake.phone_number())

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
def candidates_with_same_phone(user_first, smartlist_with_two_candidates):
    """
    This assigns same phone number to both Candidates associated with this campaign.
    It then returns both candidates of user_first.
    """
    common_phone = fake.phone_number()
    db.session.commit()
    user_first.candidates[0].phones[0].update(value=common_phone)
    user_first.candidates[1].phones[0].update(value=common_phone)
    return user_first.candidates[0], user_first.candidates[1]


@pytest.fixture()
def candidates_with_same_phone_in_diff_domains(request, candidate_and_phone_1,
                                               candidate_in_other_domain):
    """
    This associates same number to candidate_first and candidate_in_other_domain
    """
    cand_phone_2 = _create_candidate_mobile_phone(candidate_in_other_domain,
                                                  candidate_and_phone_1[1]['value'])

    def tear_down():
        _delete_candidate_phone(cand_phone_2)

    request.addfinalizer(tear_down)
    return Candidate.get(candidate_and_phone_1[0]['id']), candidate_in_other_domain


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
def sent_campaign(access_token_first, sms_campaign_of_current_user):
    """
    This function serves the sending part of SMS campaign.
    This sends campaign to two candidates.
    """
    response_post = CampaignsTestsHelpers.send_campaign(
        SmsCampaignApiUrl.SEND, sms_campaign_of_current_user,
        access_token_first, SmsCampaignApiUrl.BLASTS)
    assert_api_send_response(sms_campaign_of_current_user, response_post, requests.codes.OK)
    return sms_campaign_of_current_user


@pytest.fixture()
def sent_campaign_and_blast_ids(access_token_first, sent_campaign):
    """
    This fixture returns the campaign object which has been sent.
    It also gets it's blasts and return a tuple containing campaign object and blast_ids.
    """
    blasts = CampaignsTestsHelpers.get_blasts(sent_campaign, access_token_first,
                                              SmsCampaignApiUrl.BLASTS % sent_campaign['id'])
    blasts_ids = [blast['id'] for blast in blasts]
    return sent_campaign, blasts_ids


@pytest.fixture()
def sent_campaign_in_other_domain(access_token_other, sms_campaign_in_other_domain):
    """
    This sends the campaign in some other domain. It returns sent campaign object.
    """
    response_post = CampaignsTestsHelpers.send_campaign(
        SmsCampaignApiUrl.SEND, sms_campaign_in_other_domain,
        access_token_other, SmsCampaignApiUrl.BLASTS)
    assert_api_send_response(sms_campaign_in_other_domain, response_post, requests.codes.OK)
    return sms_campaign_in_other_domain


@pytest.fixture()
def sent_campaign_and_blast_ids_in_other_domain(access_token_other, sent_campaign_in_other_domain):
    """
    This gets the blasts of sent the campaign in some other domain.
    It returns sent campaign object and blast_ids.
    """
    blasts = CampaignsTestsHelpers.get_blasts(sent_campaign_in_other_domain, access_token_other,
                                              SmsCampaignApiUrl.BLASTS %
                                              sent_campaign_in_other_domain['id'])
    blasts_ids = [blast['id'] for blast in blasts]
    return sent_campaign_in_other_domain, blasts_ids


@pytest.fixture()
def campaign_with_ten_candidates(request, access_token_first, talent_pipeline, campaign_valid_data,
                                 valid_header):
    """
    This creates an SMS campaign with ten candidates
    """
    # create candidate
    smartlist_id, candidate_ids = CampaignsTestsHelpers.create_smartlist_with_candidate(
        access_token_first, talent_pipeline, count=10, create_phone=True)
    campaign_valid_data['smartlist_ids'] = [smartlist_id]
    test_sms_campaign = create_sms_campaign_via_api(campaign_valid_data, valid_header,
                                                    talent_pipeline.user.id)

    def fin():
        _delete_campaign(test_sms_campaign)

    request.addfinalizer(fin)
    return test_sms_campaign, candidate_ids


@pytest.fixture()
def sent_campaign_bulk(campaign_with_ten_candidates, access_token_first):
    """
    This fixture sends the campaign which has 10 candidates associate with it and returns
    the campaign obj.
    """
    # send campaign
    response_post = CampaignsTestsHelpers.send_campaign(
        SmsCampaignApiUrl.SEND, campaign_with_ten_candidates[0],
        access_token_first, SmsCampaignApiUrl.BLASTS)
    assert_api_send_response(campaign_with_ten_candidates[0], response_post, 200)
    return campaign_with_ten_candidates


@pytest.fixture()
def sent_campaign_bulk_and_blast_ids(access_token_first, sent_campaign_bulk):
    """
    This fixture returns the campaign object which has been sent.
    It also gets it's blasts and return a tuple containing campaign object and blast_ids.
    """
    blasts = CampaignsTestsHelpers.get_blasts(sent_campaign_bulk[0], access_token_first,
                                              SmsCampaignApiUrl.BLASTS % sent_campaign_bulk[0][
                                                  'id'])
    blasts_ids = [blast['id'] for blast in blasts]
    return sent_campaign_bulk, blasts_ids


@pytest.fixture()
def url_conversion_by_send_test_sms_campaign(request, sent_campaign):
    """
    This sends SMS campaign (using sent_campaign fixture) and returns the source URL
    from url_conversion database table.
    """
    # Need to commit the session because Celery has its own session and our session does not
    # know about the changes that Celery session has made.
    db.session.commit()
    campaign_in_db = SmsCampaign.get_by_id(sent_campaign['id'])
    # get campaign blast
    sms_campaign_blast = campaign_in_db.blasts[0]
    CampaignsTestsHelpers.assert_blast_sends(campaign_in_db, 2, abort_time_for_sends=20)
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
    """
    smartlist_ids = campaign_data['smartlist_ids']
    del campaign_data['smartlist_ids']  # This is not a field of "sms_campaign" table.
    campaign_data['user_phone_id'] = user_phone.id
    sms_campaign = SmsCampaign(**campaign_data)
    SmsCampaign.save(sms_campaign)
    # We put it back again
    campaign_data['smartlist_ids'] = smartlist_ids
    return sms_campaign


def create_sms_campaign_via_api(campaign_data, headers, user_id):
    """
    This creates an SMS campaign in database table "sms_campaign"
    :param campaign_data: data to create campaign
    :param headers: auth headers to make HTTP request
    :param user_id: if of User object
    """
    response = requests.post(SmsCampaignApiUrl.CAMPAIGNS,
                             headers=headers,
                             data=json.dumps(campaign_data))
    print response.json()
    campaign_id = assert_campaign_creation(response, user_id, requests.codes.CREATED)
    response = requests.get(SmsCampaignApiUrl.CAMPAIGN % campaign_id,
                            headers=headers)
    assert response.status_code == 200, 'Response should be ok (200)'
    return response.json()['campaign']


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


def _get_scheduled_campaign(user, campaign, auth_header):
    """
    This schedules the given campaign and return it.
    """
    response = requests.post(
        SmsCampaignApiUrl.SCHEDULE % campaign['id'], headers=auth_header,
        data=json.dumps(generate_campaign_schedule_data()))
    assert_campaign_schedule(response, user.id, campaign['id'])
    # GET campaign from API, now it should have scheduler_task_id associated with it.
    response = requests.get(SmsCampaignApiUrl.CAMPAIGN % campaign['id'], headers=auth_header)
    assert response.ok
    return response.json()['campaign']


def _unschedule_campaign(campaign, headers):
    """
    This un schedules the given campaign from scheduler_service
    """
    try:
        scheduler_task_id = campaign['scheduler_task_id']
        delete_test_scheduled_task(scheduler_task_id, headers)
    except ObjectDeletedError:  # campaign may have been deleted in case of DELETE request
        pass


def _delete_campaign(campaign_obj):
    """
    This deletes the given campaign from database
    :param campaign_obj: sms-campaign object
    """
    try:
        SmsCampaign.delete(campaign_obj)
    except Exception:  # campaign may have been deleted in case of DELETE request
        pass


def _delete_candidate_phone(candidate_phone_obj):
    """
    This deletes the given candidate_phone record from database
    """
    try:
        CandidatePhone.delete(candidate_phone_obj)
    except Exception:  # resource may have been deleted in case of DELETE request
        pass


def _delete_user_phone(user_phone_obj):
    """
    This deletes the given user_phone record from database
    """
    try:
        UserPhone.delete(user_phone_obj)
    except Exception:  # resource may have been deleted in case of DELETE request
        pass


def _delete_blast(blast_obj):
    """
    This deletes the campaign blast obj from database.
    :param blast_obj: sms-campaign's blast object
    :type blast_obj: SmsCampaignBlast
    """
    try:
        SmsCampaignBlast.delete(blast_obj)
    except Exception:  # resource may have been deleted in case of DELETE request
        pass


def _get_auth_header(access_token):
    """
    This returns auth header dict.
    :param access_token: access token of user
    """
    auth_header = {'Authorization': 'Bearer %s' % access_token}
    auth_header.update(JSON_CONTENT_TYPE_HEADER)
    return auth_header


def _get_candidate_and_phone_tuple(request, sent_campaign_and_blast_ids, access_token_first,
                                   valid_header, candidate_index):
    """
    This returns the candidate and candidate phone as specified by the candidate index
    for given campaign.
    """
    sent_campaign_obj, blast_ids = sent_campaign_and_blast_ids
    CampaignsTestsHelpers.assert_blast_sends(sent_campaign_obj, 2,
                                             blast_url=SmsCampaignApiUrl.BLAST
                                                       % (sent_campaign_obj['id'], blast_ids[0]),
                                             access_token=access_token_first)
    candidate_ids = candidate_ids_associated_with_campaign(sent_campaign_obj, access_token_first)
    candidate_get_response = requests.get(
        CandidateApiUrl.CANDIDATE % candidate_ids[candidate_index],
        headers=valid_header)
    json_response = candidate_get_response.json()
    candidate_phone = json_response['candidate']['phones'][0]

    def tear_down():
        _delete_candidate_phone(candidate_phone['id'])

    request.addfinalizer(tear_down)
    return json_response['candidate'], candidate_phone
