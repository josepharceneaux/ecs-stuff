"""
This file contains some (supposedly) common utility functions that may be used
or consumed by various programs.
"""

import datetime
import logging
from gt_models.user import User
from requests_oauthlib import OAuth2Session

logger = logging.getLogger('event_service.app')
OAUTH_SERVER = 'http://127.0.0.1:8888/oauth2/authorize'


class Attendee(object):
    """
    Basically a placeholder object that will be used while processing
    RSVPs. See base.py
    """

    def __init__(self, *args, **kwargs):

        self.first_name = None  # first name of attendee
        self.last_name = None  # last name of attendee
        self.full_name = None  # full name of attendee
        self.profile_url = None  # profile url of attendee
        self.picture_url = None  # picture url of attendee
        self.city = None  # city of attendee
        self.country = None  # country of attendee
        self.latitude = None  # latitude of attendee's location
        self.longitude = None  # longitude of attendee's location
        self.zip = None   # zip code of attendee's city/location
        self.rsvp_id = None  # attendee's rsvp id in db
        self.email = None  # attendee's email address
        self.rsvp_status = None  # attendee's rsvp status
        self.candidate_id = None  # attendee's id in candidate table
        self.event = None  # attendee's corresponding event in database
        self.vendor_img_link = None  # attendee's vendor image link
        # (image is present in static files of gt-app)
        self.added_time = None  # attendee's time of rsvp
        self.gt_user_id = None  # attendee's corresponding gt-user id
        self.vendor_rsvp_id = None  # attendee's vendor rsvp id
        self.social_network_id = None  # attendee's social network id
        self.candidate_event_rsvp_id = None  # attendee's entry id in
        self.candidate_source_id = None  # attendee's candidate_source id
        # from db
        self.source_product_id = None # attendee's source product id in database
        # candidate_event_rsvp

    def __str__(self):
        return 'Name: %s, RSVP_ID: %s, EMAIL: %s' % (self.full_name,
                                                     self.rsvp_id,
                                                     self.email)


def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()


def milliseconds_since_epoch(dt):
    assert isinstance(dt, datetime.datetime) == True
    return unix_time(dt) * 1000.0


def milliseconds_since_epoch_to_dt(epoch):
    return datetime.datetime.fromtimestamp(epoch / 1000.0)


def log_exception(traceback_info, message):
    """
    This function logs exception when it is called inside a catch block
    where ever it is called, traceback_info and error message is passed
    in arguments.
    :param message:
    :param traceback_info:
    :return:
    """
    traceback_info['error'] = message
    logger.exception("| Reason: %(error)s \n"
                     "functionName: %(functionName)s, "
                     "User: %(User)s, class: %(class)s, "
                     "memberId: %(memberId)s, |"
                     % traceback_info)


def log_error(traceback_info, message):
    """
    This function logs error when it is called inside a catch block
    where ever it is called, traceback_info and error message is passed
    in arguments.
    :param message:
    :param traceback_info:
    :return:
    """
    traceback_info['error'] = message
    logger.error("| Reason: %(error)s |"
                 "functionName: %(functionName)s, "
                 "User: %(User)s, class: %(class)s, "
                 "memberId: %(memberId)s, "
                 % traceback_info)


def authenticate_user(request):
    """
    :rtype: gluon.dal.objects.Row | None
    """
    auth_token = request.headers.get('Authorization')
    if auth_token and isinstance(auth_token, basestring):
        auth_token = auth_token.lower().replace('bearer ', '')
        try:
            remote = OAuth2Session(token={'access_token': auth_token})
            response = remote.get(OAUTH_SERVER)
            if response.status_code == 200:
                user_id = response.json().get('user_id') or ''
                return User.get_by_id(user_id) if user_id else None
            else:
                return None
        except Exception as e:
            return None
    else:
        return None