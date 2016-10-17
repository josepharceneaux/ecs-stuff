"""
This module contains code to initialize test app so we can test our model related code
in any file by importing this app and to log error etc. using this logger
"""
from ..utils.models_utils import init_talent_app

test_app, logger = init_talent_app('test_app')
