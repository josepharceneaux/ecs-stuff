"""
Common/helper functions
"""
import datetime
from graphql_service.common.utils.datetime_utils import DatetimeUtils

from graphql_service.common.models.db import db
from graphql_service.common.models.candidate_edit import CandidateEdit


def clean(value):
    """
    :rtype: str
    """
    return (value or '').strip()


# todo: unit test this
def remove_duplicates(collection):
    """
    Function will remove duplicate dict_data from collection
    :type collection: list
    :rtype: list
    """
    seen = set()
    unique_items = []
    for dict_data in collection:
        t = tuple(dict_data.items())
        if t not in seen:
            seen.add(t)
            unique_items.append(dict_data)
    return unique_items


class Diff(object):
    """
    Usage:
        >>> existing_data = {'first_name': 'jerry', 'last_name': 'seinfeld'}
        >>> new_data = {'first_name': 'larry', 'last_name': 'david'}
        >>> user_id = 1
        >>> changes = Diff(existing_data, new_data, user_id, attribute=None)
        >>> print changes.find_diffs()
        {'field': 'first_name', 'old_value': 'jerry', 'new_value': 'larry'}}
    """

    def __init__(self, existing_data, new_data, user_id, attribute):
        self.existing_data = existing_data
        self.new_data = new_data
        self.user_id = user_id
        self.attribute = attribute
        self.changes = dict()

    def find_diffs(self):
        """
        function will find the difference between existing_data & old_data
        :rtype: dict
        """
        if not self.attribute:
            err_msg = "{} must be of type dict".format(self.attribute)
            assert isinstance(self.existing_data, dict) and isinstance(self.new_data, dict), err_msg

            for k, existing_v in self.existing_data.iteritems():

                new_v = self.new_data[k] if self.new_data.get(k) else None
                if new_v and new_v != existing_v:
                    self.changes.update(dict(
                        field=k,
                        old_value=existing_v,
                        new_value=new_v
                    ))

            return self.changes

        else:
            err_msg = "{} must be of type list".format(self.attribute)
            assert isinstance(self.existing_data, list) and isinstance(self.new_data, list), err_msg

            self.changes[self.attribute] = []

            if len(self.existing_data) == len(self.new_data):
                for index, existing_item in enumerate(
                        self.existing_data):  # {'address': 'ab@gmail.com', 'label': 'Other'}
                    i = 0
                    for key, existing_value in existing_item.iteritems():
                        new_value = self.new_data[index][key] if self.new_data[index].get(key) else None
                        if new_value and new_value != existing_value:
                            self.changes[self.attribute].append({key: {}})
                            self.changes[self.attribute][i][key]['old_value'] = existing_value
                            self.changes[self.attribute][i][key]['new_value'] = new_value
                            i += 1
                return self.changes


def track_updates(user_id, candidate_id, existing_data, new_data, attribute=None):
    """
    Function will insert the old value, new value, candidate's ID, user ID, field ID, and current datetime
    into CandidateEdit table. This is to help identify:
    - the candidate
    - its updating user
    - the attribute & field that was updated/edited
    - date & time of its occurrence
    - value before update, and
    - value after update
    :type user_id: int | long
    :type candidate_id: int | long
    :type existing_data: candidate's existing data
    :type new_data: candidate's new data
    :type attribute: candidate's attribute, such as email, phone, address, etc.
    """
    if not attribute:
        attribute = 'primary'

    for k, existing_v in existing_data.iteritems():

        new_v = new_data[k] if new_data.get(k) else None

        if new_v and new_v != existing_v:
            field_id = field_id_from_name(attribute, k)
            db.session.add(CandidateEdit(
                user_id=user_id,
                candidate_id=candidate_id,
                field_id=field_id,
                old_value=existing_v,
                new_value=new_v,
                edit_action=None,
                edit_datetime=datetime.datetime.utcnow()
            ))


def field_id_from_name(attribute, field_name):
    for attr, item in field_name_and_id_mapping.iteritems():
        if attribute == attr:
            for field, field_id in item.iteritems():
                if field_name == field:
                    return field_id
    else:
        assert False, "Field ID not found. attribute: '{}'; field_name: '{}'".format(attribute, field_name)


field_name_and_id_mapping = {
    'primary': {
        'first_name': 1,
        'middle_name': 2,
        'last_name': 3,
        'formatted_name': 4,
        'status_id': 5,
        'user_id': 6,
        'added_datetime': 7,
        'source_id': 8,
        'resume_url': 9,
        'objective': 10,
        'summary': 11,
        'total_months_experience': 12,
        'culture_id': 13,
    },
    'address': {
        'address_line_1': 101,
        'address_line_2': 102,
        'city': 103,
        'state': 104,
        'country_id': 105,
        'zip_code': 106,
        'po_box': 107,
        'is_default': 108,
        'longitude_radians': 109,
        'latitude_radians': 110,
        'coordinates': 111,
        'iso3166_country': 112,
        'iso3166_subdivision': 113,
    },
    'area_of_interest': {
        'area_of_interest_id': 201,
        'notes': 202
    },
    'custom_field': {
        'value': 301,
        'custom_field_id': 302
    },
    'education': {
        'school_name': 401,
        'school_type': 402,
        'city': 403,
        'state': 404,
        'country_id': 405,
        'is_current': 406,
        'iso3166_country': 407,
        'iso3166_subdivision': 408
    },
    'education_degree': {
        'degree_type': 501,
        'degree_title': 502,
        'start_year': 503,
        'start_month': 504,
        'end_year': 505,
        'end_month': 506,
        'gpa': 507,
        'concentration': 509,
        'comments': 509,
    },
    'experience': {
        'organization': 601,
        'position': 602,
        'city': 603,
        'state': 604,
        'end_month': 605,
        'end_year': 606,
        'start_month': 607,
        'start_year': 608,
        'country_id': 609,
        'is_current': 610,
        'description': 611,
        'iso3166_country': 612,
        'iso3166_subdivision': 613
    },
    'work_preference': {
        'relocate': 701,
        'authorization': 702,
        'telecommute': 703,
        'travel_percentage': 704,
        'hourly_rate': 705,
        'salary': 706,
        'tax_terms': 707,
        'security_clearance': 708,
        'third_party': 709
    },
    'email': {
        'label': 801,
        'address': 802,
        'is_default': 803
    },
    'phone': {
        'label': 901,
        'value': 902,
        'extension': 903,
        'is_default': 904
    },
    'military_service': {
        'country_id': 1001,
        'service_status': 1002,
        'highest_rank': 1003,
        'highest_grade': 1004,
        'branch': 1005,
        'comments': 1006,
        'start_year': 1007,
        'start_month': 1008,
        'end_year': 1009,
        'end_month': 1010,
        'iso3166_country': 1111
    },
    'preferred_location': {
        'city': 1101,
        'state': 1102,
        'zip_code': 1104,
        'country_id': 1105,
        'iso3166_country': 1106,
        'iso3166_subdivision': 1107,
    },
    'skill': {
        'name': 1201,
        'total_months_used': 1202,
        'last_user_year': 1203,
        'last_user_month': 1204,
    },
    'social_network': {
        'name': 1301,
        'profile_url': 1302
    },
    'photo': {
        'image_url': 1401,
        'is_default': 1402
    },
    'tag': {
        'name': 1501,
    },
    'reference': {
        'person_name': 1601,
        'person_title': 1602,
        'comments': 1603
    }
}
