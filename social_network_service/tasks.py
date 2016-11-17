"""
Celery tasks are defined here. It will be a separate celery process.
These methods are called by run_job method asynchronously

- Running celery using commandline (social_network_service directory) =>

    celery -A social_network_service.social_network_app.celery_app worker  worker --concurrency=4 --loglevel=info

"""
# Builtin imports
import datetime
import json
import time

# 3rd party imports
import requests

# Application imports
from celery.result import AsyncResult

from social_network_service.common.error_handling import InternalServerError
from social_network_service.common.models.db import db
from social_network_service.common.models.candidate import SocialNetwork
from social_network_service.common.models.event import MeetupGroup, Event
from social_network_service.common.models.user import UserSocialNetworkCredential
from social_network_service.common.talent_config_manager import TalentConfigKeys
from social_network_service.common.utils.handy_functions import http_request
from social_network_service.common.vendor_urls.sn_relative_urls import SocialNetworkUrls
from social_network_service.modules.constants import (ACTIONS, MEETUP_EVENT_STREAM_API_URL, MEETUP_EVENT_STATUS,
                                                      MEETUP_RSVPS_STREAM_API_URL)
from social_network_service.modules.event.meetup import Meetup
from social_network_service.modules.rsvp.meetup import Meetup as MeetupRsvp
from social_network_service.modules.event.eventbrite import Eventbrite as EventbriteEventBase
from social_network_service.modules.social_network.meetup import Meetup as MeetupSocialNetwork
from social_network_service.modules.social_network.eventbrite import Eventbrite as EventbriteSocialNetwork
from social_network_service.modules.urls import get_url
from social_network_service.modules.utilities import get_class
from social_network_service.social_network_app import celery_app as celery, app


@celery.task(name="events_and_rsvps_importer")
def rsvp_events_importer(social_network_name, mode, user_credentials_id, datetime_range):
    """
    Imports RSVPs or events of a user, create candidates store them in db and also upload them on Cloud search
    :param str social_network_name: Facebook, Eventbrite, Meetup
    :param str mode: rsvp or event
    :param int user_credentials_id: user credentials entry
    :param dict datetime_range:
    """
    with app.app_context():
        logger = app.config[TalentConfigKeys.LOGGER]
        user_credentials = UserSocialNetworkCredential.get_by_id(user_credentials_id)
        user_id = user_credentials.user_id
        try:
            social_network = SocialNetwork.get_by_name(social_network_name.lower())
            social_network_class = get_class(social_network.name.lower(), 'social_network',
                                             user_credentials=user_credentials)
            # we call social network class here for auth purpose, If token is expired
            # access token is refreshed and we use fresh token8
            sn = social_network_class(user_id)

            logger.debug('%s Importer has started for %s(UserId: %s).'
                         ' Social Network is %s.'
                         % (mode.title(), sn.user.name, sn.user.id,
                            social_network.name))
            # Call social network process method to start importing rsvps/event
            sn.process(mode, user_credentials=user_credentials, **datetime_range)
            # Update last_updated of each user_credentials.
            user_credentials.update(updated_datetime=datetime.datetime.utcnow())
        except Exception as e:
            logger.exception('start: running %s importer, user_id: %s failed. %s',
                             mode, user_id, e.message)


@celery.task(name="import_meetup_events")
def import_meetup_events(start_datetime=None):
    """
    This task starts at service startup and then it keeps fetching events using Meetup stream API.
    :param string | int | None start_datetime: epoch time , we will import events after this time, None for now
    """
    with app.app_context():
        logger = app.config[TalentConfigKeys.LOGGER]
        logger.info('Meetup Event Importer started at UTC: %s' % datetime.datetime.utcnow())
        meetup = SocialNetwork.get_by_name('Meetup')
        if not meetup:
            raise InternalServerError('Unable to find Meetup social network in gt database')

        while True:
            try:
                url = MEETUP_EVENT_STREAM_API_URL
                response = requests.get(url, stream=True, timeout=30)
                logger.info('Meetup Stream Response Status: %s' % response.status_code)
                for raw_event in response.iter_lines():
                    if raw_event:
                        try:
                            event = json.loads(raw_event)
                            group_id = event['group']['id']
                            MeetupGroup.session.commit()
                            group = MeetupGroup.get_by_group_id(group_id)
                            if group:
                                logger.info('Going to save event: %s' % event)
                                fetch_meetup_event.apply_async((event, group, meetup))
                        except Exception:
                            logger.exception('Error occurred while parsing event data, Date: %s' % raw_event)
                            rollback()
            except Exception as e:
                logger.warning('Out of main loop. Cause: %s' % e)
                rollback()


@celery.task(name="import_meetup_rsvps")
def import_meetup_rsvps(start_datetime=None):
    """
    This task starts at service startup and then it keeps fetching events using Meetup stream API.
    Raw data of rsvp looks like

    {
        u'group':
                {u'group_city': u'Denver', u'group_lat': 39.68, u'group_urlname': u'denver-metro-chadd-support',
                    u'group_name': u'Denver-Metro CHADD (Children and Adults with ADHD) Meetup',
                    u'group_lon': -104.92,
                    u'group_topics': [
                                        {u'topic_name': u'ADHD', u'urlkey': u'adhd'},
                                        {u'topic_name': u'ADHD Support', u'urlkey': u'adhd-support'},
                                        {u'topic_name': u'Adults with ADD', u'urlkey': u'adults-with-add'},
                                        {u'topic_name': u'Families of Children who have ADD/ADHD',
                                            u'urlkey': u'families-of-children-who-have-add-adhd'},
                                        {u'topic_name': u'ADHD, ADD', u'urlkey': u'adhd-add'},
                                        {u'topic_name': u'ADHD Parents with ADHD Children',
                                            u'urlkey': u'adhd-parents-with-adhd-children'},
                                        {u'topic_name': u'Resources for ADHD', u'urlkey': u'resources-for-adhd'},
                                        {u'topic_name': u'Parents of Children with ADHD',
                                            u'urlkey': u'parents-of-children-with-adhd'},
                                        {u'topic_name': u'Support Groups for Parents with ADHD Children',
                                            u'urlkey': u'support-groups-for-parents-with-adhd-children'},
                                        {u'topic_name': u'Educators Training on AD/HD',
                                            u'urlkey': u'educators-training-on-ad-hd'},
                                        {u'topic_name': u'Adults with ADHD', u'urlkey': u'adults-with-adhd'}
                                    ],
                    u'group_state': u'CO', u'group_id': 1632579, u'group_country': u'us'
                },
        u'rsvp_id': 1639776896,
        u'venue': {u'lat': 39.674759, u'venue_id': 3407262, u'lon': -104.936317,
                   u'venue_name': u'Denver Academy-Richardson Hall'},
        u'visibility': u'public',
        u'event': {u'event_name': u'Manage the Impact of Technology on
                   Your Child and Family with Lana Gollyhorn',
                   u'event_id': u'235574682',
                   u'event_url': u'https://www.meetup.com/denver-metro-chadd-support/events/235574682/',
                   u'time': 1479778200000},
        u'member': {u'member_name': u'Valerie Brown', u'member_id': 195674019}, u'guests': 0,
        u'mtime': 1479312043215, u'response': u'yes'
    }

    :param string | int | None start_datetime: epoch time , we will import events after this time, None for now
    """
    with app.app_context():
        logger = app.config[TalentConfigKeys.LOGGER]
        start_datetime = start_datetime or (datetime.datetime.utcnow().strftime("%s") + "000")
        try:
            logger.info("RSVP streaming started for Meetup")
            url = MEETUP_RSVPS_STREAM_API_URL % start_datetime
            meetup = SocialNetwork.get_by_name('Meetup')
            if not meetup:
                raise InternalServerError('Unable to find Meetup social network in gt database')

            while True:
                try:
                    response = requests.get(url, stream=True)
                    for raw_rsvp in response.iter_lines():
                    # for raw_rsvp in [1]:
                        if raw_rsvp:
                            try:
                                rsvp = json.loads(raw_rsvp)
                                # rsvp = {u'group': {u'group_city': u'Mountain View', u'group_lat': 37.38, u'group_urlname': u'Python-Learning-Meetup', u'group_name': u'Python Learning Meetup', u'group_lon': -122.08, u'group_topics': [{u'topic_name': u'Linux', u'urlkey': u'linux'}, {u'topic_name': u'Open Source', u'urlkey': u'opensource'}, {u'topic_name': u'Python', u'urlkey': u'python'}, {u'topic_name': u'Functional Programming in Python', u'urlkey': u'functional-programming-in-python'}, {u'topic_name': u'Python Web Development', u'urlkey': u'python-web-development'}, {u'topic_name': u'Open Source Python', u'urlkey': u'open-source-python'}, {u'topic_name': u'Software Development', u'urlkey': u'softwaredev'}, {u'topic_name': u'Web Development', u'urlkey': u'web-development'}, {u'topic_name': u'Computer programming', u'urlkey': u'computer-programming'}], u'group_state': u'CA', u'group_id': 18837203, u'group_country': u'us'}, u'rsvp_id': 1639760447, u'venue': {u'lat': 31.537783, u'venue_id': 17028862, u'lon': 74.347748, u'venue_name': u'Lahore, Pakistan '}, u'visibility': u'public', u'event': {u'event_name': u'Testing event importer', u'event_id': u'235620735', u'event_url': u'https://www.meetup.com/Python-Learning-Meetup/events/235620735/', u'time': 1480561200000}, u'member': {u'member_name': u'getTalent, Inc.', u'member_id': 190979089}, u'guests': 0, u'mtime': 1479414331441, u'response': u'yes'}
                                group_id = rsvp['group']['group_id']
                                group = MeetupGroup.get_by_group_id(group_id)
                                if group:
                                    logger.info('Going to save Meetup rsvp for user(id:%s).\nrsvp:%s'
                                                % (group.user_id, rsvp))
                                    process_meetup_rsvp.apply_async((rsvp, group, meetup))
                            except Exception:
                                logger.exception('Error occurred while parsing rsvp data, Date: %s' % raw_rsvp)
                except Exception as e:
                    logger.warning('Some bad data caused main loop to break. Cause: %s' % e)

        except Exception as e:
            logger.exception(e.message)


@celery.task(name="fetch_meetup_event")
def fetch_meetup_event(event, group, meetup):
    """
    This celery task is for an individual event to be processed. When `rsvp_events_importer` task finds that some
    event belongs to getTalent user, it passes this event to this task for further processing.

    In this task, we create meetup objects for social network and event and the finally save this event by mapping
    meetup event fields to gt event fields. If event already exists in database, it is updated.

    If an event contains venue information, is is save in `venue` table or updated an existing venue.
    :param dict event: event dictionary from meetup
    :param MeetupGroup group: MeetupGroup Object
    :param SocialNetwork meetup: SocialNetwork object for meetup
    """
    with app.app_context():
        logger = app.config[TalentConfigKeys.LOGGER]
        logger.info('Going to process Meetup Event: %s' % event)
        try:
            time.sleep(5)  # wait for event creation api to save event in database otherwise there can be duplicate
            # event created in database (one by api and other by importer)
            group = db.session.merge(group)
            meetup = db.session.merge(meetup)

            if event['status'] == MEETUP_EVENT_STATUS['upcoming']:
                meetup_sn = MeetupSocialNetwork(user_id=group.user.id, social_network_id=meetup.id)
                meetup_event_base = Meetup(user_credentials=meetup_sn.user_credentials, social_network=meetup)
                event_url = get_url(meetup_sn, SocialNetworkUrls.EVENT).format(event['id'])
                response = http_request('get', event_url, headers=meetup_sn.headers)
                if response.ok:
                    event = response.json()
                    event = meetup_event_base.event_sn_to_gt_mapping(event)
                    logger.info('Event imported successfully : %s' % event.to_json())
            elif event['status'] in [MEETUP_EVENT_STATUS['canceled'], MEETUP_EVENT_STATUS['deleted']]:
                event_id = event['id']
                event_in_db = Event.get_by_user_id_social_network_id_vendor_event_id(group.user.id,
                                                                                     meetup.id,
                                                                                     event_id
                                                                                     )
                if event_in_db:
                    Event.delete(event_in_db)
                    logger.info("Meetup event has been deleted from gt database. event:`%s`" % event_in_db.to_json())
                else:
                    logger.info("Meetup event not found in database. event:`%s`." % event)

        except Exception:
            logger.exception('Failed to save event: %s' % event)
            rollback()


@celery.task(name="process_meetup_rsvp")
def process_meetup_rsvp(rsvp, group, meetup):
    """
    This celery task is for an individual rsvp to be processed. When `meetup_rsvp_importer` task finds that some
    rsvp belongs to event of getTalent's user, it passes this rsvp to this task for further processing.

    In this task, we create meetup objects for social network and event and the finally save this event by mapping
    meetup event fields to gt event fields. If event already exists in database, it is updated.

    Response from Meetup API looks like
    {
        u'group':
                {u'group_city': u'Denver', u'group_lat': 39.68, u'group_urlname': u'denver-metro-chadd-support',
                    u'group_name': u'Denver-Metro CHADD (Children and Adults with ADHD) Meetup',
                    u'group_lon': -104.92,
                    u'group_topics': [
                                        {u'topic_name': u'ADHD', u'urlkey': u'adhd'},
                                        {u'topic_name': u'ADHD Support', u'urlkey': u'adhd-support'},
                                        {u'topic_name': u'Adults with ADD', u'urlkey': u'adults-with-add'},
                                        {u'topic_name': u'Families of Children who have ADD/ADHD',
                                            u'urlkey': u'families-of-children-who-have-add-adhd'},
                                        {u'topic_name': u'ADHD, ADD', u'urlkey': u'adhd-add'},
                                        {u'topic_name': u'ADHD Parents with ADHD Children',
                                            u'urlkey': u'adhd-parents-with-adhd-children'},
                                        {u'topic_name': u'Resources for ADHD', u'urlkey': u'resources-for-adhd'},
                                        {u'topic_name': u'Parents of Children with ADHD',
                                            u'urlkey': u'parents-of-children-with-adhd'},
                                        {u'topic_name': u'Support Groups for Parents with ADHD Children',
                                            u'urlkey': u'support-groups-for-parents-with-adhd-children'},
                                        {u'topic_name': u'Educators Training on AD/HD',
                                            u'urlkey': u'educators-training-on-ad-hd'},
                                        {u'topic_name': u'Adults with ADHD', u'urlkey': u'adults-with-adhd'}
                                    ],
                    u'group_state': u'CO', u'group_id': 1632579, u'group_country': u'us'
                },
        u'rsvp_id': 1639776896,
        u'venue': {u'lat': 39.674759, u'venue_id': 3407262, u'lon': -104.936317,
                   u'venue_name': u'Denver Academy-Richardson Hall'},
        u'visibility': u'public',
        u'event': {u'event_name': u'Manage the Impact of Technology on
                   Your Child and Family with Lana Gollyhorn',
                   u'event_id': u'235574682',
                   u'event_url': u'https://www.meetup.com/denver-metro-chadd-support/events/235574682/',
                   u'time': 1479778200000},
        u'member': {u'member_name': u'Valerie Brown', u'member_id': 195674019}, u'guests': 0,
        u'mtime': 1479312043215, u'response': u'yes'
    }

    :param dict rsvp: rsvp dictionary from meetup
    :param MeetupGroup group: MeetupGroup Object
    :param SocialNetwork meetup: SocialNetwork object for meetup
    """
    with app.app_context():
        logger = app.config[TalentConfigKeys.LOGGER]
        logger.info('Going to process Meetup RSVP: %s' % rsvp)
        try:
            group = db.session.merge(group)
            meetup = db.session.merge(meetup)
            meetup_sn = MeetupSocialNetwork(user_id=group.user.id, social_network_id=meetup.id)
            meetup_rsvp_object = MeetupRsvp(user_credentials=meetup_sn.user_credentials, social_network=meetup)
            attendee = meetup_rsvp_object.post_process_rsvp(rsvp)
            if attendee and attendee.rsvp_id:
                logger.info('RSVP imported successfully. rsvp:%s' % rsvp)
            else:
                logger.info('RSVP already present in database. rsvp:%s' % rsvp)
        except Exception:
            logger.exception('Failed to save rsvp: %s' % rsvp)


@celery.task(name="fetch_eventbrite_event")
def fetch_eventbrite_event(user_id, event_url, action_type):
    """
    This celery task retrieves user event from eventbrite and then saves or
    """
    with app.app_context():
        logger = app.config[TalentConfigKeys.LOGGER]
        logger.info('Going to process Eventbrite Event: %s' % event_url)
        try:
            eventbrite = SocialNetwork.get_by_name('Eventbrite')
            if action_type in [ACTIONS['created'], ACTIONS['published']]:
                logger.info('Event Published on Eventbrite, Event URL: %s' % event_url)
                eventbrite_sn = EventbriteSocialNetwork(user_id=user_id, social_network_id=eventbrite.id)
                eventbrite_event_base = EventbriteEventBase(headers=eventbrite_sn.headers,
                                                            user_credentials=eventbrite_sn.user_credentials,
                                                            social_network=eventbrite_sn.user_credentials.social_network)
                response = http_request('get', event_url, headers=eventbrite_sn.headers)
                if response.ok:
                    event = response.json()
                    event = eventbrite_event_base.event_sn_to_gt_mapping(event)
                    logger.info('Event imported/updated successfully : %s' % event.to_json())
            elif action_type == ACTIONS['unpublished']:
                event_id = event_url.split('/')[-2]
                event_id = int(event_id)
                event_in_db = Event.get_by_user_id_social_network_id_vendor_event_id(user_id,
                                                                                     eventbrite.id,
                                                                                     event_id
                                                                                     )
                if event_in_db:
                    Event.delete(event_in_db)
                    logger.info('Delete event from gt database, event: %s' % event_in_db.to_json())
                else:
                    logger.info("Event unpublished from Eventbrite but it does not exist, don't worry. Event URL: %s"
                                % event_url)
            elif action_type == ACTIONS['updated']:
                pass  # We are handling update action yet because it causes duplicate entries

        except Exception:
            logger.exception('Failed to save event. URL: %s' % event_url)
            rollback()


@celery.task
def error_callback(uuid):
    with app.app_context():
        logger = app.config[TalentConfigKeys.LOGGER]
        print uuid
        result = AsyncResult(uuid)
        exc = result.get(propagate=False)
        logger.error('Task {0} raised exception: {1!r}\n{2!r}'.format(
            uuid, exc, result.traceback))
        db.session.rollback()


def rollback():
    try:
        db.session.rollback()
    except Exception:
        pass
