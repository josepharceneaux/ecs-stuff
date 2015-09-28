"""
An end to end test that does the following:
    a)- Creates culture, organization, user, and user_credentials data
    to be used in test.
    b)- We use a test Meetup account, we should replace it with something
    else though. Using this account we first create an event on Meetup's
    end.
    c)- Once the event is created we run the _process_event() for Meetup.
    d)- Then we try to retrieve the event we just created from the database.
    We assert on found values.
    e)- In the end, in the tear down, we delete all test data.
"""
import requests
import unittest
import sys, os
file_path = os.path.realpath(__file__)
dir_path, _ = os.path.split(file_path)
PATH = os.path.abspath(os.path.join(dir_path, '../..'))
sys.path.append(PATH)
print sys.path
from datetime import datetime, timedelta
from event_importer.utilities import milliseconds_since_epoch
from event_importer.meetup import Meetup
from gt_models.config import init_db, db_session
from gt_models.user import User, UserCredentials
from gt_models.domain import Domain
from gt_models.event import Event
from gt_models.culture import Culture
from gt_models.social_network import SocialNetwork
init_db()


from mixer.backend.sqlalchemy import Mixer

class MeetupTests(unittest.TestCase):

    def setUp(self):
        self.api_url = "https://api.meetup.com/2/"
        self.auth_token = "6940527437f4b11d495176e81f13"
        self.group_id = "18837246"
        self.group_url = "QC-Python-Learning"
        self.member_id = '183366764'
        self.now_timestamp = datetime.now().strftime("%Y:%m:%d %H:%M:%S%f")
        mixer = Mixer(session=db_session, commit=True)
        # we need better strategy to create 'culture' data
        self.culture = mixer.blend('gt_models.culture.Culture',
                            description=self.now_timestamp,
                            code='ttttt')
        organization = mixer.blend('gt_models.organization.Organization')
        self.domain = mixer.blend(Domain, organization=organization, culture=self.culture,
                                  defaultTrackingCode=self.now_timestamp)
        meetup = SocialNetwork.get_by_name('Meetup')
        self.user = mixer.blend(User, domain=self.domain, culture=self.culture)
        self.user_id = self.user.id
        self.user_credential = mixer.blend(UserCredentials, userId=self.user_id,
                                authToken=self.auth_token, memberId=self.member_id,
                                socialNetworkId=meetup.id)
        self.user_credential_id = self.user_credential.id

    def create_event(self):
        self.event_description = """This is a test event! Lorel Ipsum. Lorel Ipsum.
         Lorel Ipsum. Lorel Ipsum. Lorel Ipsum. Lorel Ipsum. Lorel Ipsum.
         Lorel Ipsum. Lorel Ipsum. Lorel Ipsum. Lorel Ipsum. Lorel Ipsum.
         Lorel Ipsum. Lorel Ipsum. Lorel Ipsum. Lorel Ipsum. Lorel Ipsum.
         Lorel Ipsum. Lorel Ipsum. Lorel Ipsum. Lorel Ipsum. Lorel Ipsum.
         """
        rsvp_limit = 100
        event_time = (datetime.now() + timedelta(days=10))
        time = "%.0f" % (milliseconds_since_epoch(event_time))
        self.event_name = 'Test Event'
        params = {
            'description': self.event_description, 'rsvp_limit': rsvp_limit,
            'time': time, 'key': self.auth_token, 'group_id': self.group_id,
            'group_urlname': self.group_url, 'name': self.event_name
        }
        result = requests.post(self.api_url + "event/?sign=true&key=" + self.auth_token, \
                               params=params).json()
        assert result['status'] == 'upcoming'
        assert result['name'] == self.event_name
        self.vendor_event_id = result['id']

    def run_process_event(self):
        self.create_event()
        start_date = (datetime.now() + timedelta(days=9))
        end_date = (datetime.now() + timedelta(days=11))
        meetup = Meetup(start_date=start_date, end_date=end_date,
                        alchemy_session_init=True)
        meetup._process_events(self.user_credential)


    def test_meetup_event(self):
        self.run_process_event()
        event = Event.get_by_user_and_vendor_id(self.user_id, self.vendor_event_id)
        assert event.eventDescription.find("This is a test event! Lorel Ipsum. Lorel Ipsum.")

    def tearDown(self):
        print Domain.delete(self.domain.id)
        print Culture.delete(self.culture.id)
        print User.delete(self.user_id)
        print UserCredentials.delete(self.user_credential_id)
        result = requests.delete(self.api_url + "event/" + self.vendor_event_id + \
                               "?sign=true&key=" + self.auth_token)
        assert result.status_code == 200

if __name__ == "__main__":
    unittest.main()



