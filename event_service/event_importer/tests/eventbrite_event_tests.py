"""
An end to end test that does the following:
    a)- Creates culture, organization, user, and user_credentials data
    to be used in test.
    b)- We use a test Eventbrite account, we should replace it with something
    else though. Using this account we first create an event on Eventbrite's
    end.
    c)- Once the event is created we run the _process_event() for Eventbrite.
    d)- Then we try to retrieve the event we just created from the database.
    We assert on found values.
    e)- In the end, in the tear down, we delete all test data.
"""
import requests
import unittest
import sys, os
from event_importer.eventbrite import Eventbrite

file_path = os.path.realpath(__file__)
dir_path, _ = os.path.split(file_path)
PATH = os.path.abspath(os.path.join(dir_path, '../..'))
sys.path.append(PATH)
print sys.path
from datetime import datetime, timedelta, time
from gt_models.config import init_db, db_session
from gt_models.user import User, UserCredentials
from gt_models.domain import Domain
from gt_models.event import Event
from gt_models.culture import Culture
from gt_models.social_network import SocialNetwork

init_db()

from mixer.backend.sqlalchemy import Mixer


class EventbriteTests(unittest.TestCase):
    def setUp(self):
        self.api_url = "https://www.eventbriteapi.com/v3"
        self.auth_token = "URPBHL3JRF4SY3I43OM5"
        self.member_id = '149509931459'
        # datetime pattern for eventbrite API call
        self.start_time = (datetime.now() + timedelta(days=9)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.end_time = (datetime.now() + timedelta(days=11)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.time_zone = 'Asia/Karachi'
        self.currency = 'USD'
        self.now_timestamp = datetime.now().strftime("%Y:%m:%d %H:%M:%S%f")
        mixer = Mixer(session=db_session, commit=True)
        # we need better strategy to create 'culture' data
        self.culture = mixer.blend('gt_models.culture.Culture',
                                   description=self.now_timestamp,
                                   code='ttttt')
        organization = mixer.blend('gt_models.organization.Organization')
        self.domain = mixer.blend(Domain, organization=organization, culture=self.culture,
                                  defaultTrackingCode=self.now_timestamp)
        eventbrite = SocialNetwork.get_by_name('Eventbrite')
        self.user = mixer.blend(User, domain=self.domain, culture=self.culture)
        self.user_id = self.user.id
        self.user_credential = mixer.blend(UserCredentials, userId=self.user_id,
                                           authToken=self.auth_token, memberId=self.member_id,
                                           socialNetworkId=eventbrite.id)
        self.user_credential_id = self.user_credential.id

    def create_event(self):
        self.event_description = """This is a test event! Lorel Ipsum.
        Lorel Ipsum. Lorel Ipsum. Lorel Ipsum. Lorel Ipsum. Lorel Ipsum.
        Lorel Ipsum. Lorel Ipsum. Lorel Ipsum. Lorel Ipsum. Lorel Ipsum.
        Lorel Ipsum. Lorel Ipsum. Lorel Ipsum. Lorel Ipsum. Lorel Ipsum.
        Lorel Ipsum. Lorel Ipsum. Lorel Ipsum. Lorel Ipsum. Lorel Ipsum.
        Lorel Ipsum."""
        self.event_name = 'Test Event'
        params = {'token': self.auth_token,
                  'event.start.utc': self.start_time,
                  'event.start.timezone': self.time_zone,
                  'event.end.utc': self.end_time,
                  'event.end.timezone': self.time_zone,
                  'event.currency': self.currency,
                  'event.name.html': self.event_name,
                  'event.description.html': self.event_description}
        result = requests.post(self.api_url + "/events/", params=params).json()
        assert result['status'] == 'draft'
        assert result['name']['text'] == self.event_name
        self.vendor_event_id = result['id']
        tickets_created = self.create_event_tickets(self.vendor_event_id)
        assert tickets_created is True
        result_published = self.publish_event(self.vendor_event_id)
        assert result_published is True

    def create_event_tickets(self, vendor_event_id):
        url = self.api_url + "/events/" + vendor_event_id + "/ticket_classes/"
        params = {
            'token': self.auth_token,
            'ticket_class.name': 'Free Ticket',
            'ticket_class.quantity_total': 50,
            'ticket_class.free': True}
        result = requests.post(url, params=params)
        return result.ok

    def publish_event(self, vendor_event_id):
        # create url to publish event/
        url = self.api_url + "/events/" + vendor_event_id + "/publish/"
        params = {'token': self.auth_token}
        result = requests.post(url, params=params)
        return result.ok

    def run_process_event(self):
        self.create_event()
        eventbrite = Eventbrite(start_date=self.start_time,
                                end_date=self.end_time,
                                alchemy_session_init=True)
        eventbrite._process_events(self.user_credential)

    def test_eventbrite_event(self):
        self.run_process_event()
        event = Event.get_by_user_and_vendor_id(self.user_id, self.vendor_event_id)
        assert event is not None
        assert event.eventDescription.find("This is a test event! Lorel Ipsum. Lorel Ipsum.")

    def tearDown(self):
        print Domain.delete(self.domain.id)
        print Culture.delete(self.culture.id)
        print User.delete(self.user_id)
        print UserCredentials.delete(self.user_credential_id)
        result = requests.post(self.api_url + "/events/" + self.vendor_event_id
                               + "/unpublish/" + "?token=" + self.auth_token)
        assert result.status_code == 200


if __name__ == "__main__":
    unittest.main()
