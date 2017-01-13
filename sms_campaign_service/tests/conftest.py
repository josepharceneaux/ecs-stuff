"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This file contains pyTest fixtures for tests of SMS Campaign Service.
"""
# Third Party
from requests import codes
from sqlalchemy.orm.exc import ObjectDeletedError

# Application Specific
# common conftest
from sms_campaign_service.common.tests.conftest import *

# Service specific
from sms_campaign_service.common.routes import SmsCampaignApiUrl
from sms_campaign_service.modules.constants import (TWILIO, MOBILE_PHONE_LABEL)
from sms_campaign_service.common.tests.fake_testing_data_generator import FakeCandidatesData
from sms_campaign_service.tests.modules.common_functions import (assert_api_send_response,
                                                                 delete_test_scheduled_task,
                                                                 assert_campaign_creation,
                                                                 candidate_ids_associated_with_campaign,
                                                                 reply_and_assert_response,
                                                                 assert_campaign_delete, generate_campaign_data,
                                                                 generate_campaign_schedule_data,
                                                                 remove_any_user_phone_record_with_twilio_test_number)

# Database Models
from sms_campaign_service.common.models.user import UserPhone
from sms_campaign_service.common.models.misc import (UrlConversion, Frequency)
from sms_campaign_service.common.models.sms_campaign import (SmsCampaign, SmsCampaignBlast)
from sms_campaign_service.common.models.candidate import (PhoneLabel, CandidatePhone, Candidate)

# Common Utils
from sms_campaign_service.common.routes import CandidateApiUrl
from sms_campaign_service.common.campaign_services.tests_helpers import (CampaignsTestsHelpers, FixtureHelpers)

# clean database tables user_phone and candidate_phone first
remove_any_user_phone_record_with_twilio_test_number()


@pytest.fixture(params=['user_first', 'user_same_domain'])
def data_for_different_users_of_same_domain(request, access_token_first, access_token_same,
                                            user_first, user_same_domain, headers, headers_same):
    """
    This fixture is used to test the API with two users of same domain("user_first" and "user_same_domain")
    using their access_tokens. This returns a dict containing access_token, user object and auth headers.
    """
    if request.param == 'user_first':
        return {'access_token': access_token_first, 'user': user_first, 'headers': headers}
    elif request.param == 'user_same_domain':
        return {'access_token': access_token_same, 'user': user_same_domain, 'headers': headers_same}


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
    campaign_data = generate_campaign_data()
    campaign_data['smartlist_ids'] = [smartlist_with_two_candidates[0]]
    return campaign_data


@pytest.fixture(params=generate_campaign_data().keys())
def invalid_data_for_campaign_creation(request):
    """
    This function returns the data to create an sms-campaign. It also removes a required
    field from data to make it invalid.
    Required fields are 'name', 'body_text', 'smartlist_ids'
    """
    campaign_data = generate_campaign_data()
    del campaign_data[request.param]
    return campaign_data, request.param


@pytest.fixture()
def smartlist_with_two_candidates(access_token_first, talent_pipeline):
    """
    This creates a smartlist with two candidates
    """
    smartlist_id, candidate_ids = CampaignsTestsHelpers.create_smartlist_with_candidate(
        access_token_first, talent_pipeline, count=2, create_phone=True)
    return smartlist_id, candidate_ids


@pytest.fixture()
def smartlist_with_two_candidates_in_other_domain(access_token_other, talent_pipeline_other):
    """
    This creates a smartlist with two candidates for user_from_diff_domain
    """
    smartlist_id, candidate_ids = CampaignsTestsHelpers.create_smartlist_with_candidate(
        access_token_other, talent_pipeline_other, count=2, create_phone=True)
    return smartlist_id, candidate_ids


@pytest.fixture()
def sms_campaign_of_user_first(request, campaign_valid_data, talent_pipeline, headers, smartlist_with_two_candidates,
                               user_phone_1):
    """
    This creates the SMS campaign for user_first using valid data.
    """
    smartlist_id, _ = smartlist_with_two_candidates
    campaign_valid_data['smartlist_ids'] = [smartlist_id]
    test_sms_campaign = create_sms_campaign_via_api(campaign_valid_data, headers, talent_pipeline.user.id)

    def fin():
        _delete_campaign(test_sms_campaign, headers)

    request.addfinalizer(fin)
    return test_sms_campaign


@pytest.fixture()
def campaign_with_archived_candidate(campaign_valid_data, talent_pipeline, headers,
                                     smartlist_with_archived_candidate):
    """
    This creates an sms-campaign associated to smartlist which has one archived candidate in it.
    """
    campaign_valid_data['smartlist_ids'] = [smartlist_with_archived_candidate['id']]
    sms_campaign = create_sms_campaign_via_api(campaign_valid_data, headers, talent_pipeline.user.id)
    return sms_campaign


@pytest.fixture()
def sms_campaign_with_two_smartlists(request, campaign_valid_data, access_token_first, talent_pipeline, headers):
    """
    This creates the SMS campaign for "user_first"(fixture) using valid data and two smartlists.
    It then returns the campaign object.
    """
    smartlist_1_id, _ = CampaignsTestsHelpers.create_smartlist_with_candidate(access_token_first,
                                                                              talent_pipeline, create_phone=True)
    smartlist_2_id, _ = CampaignsTestsHelpers.create_smartlist_with_candidate(access_token_first,
                                                                              talent_pipeline, create_phone=True)
    campaign_valid_data['smartlist_ids'] = [smartlist_1_id, smartlist_2_id]
    test_sms_campaign = create_sms_campaign_via_api(campaign_valid_data, headers, talent_pipeline.user.id)

    def fin():
        _delete_campaign(test_sms_campaign, headers)

    request.addfinalizer(fin)
    return test_sms_campaign


@pytest.fixture()
def sms_campaign_with_one_valid_candidate(request, campaign_valid_data, access_token_first, talent_pipeline, headers):
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
    test_sms_campaign = create_sms_campaign_via_api(campaign_valid_data, headers,
                                                    talent_pipeline.user.id)

    def fin():
        _delete_campaign(test_sms_campaign, headers)

    request.addfinalizer(fin)
    return test_sms_campaign


@pytest.fixture()
def sms_campaign_with_same_candidate_in_multiple_smartlists(request, campaign_valid_data, talent_pipeline, headers,
                                                            access_token_first, smartlist_with_two_candidates):
    """
    This fixture creates an SMS campaign with two smartlists.
    Smartlist 1 will have two candidates and smartlist 2 will have one candidate (which will be
    same as one of the two candidates of smartlist 1).
    """
    smartlist_ids = CampaignsTestsHelpers.get_two_smartlists_with_same_candidate(
        talent_pipeline, access_token_first, smartlist_and_candidate_ids=smartlist_with_two_candidates)
    campaign_valid_data['smartlist_ids'] = smartlist_ids
    test_sms_campaign = create_sms_campaign_via_api(campaign_valid_data, headers, talent_pipeline.user.id)

    def fin():
        _delete_campaign(test_sms_campaign, headers)

    request.addfinalizer(fin)
    return test_sms_campaign


@pytest.fixture()
def sms_campaign_with_no_candidate(request, campaign_valid_data, access_token_first, talent_pipeline, headers,
                                   user_phone_1):
    """
    This creates the SMS campaign for user_first using valid data. It associates such a smartlist
    with sms-campaign which has no candidates associated with it.
    """
    smartlist_id = FixtureHelpers.create_smartlist_with_search_params(access_token_first, talent_pipeline.id)
    campaign_valid_data['smartlist_ids'] = [smartlist_id]
    test_sms_campaign = create_sms_campaign_via_api(campaign_valid_data, headers, talent_pipeline.user.id)

    def fin():
        _delete_campaign(test_sms_campaign, headers)

    request.addfinalizer(fin)
    return test_sms_campaign


@pytest.fixture()
def sms_campaign_of_other_user_in_same_domain(request, campaign_valid_data, user_same_domain, headers_same,
                                              user_phone_3, smartlist_with_two_candidates):
    """
    This creates the SMS campaign for user_same_domain using valid data, so that we have
    another campaign in the user_first's domain.
    """
    smartlist_id, _ = smartlist_with_two_candidates
    campaign_valid_data['smartlist_ids'] = [smartlist_id]
    test_sms_campaign = create_sms_campaign_via_api(campaign_valid_data, headers_same, user_same_domain.id)

    def fin():
        _delete_campaign(test_sms_campaign, headers)

    request.addfinalizer(fin)
    return test_sms_campaign


@pytest.fixture()
def bulk_sms_campaigns(request, campaign_valid_data, talent_pipeline, headers, smartlist_with_two_candidates,
                       user_phone_1):
    """
    This creates the 10 SMS campaign for user_first using valid data.
    """
    smartlist_id, _ = smartlist_with_two_candidates
    campaign_valid_data['smartlist_ids'] = [smartlist_id]
    test_campaigns = []
    for _ in xrange(10):
        campaign_valid_data['name'] = 'bulk_campaigns: %s' % fake.name()
        test_campaigns.append(create_sms_campaign_via_api(campaign_valid_data, headers,
                                                          talent_pipeline.user.id))

    def fin():
        for test_sms_campaign in test_campaigns:
            _delete_campaign(test_sms_campaign, headers)

    request.addfinalizer(fin)
    return test_campaigns


@pytest.fixture()
def invalid_sms_campaign(request, campaign_valid_data, user_phone_1, headers):
    """
    This creates the SMS campaign for sample_user using valid data.
    """
    test_sms_campaign = _create_sms_campaign(campaign_valid_data, user_phone_1)

    def fin():
        _delete_campaign(test_sms_campaign, headers)

    request.addfinalizer(fin)
    return test_sms_campaign


@pytest.fixture()
def sms_campaign_with_no_valid_candidate(request, campaign_valid_data, access_token_first, talent_pipeline, headers):
    """
    This creates the SMS campaign for user_first using valid data. Candidates associated
    with this campaign have no phone number saved in database.
    """
    smartlist_id, _ = CampaignsTestsHelpers.create_smartlist_with_candidate(access_token_first, talent_pipeline,
                                                                            count=2)
    campaign_valid_data['smartlist_ids'] = [smartlist_id]
    test_sms_campaign = create_sms_campaign_via_api(campaign_valid_data, headers,
                                                    talent_pipeline.user.id)

    def fin():
        _delete_campaign(test_sms_campaign, headers)

    request.addfinalizer(fin)
    return test_sms_campaign


@pytest.fixture()
def sms_campaign_in_other_domain(request, campaign_valid_data, headers_other,
                                 talent_pipeline_other,
                                 smartlist_with_two_candidates_in_other_domain):
    """
    This creates SMS campaign for some other user in different domain.
    """
    smartlist_id, _ = smartlist_with_two_candidates_in_other_domain
    campaign_valid_data['smartlist_ids'] = [smartlist_id]
    test_sms_campaign = create_sms_campaign_via_api(campaign_valid_data,
                                                    headers_other,
                                                    talent_pipeline_other.user.id)

    def fin():
        _delete_campaign(test_sms_campaign, headers_other)

    request.addfinalizer(fin)
    return test_sms_campaign


@pytest.fixture(params=[Frequency.ONCE, Frequency.DAILY])
def one_time_and_periodic(request, headers):
    """
    This returns data to schedule a campaign one time and periodically.
    """
    data = generate_campaign_schedule_data()

    def fin():
        if 'task_id' in data:
            delete_test_scheduled_task(data['task_id'], headers)

    if request.param == Frequency.ONCE:
        request.addfinalizer(fin)
        return data
    else:
        request.addfinalizer(fin)
        data['frequency_id'] = request.param
    return data


@pytest.fixture()
def scheduled_sms_campaign_of_user_first(request, user_first, access_token_first, headers,
                                         sms_campaign_of_user_first):
    """
    This creates the SMS campaign for user_first using valid data.
    """
    campaign = _get_scheduled_campaign(user_first, sms_campaign_of_user_first, access_token_first)

    def delete_scheduled_task():
        _unschedule_campaign(campaign, headers)

    request.addfinalizer(delete_scheduled_task)
    return campaign


@pytest.fixture()
def scheduled_sms_campaign_of_other_domain(request, user_from_diff_domain, headers_other,
                                           access_token_other, sms_campaign_in_other_domain):
    """
    This creates the SMS campaign for user_from_diff_domain using valid data.
    """
    campaign = _get_scheduled_campaign(user_from_diff_domain, sms_campaign_in_other_domain, access_token_other)

    def delete_scheduled_task():
        _unschedule_campaign(campaign, headers_other)

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
                                  reply_count=count)

    for count in xrange(1, 6):
        reply_and_assert_response(sent_campaign, user_phone_1,
                                  candidate_and_phone_2[1], access_token_first,
                                  reply_count=count)


@pytest.fixture()
def candidate_and_phone_1(request, sent_campaign_and_blast_ids, access_token_first, headers):
    """
    This returns the candidate object and candidate_phone for first candidate associated with
    the sms-campaign in a tuple. Here we assume campaign has been sent to candidate.
    """
    candidate, candidate_phone = _get_candidate_and_phone_tuple(request,
                                                                sent_campaign_and_blast_ids,
                                                                access_token_first,
                                                                headers, candidate_index=0)
    return candidate, candidate_phone


@pytest.fixture()
def candidate_and_phone_2(request, sent_campaign_and_blast_ids, access_token_first, headers):
    """
    This returns the candidate object and candidate_phone for first candidate associated with
    the sms-campaign in a tuple. Here we assume campaign has been sent to candidate.
    """
    candidate, candidate_phone = _get_candidate_and_phone_tuple(request,
                                                                sent_campaign_and_blast_ids,
                                                                access_token_first,
                                                                headers, candidate_index=1)
    return candidate, candidate_phone


@pytest.fixture()
def candidate_phone_2(request, candidate_second):
    """
    This associates sample_smartlist with the sms_campaign_of_user_first
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
    This associates sample_smartlist with the sms_campaign_of_user_first
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
def sent_campaign(access_token_first, sms_campaign_of_user_first):
    """
    This function serves the sending part of SMS campaign.
    This sends campaign to two candidates.
    """
    response_post = CampaignsTestsHelpers.send_campaign(
        SmsCampaignApiUrl.SEND, sms_campaign_of_user_first,
        access_token_first, SmsCampaignApiUrl.BLASTS)
    assert_api_send_response(sms_campaign_of_user_first, response_post, codes.OK)
    return sms_campaign_of_user_first


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
    assert_api_send_response(sms_campaign_in_other_domain, response_post, codes.OK)
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
                                 headers):
    """
    This creates an SMS campaign with ten candidates
    """
    # create candidate
    smartlist_id, candidate_ids = CampaignsTestsHelpers.create_smartlist_with_candidate(
        access_token_first, talent_pipeline, count=10, create_phone=True)
    campaign_valid_data['smartlist_ids'] = [smartlist_id]
    test_sms_campaign = create_sms_campaign_via_api(campaign_valid_data, headers,
                                                    talent_pipeline.user.id)

    def fin():
        _delete_campaign(test_sms_campaign, headers)

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
                                              SmsCampaignApiUrl.BLASTS % sent_campaign_bulk[0]['id'])
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
    CampaignsTestsHelpers.assert_blast_sends(campaign_in_db, 2)
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
    campaign_id = assert_campaign_creation(response, user_id, codes.CREATED)
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


def _get_scheduled_campaign(user, campaign, access_token):
    """
    This schedules the given campaign and return it.
    """
    CampaignsTestsHelpers.assert_campaign_schedule_or_reschedule('post',
                                                                 SmsCampaignApiUrl.SCHEDULE,
                                                                 access_token, user.id, campaign['id'],
                                                                 SmsCampaignApiUrl.CAMPAIGN,
                                                                 generate_campaign_schedule_data())
    # GET campaign from API, now it should have scheduler_task_id associated with it.
    response = requests.get(SmsCampaignApiUrl.CAMPAIGN % campaign['id'],
                            headers={'Authorization': 'Bearer %s' % access_token})
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


def _delete_campaign(sms_campaign, headers):
    """
    This deletes the given campaign from database
    :param (dict | SmsCampaign) sms_campaign: sms-campaign object
    """
    try:
        campaign_id = sms_campaign.id if hasattr(sms_campaign, 'id') else sms_campaign['id']
        response = requests.delete(SmsCampaignApiUrl.CAMPAIGN % campaign_id, headers=headers)
        assert_campaign_delete(response, user_first.id, sms_campaign_of_user_first['id'])
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


def _get_candidate_and_phone_tuple(request, sent_campaign_and_blast_ids, access_token_first,
                                   headers, candidate_index):
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
        headers=headers)
    json_response = candidate_get_response.json()
    candidate_phone = json_response['candidate']['phones'][0]

    def tear_down():
        _delete_candidate_phone(candidate_phone['id'])

    request.addfinalizer(tear_down)
    return json_response['candidate'], candidate_phone
