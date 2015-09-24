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
from activities_app.models import Activity
from activities_app.models import db

ISO_FORMAT = '%Y-%m-%d %H:%M'
POSTS_PER_PAGE = 20
mod = Blueprint('activities_api', __name__)


@mod.route('/activities/', defaults={'page': None}, methods=['POST'])
@mod.route('/activities/<page>', methods=['GET'])
def get_activities(page=None):
    try:
        oauth_token = request.headers['Authorization']
    except KeyError:
        return jsonify({'error': 'Invalid query params'}), 400
    req = urllib2.Request(app.config['OAUTH_SERVER_URI'], headers={'Authorization': oauth_token})
    try:
        response = urllib2.urlopen(req)
    except urllib2.HTTPError:
        return jsonify({'error': 'Invalid query params'}), 400
    auth_response = response.read()
    json_response = json.loads(auth_response)
    if not json_response.get('user_id'):
        return jsonify({'error': 'Invalid query params'}), 400
    valid_user_id = json_response.get('user_id')
    taAPI = TalentActivityAPI()
    if request.method == 'GET':
        request_startTime = request_endTime = None
        if request.form.get('start'): request_startTime = datetime.strptime(request.form.get('start'), ISO_FORMAT)
        if request.form.get('end'): request_startTime = datetime.strptime(request.form.get('end'), ISO_FORMAT)
        return taAPI.get(user_id=valid_user_id, start_datetime=request_startTime, end_datetime=request_endTime, page=int(page))
    elif request.method == 'POST':
        taAPI.create(valid_user_id, request.form.get('type'), request.form.get('sourceTable'),
                     request.form.get('sourceId'), request.form.get('params'))
        return 'Post Created', 200
    else:
        return 'Method not Allowed', 405


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

    def get(self, user_id, start_datetime=None, end_datetime=None, page=1):
        filters = [Activity.userId == user_id]
        if start_datetime: filters.append(Activity.addedTime > start_datetime)
        if end_datetime: filters.append(Activity.addedTime < end_datetime)
        # activities = db.session.query(Activity).filter(*filters)
        activities = Activity.query.filter(*filters).paginate(page, POSTS_PER_PAGE, False)
        next_page = page + 1 if activities.has_next else None
        prev_page = page - 1 if activities.has_prev else None
        activities_reponse = {
            'has_prev': activities.has_prev,
            'prev_page': prev_page,
            'has_next': activities.has_next,
            'next_page': next_page,
            'items': [a.params for a in activities.items]
        }
        return json.dumps(activities_reponse)


    def create(self, user_id, type, source_table=None, source_id=None, params=dict()):

        activity = Activity(
            userId=int(user_id),
            type=type,
            sourceTable=source_table,
            sourceId=source_id,
            params=json.dumps(params) if params else None
        )
        db.session.add(activity)
        db.session.commit()
