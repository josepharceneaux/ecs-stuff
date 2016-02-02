

class ActivityServiceKeys:

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

    EVENT_CREATE = 25
    EVENT_DELETE = 26
    EVENT_UPDATE = 27