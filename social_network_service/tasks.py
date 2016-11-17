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
from social_network_service.modules.constants import ACTIONS, MEETUP_STREAM_API_URL, MEETUP_EVENT_STATUS
from social_network_service.modules.event.meetup import Meetup
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
                url = MEETUP_STREAM_API_URL
                response = requests.get(url, stream=True, timeout=30)
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
                    logger.info('Delete Meetup event from gt database, event: %s' % event_in_db.to_json())

        except Exception:
            logger.exception('Failed to save event: %s' % event)
            rollback()


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
