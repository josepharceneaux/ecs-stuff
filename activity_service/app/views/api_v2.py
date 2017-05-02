from flask import Blueprint
from flask import request
from flask import jsonify
# from activity_service.app import db, logger
from activity_service.common.utils.auth_utils import require_oauth
from activity_service.app.modules.validators import users_are_in_same_domain
from activity_service.common.models.db import db
from activity_service.common.models.user import User
from activity_service.common.error_handling import UnauthorizedError
from activity_service.app.modules.activity_fetchers import fetch_user_activities
from activity_service.app.modules.v2_activity_manager import get_recent_readable

api_v2 = Blueprint('activities_api_v2', __name__)
DEFAULT_LIMIT = 20


@api_v2.route('/activities/<int:page>/user/<int:user_id>')
@require_oauth()
def get_user_activities(page, user_id):
    requested_user_id = user_id
    requesting_user_id = request.user.id
    user_name = 'You'
    if requested_user_id != requesting_user_id:
        if not users_are_in_same_domain(set([requested_user_id, requesting_user_id]), request.user.domain_id):
            raise UnauthorizedError(error_message='You are not authorized to view that users activity')
        user_name = db.session.query(User).get(requested_user_id).first_name

    requested_qty = request.args.get('qty')
    if requested_qty:
        qty = int(requested_qty)
    else:
        qty = DEFAULT_LIMIT

    activities = fetch_user_activities(requested_user_id, page, qty)
    readable_activities = get_recent_readable(activities, user_name)
    return jsonify(readable_activities), 200


# # Create activities
# @api_v2.route('/activities', methods=['POST'])
# def create_activity():
#     return 'create'
#
#
# # Get list of domain activities excluding user for toasts
# @api_v2.route('/activities', methods=['GET'])
# def get_domain_activities():
#     rargs = request.args
#     params = {
#         'api_call': uuid4(),
#         'user_id': request.user.id,
#         'start_param': rargs.get('start_datetime'),
#     }
#     logger.info("ActivityService::Info::DomainInit: {}".format(params['api_id']))
#     return 'domain'
#
#
# # Get paginated domain activities for list page for last 30 days
# @api_v2.route('/activities/<page>', methods=['GET'])
# def get_paginated_activities(page):
#     params = {
#         'api_call': uuid4(),
#         'user_id': request.user.id,
#         'page': page,
#     }
#     logger.info("ActivityService::Info::PaginatedInit: {}".format(params['api_id']))
#     return 'domain paginated {}'.format(page)
#
#
# # Get aggregated activities for drop down
# @api_v2.route('/aggregate', methods=['GET'])
# def get_aggregated_activities():
#     params = {
#         'api_call': uuid4(),
#         'domain_id': request.user.domain_id,
#         'start': request.args.get('start_datetime'),
#         'user_id': request.user.id,
#     }
#     logger.info("ActivityService::Info::AggregateInit: {}".format(params['api_id']))
#     return 'aggregated'
