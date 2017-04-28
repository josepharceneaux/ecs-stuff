from activity_service.app import db
from activity_service.common.models.misc import Activity
from activity_service.common.models.user import User
from activity_service.common.campaign_services.campaign_utils import CampaignUtils
import re
import json
from datetime import datetime
from time import time
from sqlalchemy import not_
from activity_service.app import logger

EXCLUSIONS = (15, 16, 17, 1201, 1202, 1203)
EPOCH = datetime(year=1970, month=1, day=1)
DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'
TIMEOUT_THRESHOLD = 5


class TalentActivityManager(object):
    """API class for ActivityService."""
    # TODO Make these dicts in v2 because properties/keys are more betterer than indexes.

    _check_format_string_regexp = re.compile(r'%\((\w+)\)s')

    MESSAGES = {
        Activity.MessageIds.RSVP_EVENT: (
            "<b>%(firstName)s %(lastName)s</b> responded %(response)s on <b>%(creator)s's</b> "
            "event: <b>'%(eventTitle)s'</b>", "<b>%(firstName)s %(lastName)s<b> responded %(response)s on event: "
            "'<b>%(eventTitle)s</b>'", "candidate.png"),
        Activity.MessageIds.EVENT_CREATE: ("<b>%(username)s</b> created an event: <b>%(event_title)s</b>",
                                           "<b>%(username)s</b> created %(count)s events.</b>", "event.png"),
        Activity.MessageIds.EVENT_DELETE: ("<b>%(username)s</b> deleted an event <b>%(event_title)s</b>",
                                           "<b>%(username)s</b> deleted %(count)s events.", "event.png"),
        Activity.MessageIds.EVENT_UPDATE: ("<b>%(username)s</b> updated an event <b>%(event_title)s</b>.",
                                           "<b>%(username)s</b> updated %(count)s events.", "event.png"),
        Activity.MessageIds.CANDIDATE_CREATE_WEB:
        ("<b>%(username)s</b> uploaded the resume of candidate <b>%(formattedName)s</b>",
         "<b>%(username)s</b> uploaded the resume(s) of %(count)s candidate(s)", "candidate.png"),
        Activity.MessageIds.CANDIDATE_CREATE_CSV:
        ("<b>%(username)s</b> imported the candidate <b>%(formattedName)s</b> via spreadsheet",
         "<b>%(username)s</b> imported %(count)s candidate(s) via spreadsheet", "candidate.png"),
        Activity.MessageIds.CANDIDATE_CREATE_WIDGET: ("Candidate <b>%(formattedName)s</b> joined via widget",
                                                      "%(count)s candidate(s) joined via widget", "widget.png"),
        Activity.MessageIds.CANDIDATE_CREATE_MOBILE: (
            "<b>%(username)s</b> added the candidate <b>%(formattedName)s</b> via mobile",
            "<b>%(username)s</b> added %(count)s candidate(s) via mobile", "candidate.png"),
        Activity.MessageIds.CANDIDATE_UPDATE: ("<b>%(username)s</b> updated the candidate <b>%(formattedName)s</b>",
                                               "<b>%(username)s</b> updated %(count)s candidates", "candidate.png"),
        Activity.MessageIds.CANDIDATE_DELETE: ("<b>%(username)s</b> deleted the candidate <b>%(formattedName)s</b>",
                                               "<b>%(username)s</b> deleted %(count)s candidates", "candidate.png"),

        # Candidate De-Duping Activities
        Activity.MessageIds.CANDIDATE_AUTO_MERGED: ("Candidate <b>%(formatted_name)s</b> was automatically merged with "
                                                    "a duplicated profile.",
                                                    "%(count)s candidates were updated", "candidate.png"),
        Activity.MessageIds.CANDIDATE_USER_MERGED: ("<b>%(username)s</b> (User) merged candidate "
                                                    "<b>%(formatted_name)s</b> with a duplicated profiles.",
                                                    "%(count)s candidates were updated", "candidate.png"),
        Activity.MessageIds.CANDIDATE_SENT_TO_MERGE_HUB: ("<b>%(formatted_name)s</b> was identified as a possible "
                                                          "match. View in <a href='/candidates/mergehub'>Merge Hub</a> "
                                                          "to resolve.",
                                                          "%(count)s candidates were updated", "candidate.png"),
        Activity.MessageIds.CAMPAIGN_CREATE: (
            "<b>%(username)s</b> created an %(campaign_type)s campaign: <b>%(name)s</b>",
            "<b>%(username)s</b> created %(count)s campaigns", "campaign.png"),
        Activity.MessageIds.CAMPAIGN_DELETE: (
            "<b>%(username)s</b> deleted an %(campaign_type)s campaign: <b>%(name)s</b>",
            "<b>%(username)s</b> deleted %(count)s campaign(s)", "campaign.png"),
        Activity.MessageIds.CAMPAIGN_SEND: (
            "%(campaign_type)s campaign <b>%(name)s</b> was sent to <b>%(num_candidates)s</b> candidate(s)",
            "%(count)s campaign(s) sent", "campaign.png"),
        Activity.MessageIds.CAMPAIGN_EXPIRE: ("<b>%(username)s's</b> recurring campaign <b>%(name)s</b> has expired",
                                              "%(count)s recurring campaign(s) of <b>%(username)s</b> have expired",
                                              "campaign.png"),
        Activity.MessageIds.CAMPAIGN_PAUSE: ("<b>%(username)s</b> paused the campaign <b>%(name)s</b>",
                                             "<b>%(username)s</b> paused %(count)s campaign(s)", "campaign.png"),
        Activity.MessageIds.CAMPAIGN_RESUME: ("<b>%(username)s</b> resumed campaign <b>%(name)s</b>",
                                              "<b>%(username)s</b> resumed %(count)s campaign(s)", "campaign.png"),
        Activity.MessageIds.SMARTLIST_CREATE: ("<b>%(username)s</b> created the list <b>%(name)s</b>",
                                               "<b>%(username)s</b> created %(count)s list(s)", "smartlist.png"),
        Activity.MessageIds.SMARTLIST_DELETE: ("<b>%(username)s</b> deleted the list: <b>%(name)s</b>",
                                               "<b>%(username)s</b> deleted %(count)s list(s)", "smartlist.png"),
        Activity.MessageIds.DUMBLIST_CREATE: ("<b>%(username)s</b> created a list: <b>%(name)s</b>.",
                                              "<b>%(username)s</b> created %(count)s list(s)", "dumblist.png"),
        Activity.MessageIds.DUMBLIST_DELETE: ("<b>%(username)s</b> deleted list <b>%(name)s</b>",
                                              "<b>%(username)s</b> deleted %(count)s list(s)", "dumblist.png"),
        Activity.MessageIds.SMARTLIST_ADD_CANDIDATE: ("<b>%(formattedName)s<b> was added to list <b>%(name)s</b>",
                                                      "%(count)s candidates were added to list <b>%(name)s</b>",
                                                      "smartlist.png"),
        Activity.MessageIds.SMARTLIST_REMOVE_CANDIDATE: (
            "<b>%(formattedName)s</b> was removed from the list <b>%(name)s</b>",
            "%(count)s candidates were removed from the list <b>%(name)s</b>", "smartlist.png"),
        Activity.MessageIds.PIPELINE_ADD_CANDIDATE: ("<b>%(formattedName)s<b> was added to pipeline <b>%(name)s</b>",
                                                     "%(count)s candidates were added to pipeline <b>%(name)s</b>",
                                                     "pipeline.png"),
        Activity.MessageIds.PIPELINE_REMOVE_CANDIDATE: (
            "<b>%(formattedName)s</b> was removed from the pipeline <b>%(name)s</b>",
            "%(count)s candidates were removed from the pipeline <b>%(name)s</b>", "pipeline.png"),
        Activity.MessageIds.USER_CREATE: ("<b>%(username)s</b> has joined", "%(count)s users have joined",
                                          "notification.png"),
        Activity.MessageIds.WIDGET_VISIT: ("Widget was visited", "Widget was visited %(count)s time(s)", "widget.png"),
        Activity.MessageIds.NOTIFICATION_CREATE: ("You received an update notification",
                                                  "You received %(count)s update notification(s)", "notification.png"),
        Activity.MessageIds.CAMPAIGN_EMAIL_SEND: (
            "<b>%(candidate_name)s</b> received an email from campaign <b>%(campaign_name)s</b>",
            "%(count)s candidate(s) received an email from campaign <b>%(campaign_name)s</b>", "campaign.png"),
        Activity.MessageIds.CAMPAIGN_EMAIL_OPEN: (
            "<b>%(candidate_name)s</b> opened an email from campaign <b>%(campaign_name)s</b>",
            "%(count)s candidates opened an email from campaign <b>%(campaign_name)s</b>", "campaign.png"),
        Activity.MessageIds.CAMPAIGN_EVENT_CLICK: (
            "<b>%(candidate_name)s</b> clicked on an email from event campaign <b>%(campaign_name)s</b>",
            "Event Campaign <b>%(campaign_name)s</b> was clicked %(count)s time(s)", "campaign.png"),
        Activity.MessageIds.CAMPAIGN_EVENT_SEND: (
            "<b>%(candidate_name)s</b> received an invite for <b>%(campaign_name)s</b>",
            "%(count)s candidate(s) received an invite for <b>%(campaign_name)s</b>", "campaign.png"),
        Activity.MessageIds.CAMPAIGN_EVENT_OPEN: (
            "<b>%(candidate_name)s</b> opened an email from event campaign <b>%(campaign_name)s</b>",
            "%(count)s candidates opened an email from event campaign <b>%(campaign_name)s</b>", "campaign.png"),
        Activity.MessageIds.CAMPAIGN_EMAIL_CLICK: (
            "<b>%(candidate_name)s</b> clicked on an email from campaign <b>%(campaign_name)s</b>",
            "Campaign <b>%(campaign_name)s</b> was clicked %(count)s time(s)", "campaign.png"),
        Activity.MessageIds.CAMPAIGN_SMS_SEND: (
            "SMS Campaign <b>%(campaign_name)s</b> has been sent to %(candidate_name)s.",
            "SMS Campaign <b>%(campaign_name)s</b> has been sent to %(candidate_name)s.", "campaign.png"),
        Activity.MessageIds.CAMPAIGN_SMS_CLICK: (
            "<b>%(candidate_name)s</b> clicked on the SMS Campaign <b>%(name)s</b>.",
            "<b>%(candidate_name)s</b> clicked on %(name)s.", "campaign.png"),
        Activity.MessageIds.CAMPAIGN_SMS_REPLY: (
            "<b>%(candidate_name)s</b> replied %(reply_text)s to the SMS campaign <b>%(campaign_name)s</b>.",
            "<b>%(candidate_name)s</b> replied '%(reply_text)s' on campaign %(campaign_name)s.", "campaign.png"),
        Activity.MessageIds.CAMPAIGN_SCHEDULE: (
            "<b>%(username)s</b> scheduled an %(campaign_type)s campaign: <b>%(campaign_name)s</b>.",
            "<b>%(username)s</b> scheduled an %(campaign_type)s campaign: <b>%(campaign_name)s</b>.", "campaign.png"),
        Activity.MessageIds.PIPELINE_CREATE: ("<b>%(username)s</b> created a pipeline: <b>%(name)s</b>.",
                                              "<b>%(username)s</b> created a pipeline: <b>%(name)s</b>.",
                                              "pipeline.png"),
        Activity.MessageIds.PIPELINE_DELETE: ("<b>%(username)s</b> deleted pipeline: <b>%(name)s</b>.",
                                              "<b>%(username)s</b> deleted pipeline: <b>%(name)s</b>.", "pipeline.png"),
        Activity.MessageIds.TALENT_POOL_CREATE: ("<b>%(username)s</b> created a Talent Pool: <b>%(name)s</b>.",
                                                 "<b>%(username)s</b> created a Talent Pool: <b>%(name)s</b>.",
                                                 "talent_pool.png"),
        Activity.MessageIds.TALENT_POOL_DELETE: ("<b>%(username)s</b> deleted Talent Pool: <b>%(name)s</b>.",
                                                 "<b>%(username)s</b> deleted Talent Pool: <b>%(name)s</b>.",
                                                 "talent_pool.png"),
        Activity.MessageIds.CAMPAIGN_PUSH_CREATE: ("<b>%(username)s</b> created a Push campaign: '%(campaign_name)s'",
                                                   "<b>%(username)s</b> created a Push campaign: '%(campaign_name)s'",
                                                   "campaign.png"),
        Activity.MessageIds.CAMPAIGN_PUSH_SEND: (
            "Push Campaign <b>%(campaign_name)s</b> has been sent to <b>%(candidate_name)s</b>.",
            "Push Campaign <b>%(campaign_name)s</b> has been sent to <b>%(candidate_name)s</b>.", "campaign.png"),
        Activity.MessageIds.CAMPAIGN_PUSH_CLICK: (
            "<b>%(candidate_name)s</b> clicked on Push Campaign <b>%(campaign_name)s</b>.",
            "<b>%(candidate_name)s</b> clicked on %(campaign_name)s.", "campaign.png"),
        Activity.MessageIds.CANDIDATE_DOCUMENT_UPLOADED: (
            "User %(user)s uploaded %(filename)s on %(candidate)s candidate's profile at %(time)s",
            "%(count)s Candidate Documents have been uploaded"
        ),
        Activity.MessageIds.CANDIDATE_DOCUMENT_DELETED: (
            "User %(user)s deleted %(filename)s on %(candidate)s candidate's profile at %(time)s",
            "%(count)s Candidate Documents have been deleted"
        )
    }

    def __init__(self, activity_params):
        self.activity_params = activity_params

    def get_activities(self):
        """Method for retrieving activity logs based on a domain ID that is extracted via an
           authenticated user ID.
        :param int user_id: ID of the authenticated user.
        :param datetime|None start_datetime: Optional datetime object for query filters.
        :param datetime|None end_datetime: Optional datetime object for query filters.
        :param int page: Pagination start.
        :return: JSON encoded SQL-Alchemy.pagination response.
        """
        user_id = self.activity_params.user_id
        current_user = User.query.filter_by(id=user_id).first()
        user_domain_id = User.query.filter_by(id=user_id).value('domainId')
        user_ids = User.query.filter_by(domain_id=user_domain_id).values('id')
        flattened_user_ids = [item for sublist in user_ids for item in sublist]
        filters = []

        # GET - 1998 / WEB - 912.
        # Some activity streams do not want the current user's activities.
        # Additionally we do not want to see some types of activities.
        if self.activity_params.exclude_current_user:
            flattened_user_ids.remove(user_id)
            filters.append(not_(Activity.type.in_(EXCLUSIONS)))

        filters.append(Activity.user_id.in_(flattened_user_ids))
        start, end = self.activity_params.start_datetime, self.activity_params.end_datetime
        if start:
            filters.append(Activity.added_time > start)
        if end:
            filters.append(Activity.added_time < end)

        page, post_qty = self.activity_params.page, self.activity_params.post_qty

        if self.activity_params.is_aggregate_request:
            activities = Activity.query.filter(*filters).order_by(Activity.added_time.desc()).all()
        else:
            activities = Activity.query.filter(*filters).order_by(Activity.added_time.desc()).paginate(page, post_qty,
                                                                                                       False)

        activities_response = {
            'total_count':
            activities.total,
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
            } for activity in activities.items]
        }
        return activities_response

    # Like 'get' but gets the last 200 consecutive activity types. can't use GROUP BY because it doesn't respect ordering.
    def get_recent_readable(self):
        logs = [
            "Getting recent readable for {} - {}\n".format(self.activity_params.start_datetime or 'N/A',
                                                           self.activity_params.end_datetime or 'N/A')
        ]

        limit = self.activity_params.aggregate_limit
        start_time = time()
        current_user = User.query.filter_by(id=self.activity_params.user_id).first()
        logs.append("Fetched current user in {} seconds\n".format(time() - start_time))

        # Get the last 200 activities and aggregate them by type, with order.
        user_domain_id = current_user.domain_id
        user_ids = User.query.filter_by(domain_id=user_domain_id).values('id')
        logs.append("Fetched domain IDs in {} seconds\n".format(time() - start_time))
        flattened_user_ids = [item for sublist in user_ids for item in sublist]
        logs.append("Flattened domain IDs in {} seconds\n".format(time() - start_time))
        filters = [Activity.user_id.in_(flattened_user_ids)]

        start, end = self.activity_params.start_datetime, self.activity_params.end_datetime
        if start:
            filters.append(Activity.added_time >= start)
        if end:
            filters.append(Activity.added_time <= end)

        activities = Activity.query.filter(*filters).order_by(Activity.added_time.desc()).limit(200).all()
        activities_count = len(activities)

        logs.append("Fetched {} activities in {} seconds\n".format(activities_count, time() - start_time))

        aggregated_activities = []
        aggregated_activities_count = 0
        current_activity_count = 0
        aggregate_start, aggregate_end = datetime.today(), EPOCH

        for i, activity in enumerate(activities):
            if activity.added_time < aggregate_start:
                aggregate_start = activity.added_time
            if activity.added_time > aggregate_end:
                aggregate_end = activity.added_time

            current_activity_count += 1
            if activity.type not in self.MESSAGES:
                logger.error('Given Campaign Type (%s) not found.' % activity.type)
                continue
            next_activity_type = activities[i + 1].type if (i < activities_count - 1) else None

            # next activity is new, or the very last one, so aggregate these ones
            if activity.type != next_activity_type:
                activity_aggregate = {
                    'count': current_activity_count,
                    'start': aggregate_start.strftime(DATE_FORMAT),
                    'end': aggregate_end.strftime(DATE_FORMAT)
                }
                activity_aggregate['readable_text'] = self.activity_text(activity, activity_aggregate['count'],
                                                                         current_user)

                aggregate_start, aggregate_end = datetime.today(), EPOCH
                aggregated_activities.append(activity_aggregate)
                aggregated_activities_count += 1

                if aggregated_activities_count == limit:  # if we've got enough activity groups, quit
                    break

                current_activity_count = 0

        finishing_time = time() - start_time
        logs.append("Finished making readable in {} seconds\n".format(finishing_time))
        if finishing_time > TIMEOUT_THRESHOLD:
            logs.append('ActivityService::INFO::Timeout -  {} exceeded desired timeout at {}s'.format(
                self.activity_params, finishing_time))
            log_string = ''
            for log in logs:
                log_string += log
            logger.info(log_string)
        return aggregated_activities

    def activity_text(self, activity, count, current_user):
        start = time()
        single_count = count == 1
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
                format_string = format_string.replace(" an ", " a ")

        formatted_string = format_string % params

        if 'You has' in formatted_string:
            # To fix 'You has joined'
            formatted_string = formatted_string.replace('You has', 'You have')
        elif "You's" in formatted_string:
            # To fix "You's recurring campaign has expired"
            formatted_string = formatted_string.replace("You's", "Your")

        return formatted_string
