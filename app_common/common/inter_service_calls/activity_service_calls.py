# This file contains various common functions to call activity service and can be used across
# all the services.

import json
import traceback
from ..utils.handy_functions import http_request
from ..routes import ActivityApiUrl
from ..utils.talent_reporting import email_error_to_admins
from ..utils.handy_functions import generate_jwt_headers


def add_activity(user_id, activity_type, source_table, source_id=None, params=None):
    """
    Adds activity in system using Activity service
    This function fails silently, because in case of any activity error i.e. it will be some sort of programming error
    so we don't want user to stuck just because of activity is not logged. Instead errors are logged and notified to admins

    All errors or exceptions are notified to Admins and doesn't raises any exception.

    :param user_id: Id of user against whom activity is to be created
    :param oauth_token: oauth token (TODO: Should not be required though, Once activity API is corrected, remove it)
    :param activity_type: Type of activity
    :param source_table: Table name for which activity is created. TODO: Should be removed.
    :param source_id: Integer of the source_table's ID for entering specific activity.
    :param params: Dictionary of created/updated source_table attributes.
    :return: Nothing
    """
    try:
        json_data = json.dumps({'user_id': user_id,
                                'type': activity_type,
                                'source_table': source_table,
                                'source_id': source_id,
                                'params': params})
    except Exception as ex:
        # Email admins about the error and then return silently
        email_error_to_admins(body="Not able to json.dumps. The exception was: %s" %ex, subject="Activity Service Error: Error occurred while adding activity")
        return
    # TODO: Remove bearer token because system should create activity not the user.
    headers = generate_jwt_headers(content_type='application/json', user_id=user_id)
    # call (POST) to activity_service to create activity
    try:
        http_request('POST', ActivityApiUrl.ACTIVITIES, headers=headers,
                     data=json_data)
    except Exception as ex:
        # Email admins and return silently
        tb = traceback.format_exc()
        email_body = """Exception occurred while adding activity (POST API). <br/>
        The exception was: <em> {exception}. <br/><br/>
        Traceback: <br/>
        <pre> {traceback} </pre>""".format(exception=ex, traceback=tb)

        email_error_to_admins(body=email_body, subject="Activity Service Error: Calling POST API of activity service")
        return


class ActivityTypes(object):
    """
    getTalent Activity types.
    """
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