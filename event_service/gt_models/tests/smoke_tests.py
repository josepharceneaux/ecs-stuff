"""
Contains basic smoke tests to, e.g., test whether a record can be inserted,
retrieved, deleted, a foreign key relationship is working and etc.
"""
import unittest
import sys, os
import datetime
file_path = os.path.realpath(__file__)
dir_path, _ = os.path.split(file_path)
PATH = os.path.abspath(os.path.join(dir_path, '../..'))
sys.path.append(PATH)
from gt_models.config import init_db, db_session
from gt_models.user import User
from gt_models.domain import Domain
from gt_models.culture import Culture
init_db()


from mixer.backend.sqlalchemy import Mixer

class SmokeTests(unittest.TestCase):
    def setUp(self):
        self.user = None
        self.domain = None
        self.culture = None
        self.now_timestamp = datetime.datetime.now().strftime("%Y:%m:%d %H:%M:%S%f")
        mixer = Mixer(session=db_session, commit=True)

        self.culture = mixer.blend('gt_models.culture.Culture', description=self.now_timestamp)
        organization = mixer.blend('gt_models.organization.Organization')
        self.domain = mixer.blend(Domain, organization=organization, culture=self.culture,
                                  defaultTrackingCode=self.now_timestamp)
        self.user = mixer.blend(User, domain=self.domain, culture=self.culture)
        self.user_id = self.user.id

    def test_inserts(self):
        """
        Check whether the data was saved and inserts are working.
        :return:
        """
        assert self.culture
        assert self.culture.description == self.now_timestamp
        assert self.domain
        assert self.domain.defaultTrackingCode == self.now_timestamp
        assert self.user
        assert isinstance(self.user, User)

    def test_relations(self):
        """
        We test whether relations still make sense after being saved in
        database.
        :return:
        """
        assert self.user.domainId == self.domain.id
        assert self.user.defaultCultureId == self.culture.id
        domain = Domain.get_by_id(self.domain.id)
        assert isinstance(domain, Domain)
        assert isinstance(domain.culture, Culture)
        assert domain.culture.code == self.culture.code
        assert domain.culture.description == self.culture.description

    def tearDown(self):
        print Domain.delete(self.domain.id)
        print Culture.delete(self.culture.id)
        print User.delete(self.user_id)

if __name__=="__main__":
    unittest.main()
