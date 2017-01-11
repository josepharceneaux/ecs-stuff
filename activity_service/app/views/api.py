"""Activities API for getting activities for a user's domain or posting new activities
   to the database.
"""
__author__ = 'erikfarmer'
# stdlib
from datetime import datetime
from uuid import uuid4
import json
import re
from time import time
# framework specific/third party
from flask import jsonify
from flask import request
from flask import Blueprint
from requests import codes as STATUS_CODES
from sqlalchemy import not_

# application specific
from activity_service.common.models.user import User
from activity_service.app import db, logger
from activity_service.common.routes import ActivityApi
from activity_service.common.models.misc import Activity
from activity_service.common.error_handling import NotFoundError
from activity_service.common.utils.api_utils import ApiResponse
from activity_service.common.utils.auth_utils import require_oauth
from activity_service.common.campaign_services.campaign_utils import CampaignUtils

DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'
POSTS_PER_PAGE = 20
EPOCH = datetime(year=1970, month=1, day=1)
EXCLUSIONS = (15, 16, 17)
mod = Blueprint('activities_api', __name__)


@mod.route(ActivityApi.ACTIVITIES_PAGE, methods=['GET'])
@require_oauth()
def get_activities(page):
    """
    :param int page: Page used in pagination for GET requests.
    :return: JSON formatted pagination response or message notifying creation status.
    """
    api_id = uuid4()
    logger.info("Call to activity service with id: {}".format(api_id))
    start_datetime, end_datetime = None, None
    valid_user_id = request.user.id
    is_aggregate_request = request.args.get('aggregate') == '1'
    aggregate_limit = request.args.get('aggregate_limit', '5')
    start_param = request.args.get('start_datetime')
    end_param = request.args.get('end_datetime')
    exclude_current_user = True if request.args.get('exclude_current_user') == '1' else False
    tam = TalentActivityManager(api_id)

    if start_param:
        start_datetime = datetime.strptime(start_param, DATE_FORMAT)

    if end_param:
        end_datetime = datetime.strptime(end_param, DATE_FORMAT)

    if is_aggregate_request:
        logger.info('Aggregate call made with id: {}'.format(api_id))
        try:
            aggregate_limit = int(aggregate_limit)

        except ValueError:
            return jsonify({'error': {'message': 'aggregate_limit must be an integer'}}), STATUS_CODES.bad

        return jsonify({
            'activities': tam.get_recent_readable(
                valid_user_id, start_datetime=start_datetime, end_datetime=end_datetime,
                limit=aggregate_limit
            )
        })

    else:
        logger.info('Individual call made with id: {}'.format(api_id))
        post_qty = request.args.get('post_qty') if request.args.get('post_qty') else POSTS_PER_PAGE

        try:
            request_page = int(page)

        except ValueError:
            return jsonify({'error': {'message': 'page parameter must be an integer'}}), STATUS_CODES.bad

        return jsonify(tam.get_activities(user_id=valid_user_id, post_qty=post_qty,
                                          start_datetime=start_datetime,
                                          end_datetime=end_datetime, page=request_page,
                                          exlude_current=exclude_current_user))


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
    return jsonify(dict(messages=TalentActivityManager.MESSAGES))


@mod.route(ActivityApi.ACTIVITIES, methods=['GET', 'POST'])
@require_oauth()
def post_activity():
    valid_user_id = request.user.id
    if request.method == 'POST':
        content = request.get_json()

        return create_activity(valid_user_id, content.get('type'), content.get('source_table'),
                               content.get('source_id'), content.get('params'))
    source_table = request.args.get('source_table')
    source_id = request.args.get('source_id')
    type_id = request.args.get('type')
    activity = Activity.get_single_activity(valid_user_id, type_id, source_id, source_table)
    if not activity:
        raise NotFoundError('Activity not found for given query params.')

    return ApiResponse(json.dumps({"activity": activity.to_json()}), status=STATUS_CODES.OK)


def create_activity(user_id, type_, source_table=None, source_id=None, params=None):
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
        added_time=datetime.utcnow()
    )
    try:
        db.session.add(activity)
        db.session.commit()
        return json.dumps({'activity': {'id': activity.id}}), STATUS_CODES.created
    except Exception:
        # TODO logging
        return json.dumps({'error': 'There was an error saving your log entry'}), STATUS_CODES.internal_server_error


class TalentActivityManager(object):
    """API class for ActivityService."""
    #TODO Make these dicts in v2 because properties/keys are more betterer than indexes. 
    MESSAGES = {
        Activity.MessageIds.RSVP_EVENT: (
            "<b>%(firstName)s %(lastName)s</b> responded %(response)s on <b>%(creator)s's</b> "
            "event: <b>'%(eventTitle)s'</b> %(img)s",
            "<b>%(firstName)s %(lastName)s<b> responded %(response)s on event: "
            "'<b>%(eventTitle)s</b>'",
            "candidate.png"),
        Activity.MessageIds.EVENT_CREATE: (
            "<b>%(username)s</b> created an event: <b>%(event_title)s</b>",
            "<b>%(username)s</b> created %(count)s events.</b>",
            "event.png"),
        Activity.MessageIds.EVENT_DELETE: (
            "<b>%(username)s</b> deleted an event <b>%(event_title)s</b>",
            "<b>%(username)s</b> deleted %(count)s events.",
            "event.png"),
        Activity.MessageIds.EVENT_UPDATE: (
            "<b>%(username)s</b> updated an event <b>%(event_title)s</b>.",
            "<b>%(username)s</b> updated %(count)s events.",
            "event.png"),
        Activity.MessageIds.CANDIDATE_CREATE_WEB: (
            "<b>%(username)s</b> uploaded the resume of candidate <b>%(formattedName)s</b>",
            "<b>%(username)s</b> uploaded the resume(s) of %(count)s candidate(s)",
            "candidate.png"),
        Activity.MessageIds.CANDIDATE_CREATE_CSV: (
            "<b>%(username)s</b> imported the candidate <b>%(formattedName)s</b> via spreadsheet",
            "<b>%(username)s</b> imported %(count)s candidate(s) via spreadsheet",
            "candidate.png"),
        Activity.MessageIds.CANDIDATE_CREATE_WIDGET: (
            "Candidate <b>%(formattedName)s</b> joined via widget",
            "%(count)s candidate(s) joined via widget",
            "widget.png"),
        Activity.MessageIds.CANDIDATE_CREATE_MOBILE: (
            "<b>%(username)s</b> added the candidate <b>%(formattedName)s</b> via mobile",
            "<b>%(username)s</b> added %(count)s candidate(s) via mobile",
            "candidate.png"),
        Activity.MessageIds.CANDIDATE_UPDATE: (
            "<b>%(username)s</b> updated the candidate <b>%(formattedName)s</b>",
            "<b>%(username)s</b> updated %(count)s candidates",
            "candidate.png"),
        Activity.MessageIds.CANDIDATE_DELETE: (
            "<b>%(username)s</b> deleted the candidate <b>%(formattedName)s</b>",
            "<b>%(username)s</b> deleted %(count)s candidates",
            "candidate.png"),
        Activity.MessageIds.CAMPAIGN_CREATE: (
            "<b>%(username)s</b> created an %(campaign_type)s campaign: <b>%(name)s</b>",
            "<b>%(username)s</b> created %(count)s campaigns",
            "campaign.png"),
        Activity.MessageIds.CAMPAIGN_DELETE: (
            "<b>%(username)s</b> deleted an %(campaign_type)s campaign: <b>%(name)s</b>",
            "<b>%(username)s</b> deleted %(count)s campaign(s)",
            "campaign.png"),
        Activity.MessageIds.CAMPAIGN_SEND: (
            "Campaign <b>%(name)s</b> was sent to <b>%(num_candidates)s</b> candidate(s)",
            "%(count)s campaign(s) sent",
            "campaign.png"),
        Activity.MessageIds.CAMPAIGN_EXPIRE: (
            "<b>%(username)s's</b> recurring campaign <b>%(name)s</b> has expired",
            "%(count)s recurring campaign(s) of <b>%(username)s</b> have expired",
            "campaign.png"),
        Activity.MessageIds.CAMPAIGN_PAUSE: (
            "<b>%(username)s</b> paused the campaign <b>%(name)s</b>",
            "<b>%(username)s</b> paused %(count)s campaign(s)",
            "campaign.png"),
        Activity.MessageIds.CAMPAIGN_RESUME: (
            "<b>%(username)s</b> resumed campaign <b>%(name)s</b>",
            "<b>%(username)s</b> resumed %(count)s campaign(s)",
            "campaign.png"),
        Activity.MessageIds.SMARTLIST_CREATE: (
            "<b>%(username)s</b> created the list <b>%(name)s</b>",
            "<b>%(username)s</b> created %(count)s list(s)",
            "smartlist.png"),
        Activity.MessageIds.SMARTLIST_DELETE: (
            "<b>%(username)s</b> deleted the list: <b>%(name)s</b>",
            "<b>%(username)s</b> deleted %(count)s list(s)",
            "smartlist.png"),
        Activity.MessageIds.DUMBLIST_CREATE: (
            "<b>%(username)s</b> created a list: <b>%(name)s</b>.",
            "<b>%(username)s</b> created %(count)s list(s)",
            "dumblist.png"),
        Activity.MessageIds.DUMBLIST_DELETE: (
            "<b>%(username)s</b> deleted list <b>%(name)s</b>",
            "<b>%(username)s</b> deleted %(count)s list(s)",
            "dumblist.png"),
        Activity.MessageIds.SMARTLIST_ADD_CANDIDATE: (
            "<b>%(formattedName)s<b> was added to list <b>%(name)s</b>",
            "%(count)s candidates were added to list <b>%(name)s</b>",
            "smartlist.png"),
        Activity.MessageIds.SMARTLIST_REMOVE_CANDIDATE: (
            "<b>%(formattedName)s</b> was removed from the list <b>%(name)s</b>",
            "%(count)s candidates were removed from the list <b>%(name)s</b>",
            "smartlist.png"),
        Activity.MessageIds.USER_CREATE: (
            "<b>%(username)s</b> has joined",
            "%(count)s users have joined",
            "notification.png"),
        Activity.MessageIds.WIDGET_VISIT: (
            "Widget was visited",
            "Widget was visited %(count)s time(s)",
            "widget.png"),
        Activity.MessageIds.NOTIFICATION_CREATE: (
            "You received an update notification",
            "You received %(count)s update notification(s)",
            "notification.png"),
        Activity.MessageIds.CAMPAIGN_EMAIL_SEND: (
            "<b>%(candidate_name)s</b> received an email from campaign <b>%(campaign_name)s</b>",
            "%(count)s candidate(s) received an email from campaign <b>%(campaign_name)s</b>",
            "campaign.png"),
        Activity.MessageIds.CAMPAIGN_EMAIL_OPEN: (
            "<b>%(candidate_name)s</b> opened an email from campaign <b>%(campaign_name)s</b>",
            "%(count)s candidates opened an email from campaign <b>%(campaign_name)s</b>",
            "campaign.png"),
        Activity.MessageIds.CAMPAIGN_EVENT_CLICK: (
            "<b>%(candidate_name)s</b> clicked on an email from event campaign <b>%(campaign_name)s</b>",
            "Event Campaign <b>%(campaign_name)s</b> was clicked %(count)s time(s)",
            "campaign.png"),
        Activity.MessageIds.CAMPAIGN_EVENT_SEND: (
            "<b>%(candidate_name)s</b> received an invite for <b>%(campaign_name)s</b>",
            "%(count)s candidate(s) received an invite for <b>%(campaign_name)s</b>",
            "campaign.png"),
        Activity.MessageIds.CAMPAIGN_EVENT_OPEN: (
            "<b>%(candidate_name)s</b> opened an email from event campaign <b>%(campaign_name)s</b>",
            "%(count)s candidates opened an email from event campaign <b>%(campaign_name)s</b>",
            "campaign.png"),
        Activity.MessageIds.CAMPAIGN_EMAIL_CLICK: (
            "<b>%(candidate_name)s</b> clicked on an email from campaign <b>%(campaign_name)s</b>",
            "Campaign <b>%(campaign_name)s</b> was clicked %(count)s time(s)",
            "campaign.png"),
        Activity.MessageIds.CAMPAIGN_SMS_SEND: (
            "SMS Campaign <b>%(campaign_name)s</b> has been sent to %(candidate_name)s.",
            "SMS Campaign <b>%(campaign_name)s</b> has been sent to %(candidate_name)s.",
            "campaign.png"),
        Activity.MessageIds.CAMPAIGN_SMS_CLICK: (
            "<b>%(candidate_name)s</b> clicked on the SMS Campaign <b>%(name)s</b>.",
            "<b>%(candidate_name)s</b> clicked on %(name)s.",
            "campaign.png"),
        Activity.MessageIds.CAMPAIGN_SMS_REPLY: (
            "<b>%(candidate_name)s</b> replied %(reply_text)s to the SMS campaign <b>%(campaign_name)s</b>.",
            "<b>%(candidate_name)s</b> replied '%(reply_text)s' on campaign %(campaign_name)s.",
            "campaign.png"),
        Activity.MessageIds.CAMPAIGN_SCHEDULE: (
            "<b>%(username)s</b> scheduled an %(campaign_type)s campaign: <b>%(campaign_name)s</b>.",
            "<b>%(username)s</b> scheduled an %(campaign_type)s campaign: <b>%(campaign_name)s</b>.",
            "campaign.png"),
        Activity.MessageIds.PIPELINE_CREATE: (
            "<b>%(username)s</b> created a pipeline: <b>%(name)s</b>.",
            "<b>%(username)s</b> created a pipeline: <b>%(name)s</b>.",
            "pipeline.png"),
        Activity.MessageIds.PIPELINE_DELETE: (
            "<b>%(username)s</b> deleted pipeline: <b>%(name)s</b>.",
            "<b>%(username)s</b> deleted pipeline: <b>%(name)s</b>.",
            "pipeline.png"),
        Activity.MessageIds.TALENT_POOL_CREATE: (
            "<b>%(username)s</b> created a Talent Pool: <b>%(name)s</b>.",
            "<b>%(username)s</b> created a Talent Pool: <b>%(name)s</b>.",
            "talent_pool.png"),
        Activity.MessageIds.TALENT_POOL_DELETE: (
            "<b>%(username)s</b> deleted Talent Pool: <b>%(name)s</b>.",
            "<b>%(username)s</b> deleted Talent Pool: <b>%(name)s</b>.",
            "talent_pool.png"),
        Activity.MessageIds.CAMPAIGN_PUSH_CREATE: (
            "<b>%(username)s</b> created a Push campaign: '%(campaign_name)s'",
            "<b>%(username)s</b> created a Push campaign: '%(campaign_name)s'",
            "campaign.png"),
        Activity.MessageIds.CAMPAIGN_PUSH_SEND: (
            "Push Campaign <b>%(campaign_name)s</b> has been sent to <b>%(candidate_name)s</b>.",
            "Push Campaign <b>%(campaign_name)s</b> has been sent to <b>%(candidate_name)s</b>.",
            "campaign.png"),
        Activity.MessageIds.CAMPAIGN_PUSH_CLICK: (
            "<b>%(candidate_name)s</b> clicked on Push Campaign <b>%(campaign_name)s</b>.",
            "<b>%(candidate_name)s</b> clicked on %(campaign_name)s.",
            "campaign.png")
    }

    def __init__(self, call_id):
        self._check_format_string_regexp = re.compile(r'%\((\w+)\)s')
        self.call_id = call_id

    def get_activities(self, user_id, post_qty, start_datetime=None, end_datetime=None, page=1,
                       exlude_current=None):
        """Method for retrieving activity logs based on a domain ID that is extracted via an
           authenticated user ID.
        :param int user_id: ID of the authenticated user.
        :param datetime|None start_datetime: Optional datetime object for query filters.
        :param datetime|None end_datetime: Optional datetime object for query filters.
        :param int page: Pagination start.
        :return: JSON encoded SQL-Alchemy.pagination response.
        """
        current_user = User.query.filter_by(id=user_id).first()
        user_domain_id = User.query.filter_by(id=user_id).value('domainId')
        user_ids = User.query.filter_by(domain_id=user_domain_id).values('id')
        flattened_user_ids = [item for sublist in user_ids for item in sublist]
        filters = []


        # GET - 1998 / WEB - 912.
        # Some activity streams do not want the current user's activities.
        # Additionally we do not want to see some types of activities.
        if exlude_current:
            flattened_user_ids.remove(user_id)
            filters.append(not_(Activity.type.in_(EXCLUSIONS)))

        filters.append(Activity.user_id.in_(flattened_user_ids))
        if start_datetime: filters.append(Activity.added_time > start_datetime)
        if end_datetime: filters.append(Activity.added_time < end_datetime)

        activities = Activity.query.filter(*filters).order_by(Activity.added_time.desc())\
            .paginate(page, post_qty, False)

        activities_response = {
            'total_count': activities.total,
            'items': [{
                          'params': json.loads(activity.params),
                          'source_table': activity.source_table,
                          'source_id': activity.source_id,
                          'type': activity.type,
                          'user_id': activity.user_id,
                          'user_name': activity.user.name if activity.user else '',
                          'added_time': str(activity.added_time),
                          'id': activity.id,
                          'readable_text': self.activity_text(activity, 1, current_user)
                      }
                      for activity in activities.items
                      ]
        }
        return activities_response

    # Like 'get' but gets the last 200 consecutive activity types. can't use GROUP BY because it doesn't respect ordering.
    def get_recent_readable(self, user_id, start_datetime=None, end_datetime=None, limit=3):
        logger.info(limit)
        logger.info("{} getting recent readable for {} - {}".format(
            self.call_id, start_datetime or 'N/A', end_datetime or 'N/A'
        ))

        start_time = time()
        current_user = User.query.filter_by(id=user_id).first()
        logger.info("{} fetched current user in {} seconds".format(self.call_id, time() - start_time))

        # Get the last 200 activities and aggregate them by type, with order.
        user_domain_id = current_user.domain_id
        user_ids = User.query.filter_by(domain_id=user_domain_id).values('id')
        logger.info("{} fetched domain IDs in {} seconds".format(self.call_id, time() - start_time))
        flattened_user_ids = [item for sublist in user_ids for item in sublist]
        logger.info("{} flattened domain IDs in {} seconds".format(self.call_id, time() - start_time))
        filters = [Activity.user_id.in_(flattened_user_ids)]

        if start_datetime:
            filters.append(Activity.added_time>=start_datetime)
        if end_datetime:
            filters.append(Activity.added_time<=end_datetime)

        activities = Activity.query.filter(*filters).order_by(Activity.added_time.desc()).limit(200)
        logger.info("{} fetched activities in {} seconds".format(
            self.call_id, time() - start_time)
        )

        aggregated_activities = []
        current_activity_count = 0
        aggregate_start, aggregate_end = datetime.today(), EPOCH

        for i, activity in enumerate(activities):
            if activity.added_time < aggregate_start:
                aggregate_start = activity.added_time
            if activity.added_time > aggregate_end:
                aggregate_end = activity.added_time

            current_activity_count += 1
            current_activity_type = activity.type
            if current_activity_type not in self.MESSAGES:
                logger.error('Given Campaign Type (%s) not found.' % current_activity_type)
                continue
            next_activity_type = activities[i + 1].type if (
                i < activities.count() - 1) else None  # None means last activity

            if current_activity_type != next_activity_type:  # next activity is new, or the very last one, so aggregate these ones
                activity_aggregate = {}
                activity_aggregate['count'] = current_activity_count
                activity_aggregate['readable_text'] = self.activity_text(activity,
                                                                         activity_aggregate['count'],
                                                                         current_user)
                activity_aggregate['image'] = self.MESSAGES[activity.type][2]
                activity_aggregate['start'] = aggregate_start.strftime(DATE_FORMAT)
                activity_aggregate['end'] = aggregate_end.strftime(DATE_FORMAT)

                aggregate_start, aggregate_end = datetime.today(), EPOCH
                aggregated_activities.append(activity_aggregate)
                if len(aggregated_activities) == limit:  # if we've got enough activity groups, quit
                    break

                current_activity_count = 0

        logger.info("{} finished making readable in {} seconds".format(self.call_id, time() - start_time))
        return aggregated_activities

    def activity_text(self, activity, count, current_user):
        if activity.user_id != current_user.id:
            username = User.query.filter_by(id=activity.user_id).value('firstName')
        else:
            username = "You"

        params = json.loads(activity.params) if activity.params else dict()
        # See GET-1946. JSON loads is returning unicode objects for some entries stored in DB.
        if isinstance(params, unicode):
            params = json.loads(params)

        params['username'] = username

        format_strings = self.MESSAGES.get(activity.type)
        if not format_strings:
            format_string = "No message for activity type %s" % activity.type
        elif not count or count == 1:  # one single activity
            format_string = format_strings[0]
        else:  # many activities
            format_string = format_strings[1]
            params['count'] = count

        # If format_string has a param not in params, set it to unknown
        for param in re.findall(self._check_format_string_regexp, format_string):
            if not params.get(param):
                params[param] = 'unknown'
            if param == 'campaign_type' and params[param].lower() not in CampaignUtils.WITH_ARTICLE_AN:
                format_string = format_string.replace("an", "a")

        formatted_string = format_string % params

        if 'You has' in formatted_string:
            # To fix 'You has joined'
            formatted_string = formatted_string.replace('You has', 'You have')
        elif "You's" in formatted_string:
            # To fix "You's recurring campaign has expired"
            formatted_string = formatted_string.replace("You's", "Your")

        return formatted_string
