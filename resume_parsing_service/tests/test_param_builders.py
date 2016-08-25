from resume_parsing_service.app import app
import json
import pytest
from resume_parsing_service.app.views.param_builders import build_params_from_json
from resume_parsing_service.common.error_handling import InvalidUsage


def test_valid_json_builder():
    test_json = {
        'create_candidate': True,
        'filename': 'rfn',
        'filepicker_key': 'fpk',
        'talent_pool_ids': None,
    }

    #  Params derived from http://werkzeug.pocoo.org/docs/0.11/test/#testing-api
    with app.test_request_context(
            path='/v1/parse_resume', method='POST', data=json.dumps(test_json),
            content_type='application/json') as request:
        assert build_params_from_json(request.request) == {
            'create_candidate': True,
            'filename': 'fpk',
            'filepicker_key': 'fpk',
            'resume_file': None,
            'talent_pools': None
        }


def test_valid_json_builder_tpids():
    test_json = {
        'create_candidate': True,
        'filename': 'rfn',
        'filepicker_key': 'fpk',
        'talent_pool_ids': [1, 2, 3],
    }

    #  Params derived from http://werkzeug.pocoo.org/docs/0.11/test/#testing-api
    with app.test_request_context(
            path='/v1/parse_resume', method='POST', data=json.dumps(test_json),
            content_type='application/json') as request:
        assert build_params_from_json(request.request) == {
            'create_candidate': True,
            'filename': 'fpk',
            'filepicker_key': 'fpk',
            'resume_file': None,
            'talent_pools': [1, 2, 3]
        }


def test_invalid_json_params():
    """
    Tests that the missing (required) key (filepicker key) raises an InvalidUsage
    """
    test_json = {
        'create_candidate': True,
        'filename': 'rfn',
        'talent_pool_ids': [1, 2, 3],
    }

    #  Params derived from http://werkzeug.pocoo.org/docs/0.11/test/#testing-api
    with app.test_request_context(
            path='/v1/parse_resume', method='POST', data=json.dumps(test_json),
            content_type='application/json') as request:
        with pytest.raises(InvalidUsage):
            build_params_from_json(request.request)


