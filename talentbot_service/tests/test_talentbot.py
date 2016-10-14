"""
This module tests talentbot_service
"""
# Builtin imports
import datetime
from dateutil.relativedelta import relativedelta
# Common utils
from talentbot_service.common.tests.conftest import domain_first, first_group, domain_second, second_group,\
    access_token_first, user_first, candidate_first, talent_pool, user_same_domain, user_second, candidate_second
from talentbot_service.common.models.talent_pools_pipelines import TalentPoolCandidate
from talentbot_service.common.models.user import User
from talentbot_service.common.models.candidate import Candidate, CandidateSkill


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
    # Tests with 3 months earlier added ad updated time
    changed_date = datetime.datetime.utcnow() - relativedelta(months=3)
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
    users, domain_name = User.get_domain_name_and_its_users(user_first.id)
    # Testing if number of users in user_first's domain are equal to 2
    assert isinstance(users, list) and len(users) == 2
    # Testing that domain name exists and is instance of basestring
    assert isinstance(domain_name, basestring) and domain_name
    # Testing with user_id as None
    try:
        users, domain_name = User.get_domain_name_and_its_users(None)
    except AssertionError as error:
        assert error.message.lower() == 'invalid user id'
    # Testing if user_id is not an int or long
    try:
        users, domain_name = User.get_domain_name_and_its_users('1')
    except AssertionError as error:
        assert error.message.lower() == 'invalid user id'
    users, domain_name = User.get_domain_name_and_its_users(user_second.id)
    # Testing if number of users in user_second's domain are equal to 1
    assert isinstance(users, list) and len(users) == 1
    users, domain_name = User.get_domain_name_and_its_users(user_same_domain.id)
    # Testing if number of users in user_same_domain's domain are equal to 2
    assert isinstance(users, list) and len(users) == 2


def test_get_candidates_with_skills(user_first, candidate_first, candidate_second):
    """
    This method checks number of candidates against skills
    """
    candidate_skill = CandidateSkill(candidate_id=candidate_first.id, description='java')
    candidate_skill.save()
    count = Candidate.get_candidate_count_with_skills(['java'], user_first.id)
    assert count == 1
    count = Candidate.get_candidate_count_with_skills(['c++'], user_first.id)
    assert count == 0
    # Adding another candidate skill
    candidate_skill = CandidateSkill(candidate_id=candidate_second.id, description='java')
    candidate_skill.save()
    count = Candidate.get_candidate_count_with_skills(['java'], user_first.id)
    assert count == 2
    # Adding second skill for first candidate
    candidate_skill = CandidateSkill(candidate_id=candidate_first.id, description='python')
    candidate_skill.save()
    count = Candidate.get_candidate_count_with_skills(['c++', 'python'], user_first.id)
    assert count == 1
