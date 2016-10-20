"""
This module tests talentbot_service
"""
# Builtin imports
import datetime
from dateutil.relativedelta import relativedelta
# Common utils
from talentbot_service.common.tests.conftest import domain_first, first_group, domain_second, second_group,\
    access_token_first, user_first, candidate_first, talent_pool, user_same_domain, user_second, candidate_second,\
    user_second_candidate, user_same_domain_candidate, email_campaign_first, email_campaign_first_blast,\
    email_campaign_same_domain, email_campaign_same_domain_blast, email_campaign_second_domain,\
    email_campaign_second_domain_blast, sms_campaign_first, sms_campaign_first_blast, user_phone_first, \
    sms_campaign_second, sms_campaign_second_blast, user_phone_second,push_campaign_first, push_campaign_first_blast,\
    user_phone_same_domain, sms_campaign_same_domain, sms_campaign_same_domain_blast, push_campaign_same_domain,\
    push_campaign_same_domain_blast, push_campaign_second, push_campaign_second_blast, talent_pool_second, fake
from talentbot_service.common.models.talent_pools_pipelines import TalentPoolCandidate, TalentPool
from talentbot_service.common.models.user import User
from talentbot_service.common.models.email_campaign import EmailCampaignBlast
from talentbot_service.common.models.sms_campaign import SmsCampaignBlast
from talentbot_service.common.models.push_campaign import PushCampaignBlast
from talentbot_service.common.models.candidate import Candidate, CandidateSkill, CandidateAddress


def test_candidate_added(user_first, talent_pool, candidate_first):
    """
    This method tests that weather bot returns accurate number of candidates added by a user
    in a talent pool.
    """
    user_name = User.filter_by_keywords(id=user_first.id)[0].first_name = "test"
    talent_pool_candidate = TalentPoolCandidate(talent_pool_id=talent_pool.id, candidate_id=candidate_first.id,
                                                added_time=user_first.added_time)
    talent_pool_candidate.save()
    # Tests if number of candidates added by user with the same added time
    count = TalentPoolCandidate.candidates_added_last_month(user_first.id, user_name, [talent_pool.name],
                                                            None)
    assert count == 1
    # Tests without specifying time
    count = TalentPoolCandidate.candidates_added_last_month(user_first.id, user_name, [talent_pool.name])
    assert count == 1
    # Tests with 3 months earlier added and updated time
    changed_date = datetime.datetime.utcnow() - relativedelta(years=3)
    talent_pool.added_time = changed_date
    talent_pool.updated_time = changed_date
    current_datetime = datetime.datetime.utcnow()
    count = TalentPoolCandidate.candidates_added_last_month(user_first.id, user_name, [talent_pool.name],
                                                            current_datetime)
    assert count == 0
    # Tests without specifying time
    count = TalentPoolCandidate.candidates_added_last_month(user_first.id, user_name, [talent_pool.name])
    assert count == 1


def test_get_domain_name_and_its_users(user_first, user_second, user_same_domain):
    """
    This method tests that users in a user's domain and domain name of a user is valid.
    """
    user_ids = [user_first.id, user_same_domain.id]
    for i in range(2):
        users, domain_name = User.get_domain_name_and_its_users(user_ids[i])
        # Testing if number of users in user_first's domain are equal to 2
        assert isinstance(users, list) and len(users) == 2
        # Testing that domain name exists and is instance of basestring
        assert isinstance(domain_name, basestring) and domain_name
    # Testing with user_id as None
    users, domain_name = User.get_domain_name_and_its_users(user_second.id)
    # Testing if number of users in user_second's domain are equal to 1
    assert isinstance(users, list) and len(users) == 1


def test_get_candidates_with_skills(user_first, candidate_first, candidate_second, user_same_domain,
                                    user_second_candidate, user_second, user_same_domain_candidate):
    """
    This method checks number of candidates against skills in user's domain.
    """
    skill_1 = fake.word()
    skill_2 = fake.word()
    skill_3 = fake.word()
    skill_4 = fake.word()
    candidate_skill = CandidateSkill(candidate_id=candidate_first.id, description=skill_1, resume_id=0)
    candidate_skill.save()
    count = Candidate.get_candidate_count_with_skills([skill_1], user_first.id)
    assert count == 1
    count = Candidate.get_candidate_count_with_skills([skill_4], user_first.id)
    assert count == 0
    # Adding another candidate skill
    candidate_skill = CandidateSkill(candidate_id=candidate_second.id, description=skill_1, resume_id=0)
    candidate_skill.save()
    count = Candidate.get_candidate_count_with_skills([skill_1], user_first.id)
    assert count == 2
    # Adding second skill for first candidate
    candidate_skill = CandidateSkill(candidate_id=candidate_first.id, description=skill_2, resume_id=0)
    candidate_skill.save()
    count = Candidate.get_candidate_count_with_skills([skill_4, skill_2], user_first.id)
    assert count == 1
    # Adding skill for second_user's candidate
    candidate_skill = CandidateSkill(candidate_id=user_second_candidate.id, description=skill_3, resume_id=0)
    candidate_skill.save()
    count = Candidate.get_candidate_count_with_skills([skill_3], user_same_domain.id)
    assert count == 0
    count = Candidate.get_candidate_count_with_skills([skill_3], user_second.id)
    assert count == 1
    # Adding skill for user_same_domain's candidate
    candidate_skill = CandidateSkill(candidate_id=user_same_domain_candidate.id, description=skill_1, resume_id=0)
    candidate_skill.save()
    count = Candidate.get_candidate_count_with_skills([skill_1], user_same_domain.id)
    assert count == 3


def test_candidates_from_zipcode(user_first, candidate_first, candidate_second, user_same_domain,
                                 user_same_domain_candidate, user_second, user_second_candidate):
    """
    This method checks number of candidates against a zipcode in a user's domain
    """
    # Adding address for user_first's candidate
    candidate_address = CandidateAddress(candidate_id=candidate_first.id, zip_code='54000', resume_id=0)
    candidate_address.save()
    count = Candidate.get_candidate_count_from_zipcode('54000', user_first.id)
    assert count == 1
    # Adding address for user_first's second candidate
    candidate_address = CandidateAddress(candidate_id=candidate_second.id, zip_code='54000', resume_id=0)
    candidate_address.save()
    count = Candidate.get_candidate_count_from_zipcode('54000', user_first.id)
    assert count == 2
    # Adding address for user_same_domain's candidate
    candidate_address = CandidateAddress(candidate_id=user_same_domain_candidate.id, zip_code='54000', resume_id=0)
    candidate_address.save()
    count = Candidate.get_candidate_count_from_zipcode('54000', user_first.id)
    assert count == 3
    # Adding address for second_user candidate
    candidate_address = CandidateAddress(candidate_id=user_second_candidate.id, zip_code='54000', resume_id=0)
    candidate_address.save()
    count = Candidate.get_candidate_count_from_zipcode('54000', user_first.id)
    assert count == 3
    count = Candidate.get_candidate_count_from_zipcode('54000', user_second.id)
    assert count == 1
    # Checking with user_same_domain
    count = Candidate.get_candidate_count_from_zipcode('54000', user_same_domain.id)
    assert count == 3
    # Checking against a random fake zipcode
    count = Candidate.get_candidate_count_from_zipcode(str(fake.random_int()), user_same_domain.id)
    assert count == 0


def test_top_performing_email_campaign(user_first, user_second, email_campaign_first, email_campaign_first_blast,
                                       email_campaign_same_domain, email_campaign_same_domain_blast,
                                       email_campaign_second_domain, email_campaign_second_domain_blast):
    """
    This method tests top performing email campaigns are being fetched correctly within a domain
    """
    # With 3 months earlier datetime
    datetime_3_months_earlier = datetime.datetime.utcnow() - relativedelta(months=3)
    email_campaign = EmailCampaignBlast.top_performing_email_campaign(datetime_3_months_earlier, user_first.id)
    assert email_campaign.campaign.name == email_campaign_same_domain.name
    email_campaign_first_blast.opens = 20
    email_campaign = EmailCampaignBlast.top_performing_email_campaign(datetime_3_months_earlier, user_first.id)
    assert email_campaign.campaign.name == email_campaign_first.name
    # With 0 sends and opens greater than 0
    email_campaign_first_blast.sends = 0
    email_campaign = EmailCampaignBlast.top_performing_email_campaign(datetime_3_months_earlier, user_first.id)
    assert email_campaign.campaign.name == email_campaign_same_domain.name
    # Now top campaign with user_second's Id
    email_campaign_first_blast.sends = 20
    email_campaign_first_blast.opens = 20
    email_campaign = EmailCampaignBlast.top_performing_email_campaign(datetime_3_months_earlier, user_second.id)
    assert email_campaign.campaign.name == email_campaign_second_domain.name
    # With year
    year = str(datetime.datetime.utcnow().year)
    email_campaign = EmailCampaignBlast.top_performing_email_campaign(year, user_first.id)
    assert email_campaign.campaign.name == email_campaign_first.name
    email_campaign_first_blast.opens = 10
    email_campaign = EmailCampaignBlast.top_performing_email_campaign(year, user_first.id)
    assert email_campaign.campaign.name == email_campaign_same_domain.name
    email_campaign_first_blast.opens = 20
    email_campaign = EmailCampaignBlast.top_performing_email_campaign(year, user_first.id)
    assert email_campaign.campaign.name == email_campaign_first.name
    # With 0 sends and opens greater than 0
    email_campaign_first_blast.sends = 0
    email_campaign = EmailCampaignBlast.top_performing_email_campaign(year, user_first.id)
    assert email_campaign.campaign.name == email_campaign_same_domain.name
    # With Datetime_value None
    email_campaign_first_blast.sends = 20
    email_campaign = EmailCampaignBlast.top_performing_email_campaign(None, user_first.id)
    assert email_campaign.campaign.name == email_campaign_first.name
    email_campaign = EmailCampaignBlast.top_performing_email_campaign(None, user_second.id)
    assert email_campaign.campaign.name == email_campaign_second_domain.name
    #####
    email_campaign_first_blast.opens = 20
    email_campaign = EmailCampaignBlast.top_performing_email_campaign(None, user_first.id)
    assert email_campaign.campaign.name == email_campaign_first.name
    email_campaign = EmailCampaignBlast.top_performing_email_campaign(None, user_first.id)
    assert email_campaign.campaign.name == email_campaign_first.name
    # With 0 sends and opens greater than 0
    email_campaign_first_blast.sends = 0
    email_campaign = EmailCampaignBlast.top_performing_email_campaign(None, user_first.id)
    assert email_campaign.campaign.name == email_campaign_same_domain.name
    # Now top campaign with user_second's Id
    email_campaign_first_blast.sends = 20
    email_campaign_first_blast.opens = 20
    email_campaign = EmailCampaignBlast.top_performing_email_campaign(None, user_second.id)
    assert email_campaign.campaign.name == email_campaign_second_domain.name


def test_top_performing_sms_campaign(user_first, user_second, sms_campaign_first, sms_campaign_first_blast,
                                     sms_campaign_second, sms_campaign_second_blast, user_phone_second,
                                     user_same_domain, sms_campaign_same_domain, sms_campaign_same_domain_blast):
    # With 3 months earlier datetime
    datetime_3_months_earlier = datetime.datetime.utcnow() - relativedelta(months=3)
    sms_campaign = SmsCampaignBlast.top_performing_sms_campaign(datetime_3_months_earlier, user_first.id)
    assert sms_campaign.campaign.name == sms_campaign_first.name
    # Checking with user_second's Id
    sms_campaign = SmsCampaignBlast.top_performing_sms_campaign(datetime_3_months_earlier, user_second.id)
    assert sms_campaign.campaign.name == sms_campaign_second.name
    # Checking with user_same_domain's Id
    sms_campaign = SmsCampaignBlast.top_performing_sms_campaign(datetime_3_months_earlier, user_same_domain.id)
    assert sms_campaign.campaign.name == sms_campaign_first.name
    # Increasing sms_campaign_same_domain_blast's number of replies
    sms_campaign_same_domain_blast.replies = 10
    sms_campaign = SmsCampaignBlast.top_performing_sms_campaign(datetime_3_months_earlier, user_same_domain.id)
    assert sms_campaign.campaign.name == sms_campaign_same_domain.name
    # Testing with year
    sms_campaign_same_domain_blast.replies = 8
    year = str(datetime.datetime.utcnow().year)
    sms_campaign = SmsCampaignBlast.top_performing_sms_campaign(year, user_first.id)
    assert sms_campaign.campaign.name == sms_campaign_first.name
    # Checking with user_second's Id
    sms_campaign = SmsCampaignBlast.top_performing_sms_campaign(year, user_second.id)
    assert sms_campaign.campaign.name == sms_campaign_second.name
    # Checking with user_same_domain's Id
    sms_campaign = SmsCampaignBlast.top_performing_sms_campaign(year, user_same_domain.id)
    assert sms_campaign.campaign.name == sms_campaign_first.name
    # Increasing sms_campaign_same_domain_blast's number of replies
    sms_campaign_same_domain_blast.replies = 10
    sms_campaign = SmsCampaignBlast.top_performing_sms_campaign(year, user_same_domain.id)
    assert sms_campaign.campaign.name == sms_campaign_same_domain.name
    # Testing with datetime_value as None
    sms_campaign_same_domain_blast.replies = 8
    sms_campaign = SmsCampaignBlast.top_performing_sms_campaign(None, user_first.id)
    assert sms_campaign.campaign.name == sms_campaign_first.name
    # Checking with user_second's Id
    sms_campaign = SmsCampaignBlast.top_performing_sms_campaign(None, user_second.id)
    assert sms_campaign.campaign.name == sms_campaign_second.name
    # Checking with user_same_domain's Id
    sms_campaign = SmsCampaignBlast.top_performing_sms_campaign(None, user_same_domain.id)
    assert sms_campaign.campaign.name == sms_campaign_first.name
    # Increasing sms_campaign_same_domain_blast's number of replies
    sms_campaign_same_domain_blast.replies = 10
    sms_campaign = SmsCampaignBlast.top_performing_sms_campaign(None, user_same_domain.id)
    assert sms_campaign.campaign.name == sms_campaign_same_domain.name


def test_top_performing_push_campaign(user_first, push_campaign_first, push_campaign_first_blast, user_same_domain,
                                      user_second, push_campaign_same_domain, push_campaign_same_domain_blast,
                                      push_campaign_second, push_campaign_second_blast):
    # With 3 months earlier datetime
    datetime_3_months_earlier = datetime.datetime.utcnow() - relativedelta(months=3)
    push_campaign = PushCampaignBlast.top_performing_push_campaign(datetime_3_months_earlier, user_first.id)
    assert push_campaign.campaign.name == push_campaign_first.name
    # Increasing number of clicks for push_campaign_same_domain
    push_campaign_same_domain_blast.clicks = 10
    push_campaign = PushCampaignBlast.top_performing_push_campaign(datetime_3_months_earlier, user_first.id)
    assert push_campaign.campaign.name == push_campaign_same_domain.name
    # Checking in user_second's domain
    push_campaign = PushCampaignBlast.top_performing_push_campaign(datetime_3_months_earlier, user_second.id)
    assert push_campaign.campaign.name == push_campaign_second.name
    # With year
    push_campaign_same_domain_blast.clicks = 5
    year = str(datetime.datetime.utcnow().year)
    push_campaign = PushCampaignBlast.top_performing_push_campaign(year, user_first.id)
    assert push_campaign.campaign.name == push_campaign_first.name
    # Increasing number of clicks for push_campaign_same_domain
    push_campaign_same_domain_blast.clicks = 10
    push_campaign = PushCampaignBlast.top_performing_push_campaign(year, user_first.id)
    assert push_campaign.campaign.name == push_campaign_same_domain.name
    # Checking in user_second's domain
    push_campaign = PushCampaignBlast.top_performing_push_campaign(year, user_second.id)
    assert push_campaign.campaign.name == push_campaign_second.name
    # With datetime_value as None
    push_campaign_same_domain_blast.clicks = 5
    push_campaign = PushCampaignBlast.top_performing_push_campaign(None, user_first.id)
    assert push_campaign.campaign.name == push_campaign_first.name
    # Increasing number of clicks for push_campaign_same_domain
    push_campaign_same_domain_blast.clicks = 10
    push_campaign = PushCampaignBlast.top_performing_push_campaign(None, user_first.id)
    assert push_campaign.campaign.name == push_campaign_same_domain.name
    # Checking in user_second's domain
    push_campaign = PushCampaignBlast.top_performing_push_campaign(None, user_second.id)
    assert push_campaign.campaign.name == push_campaign_second.name


def test_get_talent_pools_in_my_domain(talent_pool, user_second, user_first, user_same_domain,
                                       talent_pool_second):
    """
    This method verifies talent pools in a user's domain
    """
    talent_pools = TalentPool.get_talent_pools_in_user_domain(user_first.id)
    assert talent_pools[0].id == talent_pool.id
    # Testing with user_same_domain' Id
    talent_pools = TalentPool.get_talent_pools_in_user_domain(user_same_domain.id)
    assert talent_pools[0].id == talent_pool.id
    # Checking that talent_pool in second_domain is not visible to user_first
    talent_pools = TalentPool.get_talent_pools_in_user_domain(user_first.id)
    assert len(talent_pools) == 1 and talent_pools[0].id == talent_pool.id
    # Talent pool in second domain should be visible to user from second domain
    talent_pools = TalentPool.get_talent_pools_in_user_domain(user_second.id)
    assert talent_pools[0].id == talent_pool_second.id
