"""Activities API for getting activities for a user's domain or posting new activities
   to the database.
"""
__author__ = 'erikfarmer'
# stdlib
from collections import namedtuple
from datetime import datetime
from uuid import uuid4
import json

# framework specific/third party
from flask import Blueprint
from flask import jsonify
from flask import request
from requests import codes as STATUS_CODES

# application specific
from activity_service.app import db, logger
from activity_service.common.routes import ActivityApi
from activity_service.common.models.misc import Activity
from activity_service.common.utils.auth_utils import require_oauth
from activity_service.app.views.activity_manager import TalentActivityManager

DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'
POSTS_PER_PAGE = 20
mod = Blueprint('activities_api_v1', __name__)

ACTIVITY_REQUIREMENTS = [
    'user_id', 'exclude_current_user', 'start_datetime', 'end_datetime', 'is_aggregate_request', 'aggregate_limit',
    'post_qty', 'page'
]
ActivityParams = namedtuple('ActivityParams', ACTIVITY_REQUIREMENTS)


@mod.route(ActivityApi.ACTIVITIES_PAGE, methods=['GET'])
@require_oauth()
def get_activities(page):
    """
    :param int page: Page used in pagination for GET requests.
    :return: JSON formatted pagination response or message notifying creation status.
    """
    rargs = request.args
    start_datetime, end_datetime = None, None
    valid_user_id = request.user.id
    aggregate = rargs.get('aggregate') == '1'  # TODO see if int arg can be used
    aggregate_limit = rargs.get('aggregate_limit', '5')
    post_qty = int(rargs.get('post_qty')) if rargs.get('post_qty') else POSTS_PER_PAGE
    start_param = rargs.get('start_datetime')
    end_param = rargs.get('end_datetime')
    exclude_current_user = True if rargs.get('exclude_current_user') == '1' else False

    if start_param:
        start_datetime = datetime.strptime(start_param, DATE_FORMAT)

    if end_param:
        end_datetime = datetime.strptime(end_param, DATE_FORMAT)

    if aggregate_limit:
        try:
            aggregate_limit = int(aggregate_limit)
            aggregate_limit = 5 if aggregate_limit > 5 else aggregate_limit
        except ValueError:
            return jsonify({'error': {'message': 'aggregate_limit must be an integer'}}), STATUS_CODES.bad

    if page:
        try:
            request_page = int(page)
        except ValueError:
            return jsonify({'error': {'message': 'page parameter must be an integer'}}), STATUS_CODES.bad

    activity_params = ActivityParams(valid_user_id, exclude_current_user, start_datetime, end_datetime, aggregate,
                                     aggregate_limit, post_qty, request_page)

    tam = TalentActivityManager(activity_params)

    if aggregate:
        return jsonify({'activities': tam.get_recent_readable()}), 200

    else:
        return jsonify(tam.get_activities())


@mod.route(ActivityApi.ACTIVITY_MESSAGES, methods=['GET'])
@require_oauth()
def get_activity_messages():
    """
    This endpoint returns a dictionary where keys are activity type ids and values are
    raw messages for that kind of activities.

    .. Response::

        {
            1: [
                "%(username)s uploaded resume of candidate %(formattedName)s",
                "%(username)s uploaded %(count)s candidate resumes",
                "candidate.png" ],

            2: [
                "%(username)s updated candidate %(formattedName)s",
                "%(username)s updated %(count)s candidates",
                "candidate.png" ],
            .
            .
            .
        }
    :return:
    """
    logger.info("ActivityService::Info:: Call to `get_activity_messages`")
    return jsonify(dict(messages=TalentActivityManager.MESSAGES))


@mod.route(ActivityApi.ACTIVITIES, methods=['POST'])
@require_oauth()
def post_activity():
    valid_user_id = request.user.id
    domain_id = request.user.domain_id
    content = request.get_json()
    logger.info("ActivityService::Info:: Call to `post_activity` UserId: {} DomainId: {} Content: {}".format(
        valid_user_id, domain_id, content))

    return create_activity(valid_user_id,
                           content.get('type'), domain_id,
                           content.get('source_table'), content.get('source_id'), content.get('params'))


# TODO move this is a module
def create_activity(user_id, type_, domain_id, source_table=None, source_id=None, params=None):
    """Method for creating a DB entry in the activity table.
    :param int user_id: ID of the authenticated user.
    :param int type_: Integer corresponding to TalentActivityAPI attributes.
    :param str|None source_table: String representing the DB table the activity relates to.
    :param int|None source_id: Integer of the source_table's ID for entered specific activity.
    :param dict|None params: Dictionary of created/updated source_table attributes.
    :return: HTTP Response
    """
    activity = Activity(
        user_id=int(user_id),
        type=type_,
        source_table=source_table,
        source_id=source_id,
        params=json.dumps(params) if params else None,
        added_time=datetime.utcnow(),
        domain_id=domain_id)
    try:
        db.session.add(activity)
        db.session.commit()
        return json.dumps({'activity': {'id': activity.id}}), STATUS_CODES.created
    except Exception as e:
        logger.exception('ActivityService::Error::CreationError - {}'.format(e))
        return json.dumps({'error': 'There was an error saving your log entry'}), STATUS_CODES.internal_server_error
