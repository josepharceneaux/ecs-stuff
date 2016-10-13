"""
This module tests talentbot_service
"""
# Builtin imports
import datetime
from dateutil.relativedelta import relativedelta
# Common utils
from talentbot_service.common.tests.api_conftest import test_data, token_first, user_first, \
    candidate_first, talent_pool
from talentbot_service.common.models.talent_pools_pipelines import TalentPoolCandidate
from talentbot_service.common.models.user import User


def test_candidate_added(user_first, talent_pool, candidate_first):
    """
    This method tests that weather bot returns accurate number of candidates added by a user
    in a talent pool.
    :param User user_first: Randomly added user using fixture
    :param TalentPool talent_pool: Randomly added talent pool
    :param Candidate candidate_first: Randomly added candidate in talent_pool by user_first
    """
    user_name = User.filter_by_keywords(id=user_first.get("id"))[0].first_name = "test"
    # Tests if number of candidates added by user with the same added time
    count = TalentPoolCandidate.candidates_added_last_month(user_name, [talent_pool["name"]],
                                                            talent_pool["added_time"], user_first["id"])
    assert count == 1
    # Tests without specifying time
    count = TalentPoolCandidate.candidates_added_last_month(user_name, [talent_pool["name"]],
                                                            None, user_first["id"])
    assert count == 1
    # Tests with 3 months earlier added ad updated time
    changed_date = datetime.datetime.utcnow() - relativedelta(months=3)
    talent_pool["added_time"] = changed_date
    talent_pool["updated_time"] = changed_date
    current_datetime = datetime.datetime.utcnow()
    count = TalentPoolCandidate.candidates_added_last_month(user_name, [talent_pool["name"]],
                                                            current_datetime, user_first["id"])
    assert count == 0
    # Tests without specifying time
    count = TalentPoolCandidate.candidates_added_last_month(user_name, [talent_pool["name"]],
                                                            None, user_first["id"])
    assert count == 1
