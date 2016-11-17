from time import sleep
from social_network_service.tasks import import_meetup_events

sleep(10)
import_meetup_events.apply_async()