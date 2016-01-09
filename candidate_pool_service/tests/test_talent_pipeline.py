__author__ = 'ufarooqi'

from datetime import timedelta
from candidate_pool_service.candidate_pool_app import app
from candidate_pool_service.common.tests.conftest import *
from candidate_pool_service.common.utils.handy_functions import add_role_to_test_user
from candidate_pool_service.common.models.talent_pools_pipelines import TalentPipeline
from candidate_pool_service.common.tests.cloud_search_common_functions import *
from common_functions import *


def test_talent_pipeline_api_post(access_token_first, user_first, talent_pool, talent_pool_second):

    data = {
        'talent_pipelines': [
            {
                'description': gen_salt(10),
                'positions': 'ab',
                'search_params': 'empty'
            }
        ]
    }

    # Logged-in user trying to add a new talent-pipeline
    response, status_code = talent_pipeline_api(access_token_first, data=data, action='POST')
    assert status_code == 401

    # Adding 'CAN_ADD_TALENT_PIPELINES' in user_first
    add_role_to_test_user(user_first, ['CAN_ADD_TALENT_PIPELINES'])

    # Logged-in user trying to add a new talent-pipeline with empty request body
    response, status_code = talent_pipeline_api(access_token_first, action='POST')
    assert status_code == 400

    # Logged-in user trying to add a new talent-pipeline without name
    response, status_code = talent_pipeline_api(access_token_first, data=data, action='POST')
    assert status_code == 400

    # Logged-in user trying to add a new talent-pipeline without date_needed
    data['talent_pipelines'][0]['name'] = gen_salt(6)
    response, status_code = talent_pipeline_api(access_token_first, data=data, action='POST')
    assert status_code == 400

    # Logged-in user trying to add a new talent-pipeline without talent_pool_id
    data['talent_pipelines'][0]['date_needed'] = '12&3'
    response, status_code = talent_pipeline_api(access_token_first, data=data, action='POST')
    assert status_code == 400

    # Logged-in user trying to add a new talent-pipeline with invalid date_needed
    data['talent_pipelines'][0]['talent_pool_id'] = 'a'
    response, status_code = talent_pipeline_api(access_token_first, data=data, action='POST')
    assert status_code == 400

    # Logged-in user trying to add a new talent-pipeline with date older than current date
    data['talent_pipelines'][0]['date_needed'] = (datetime.utcnow().replace(microsecond=0) + timedelta(hours=-48)).\
        isoformat(sep=' ')
    response, status_code = talent_pipeline_api(access_token_first, data=data, action='POST')
    assert status_code == 400

    # Logged-in user trying to add a new talent-pipeline with non-integer positions
    data['talent_pipelines'][0]['date_needed'] = (datetime.utcnow().replace(microsecond=0) + timedelta(hours=3)).\
        isoformat(sep=' ')
    response, status_code = talent_pipeline_api(access_token_first, data=data, action='POST')
    assert status_code == 400

    # Logged-in user trying to add a new talent-pipeline with non-integer talent_pool_id
    data['talent_pipelines'][0]['positions'] = 2
    response, status_code = talent_pipeline_api(access_token_first, data=data, action='POST')
    assert status_code == 400

    # Logged-in user trying to add a new talent-pipeline with non-existing talent_pool
    data['talent_pipelines'][0]['talent_pool_id'] = 1000
    response, status_code = talent_pipeline_api(access_token_first, data=data, action='POST')
    assert status_code == 404

    # Logged-in user trying to add a new talent-pipeline with talent_pool of different domain
    data['talent_pipelines'][0]['talent_pool_id'] = talent_pool_second.id
    response, status_code = talent_pipeline_api(access_token_first, data=data, action='POST')
    assert status_code == 403

    # Logged-in user trying to add a new talent-pipeline with invalid search params
    data['talent_pipelines'][0]['talent_pool_id'] = talent_pool.id
    response, status_code = talent_pipeline_api(access_token_first, data=data, action='POST')
    assert status_code == 400

    # Logged-in user trying to add a new talent-pipeline with invalid search params keys
    data['talent_pipelines'][0]['search_params'] = {
        "skillDescriptionFacet": "Python",
        "minimum_age": "22",
        "location": "California"
    }
    response, status_code = talent_pipeline_api(access_token_first, data=data, action='POST')
    assert status_code == 404

    # Logged-in user trying to add a new talent-pipeline
    data['talent_pipelines'][0]['search_params'] = {
        "major": "CS",
        "minimum_years_experience": "4",
        "location": "California"
    }
    response, status_code = talent_pipeline_api(access_token_first, data=data, action='POST')
    assert status_code == 200
    assert len(response.get('talent_pipelines')) == 1

    db.session.commit()
    talent_pipeline = TalentPipeline.query.get(response.get('talent_pipelines')[0])
    assert talent_pipeline
    assert talent_pipeline.name == data['talent_pipelines'][0]['name']
    assert talent_pipeline.talent_pool_id == data['talent_pipelines'][0]['talent_pool_id']
    assert talent_pipeline.positions == data['talent_pipelines'][0]['positions']
    assert talent_pipeline.description == data['talent_pipelines'][0]['description']
    assert talent_pipeline.date_needed.isoformat(sep=' ') == data['talent_pipelines'][0]['date_needed']
    assert talent_pipeline.search_params == json.dumps(data['talent_pipelines'][0]['search_params'])

    # Logged-in user trying to add a new talent-pool with existing name in a domain
    response, status_code = talent_pipeline_api(access_token_first, data=data, action='POST')
    assert status_code == 400


def test_talent_pipeline_api_put(access_token_first, access_token_second, user_second, user_first, talent_pool_second,
                                 talent_pipeline):

    data = {
        'talent_pipeline': {
            'name': talent_pipeline.name,
            'positions': -2,
            'search_params': 'empty',
            'date_needed': '12&3',
            'talent_pool_id': 'a'
        }
    }

    talent_pipeline_id = talent_pipeline.id

    # Adding 'CAN_EDIT_TALENT_PIPELINES' in user_second
    add_role_to_test_user(user_second, ['CAN_EDIT_TALENT_PIPELINES'])

    # Logged-in user trying to edit an existing talent-pipeline of different domain
    response, status_code = talent_pipeline_api(access_token_second, talent_pipeline_id=talent_pipeline_id, data=data,
                                                action='PUT')
    assert status_code == 403

    # Logged-in user trying to edit an existing talent-pipeline of same domain
    response, status_code = talent_pipeline_api(access_token_first, talent_pipeline_id=talent_pipeline_id, data=data,
                                                action='PUT')
    assert status_code == 401

    # Adding 'CAN_EDIT_TALENT_PIPELINES' in user_first
    add_role_to_test_user(user_first, ['CAN_EDIT_TALENT_PIPELINES'])

    # Logged-in user trying to edit a talent-pipeline with empty request body
    response, status_code = talent_pipeline_api(access_token_first, talent_pipeline_id=talent_pipeline_id, action='PUT')
    assert status_code == 400

    # Logged-in user trying to edit a non-existing talent-pipeline
    response, status_code = talent_pipeline_api(access_token_first, talent_pipeline_id=talent_pipeline_id + 10,
                                                data=data, action='PUT')
    assert status_code == 404

    # Logged-in user trying to edit a talent-pipeline with existing name
    response, status_code = talent_pipeline_api(access_token_first, talent_pipeline_id=talent_pipeline_id, data=data,
                                                action='PUT')
    assert status_code == 400

    # Logged-in user trying to edit a talent-pipeline with invalid date_needed
    data['talent_pipeline']['name'] = gen_salt(6)
    response, status_code = talent_pipeline_api(access_token_first, talent_pipeline_id=talent_pipeline_id, data=data,
                                                action='PUT')
    assert status_code == 400

    # Logged-in user trying to edit a talent-pipeline with date older than current date
    data['talent_pipeline']['date_needed'] = (datetime.utcnow().replace(microsecond=0) + timedelta(hours=-48)).\
        isoformat(sep=' ')
    response, status_code = talent_pipeline_api(access_token_first, talent_pipeline_id=talent_pipeline_id, data=data,
                                                action='PUT')
    assert status_code == 400

    # Logged-in user trying to edit talent-pipeline with non-integer positions
    data['talent_pipeline']['date_needed'] = (datetime.utcnow().replace(microsecond=0) + timedelta(hours=3)).\
        isoformat(sep=' ')
    response, status_code = talent_pipeline_api(access_token_first, talent_pipeline_id=talent_pipeline_id, data=data,
                                                action='PUT')
    assert status_code == 400

    # Logged-in user trying to edit talent-pipeline with invalid talent_pool_id
    data['talent_pipeline']['positions'] = 2
    response, status_code = talent_pipeline_api(access_token_first, talent_pipeline_id=talent_pipeline_id, data=data,
                                                action='PUT')
    assert status_code == 400

    # Logged-in user trying to edit talent-pipeline with non-existing talent_pool_id
    data['talent_pipeline']['talent_pool_id'] = 1000
    response, status_code = talent_pipeline_api(access_token_first, talent_pipeline_id=talent_pipeline_id, data=data,
                                                action='PUT')
    assert status_code == 404

    # Logged-in user trying to edit talent-pipeline with talent_pool_id of different domain
    data['talent_pipeline']['talent_pool_id'] = talent_pool_second.id
    response, status_code = talent_pipeline_api(access_token_first, talent_pipeline_id=talent_pipeline_id, data=data,
                                                action='PUT')
    assert status_code == 403

    # Logged-in user trying to edit talent-pipeline with invalid search params
    del data['talent_pipeline']['talent_pool_id']
    response, status_code = talent_pipeline_api(access_token_first, talent_pipeline_id=talent_pipeline_id, data=data,
                                                action='PUT')
    assert status_code == 400

    # Logged-in user trying to edit talent-pipeline with invalid search params keys
    data['talent_pipeline']['search_params'] = {
        "minimum_years_experience": 2,
        "minimum_age": "22",
        "location": "California"
    }
    response, status_code = talent_pipeline_api(access_token_first, talent_pipeline_id=talent_pipeline_id, data=data,
                                                action='PUT')
    assert status_code == 404

    # Logged-in user trying to edit talent-pipeline with valid search params keys
    data['talent_pipeline']['search_params'] = {
        "major": "CS",
        "minimum_years_experience": "10",
        "location": "Indiana"
    }
    response, status_code = talent_pipeline_api(access_token_first, talent_pipeline_id=talent_pipeline_id, data=data,
                                                action='PUT')
    assert status_code == 200
    assert response.get('talent_pipeline').get('id') == talent_pipeline_id

    db.session.commit()
    talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)
    assert talent_pipeline
    assert talent_pipeline.name == data['talent_pipeline']['name']
    assert talent_pipeline.positions == data['talent_pipeline']['positions']
    assert talent_pipeline.date_needed.isoformat(sep=' ') == data['talent_pipeline']['date_needed']
    assert talent_pipeline.search_params == json.dumps(data['talent_pipeline']['search_params'])


def test_talent_pipeline_api_get(access_token_first, access_token_second, user_second, user_first, talent_pipeline):

    talent_pipeline_id = talent_pipeline.id

    # Logged-in user trying to get information of a talent_pipeline
    response, status_code = talent_pipeline_api(access_token_first, talent_pipeline_id=talent_pipeline_id)
    assert status_code == 401

    # Adding 'CAN_GET_TALENT_PIPELINES' in user_first and user_second
    add_role_to_test_user(user_first, ['CAN_GET_TALENT_PIPELINES'])
    add_role_to_test_user(user_second, ['CAN_GET_TALENT_PIPELINES'])

    # Logged-in user trying to get information of a non-existing talent_pipeline
    response, status_code = talent_pipeline_api(access_token_first, talent_pipeline_id=talent_pipeline_id + 1000)
    assert status_code == 404

    # Logged-in user trying to get information of a talent_pipeline of different domain
    response, status_code = talent_pipeline_api(access_token_second, talent_pipeline_id=talent_pipeline_id)
    assert status_code == 403

    # Logged-in user trying to get information of a talent_pipeline
    response, status_code = talent_pipeline_api(access_token_first, talent_pipeline_id=talent_pipeline_id)
    assert status_code == 200
    assert response['talent_pipeline']['id'] == talent_pipeline.id
    assert response['talent_pipeline']['name'] == talent_pipeline.name
    assert response['talent_pipeline']['description'] == talent_pipeline.description
    assert response['talent_pipeline']['user_id'] == talent_pipeline.owner_user_id
    assert response['talent_pipeline']['positions'] == talent_pipeline.positions
    assert json.dumps(response['talent_pipeline']['search_params']) == talent_pipeline.search_params
    assert response['talent_pipeline']['talent_pool_id'] == talent_pipeline.talent_pool_id
    assert response['talent_pipeline']['date_needed'] == str(talent_pipeline.date_needed)

    # Logged-in user trying to get talent_pipelines of his domain
    response, status_code = talent_pipeline_api(access_token_second)
    assert status_code == 200
    assert len(response['talent_pipelines']) == 0

    # Logged-in user trying to get talent_pipelines of his domain
    response, status_code = talent_pipeline_api(access_token_first)
    assert status_code == 200
    assert len(response['talent_pipelines']) == 1


def test_talent_pipeline_api_delete(access_token_first, access_token_second, user_second, user_first, talent_pipeline):

    talent_pipeline_id = talent_pipeline.id

    # Logged-in user trying to delete of a talent_pipeline
    response, status_code = talent_pipeline_api(access_token_first, talent_pipeline_id=talent_pipeline_id, action='DELETE')
    assert status_code == 401

    # Adding 'CAN_GET_TALENT_PIPELINES' in user_first and user_second
    add_role_to_test_user(user_first, ['CAN_DELETE_TALENT_PIPELINES'])
    add_role_to_test_user(user_second, ['CAN_DELETE_TALENT_PIPELINES'])

    # Logged-in user trying to delete a non-existing talent_pipeline
    response, status_code = talent_pipeline_api(access_token_first, talent_pipeline_id=talent_pipeline_id + 1000,
                                                action='DELETE')
    assert status_code == 404

    # Logged-in user trying to delete a talent_pipeline of different domain
    response, status_code = talent_pipeline_api(access_token_second, talent_pipeline_id=talent_pipeline_id, action='DELETE')
    assert status_code == 403

    # Logged-in user trying to delete a talent_pipeline
    response, status_code = talent_pipeline_api(access_token_first, talent_pipeline_id=talent_pipeline_id, action='DELETE')
    assert status_code == 200

    db.session.commit()
    assert not TalentPipeline.query.get(talent_pipeline_id)


def test_talent_pipeline_smart_list_api_post(access_token_first, access_token_second, user_second, user_first,
                                               talent_pipeline):

    talent_pipeline_id = talent_pipeline.id

    # Adding two test_smart_lists
    test_smart_first = Smartlist(name=gen_salt(5), user_id=user_first.id)
    test_smart_second = Smartlist(name=gen_salt(5), user_id=user_second.id)
    db.session.add(test_smart_first)
    db.session.add(test_smart_second)
    db.session.commit()

    data = {
        'smart_list_ids': ['a', test_smart_first.id]
    }

    # Logged-in user trying to add smart_lists to a talent_pipeline
    response, status_code = talent_pipeline_smart_list_api(access_token_first, talent_pipeline_id, data=data,
                                                           action='POST')
    assert status_code == 401

    # Adding 'CAN_ADD_TALENT_PIPELINE_SMART_LISTS' to user_first and user_second
    add_role_to_test_user(user_first, ['CAN_ADD_TALENT_PIPELINE_SMART_LISTS'])
    add_role_to_test_user(user_second, ['CAN_ADD_TALENT_PIPELINE_SMART_LISTS'])

    # Logged-in user trying to add smart_lists to a talent_pipeline with empty request body
    response, status_code = talent_pipeline_smart_list_api(access_token_first, talent_pipeline_id, action='POST')
    assert status_code == 400

    # Logged-in user trying to add smart_lists to a non-existing talent_pipeline
    response, status_code = talent_pipeline_smart_list_api(access_token_first, talent_pipeline_id + 1000, data=data,
                                                           action='POST')
    assert status_code == 404

    # Logged-in user trying to add smart_lists to a talent_pipeline of different domain
    response, status_code = talent_pipeline_smart_list_api(access_token_second, talent_pipeline_id, data=data,
                                                           action='POST')
    assert status_code == 403

    # Logged-in user trying to add smart_lists with non-integer id to talent_pipeline
    response, status_code = talent_pipeline_smart_list_api(access_token_first, talent_pipeline_id, data=data, action='POST')
    assert status_code == 400

    # Logged-in user trying to add smart_lists of different domain to talent_pipeline
    data['smart_list_ids'][0] = test_smart_second.id
    response, status_code = talent_pipeline_smart_list_api(access_token_first, talent_pipeline_id, data=data, action='POST')
    assert status_code == 403

    # Logged-in user trying to add smart_lists to talent_pipeline
    data['smart_list_ids'].pop(0)
    response, status_code = talent_pipeline_smart_list_api(access_token_first, talent_pipeline_id, data=data, action='POST')
    assert status_code == 200

    db.session.refresh(test_smart_first)
    db.session.commit()

    assert test_smart_first.talent_pipeline_id == talent_pipeline_id

    # Logged-in user trying to add already added smart_list to talent_pipeline
    response, status_code = talent_pipeline_smart_list_api(access_token_first, talent_pipeline_id, data=data, action='POST')
    assert status_code == 400


def test_talent_pipeline_smart_list_api_delete(access_token_first, access_token_second, user_second, user_first,
                                               talent_pipeline):

    talent_pipeline_id = talent_pipeline.id

    # Adding two test_smart_lists
    test_smart_first = Smartlist(name=gen_salt(5), user_id=user_first.id, talent_pipeline_id=talent_pipeline_id)
    test_smart_second = Smartlist(name=gen_salt(5), user_id=user_second.id)
    db.session.add(test_smart_first)
    db.session.add(test_smart_second)
    db.session.commit()

    data = {
        'smart_list_ids': ['a', test_smart_first.id]
    }

    # Logged-in user trying to remove smart_lists from a talent_pipeline
    response, status_code = talent_pipeline_smart_list_api(access_token_first, talent_pipeline_id, data=data,
                                                           action='DELETE')
    assert status_code == 401

    # Adding 'CAN_DELETE_TALENT_PIPELINE_SMART_LISTS' to user_first and user_second
    add_role_to_test_user(user_first, ['CAN_DELETE_TALENT_PIPELINE_SMART_LISTS'])
    add_role_to_test_user(user_second, ['CAN_DELETE_TALENT_PIPELINE_SMART_LISTS'])

    # Logged-in user trying to remove smart_lists from a talent_pipeline with empty request body
    response, status_code = talent_pipeline_smart_list_api(access_token_first, talent_pipeline_id, action='DELETE')
    assert status_code == 400

    # Logged-in user trying to remove smart_lists from a non-existing talent_pipeline
    response, status_code = talent_pipeline_smart_list_api(access_token_first, talent_pipeline_id + 1000, data=data,
                                                           action='DELETE')
    assert status_code == 404

    # Logged-in user trying to remove smart_lists from a talent_pipeline of different domain
    response, status_code = talent_pipeline_smart_list_api(access_token_second, talent_pipeline_id, data=data,
                                                           action='DELETE')
    assert status_code == 403

    # Logged-in user trying to remove smart_lists with non-integer id from a talent_pipeline
    response, status_code = talent_pipeline_smart_list_api(access_token_first, talent_pipeline_id, data=data, action='DELETE')
    assert status_code == 400

    # Logged-in user trying to remove smart_lists from a talent_pipeline
    data['smart_list_ids'][0] = test_smart_second.id
    response, status_code = talent_pipeline_smart_list_api(access_token_first, talent_pipeline_id, data=data, action='DELETE')
    assert status_code == 403

    # Logged-in user trying to remove smart_lists from a talent_pipeline
    data['smart_list_ids'].pop(0)
    response, status_code = talent_pipeline_smart_list_api(access_token_first, talent_pipeline_id, data=data, action='DELETE')
    assert status_code == 200

    db.session.refresh(test_smart_first)
    db.session.commit()

    assert not test_smart_first.talent_pipeline_id


def test_talent_pipeline_smart_list_api_get(access_token_first, access_token_second, user_second, user_first, talent_pipeline):

    talent_pipeline_id = talent_pipeline.id

    # Adding two test_smart_lists
    test_smart_first = Smartlist(name=gen_salt(5), user_id=user_first.id, talent_pipeline_id=talent_pipeline_id)
    test_smart_second = Smartlist(name=gen_salt(5), user_id=user_first.id, talent_pipeline_id=talent_pipeline_id)
    db.session.add(test_smart_first)
    db.session.add(test_smart_second)
    db.session.commit()

    # Logged-in user trying to get all smart_lists of a talent_pipeline
    response, status_code = talent_pipeline_smart_list_api(access_token_first, talent_pipeline_id)
    assert status_code == 401

    # Adding 'CAN_GET_TALENT_PIPELINE_SMART_LISTS' to user_first and user_second
    add_role_to_test_user(user_first, ['CAN_GET_TALENT_PIPELINE_SMART_LISTS'])
    add_role_to_test_user(user_second, ['CAN_GET_TALENT_PIPELINE_SMART_LISTS'])

    # Logged-in user trying to get all smart_lists of a non-existing talent_pipeline
    response, status_code = talent_pipeline_smart_list_api(access_token_first, talent_pipeline_id + 1000)
    assert status_code == 404

    # Logged-in user trying to get all smart_lists of a talent_pipeline of different domain
    response, status_code = talent_pipeline_smart_list_api(access_token_second, talent_pipeline_id)
    assert status_code == 403

    # Logged-in user trying to get all smart_lists of a talent_pipeline
    response, status_code = talent_pipeline_smart_list_api(access_token_first, talent_pipeline_id)
    assert status_code == 200
    assert len(response['smart_lists']) == 2

    assert response['smart_lists'][0]['name'] == test_smart_first.name
    assert response['smart_lists'][0]['user_id'] == test_smart_first.user_id
    assert response['smart_lists'][1]['name'] == test_smart_second.name
    assert response['smart_lists'][1]['user_id'] == test_smart_second.user_id

