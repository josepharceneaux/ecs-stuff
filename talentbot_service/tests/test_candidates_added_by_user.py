import datetime
from dateutil.relativedelta import relativedelta

from talentbot_service.common.tests.api_conftest import test_data, token_first, user_first, \
    candidate_first, talent_pool
from talentbot_service.common.models.talent_pools_pipelines import TalentPoolCandidate
from talentbot_service.common.models.user import User


def test_candidate_added(user_first, talent_pool, candidate_first):
    user_name = User.filter_by_keywords(id=user_first.get("id"))[0].first_name = "test"
    count = TalentPoolCandidate.candidates_added_last_month(user_name, talent_pool["name"],
                                                            talent_pool["added_time"], user_first["id"])
    assert count == 1
    count = TalentPoolCandidate.candidates_added_last_month(user_name, talent_pool["name"],
                                                            None, user_first["id"])
    assert count == 1
    changed_date = datetime.datetime.utcnow() - relativedelta(months=3)
    talent_pool["added_time"] = changed_date
    talent_pool["updated_time"] = changed_date
    current_datetime = datetime.datetime.utcnow()
    count = TalentPoolCandidate.candidates_added_last_month(user_name, talent_pool["name"],
                                                            current_datetime, user_first["id"])
    assert count == 0
    count = TalentPoolCandidate.candidates_added_last_month(user_name, talent_pool["name"],
                                                            None, user_first["id"])
    assert count == 1
