"""Activities API for getting activities for a user's domain or posting new activities
   to the database.
"""
from app_common.common.activity_service_config import ActivityServiceKeys

__author__ = 'erikfarmer'
# stdlib
from datetime import datetime
import json
import re
# framework specific
from flask import Blueprint
from flask import jsonify
from flask import request

# application specific
from activity_service.activities_app import db
from activity_service.common.models.user import User
from activity_service.common.routes import ActivityApi
from activity_service.common.models.misc import Activity
from activity_service.common.utils.auth_utils import require_oauth

ISO_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'
POSTS_PER_PAGE = 20
mod = Blueprint('activities_api', __name__)


@mod.route(ActivityApi.ACTIVITIES_PAGE, methods=['GET'])
@require_oauth()
def get_activities(page):
    """
    :param int page: Page used in pagination for GET requests.
    :return: JSON formatted pagination response or message notifying creation status.
    """
    valid_user_id = request.user.id
    is_aggregate_request = request.args.get('aggregate') == '1'
    tam = TalentActivityManager()
    if is_aggregate_request:
        return jsonify({'activities': tam.get_recent_readable(valid_user_id)})
    else:
        request_start_time = request_end_time = None
        if request.args.get('start_time'): request_start_time = datetime.strptime(
            request.args.get('start_time'), ISO_FORMAT)
        if request.args.get('end_time'): request_end_time = datetime.strptime(
            request.args.get('end_time'), ISO_FORMAT)
        post_qty = request.args.get('post_qty') if request.args.get('post_qty') else POSTS_PER_PAGE
        try:
            request_page = int(page)
        except ValueError:
            return jsonify({'error': {'message': 'page parameter must be an integer'}}), 400
        return json.dumps(tam.get_activities(user_id=valid_user_id, post_qty=post_qty,
                                             start_datetime=request_start_time,
                                             end_datetime=request_end_time, page=request_page))


@mod.route(ActivityApi.ACTIVITIES, methods=['POST'])
@require_oauth()
def post_activity():
    valid_user_id = request.user.id
    content = request.json
    return create_activity(valid_user_id, content.get('type'), content.get('source_table'),
                           content.get('source_id'), content.get('params'))


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
        params=json.dumps(params) if params else None
    )
    try:
        db.session.add(activity)
        db.session.commit()
        return json.dumps({'activity': {'id': activity.id}}), 200
    except:
        # TODO logging
        return json.dumps({'error': 'There was an error saving your log entry'}), 500


class TalentActivityManager(object):
    """API class for ActivityService."""
    # params=dict(id, formattedName, sourceProductId, client_ip (if widget))
    CANDIDATE_CREATE_WEB = ActivityServiceKeys.CANDIDATE_CREATE_WEB
    CANDIDATE_CREATE_CSV = ActivityServiceKeys.CANDIDATE_CREATE_CSV
    CANDIDATE_CREATE_WIDGET = ActivityServiceKeys.CANDIDATE_CREATE_WIDGET
    CANDIDATE_CREATE_MOBILE = ActivityServiceKeys.CANDIDATE_CREATE_MOBILE  # TODO add in
    CANDIDATE_UPDATE = ActivityServiceKeys.CANDIDATE_UPDATE
    CANDIDATE_DELETE = ActivityServiceKeys.CANDIDATE_DELETE

    # params=dict(id, name)
    CAMPAIGN_CREATE = ActivityServiceKeys.CAMPAIGN_CREATE
    CAMPAIGN_DELETE = ActivityServiceKeys.CAMPAIGN_DELETE
    CAMPAIGN_SEND = ActivityServiceKeys.CAMPAIGN_SEND  # also has num_candidates
    CAMPAIGN_EXPIRE = ActivityServiceKeys.CAMPAIGN_EXPIRE  # recurring campaigns only # TODO implement
    CAMPAIGN_PAUSE = ActivityServiceKeys.CAMPAIGN_PAUSE
    CAMPAIGN_RESUME = ActivityServiceKeys.CAMPAIGN_RESUME

    # params=dict(name, is_smartlist=0/1)
    SMARTLIST_CREATE = ActivityServiceKeys.SMARTLIST_CREATE
    SMARTLIST_DELETE = ActivityServiceKeys.SMARTLIST_DELETE
    SMARTLIST_ADD_CANDIDATE = ActivityServiceKeys.SMARTLIST_ADD_CANDIDATE  # also has formattedName (of candidate) and candidateId
    SMARTLIST_REMOVE_CANDIDATE = ActivityServiceKeys.SMARTLIST_REMOVE_CANDIDATE  # also has formattedName and candidateId

    USER_CREATE = ActivityServiceKeys.USER_CREATE  # params=dict(firstName, lastName)

    WIDGET_VISIT = ActivityServiceKeys.WIDGET_VISIT  # params=dict(client_ip)

    # TODO implement frontend + backend
    NOTIFICATION_CREATE = ActivityServiceKeys.NOTIFICATION_CREATE  # when we want to show the users a message

    # params=dict(candidateId, campaign_name, candidate_name)
    CAMPAIGN_EMAIL_SEND = ActivityServiceKeys.CAMPAIGN_EMAIL_SEND
    CAMPAIGN_EMAIL_OPEN = ActivityServiceKeys.CAMPAIGN_EMAIL_OPEN
    CAMPAIGN_EMAIL_CLICK = ActivityServiceKeys.CAMPAIGN_EMAIL_CLICK
    RSVP_EVENT = ActivityServiceKeys.RSVP_EVENT
    # RSVP_MEETUP = 24

    EVENT_CREATE = ActivityServiceKeys.EVENT_CREATE
    EVENT_DELETE = ActivityServiceKeys.EVENT_DELETE
    EVENT_UPDATE = ActivityServiceKeys.EVENT_UPDATE

    MESSAGES = {
        RSVP_EVENT: ("%(firstName)s  %(lastName)s responded <b>%(response)s</b> "
                     "on %(creator)s 's event <b>'%(eventTitle)s'</b> %(img)s",
                     "%(firstName)s  %(lastName)s responded <b>%(response)s<b>"
                     " on event '%(eventTitle)s'",
                     "candidate.png"),

        EVENT_CREATE:      ("%(firstName)s  %(lastName)s created an event <b>%(eventTitle)s",
                            "%(firstName)s  %(lastName)s created %(count)s events.</b>",
                            "event.png"),

        EVENT_DELETE:      ("%(firstName)s  %(lastName)s deleted an event <b>%(eventTitle)s",
                            "%(firstName)s  %(lastName)s deleted %(count)s events.</b>",
                            "event.png"),

        EVENT_UPDATE:      ("%(firstName)s  %(lastName)s updated an event <b>%(eventTitle)s.",
                            "%(firstName)s  %(lastName)s updated %(count)s events.</b>",
                            "event.png"),

        CANDIDATE_CREATE_WEB: ("%(username)s uploaded resume of candidate %(formattedName)s",
                               "%(username)s uploaded %(count)s candidate resumes", "candidate.png"),
        CANDIDATE_CREATE_CSV: ("%(username)s imported candidate %(formattedName)s via spreadsheet",
                               "%(username)s imported %(count)s candidates via spreadsheet", "candidate.png"),
        CANDIDATE_CREATE_WIDGET: (
            "Candidate %(formattedName)s joined via widget", "%(count)s candidates joined via widget", "widget.png"),
        CANDIDATE_CREATE_MOBILE: ("%(username)s added candidate %(formattedName)s via mobile",
                                  "%(username)s added %(count)s candidates via mobile", "candidate.png"),
        CANDIDATE_UPDATE: (
            "%(username)s updated candidate %(formattedName)s", "%(username)s updated %(count)s candidates",
            "candidate.png"),
        CANDIDATE_DELETE: (
            "%(username)s deleted candidate %(formattedName)s", "%(username)s deleted %(count)s candidates",
            "candidate.png"),

        CAMPAIGN_CREATE: (
            "%(username)s created a campaign: %(name)s", "%(username)s created %(count)s campaigns", "campaign.png"),
        CAMPAIGN_DELETE: (
            "%(username)s deleted a campaign: %(name)s", "%(username)s deleted %(count)s campaigns", "campaign.png"),
        CAMPAIGN_SEND: (
            "Campaign %(name)s was sent to %(num_candidates)s candidates", "%(count)s campaigns were sent out",
            "campaign.png"),
        CAMPAIGN_EXPIRE: ("%(username)s's recurring campaign %(name)s has expired",
                          "%(count)s recurring campaigns of %(username)s have expired", "campaign.png"),  # TODO
        CAMPAIGN_PAUSE: (
            "%(username)s paused campaign %(name)s", "%(username)s paused %(count)s campaigns", "campaign.png"),
        CAMPAIGN_RESUME: (
            "%(username)s resumed campaign %(name)s", "%(username)s resumed %(count)s campaigns", "campaign.png"),

        SMARTLIST_CREATE: (
            "%(username)s created list %(name)s", "%(username)s created %(count)s lists", "smartlist.png"),
        SMARTLIST_DELETE: (
            "%(username)s deleted list %(name)s", "%(username)s deleted %(count)s lists", "smartlist.png"),
        SMARTLIST_ADD_CANDIDATE: (
            "%(formattedName)s was added to list %(name)s", "%(count)s candidates were added to list %(name)s",
            "smartlist.png"),
        SMARTLIST_REMOVE_CANDIDATE: (
            "%(formattedName)s was removed from list %(name)s", "%(count)s candidates were removed from list %(name)s",
            "smartlist.png"),
        USER_CREATE: ("%(username)s has joined", "%(count)s users have joined", "notification.png"),
        WIDGET_VISIT: ("Widget was visited", "Widget was visited %(count)s times", "widget.png"),
        NOTIFICATION_CREATE: (
            "You received an update notification", "You received %(count)s update notifications", "notification.png"),

        CAMPAIGN_EMAIL_SEND: ("%(candidate_name)s received email of campaign %(campaign_name)s",
                              "%(count)s candidates received email of campaign %(campaign_name)s", "campaign.png"),
        CAMPAIGN_EMAIL_OPEN: ("%(candidate_name)s opened email of campaign %(campaign_name)s",
                              "%(count)s candidates opened email of campaign %(campaign_name)s", "campaign.png"),
        CAMPAIGN_EMAIL_CLICK: ("%(candidate_name)s clicked email of campaign %(campaign_name)s",
                               "Campaign %(campaign_name)s was clicked %(count)s times", "campaign.png")
    }

    def __init__(self):
        self._check_format_string_regexp = re.compile(r'%\((\w+)\)s')

    def get_activities(self, user_id, post_qty, start_datetime=None, end_datetime=None, page=1):
        """Method for retrieving activity logs based on a domain ID that is extraced via an
           authenticated user ID.
        :param int user_id: ID of the authenticated user.
        :param datetime|None start_datetime: Optional datetime object for query filters.
        :param datetime|None end_datetime: Optional datetime object for query filters.
        :param int page: Pagination start.
        :return: JSON encoded SQL-Alchemy.pagination response.
        """
        user_domain_id = User.query.filter_by(id=user_id).value('domainId')
        user_ids = User.query.filter_by(domain_id=user_domain_id).values('id')
        flattened_user_ids = [item for sublist in user_ids for item in sublist]
        filters = [Activity.user_id.in_(flattened_user_ids)]
        if start_datetime: filters.append(Activity.added_time > start_datetime)
        if end_datetime: filters.append(Activity.added_time < end_datetime)
        activities = Activity.query.filter(*filters).paginate(page, post_qty, False)
        activities_reponse = {
            'total_count': activities.total,
            'items': [{
                          'params': json.loads(a.params),
                          'source_table': a.source_table,
                          'source_id': a.source_id,
                          'type': a.type,
                          'user_id': a.user_id
                      }
                      for a in activities.items
                      ]
        }
        return activities_reponse

    # Like 'get' but gets the last N consecutive activity types. can't use GROUP BY because it doesn't respect ordering.
    def get_recent_readable(self, user_id, limit=3):
        current_user = User.query.filter_by(id=user_id).first()
        #
        # # Get the last 25 activities and aggregate them by type, with order.
        user_domain_id = current_user.domain_id
        user_ids = User.query.filter_by(domain_id=user_domain_id).values('id')
        flattened_user_ids = [item for sublist in user_ids for item in sublist]
        filters = [Activity.user_id.in_(flattened_user_ids)]
        activities = Activity.query.filter(*filters)  # TODO add limit.

        aggregated_activities = []
        current_activity_count = 0

        for i, activity in enumerate(activities):
            current_activity_count += 1
            current_activity_type = activity.type
            next_activity_type = activities[i + 1].type if (
                i < activities.count() - 1) else None  # None means last activity

            if current_activity_type != next_activity_type:  # next activity is new, or the very last one, so aggregate these ones
                activity_aggregate = {}
                activity_aggregate['count'] = current_activity_count
                activity_aggregate['readable_text'] = self._activity_text(activity,
                                                                          activity_aggregate['count'], current_user)
                activity_aggregate['image'] = self.MESSAGES[activity.type][2]

                aggregated_activities.append(activity_aggregate)
                if len(aggregated_activities) == limit:  # if we've got enough activity groups, quit
                    break

                current_activity_count = 0

        return aggregated_activities

    def _activity_text(self, activity, count, current_user):
        if activity.user_id != current_user.id:
            username = User.query.filter_by(id=activity.user_id).value('firstName')
        else:
            username = "You"

        params = json.loads(activity.params) if activity.params else dict()
        params['username'] = username

        format_strings = self.MESSAGES.get(activity.type)
        if not format_strings:
            format_string = "No message for activity type %s" % activity.type
        elif not count or count == 1:  # one single activity
            format_string = format_strings[0]
            if 'You has' in format_string:
                format_string = format_string.replace('You has', 'You have')  # To fix 'You has joined'
            elif "You's" in format_string:  # To fix "You's recurring campaign has expired"
                format_string = format_string.replace("You's", "Your")
        else:  # many activities
            format_string = format_strings[1]
            params['count'] = count

        # If format_string has a param not in params, set it to unknown
        for param in re.findall(self._check_format_string_regexp, format_string):
            if not params.get(param):
                params[param] = 'unknown'

        return format_string % params
