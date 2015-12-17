import uuid
import random
from faker import Faker
fake = Faker()

__author__ = 'jitesh'


class FakeCandidatesData(object):
    @classmethod
    def create(cls, count=1, first_name=True, middle_name=False, last_name=True, added_time=True, emails_list=True,
               address_list=False):

        """
        :param count: Number of candidates objects to be created
        :param first_name:
        :type first_name: bool | str
        :param middle_name:
        :type middle_name: bool | str
        :param last_name:
        :type last_name: bool | str
        :param added_time:
        :type added_time: bool | datetime.date
        :param emails_list:
        :type emails_list: bool | list[dict]
        :param address_list:
        :type address_list: bool | list[dict]
        """
        candidates = []
        for iteration in range(0, count):
            candidate = {
                'first_name': {True: uuid.uuid4().__str__()[0:8], False: None}.get(first_name, first_name),
                'middle_name': {True: uuid.uuid4().__str__()[0:8], False: None}.get(middle_name, middle_name),
                'last_name': {True: uuid.uuid4().__str__()[0:8], False: None}.get(last_name, last_name),
                # 'added_time': {True: datetime.datetime.now(), False: None}.get(added_time, added_time),
                'emails': {True: cls.create_emails_list(), False: None}.get(emails_list, emails_list),
                'addresses': cls.create_address_list() if address_list is True else address_list
            }
            candidates.append(candidate)
        return {'candidates': candidates}

    @classmethod
    def create_emails_list(cls):
        return [{'label': 'primary', 'address': fake.safe_email()}]

    @classmethod
    def create_address_list(cls):
        return [{'address_line_1': fake.street_address(), 'city': fake.city(),
                 'state': fake.state(), 'zip_code': fake.zipcode(), 'country': fake.country()}]
