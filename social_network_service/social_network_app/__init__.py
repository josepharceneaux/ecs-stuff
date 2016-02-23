""" Initializer for Social Network Service App.
"""
__author__ = 'zohaib'

# Application Specific
from social_network_service.common.utils.models_utils import init_talent_app


app, logger = init_talent_app('social_network_app')
