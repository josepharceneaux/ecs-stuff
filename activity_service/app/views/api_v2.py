from uuid import uuid4
from flask import Blueprint
from flask import request
from activity_service.app import db, logger


api_v2 = Blueprint('activities_api_v2', __name__)


# Create activities
@api_v2.route('/activities', methods=['POST'])
def create_activity():
    return 'create'


# Get list of domain activities excluding user for toasts
@api_v2.route('/activities', methods=['GET'])
def get_domain_activities():
    rargs = request.args
    params = {
        'api_call': uuid4(),
        'user_id': request.user.id,
        'start_param': rargs.get('start_datetime'),
    }
    logger.info("ActivityService::Info::DomainInit: {}".format(params['api_id']))
    return 'domain'


# Get paginated domain activities for list page for last 30 days
@api_v2.route('/activities/<page>', methods=['GET'])
def get_paginated_activities(page):
    params = {
        'api_call': uuid4(),
        'user_id': request.user.id,
        'page': page,
    }
    logger.info("ActivityService::Info::PaginatedInit: {}".format(params['api_id']))
    return 'domain paginated {}'.format(page)


# Get aggregated activities for drop down
@api_v2.route('/aggregate', methods=['GET'])
def get_aggregated_activities():
    params = {
        'api_call': uuid4(),
        'domain_id': request.user.domain_id,
        'start': request.args.get('start_datetime'),
        'user_id': request.user.id,
    }
    logger.info("ActivityService::Info::AggregateInit: {}".format(params['api_id']))
    return 'aggregated'
