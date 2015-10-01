"""Activities API for getting activities for a user's domain or posting new activities
   to the database.
"""
__author__ = 'erikfarmer'

#stdlib
from datetime import datetime
import json
import re
import urllib2

#third party packages
import requests

#framework specific
from flask import Blueprint
from flask import current_app as app
from flask import jsonify
from flask import request

#application specific
from activities_service.models.db import db
from activities_service.models.user import User
from activities_service.utils.auth_utils import authenticate_oauth_user

ISO_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'
POSTS_PER_PAGE = 20
mod = Blueprint('activities_api', __name__)


@mod.route('/activities/', defaults={'page': None}, methods=['POST'])
@mod.route('/activities/<page>', methods=['GET'])
def activities(page=None):
    """Authenticate endpoint requests and then properly route then to the retrieve or creation
       functions.
    :param page: (int) Page used in pagination for GET requests.
    :return: JSON formatted pagination response or message notifying creation status.
    """
    # try:
    #     oauth_token = request.headers['Authorization']
    # except KeyError:
    #     return jsonify({'error': {'message':'No Authorization set'}}), 400
    # r = requests.get(app.config['OAUTH_SERVER_URI'], headers={'Authorization': oauth_token})
    # if r.status_code != 200:
    #     return jsonify({'error': {'code': 3, 'message': 'Not authorized'}}), 401
    # valid_user_id = json.loads(r.text).get('user_id')
    # if not valid_user_id:
    #     return jsonify({'error': {'code': 25,
    #                               'message': "Access token is invalid. Please refresh your token"}}), 400
    authentication_result = authenticate_oauth_user(request)
    error_result = authentication_result.get('error')
    if error_result:
        return jsonify({'error': {'code':error_result.get('code'),
                                  'message': error_result.get('message')}}), error_result.get('http_code', 400)
    is_aggregate_request = request.args.get('aggregate') == '1'
    tam = TalentActivityManager()
    if request.method == 'GET' and is_aggregate_request:
        return jsonify({'activities': tam.get_recent_readable(valid_user_id)})
    elif request.method == 'GET': # Checking for method again is to avoid nesting.
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
    elif request.method == 'POST':
        return tam.create_activity(valid_user_id, request.form.get('type'),
                                   request.form.get('source_table'), request.form.get('source_id'),
                                   request.form.get('params'))
    else:
        return jsonify({'error': {'code': 21, 'message': 'Page not found'}}), 405


class TalentActivityManager(object):
    """API class for ActivityService."""
    # params=dict(id, formattedName, sourceProductId, client_ip (if widget))
    CANDIDATE_CREATE_WEB = 1
    CANDIDATE_CREATE_CSV = 18
    CANDIDATE_CREATE_WIDGET = 19
    CANDIDATE_CREATE_MOBILE = 20  # TODO add in
    CANDIDATE_UPDATE = 2
    CANDIDATE_DELETE = 3

    # params=dict(id, name)
    CAMPAIGN_CREATE = 4
    CAMPAIGN_DELETE = 5
    CAMPAIGN_SEND = 6  # also has num_candidates
    CAMPAIGN_EXPIRE = 7  # recurring campaigns only # TODO implement
    CAMPAIGN_PAUSE = 21
    CAMPAIGN_RESUME = 22

    # params=dict(name, is_smartlist=0/1)
    SMARTLIST_CREATE = 8
    SMARTLIST_DELETE = 9
    SMARTLIST_ADD_CANDIDATE = 10  # also has formattedName (of candidate) and candidateId
    SMARTLIST_REMOVE_CANDIDATE = 11  # also has formattedName and candidateId

    USER_CREATE = 12  # params=dict(firstName, lastName)

    WIDGET_VISIT = 13  # params=dict(client_ip)

    # TODO implement frontend + backend
    NOTIFICATION_CREATE = 14  # when we want to show the users a message

    # params=dict(candidateId, campaign_name, candidate_name)
    CAMPAIGN_EMAIL_SEND = 15
    CAMPAIGN_EMAIL_OPEN = 16
    CAMPAIGN_EMAIL_CLICK = 17
    RSVP_EVENT = 23
    # RSVP_MEETUP = 24

    MESSAGES = {
        RSVP_EVENT: ("%(firstName)s  %(lastName)s responded <b>%(response)s</b> "
                     "on %(creator)s 's event <b>'%(eventTitle)s'</b> %(img)s",
                     "%(firstName)s  %(lastName)s responded <b>%(response)s<b>"
                     " on event '%(eventTitle)s'",
                     "candidate.png"),
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
        :param user_id: (int) ID of the authenticated user.
        :param start_datetime: (object) Optional datetime object for query filters.
        :param end_datetime: (object) Optional datetime object for query filters.
        :param page: (int) Pagination start.
        :return: JSON encoded SQL-Alchemy.pagination response.
        """
        user_domain_id = User.query.filter_by(id=user_id).value('domainId')
        user_ids = User.query.filter_by(domainId=user_domain_id).values('id')
        flattened_user_ids = [item for sublist in user_ids for item in sublist]
        filters = [Activity.userId.in_(flattened_user_ids)]
        if start_datetime: filters.append(Activity.addedTime > start_datetime)
        if end_datetime: filters.append(Activity.addedTime < end_datetime)
        activities = Activity.query.filter(*filters).paginate(page, post_qty, False)
        activities_reponse = {
            'total_count': activities.total,
            'items': [{
                'params': a.params,
                'source_table': a.sourceTable,
                'source_id': a.sourceId,
                'type': a.type,
                'user_id': a.userId
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
        user_domain_id = current_user.domainId
        user_ids = User.query.filter_by(domainId=user_domain_id).values('id')
        flattened_user_ids = [item for sublist in user_ids for item in sublist]
        filters = [Activity.userId.in_(flattened_user_ids)]
        activities = Activity.query.filter(*filters) # TODO add limit.

        aggregated_activities = []
        current_activity_count = 0

        # user_id_to_name_dict = self._user_id_to_name_dict(current_user.domainId)

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
        if activity.userId != current_user.id:
            username = User.query.filter_by(id=activity.userId).value('firstName')
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
                format_string = format_string.replace('you has', 'you have')  # To fix 'You has joined'
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


    def create_activity(self, user_id, type_, source_table=None, source_id=None, params=dict()):
        """Method for creating a DB entry in the activity table.
        :param user_id: (int) ID of the authenticated user.
        :param type: (int) Integer corresponding to TalentActivityAPI attributes.
        :param source_table: (string) String representing the DB table the activity relates to.
        :param source_id: (int) Integer of the source_table's ID for entered specific activity.
        :param params: (dict) Dictionary of created/updated source_table attributes.
        :return: HTTP Response
        """
        activity = Activity(
            userId=int(user_id),
            type=type_,
            sourceTable=source_table,
            sourceId=source_id,
            params=json.dumps(params) if params else None
        )
        try:
            db.session.add(activity)
            db.session.commit()
            return json.dumps({'activity': {'id':activity.id}}), 200
        except:
            # TODO logging
            return json.dumps({'error': 'There was an error saving your log entry'}), 500
