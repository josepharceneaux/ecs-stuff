from time import sleep
from social_network_service.tasks import import_meetup_events, import_meetup_rsvps

sleep(10)
import_meetup_events.delay()
import_meetup_rsvps.delay()