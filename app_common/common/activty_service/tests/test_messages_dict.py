"""
tests
"""
from ..activity_constants import ACTIVTY_PARAMS

def test_params_is_tuple():
    for activity_type in ACTIVTY_PARAMS.keys():
        assert isinstance(ACTIVTY_PARAMS[activity_type], tuple)
