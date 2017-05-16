from activity_service.common.models.misc import Activity

EVENTS = Activity.MessageIds
SINGLE = 'single'
PLURAL = 'plural'

MESSAGES = {
    EVENTS.RSVP_EVENT: {
        SINGLE: "<b>{firstName} {lastName}</b> responded {response} on <b>{creator}'s</b> event: <b>'{eventTitle}'</b>",
        PLURAL: "<b>{firstName} {lastName}<b> responded {response} on event: '<b>{eventTitle}</b>'"
    },
    EVENTS.EVENT_CREATE: {
        SINGLE: "<b>{username}</b> created an event: <b>{event_title}</b>",
        PLURAL: "<b>{username}</b> created {count} events.</b>"
    },
    EVENTS.EVENT_DELETE: {
        SINGLE: "<b>{username}</b> deleted an event <b>{event_title}</b>",
        PLURAL: "<b>{username}</b> deleted {count} events."
    },
    EVENTS.EVENT_UPDATE: {
        SINGLE: "<b>{username}</b> updated an event <b>{event_title}</b>.",
        PLURAL: "<b>{username}</b> updated {count} events."
    },
    EVENTS.CANDIDATE_CREATE_WEB: {
        SINGLE: "<b>{username}</b> uploaded the resume of candidate <b>{formatted_name}</b>",
        PLURAL: "<b>{username}</b> uploaded the resume(s) of {count} candidate(s)"
    },
    EVENTS.CANDIDATE_CREATE_CSV: {
        SINGLE: "<b>{username}</b> imported the candidate <b>{formattedName}</b> via spreadsheet",
        PLURAL: "<b>{username}</b> imported {count} candidate(s) via spreadsheet"
    },
    EVENTS.CANDIDATE_CREATE_WIDGET: {
        SINGLE: "Candidate <b>{formattedName}</b> joined via widget",
        PLURAL: "{count} candidate(s) joined via widget"
    },
    EVENTS.CANDIDATE_CREATE_MOBILE: {
        SINGLE: "<b>{username}</b> added the candidate <b>{formattedName}</b> via mobile",
        PLURAL: "<b>{username}</b> added {count} candidate(s) via mobile"
    },
    EVENTS.CANDIDATE_UPDATE: {
        SINGLE: "<b>{username}</b> updated the candidate <b>{formattedName}</b>",
        PLURAL: "<b>{username}</b> updated {count} candidates"
    },
    EVENTS.CANDIDATE_DELETE: {
        SINGLE: "<b>{username}</b> deleted the candidate <b>{formattedName}</b>",
        PLURAL: "<b>{username}</b> deleted {count} candidates"
    },
    EVENTS.CANDIDATE_AUTO_MERGED: {
        SINGLE: "Candidate <b>{formatted_name}</b> was automatically merged with a duplicated profile.",
        PLURAL: "{count} candidates were updated"
    },
    EVENTS.CANDIDATE_USER_MERGED: {
        SINGLE: "<b>{username}</b> (User) merged candidate <b>{formatted_name}</b> with a duplicated profiles.",
        PLURAL: "{count} candidates were updated"
    },
    EVENTS.CANDIDATES_KEPT_SEPARATE: {
        SINGLE: "<b>%(username)s</b> kept candidate <b>%(formatted_name)s</b> and "
                "<b>%(second_formatted_name)s</b> separate.",
        PLURAL: "{count} candidates were updated"
    },
    EVENTS.CAMPAIGN_CREATE: {
        SINGLE: "<b>{username}</b> created an {campaign_type} campaign: <b>{name}</b>",
        PLURAL: "<b>{username}</b> created {count} campaigns"
    },
    EVENTS.CAMPAIGN_DELETE: {
        SINGLE: "<b>{username}</b> deleted an {campaign_type} campaign: <b>{name}</b>",
        PLURAL: "<b>{username}</b> deleted {count} campaign(s)"
    },
    EVENTS.CAMPAIGN_SEND: {
        SINGLE: "{campaign_type} campaign <b>{name}</b> was sent to <b>{num_candidates}</b> candidate(s)",
        PLURAL: "{count} campaign(s) sent"
    },
    EVENTS.CAMPAIGN_EXPIRE: {
        SINGLE: "<b>{username}'s</b> recurring campaign <b>{name}</b> has expired",
        PLURAL: "{count} recurring campaign(s) of <b>{username}</b> have expired"
    },
    EVENTS.CAMPAIGN_PAUSE: {
        SINGLE: "<b>{username}</b> paused the campaign <b>{name}</b>",
        PLURAL: "<b>{username}</b> paused {count} campaign(s)"
    },
    EVENTS.CAMPAIGN_RESUME: {
        SINGLE: "<b>{username}</b> resumed campaign <b>{name}</b>",
        PLURAL: "<b>{username}</b> resumed {count} campaign(s)"
    },
    EVENTS.SMARTLIST_CREATE: {
        SINGLE: "<b>{username}</b> created the list <b>{name}</b>",
        PLURAL: "<b>{username}</b> created {count} list(s)"
    },
    EVENTS.SMARTLIST_DELETE: {
        SINGLE: "<b>{username}</b> deleted the list: <b>{name}</b>",
        PLURAL: "<b>{username}</b> deleted {count} list(s)"
    },
    EVENTS.DUMBLIST_CREATE: {
        SINGLE: "<b>{username}</b> created a list: <b>{name}</b>.",
        PLURAL: "<b>{username}</b> created {count} list(s)"
    },
    EVENTS.DUMBLIST_DELETE: {
        SINGLE: "<b>{username}</b> deleted list <b>{name}</b>",
        PLURAL: "<b>{username}</b> deleted {count} list(s)"
    },
    EVENTS.SMARTLIST_ADD_CANDIDATE: {
        SINGLE: "<b>{formattedName}<b> was added to list <b>{name}</b>",
        PLURAL: "{count} candidates were added to list <b>{name}</b>"
    },
    EVENTS.SMARTLIST_REMOVE_CANDIDATE: {
        SINGLE: "<b>{formattedName}</b> was removed from the list <b>{name}</b>",
        PLURAL: "{count} candidates were removed from the list <b>{name}</b>"
    },
    EVENTS.PIPELINE_ADD_CANDIDATE: {
        SINGLE: "<b>{formattedName}<b> was added to pipeline <b>{name}</b>",
        PLURAL: "{count} candidates were added to pipeline <b>{name}</b>"
    },
    EVENTS.PIPELINE_REMOVE_CANDIDATE: {
        SINGLE: "<b>{formattedName}</b> was removed from the pipeline <b>{name}</b>",
        PLURAL: "{count} candidates were removed from the pipeline <b>{name}</b>"
    },
    EVENTS.USER_CREATE: {
        SINGLE: "<b>{username}</b> has joined",
        PLURAL: "{count} users have joined"
    },
    EVENTS.WIDGET_VISIT: {
        SINGLE: "Widget was visited",
        PLURAL: "Widget was visited {count} time(s)"
    },
    EVENTS.NOTIFICATION_CREATE: {
        SINGLE: "You received an update notification",
        PLURAL: "You received {count} update notification(s)"
    },
    EVENTS.CAMPAIGN_EMAIL_SEND: {
        SINGLE: "<b>{candidate_name}</b> received an email from campaign <b>{campaign_name}</b>",
        PLURAL: "{count} candidate(s) received an email from campaign <b>{campaign_name}</b>"
    },
    EVENTS.CAMPAIGN_EMAIL_OPEN: {
        SINGLE: "<b>{candidate_name}</b> opened an email from campaign <b>{campaign_name}</b>",
        PLURAL: "{count} candidates opened an email from campaign <b>{campaign_name}</b>"
    },
    EVENTS.CAMPAIGN_EVENT_CLICK: {
        SINGLE: "<b>{candidate_name}</b> clicked on an email from event campaign <b>{campaign_name}</b>",
        PLURAL: "Event Campaign <b>{campaign_name}</b> was clicked {count} time(s)"
    },
    EVENTS.CAMPAIGN_EVENT_SEND: {
        SINGLE: "<b>{candidate_name}</b> received an invite for <b>{campaign_name}</b>",
        PLURAL: "{count} candidate(s) received an invite for <b>{campaign_name}</b>"
    },
    EVENTS.CAMPAIGN_EVENT_OPEN: {
        SINGLE: "<b>{candidate_name}</b> opened an email from event campaign <b>{campaign_name}</b>",
        PLURAL: "{count} candidates opened an email from event campaign <b>{campaign_name}</b>"
    },
    EVENTS.CAMPAIGN_EMAIL_CLICK: {
        SINGLE: "<b>{candidate_name}</b> clicked on an email from campaign <b>{campaign_name}</b>",
        PLURAL: "Campaign <b>{campaign_name}</b> was clicked {count} time(s)"
    },
    EVENTS.CAMPAIGN_SMS_SEND: {
        SINGLE: "SMS Campaign <b>{campaign_name}</b> has been sent to {candidate_name}.",
        PLURAL: "SMS Campaign <b>{campaign_name}</b> has been sent to {candidate_name}."
    },
    EVENTS.CAMPAIGN_SMS_CLICK: {
        SINGLE: "<b>{candidate_name}</b> clicked on the SMS Campaign <b>{name}</b>.",
        PLURAL: "<b>{candidate_name}</b> clicked on {name}."
    },
    EVENTS.CAMPAIGN_SMS_REPLY: {
        SINGLE: "<b>{candidate_name}</b> replied {reply_text} to the SMS campaign <b>{campaign_name}</b>.",
        PLURAL: "<b>{candidate_name}</b> replied '{reply_text}' on campaign {campaign_name}."
    },
    EVENTS.CAMPAIGN_SCHEDULE: {
        SINGLE: "<b>{username}</b> scheduled an {campaign_type} campaign: <b>{campaign_name}</b>.",
        PLURAL: "<b>{username}</b> scheduled an {campaign_type} campaign: <b>{campaign_name}</b>."
    },
    EVENTS.PIPELINE_CREATE: {
        SINGLE: "<b>{username}</b> created a pipeline: <b>{name}</b>.",
        PLURAL: "<b>{username}</b> created a pipeline: <b>{name}</b>."
    },
    EVENTS.PIPELINE_DELETE: {
        SINGLE: "<b>{username}</b> deleted pipeline: <b>{name}</b>.",
        PLURAL: "<b>{username}</b> deleted pipeline: <b>{name}</b>."
    },
    EVENTS.TALENT_POOL_CREATE: {
        SINGLE: "<b>{username}</b> created a Talent Pool: <b>{name}</b>.",
        PLURAL: "<b>{username}</b> created a Talent Pool: <b>{name}</b>."
    },
    EVENTS.TALENT_POOL_DELETE: {
        SINGLE: "<b>{username}</b> deleted Talent Pool: <b>{name}</b>.",
        PLURAL: "<b>{username}</b> deleted Talent Pool: <b>{name}</b>."
    },
    EVENTS.CAMPAIGN_PUSH_CREATE: {
        SINGLE: "<b>{username}</b> created a Push campaign: '{campaign_name}'",
        PLURAL: "<b>{username}</b> created a Push campaign: '{campaign_name}'"
    },
    EVENTS.CAMPAIGN_PUSH_SEND: {
        SINGLE: "Push Campaign <b>{campaign_name}</b> has been sent to <b>{candidate_name}</b>.",
        PLURAL: "Push Campaign <b>{campaign_name}</b> has been sent to <b>{candidate_name}</b>.",
    },
    EVENTS.CAMPAIGN_PUSH_CLICK: {
        SINGLE: "<b>{candidate_name}</b> clicked on Push Campaign <b>{campaign_name}</b>.",
        PLURAL: "<b>{candidate_name}</b> clicked on {campaign_name}."
    }
}
