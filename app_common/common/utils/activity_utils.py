"""
    This class contains the Activity Message Ids to create an activity for a particular action.
    This is placed inside common/utils/ so that other services can use this to create activities
    without initializing activity_service.
"""
__author__ = 'basit'


class ActivityMessageIds(object):
    """
    This class contains the Activity Message Ids to create an activity for a particular action.
    This is placed inside common/utils/ so that other services can use this to create activities
    without initializing activity_service.
    """
    CANDIDATE_CREATE_WEB = 1
    CANDIDATE_UPDATE = 2
    CANDIDATE_DELETE = 3
    CANDIDATE_CREATE_CSV = 18
    CANDIDATE_CREATE_WIDGET = 19
    CANDIDATE_CREATE_MOBILE = 20  # TODO add in

    # params=dict(id, name)
    # All Campaigns
    CAMPAIGN_CREATE = 4
    CAMPAIGN_DELETE = 5
    CAMPAIGN_SEND = 6  # also has num_candidates
    CAMPAIGN_EXPIRE = 7  # recurring campaigns only # TODO implement
    CAMPAIGN_PAUSE = 21
    CAMPAIGN_RESUME = 22
    CAMPAIGN_SCHEDULE = 27

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
    # Email campaign
    CAMPAIGN_EMAIL_SEND = 15
    CAMPAIGN_EMAIL_OPEN = 16
    CAMPAIGN_EMAIL_CLICK = 17

    # Social Network Service
    RSVP_EVENT = 23
    EVENT_CREATE = 28
    EVENT_DELETE = 29
    EVENT_UPDATE = 30

    # SMS campaign
    CAMPAIGN_SMS_SEND = 24
    CAMPAIGN_SMS_CLICK = 25
    CAMPAIGN_SMS_REPLY = 26

    # Talent Pipelines
    PIPELINE_CREATE = 31
    PIPELINE_DELETE = 32

    # Talent Pools
    TALENT_POOL_CREATE = 33
    TALENT_POOL_DELETE = 34

    # Dumblists
    # TODO
