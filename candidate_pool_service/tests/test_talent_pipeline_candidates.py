__author__ = 'ufarooqi'
from time import sleep
from datetime import timedelta
from candidate_pool_service.candidate_pool_app import app
from candidate_pool_service.common.tests.conftest import *
from candidate_pool_service.common.models.talent_pools_pipelines import TalentPipelineStats
from candidate_pool_service.common.utils.handy_functions import add_role_to_test_user
from candidate_pool_service.common.tests.cloud_search_common_functions import *
from common_functions import *


def test_update_talent_pipeline_stats(access_token_first, user_first, talent_pipeline):

    # Logged-in user trying to update statistics of all talent_pipelines in database
    status_code = talent_pipeline_update_stats(access_token_first)
    assert status_code == 401

    add_role_to_test_user(user_first, [DomainRole.Roles.CAN_EDIT_TALENT_PIPELINES_STATS,
                                       DomainRole.Roles.CAN_ADD_CANDIDATES])

    # Setting Empty search_params for talent_pipeline
    talent_pipeline.search_params = json.dumps({})
    db.session.commit()

    # Adding candidates with 'Apple' as current company
    populate_candidates(oauth_token=access_token_first, count=3, current_company='Apple',
                        talent_pool_id=talent_pipeline.talent_pool_id)

    sleep(25)

    # Logged-in user trying to update statistics of all talent_pipelines in database
    status_code = talent_pipeline_update_stats(access_token_first)
    assert status_code == 204


def test_get_talent_pipeline_stats(access_token_first, access_token_second, talent_pipeline):

    # Emptying TalentPipelineStats table
    TalentPipelineStats.query.delete()
    talent_pipeline_stat = TalentPipelineStats(talent_pipeline_id=talent_pipeline.id, total_number_of_candidates=10,
                                               candidates_engagement=40)

    db.session.add(talent_pipeline_stat)
    db.session.commit()

    # Logged-in user trying to get statistics of a non-existing talent_pipeline
    response, status_code = talent_pipeline_get_stats(access_token_first, talent_pipeline.id + 1000)
    assert status_code == 404

    # Logged-in user trying to get statistics of a talent_pipeline of different user
    response, status_code = talent_pipeline_get_stats(access_token_second, talent_pipeline.id)
    assert status_code == 403

    # Logged-in user trying to get statistics of a talent_pipeline but with empty params
    response, status_code = talent_pipeline_get_stats(access_token_first, talent_pipeline.id)
    assert status_code == 400

    from_date = str(datetime.now() - timedelta(2))
    to_date = str(datetime.now() - timedelta(1))

    # Logged-in user trying to get statistics of a talent_pipeline
    response, status_code = talent_pipeline_get_stats(access_token_first, talent_pipeline.id,
                                                      {'from_date': from_date, 'to_date': to_date})
    assert status_code == 200
    assert not response.get('talent_pipeline_data')

    # Logged-in user trying to get statistics of a talent_pipeline
    response, status_code = talent_pipeline_get_stats(access_token_first, talent_pipeline.id)

    assert status_code == 200
    assert len(response.get('talent_pipeline_data')) >= 1
    assert 10 in [talent_pipeline_data. get('total_number_of_candidates') for talent_pipeline_data in
                  response.get('talent_pipeline_data')]
    assert 3 in [talent_pipeline_data. get('number_of_candidates_added') for talent_pipeline_data in
                 response.get('talent_pipeline_data')]


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

    add_role_to_test_user(user_first, [DomainRole.Roles.CAN_GET_TALENT_PIPELINE_CANDIDATES,
                                       DomainRole.Roles.CAN_ADD_CANDIDATES, DomainRole.Roles.CAN_GET_CANDIDATES])
    add_role_to_test_user(user_second, [DomainRole.Roles.CAN_GET_TALENT_PIPELINE_CANDIDATES,
                                        DomainRole.Roles.CAN_ADD_CANDIDATES, DomainRole.Roles.CAN_GET_CANDIDATES])

    # Logged-in user trying to get all candidates of non-existing talent-pipeline
    response, status_code = talent_pipeline_candidate_api(access_token_first, talent_pipeline.id + 1000)
    assert status_code == 404

    # Logged-in user trying to get all candidates of talent-pipeline of different domain
    response, status_code = talent_pipeline_candidate_api(access_token_second, talent_pipeline.id)
    assert status_code == 403

    # Creating and Adding test smart_list and dumb_list to talent-pipeline
    test_smart_list, test_dumb_list = prepare_pipeline_candidate_data(db.session, talent_pipeline, user_first)

    # Adding candidates with 'Apple' as current company
    apple_candidate_ids = populate_candidates(oauth_token=access_token_first, count=3, current_company='Apple',
                                              talent_pool_id=talent_pool.id)

    # Adding candidates with 'Apple' as current company and 'Software Engineer' as current title
    populate_candidates(oauth_token=access_token_first, count=5, current_title='Software Engineer',
                        current_company='Apple', talent_pool_id=talent_pool.id)

    # Adding candidates with 'Apple' as current company and 'Software Engineer' as current title and 'CS' as major
    cs_sw_engineers_candidate_ids = populate_candidates(oauth_token=access_token_first, count=5, major='CS',
                                                        current_title='Software Engineer', current_company='Apple',
                                                        talent_pool_id=talent_pool.id)

    # Adding candidates dumb_list
    add_candidates_to_dumb_list(db.session, access_token_first, test_dumb_list, apple_candidate_ids)

    # Wait for addition of candidates in Amazon Cloud Search
    sleep(30)

    # Logged-in user trying to get all candidates of talent-pipeline without search_params
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
    add_candidates_to_dumb_list(db.session, access_token_first, test_dumb_list, cs_sw_engineers_candidate_ids)

    # Logged-in user trying to get all candidates of talent-pipeline with search_params
    response, status_code = talent_pipeline_candidate_api(access_token_first, talent_pipeline.id,
                                                          {'fields': 'count_only'})
    assert len(set(apple_candidate_ids + cs_sw_engineers_candidate_ids)) == response.get('total_found')


def test_talent_pipeline_campaign_get(access_token_first, access_token_second, talent_pool, talent_pipeline,
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

    add_role_to_test_user(user_first, [DomainRole.Roles.CAN_GET_TALENT_PIPELINE_CANDIDATES,
                                       DomainRole.Roles.CAN_ADD_CANDIDATES, DomainRole.Roles.CAN_GET_CANDIDATES])
    add_role_to_test_user(user_second, [DomainRole.Roles.CAN_GET_TALENT_PIPELINE_CANDIDATES,
                                        DomainRole.Roles.CAN_ADD_CANDIDATES, DomainRole.Roles.CAN_GET_CANDIDATES])

    # Logged-in user trying to get all candidates of non-existing talent-pipeline
    response, status_code = talent_pipeline_candidate_api(access_token_first, talent_pipeline.id + 1000)
    assert status_code == 404

    # Logged-in user trying to get all candidates of talent-pipeline of different domain
    response, status_code = talent_pipeline_candidate_api(access_token_second, talent_pipeline.id)
    assert status_code == 403

    # Creating and Adding test smart_list and dumb_list to talent-pipeline
    test_smart_list, test_dumb_list = prepare_pipeline_candidate_data(db.session, talent_pipeline, user_first)

    # Adding candidates with 'Apple' as current company
    apple_candidate_ids = populate_candidates(oauth_token=access_token_first, count=3, current_company='Apple',
                                              talent_pool_id=talent_pool.id)

    # Adding candidates with 'Apple' as current company and 'Software Engineer' as current title
    populate_candidates(oauth_token=access_token_first, count=5, current_title='Software Engineer',
                        current_company='Apple', talent_pool_id=talent_pool.id)

    # Adding candidates with 'Apple' as current company and 'Software Engineer' as current title and 'CS' as major
    cs_sw_engineers_candidate_ids = populate_candidates(oauth_token=access_token_first, count=5, major='CS',
                                                        current_title='Software Engineer', current_company='Apple',
                                                        talent_pool_id=talent_pool.id)

    # Adding candidates dumb_list
    add_candidates_to_dumb_list(db.session, access_token_first, test_dumb_list, apple_candidate_ids)

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
    add_candidates_to_dumb_list(db.session, access_token_first, test_dumb_list, cs_sw_engineers_candidate_ids)

    # Logged-in user trying to get all candidates of talent-pipeline with search_params
    response, status_code = talent_pipeline_candidate_api(access_token_first, talent_pipeline.id,
                                                          {'fields': 'count_only'})
    assert len(set(apple_candidate_ids + cs_sw_engineers_candidate_ids)) == response.get('total_found')

