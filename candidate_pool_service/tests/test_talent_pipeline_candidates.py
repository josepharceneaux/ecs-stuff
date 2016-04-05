__author__ = 'ufarooqi'

from time import sleep
from candidate_pool_service.candidate_pool_app import app
from candidate_pool_service.common.tests.conftest import *
from candidate_pool_service.common.utils.handy_functions import add_role_to_test_user
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

    # Adding candidates with 'Talent' as first_name
    candidate_ids = populate_candidates(oauth_token=access_token_first, count=3, first_name='Talent',
                                              talent_pool_id=talent_pool.id)

    # Adding candidates with 'Talent' as first_name and 'Software Engineer' as current title
    sw_engineers_candidate_ids = populate_candidates(oauth_token=access_token_first, count=5,
                                                     current_title='Software Engineer', first_name='Talent',
                                                     talent_pool_id=talent_pool.id)

    # Adding candidates with 'Talent' as first_name and 'Software Engineer' as current title and 'CS' as major
    cs_sw_engineers_candidate_ids = populate_candidates(oauth_token=access_token_first, count=5, major='CS',
                                                        current_title='Software Engineer', first_name='Talent',
                                                        talent_pool_id=talent_pool.id)

    # Adding candidates dumb_list
    add_candidates_to_dumb_list(db.session, access_token_first, test_dumb_list, candidate_ids)

    # Wait for addition of candidates in Amazon Cloud Search
    sleep(60)

    # Logged-in user trying to get all candidates of talent-pipeline without search_params
    # so all candidates of corresponding talent_pool will be returned
    response, status_code = talent_pipeline_candidate_api(access_token_first, talent_pipeline.id)
    assert_results(candidate_ids + sw_engineers_candidate_ids + cs_sw_engineers_candidate_ids,  response)

    talent_pipeline.search_params = json.dumps({'job_title': 'Software Engineer'})
    test_smart_list.search_params = json.dumps({'query': 'Talent', 'major': 'CS'})
    db.session.commit()

    # Logged-in user trying to get all candidates of talent-pipeline with search_params
    response, status_code = talent_pipeline_candidate_api(access_token_first, talent_pipeline.id)
    assert_results(sw_engineers_candidate_ids + cs_sw_engineers_candidate_ids,  response)

    # Logged-in user trying to get all candidates of smartlist with search_params
    response = requests.get(
            url=CandidatePoolApiUrl.SMARTLIST_CANDIDATES % test_smart_list.id,
            params={'fields': 'id'}, headers={'Authorization': 'Bearer %s' % access_token_first})
    assert response.status_code == 200
    assert_results(cs_sw_engineers_candidate_ids, response.json())
