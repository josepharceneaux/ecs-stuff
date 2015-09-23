__author__ = 'erikfarmer'

#stdlib
from datetime import datetime
import json
from math import ceil
import re
import urllib2

#framwork specific
from flask import Blueprint
from flask import current_app as app
from flask import jsonify
from flask import request

#application specific
from activities_app import db
from activities_app.models import Activity

ISO_FORMAT = '%Y-%m-%d %H:%M'

mod = Blueprint('activities_api', __name__)


@mod.route('/activities', methods=['GET', 'POST'])
def get_activities():
    taAPI = TalentActivityAPI()
    request_startTime = request_endTime = None
    if request.form.get('start'): request_startTime = datetime.strptime(request.form.get('start'), ISO_FORMAT)
    if request.form.get('end'): request_startTime = datetime.strptime(request.form.get('end'), ISO_FORMAT)
    return taAPI.get(start_datetime=request_startTime, end_datetime=request_endTime)

# class TalentPagination(Pagination):
#     def generate_links(self):
#         self.backward = self._generate_a('<<', self.current - self.display_count if self.current else None)
#         self.forward = self._generate_a('>>',
#                                         self.current + self.display_count if self.total_results > self.current + self.display_count else None)
#         self.location = 'Showing %d to %d out of %d activities' % (
#         self.current + 1, self.current + self.num_results, self.total_results)
#         return self.backward, self.forward, self.location
#
#     def _generate_a(self, title, p=None):
#         if p:
#             return A(title, _class='btn', _href=URL(r=self.r, args=self.r.args, vars={'p': p}))
#         else:
#             return A(title, _class='btn', _disabled='disabled')


class Pagination(object):

    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num


class TalentActivityAPI(object):
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

    NOTIFICATION_CREATE = 14  # when we want to show the users a message # TODO implement frontend + backend

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

    def get(self, user_ids=None, start_datetime=None, end_datetime=None, limit=0):
        try:
            oauth_token = request.headers['Authorization']
        except KeyError:
            return jsonify({'error': 'Invalid query params'}), 400
        req = urllib2.Request(app.config['OAUTH_SERVER_URI'], headers={'Authorization': oauth_token})
        try:
            response = urllib2.urlopen(req)
        except urllib2.HTTPError:
            return jsonify({'error': 'Invalid query params'}), 400
        page = response.read()
        json_response = json.loads(page)
        if not json_response.get('user_id'):
            return jsonify({'error': 'Invalid query params'}), 400

        valid_user_id = json_response.get('user_id')
        filters = [Activity.userId == valid_user_id]
        if start_datetime: filters.append(Activity.addedTime > start_datetime)
        if end_datetime: filters.append(Activity.addedTime <= end_datetime)
        activities = db.session.query(Activity).filter(*filters)
        return json.dumps([a.params for a in activities])
        # user_id_to_name_dict = self._user_id_to_name_dict(current_user.domainId)
        #
        # query = (db.activity.userId.belongs(user_ids))
        # if start_datetime:
        #     query &= (db.activity.addedTime > start_datetime)
        # if end_datetime:
        #     query &= (db.activity.addedTime < end_datetime)
        #
        # paginate = TalentPagination(db, query, orderby=(~db.activity.addedTime), display_count=limit, cache=None,
        #                             r=current.request, res=current.response)
        # activities = paginate.get_set(set_links=True)
        #
        # for activity in activities:
        #     activity['readable_text'] = self._activity_text(activity, 1, current_user=current_user,
        #                                                     user_id_to_name_dict=user_id_to_name_dict)
        #
        # return activities

    # Like 'get' but gets the last N consecutive activity types. can't use GROUP BY because it doesn't respect ordering.
    # def get_recent_readable(self, user_ids, limit=3):
    #     current_user = current.auth.user
    #
    #     # Get the last 25 activities and aggregate them by type, with order.
    #     db = current.db
    #     activities = db(db.activity.userId.belongs(user_ids)).select(orderby=(~db.activity.addedTime), limitby=(0, 25))
    #
    #     aggregated_activities = []
    #     current_activity_count = 0
    #
    #     user_id_to_name_dict = self._user_id_to_name_dict(current_user.domainId)
    #
    #     for i, activity in enumerate(activities):
    #         current_activity_count += 1
    #         current_activity_type = activity.type
    #         next_activity_type = activities[i + 1].type if (
    #         i < len(activities) - 1) else None  # None means last activity
    #
    #         if current_activity_type != next_activity_type:  # next activity is new, or the very last one, so aggregate these ones
    #             activity['count'] = current_activity_count
    #             activity['readable_text'] = self._activity_text(activity, activity['count'], current_user,
    #                                                             user_id_to_name_dict)
    #             activity['image'] = self.MESSAGES[activity.type][2]
    #
    #             aggregated_activities.append(activity)
    #             if len(aggregated_activities) == limit:  # if we've got enough activity groups, quit
    #                 break
    #
    #             current_activity_count = 0
    #
    #     return aggregated_activities

    # def _activity_text(self, activity, count, current_user, user_id_to_name_dict):
    #     if activity.userId != current_user.id:
    #         username = user_id_to_name_dict.get(activity.userId)
    #     else:
    #         username = "You"
    #
    #     params = json.loads(activity.params) if activity.params else dict()
    #     params['username'] = username
    #
    #     format_strings = self.MESSAGES.get(activity.type)
    #     if not format_strings:
    #         format_string = "No message for activity type %s" % activity.type
    #     elif not count or count == 1:  # one single activity
    #         format_string = format_strings[0]
    #         if 'You has' in format_string:
    #             format_string = format_string.replace('you has', 'you have')  # To fix 'You has joined'
    #         elif "You's" in format_string:  # To fix "You's recurring campaign has expired"
    #             format_string = format_string.replace("You's", "Your")
    #     else:  # many activities
    #         format_string = format_strings[1]
    #         params['count'] = count
    #
    #     # If format_string has a param not in params, set it to unknown
    #     for param in re.findall(self._check_format_string_regexp, format_string):
    #         if not params.get(param):
    #             params[param] = 'unknown'
    #
    #     return format_string % params
    #
    # def _user_id_to_name_dict(self, domain_id):
    #     db = current.db
    #     cache = current.cache
    #     user_id_to_name = dict()
    #     users = db(db.user.domainId == domain_id).select(db.user.domainId, db.user.id, db.user.firstName,
    #                                                      db.user.lastName, db.user.email, cache=(cache.ram, 120))
    #     for user in users:
    #         user_id_to_name[user.id] = user.name()
    #     return user_id_to_name

    # def create(self, user_id, type, source_table=None, source_id=None, params=dict()):
    #     db = current.db
    #
    #     return db.activity.insert(
    #         userId=user_id,
    #         type=type,
    #         sourceTable=source_table,
    #         sourceId=source_id,
    #         params=json.dumps(params) if params else None
    #     )
