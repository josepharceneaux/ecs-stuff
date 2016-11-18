from time import sleep
from social_network_service.tasks import import_meetup_events, import_meetup_rsvps

sleep(15)
import_meetup_events()
import_meetup_rsvps()
