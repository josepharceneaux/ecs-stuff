__author__ = 'ufarooqi'
from datetime import timedelta
from time import sleep
from candidate_pool_service.candidate_pool_app import app
from candidate_pool_service.common.tests.conftest import *
from candidate_pool_service.common.utils.common_functions import add_role_to_test_user
from candidate_pool_service.common.tests.cloud_search_common_functions import *
from common_functions import *


def test_talent_pipeline_candidate_get(access_token_first, access_token_second, talent_pool, talent_pipeline,
                                       user_first, user_second):
    """
    This function will test TalentPipelineCandidates API

    :param access_token_first: Test access_token for first user
    :param talent_pool:  Test TalentPool object
    :param talent_pipeline: Test TalentPipeline object
    :param user_first: Test User object
    :return:
    """

    # Logged-in user trying to get all candidates of given talent-pipeline
    response, status_code = talent_pipeline_candidate_api(access_token_first, talent_pipeline.id)
    assert status_code == 401

    # Adding 'CAN_GET_TALENT_PIPELINE_CANDIDATES' role to user_first, user_second
    add_role_to_test_user(user_first, ['CAN_GET_TALENT_PIPELINE_CANDIDATES'])
    add_role_to_test_user(user_second, ['CAN_GET_TALENT_PIPELINE_CANDIDATES'])

    # Logged-in user trying to get all candidates of non-existing talent-pipeline
    response, status_code = talent_pipeline_candidate_api(access_token_first, talent_pipeline.id + 100)
    assert status_code == 404

    # Logged-in user trying to get all candidates of talent-pipeline of different domain
    response, status_code = talent_pipeline_candidate_api(access_token_second, talent_pipeline.id)
    assert status_code == 401

    # Creating and Adding test smart_list and dumb_list to talent-pipeline
    test_smart_list, test_dumb_list = prepare_pipeline_candidate_data(db.session, talent_pipeline, user_first)

    candidate_ids_without_talent_pool = populate_candidates(oauth_token=access_token_first)

    # Adding a candidate with 'Apple' as current company
    apple_candidate_ids = populate_candidates(oauth_token=access_token_first, count=3, current_company='Apple',
                                              talent_pool_id=talent_pool.id)

    # Adding a candidate with 'Apple' as current company and 'Software Engineer' as current title
    populate_candidates(oauth_token=access_token_first, count=5, current_title='Software Engineer',
                        current_company='Apple', talent_pool_id=talent_pool.id)

    # Adding a candidate with 'Apple' as current company and 'Software Engineer' as current title and 'CS' as major
    cs_sw_engineers_candidate_ids = populate_candidates(oauth_token=access_token_first, count=5, major='CS',
                                                        current_title='Software Engineer', current_company='Apple',
                                                        talent_pool_id=talent_pool.id)

    # Adding candidates dumb_list
    add_candidates_to_dumb_list(db.session, test_dumb_list, candidate_ids_without_talent_pool + apple_candidate_ids)

    # Wait for addition of candidates in Amazon Cloud Search
    sleep(30)

    # Logged-in user trying to get all candidates of talent-pipeline with out search_params
    # and only three candidates in its dumb_list
    response, status_code = talent_pipeline_candidate_api(access_token_first, talent_pipeline.id)
    assert_results(apple_candidate_ids,  response)

    talent_pipeline.search_params = json.dumps({'job_title': 'Software Engineer'})
    test_smart_list.search_params = json.dumps({'query': 'Apple', 'major': 'CS'})
    db.session.commit()

    # Logged-in user trying to get all candidates of talent-pipeline with search_params
    response, status_code = talent_pipeline_candidate_api(access_token_first, talent_pipeline.id)
    assert_results(apple_candidate_ids + cs_sw_engineers_candidate_ids,  response)

    # Adding candidates dumb_list
    add_candidates_to_dumb_list(db.session, test_dumb_list, cs_sw_engineers_candidate_ids)

    # Logged-in user trying to get all candidates of talent-pipeline with search_params
    response, status_code = talent_pipeline_candidate_api(access_token_first, talent_pipeline.id)
    assert_results(apple_candidate_ids + cs_sw_engineers_candidate_ids,  response)