import uuid, random
from faker import Faker
from ..utils.handy_functions import sample_phone_number

fake = Faker()

__author__ = 'jitesh'


class FakeCandidatesData(object):
    @classmethod
    def create(cls, talent_pool, count=1, first_name=True, middle_name=False, last_name=True,
               added_time=True, emails_list=True, address_list=None, create_phone=True):
        """
        Generates candidate data dictionary as required by candidate_service API.
        Creates candidate data dictionary with given data or random data
        if values are provided in params it will generate data with those values.
        If params value is True it will generate random data.
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
        :param create_phone:
        :type create_phone: bool
        """
        candidates = []
        for iteration in range(0, count):
            candidate = {
                'talent_pool_ids': {'add': [talent_pool.id]},
                'first_name': {True: uuid.uuid4().__str__()[0:8], False: None}.get(first_name, first_name),
                'middle_name': {True: uuid.uuid4().__str__()[0:8], False: None}.get(middle_name, middle_name),
                'last_name': {True: uuid.uuid4().__str__()[0:8], False: None}.get(last_name, last_name),
                # 'added_time': {True: datetime.datetime.now(), False: None}.get(added_time, added_time),
                'emails': {True: cls.create_emails_list(), False: None}.get(emails_list, emails_list),
                'addresses': cls.create_address_list() if address_list is True else address_list,
                'phones': [{"label": "mobile", "value": sample_phone_number(), "is_default": True}] if create_phone else []}
            candidates.append(candidate)
        return {'candidates': candidates}

    @classmethod
    def create_emails_list(cls):
        # Generate random emails list as required by candidate_service
        return [{'label': 'primary', 'address': fake.safe_email()}]

    @classmethod
    def create_address_list(cls):
        # Generate random address list as required by candidate_service
        return [{'address_line_1': fake.street_address(), 'city': fake.city(),
                 'state': fake.state(), 'zip_code': fake.zipcode(), 'country': fake.country()}]


def college_majors():
    """
    Function will return some popular college majors
    Note: dict-keys represent discipline and its key is a list of majors within that discipline.
    Testing example:
        >>> discipline = random.choice(college_majors().keys())     # => 'engineering'
        >>> random.choice(college_majors()[discipline])             # => 'Nuclear Engineering'
    :rtype:  dict
    """
    majors = {
        'engineering': [
            'Aerospace Engineering', 'Agricultural Engineering', 'Bioengineering',
            'Biomedical Engineering', 'Ceramic Engineering', 'Chemical Engineering',
            'Civil Engineering', 'Computer Engineering', 'Computer Science', 'Electrical Engineering',
            'Geophysical Engineering', 'Materials Engineering', 'Mechanical Engineering',
            'Mining & Mineral Engineering', 'Marine Engineering', 'Nuclear Engineering',
            'Petroleum Engineering', 'Software Engineering', 'Systems Analysis & Engineering'
        ]
    }
    return majors
