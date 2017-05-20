"""
This module contains all functions and classes that will be used for Candidate De-Duping

Author: Zohaib Ijaz, QC-Technologies, <mzohaib.qc@gmail.com
"""
import json
import re
import traceback
import uuid
from datetime import date, datetime
from functools import wraps
from itertools import chain, islice, combinations, izip
from fuzzywuzzy import fuzz

from candidate_service.candidate_app import logger
from candidate_service.common.error_handling import InvalidUsage
from candidate_service.modules.track_changes import track_edits
from constants import (EXACT, YES_MATCH_CASES, HIGH_MATCH_CASES, MEDIUM_MATCH_CASES,
                       LOW_MATCH_CASES, JOB_TITLE_VARIATIONS, DEGREES, ADDRESS_NOTATIONS, MATCH_CATEGORIES,
                       CANDIDATE_CACHE_TIMEOUT, CATEGORIES_NAMES, EXTENSION_SOURCE_PRODUCT_ID, MOBILE_SOURCE_PRODUCT_ID)


def cache_match(func):
    """
    This decorator saves results of a function in a self.cache dictionary so next time this function will be called
    with same arguments, it will not calculate results but will return results from cache dictionary.
    :param func: function reference
    """
    @wraps(func)
    def wrapper(self, weight=None, **kwargs):
        key = func.__name__
        if weight is None and key in self.cache:
            return self.cache[key]
        if weight in self.cache and key in self.cache[weight]:
            return self.cache[weight][key]

        if weight is None:
            result = func(self)
            self.cache[key] = result
        else:
            result = func(self, weight, **kwargs)
            if weight not in self.cache:
                self.cache[weight] = {}
            self.cache[weight][key] = result
        return result

    return wrapper


def time_it(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print('Function: {}'.format(func.__name__))
        start = datetime.utcnow()
        print('Start Time: {}'.format(start))
        result = func(*args, **kwargs)
        end = datetime.utcnow()
        print('End Time: {}'.format(end))
        print('Time taken by {} is {} milliseconds'.format(func.__name__, (end - start).microseconds / 1000))
        return result
    return wrapper


class TimeItMeta(type):

    def __new__(cls, name, bases, dct):
        for key, val in dct.iteritems():
            if not key.startswith('__') and callable(val):
                dct[key] = time_it(val)
        return super(TimeItMeta, cls).__new__(cls, name, bases, dct)


class GtDict(dict):
    """
    This class is to allow getting attribute value from dict object instead of using get item syntax.
    TODO: It does not converts lists of objects / dict inside list (nested lists).
    e.g d = {'a': [[{'b': 1}, {'c': 2}], [{'d': 3}]]}

    :Examples:

        >>> data = {'a': 123, 'b': 222, 'c': {'d': 111}, 'e': [{'f': 100}, {'g': 333}]}
        >>> data = GtDict(data)
        >>> data.a
        123
        >>> data.c.d
        111
        >>> data.e[1].g
        333
    """
    def __init__(self, data):
        super(GtDict, self).__init__(data)
        for key, val in self.items():
            if isinstance(val, dict):
                self[key] = GtDict(val)
            if isinstance(val, list):
                for index, item in enumerate(val):
                    val[index] = GtDict(item) if isinstance(item, dict) else item

    def __getattr__(self, key):
        """
        Get item value from dict object
        :param key: key name
        :return: value of object under that key
        """
        return self.get(key)

    def __setattr__(self, key, value):
        """
        Set value against a key in dict object
        :param key: key name
        :param value: value to be set against key
        :return: value of object under that key
        """
        self[key] = value


class MergeHub(object):
    # Uncomment this for debugging
    # __metaclass__ = TimeItMeta

    def __init__(self, first, second):
        """
        This class allows us to compare and merge two candidates. first argument is a candidate (dict | SqlAlchemy)
        object which want to determine that, is it a duplicate of second candidate.
        For now there are 4 categories of match:

        1. YES: Yes means that candidate second is an exact match of first one, so we need to archive second and update
        first candidate with second's data.

        2. HIGH: High match means that it is most probable that second candidate is a match of first candidate but
        we are not sure about this that is why system will not merge these candidates and will allow user through
        front end to merge or keep these candidates separate.

        3. MEDIUM: Some values matches. User can later merge these or can keep them separate.

        4. LOW: Low match means that only few properties match are there. User can merge them of keep them separate.


        :param first: candidate created before second candidate. i.e. with older added_datetime
        :param second: candidate object created after first candidate.
        """
        self.first = GtDict(first) if isinstance(first, dict) else first
        self.second = GtDict(second) if isinstance(second, dict) else second
        self.categories = CATEGORIES_NAMES

        '''
        self.cache will contain information about candidate first and second match data.
        '''
        self.cache = {
            "exact_match_fields": {
                "first":  {
                    "first_name": self.first.first_name,
                    "middle_name": self.first.middle_name,
                    "last_name": self.first.last_name,
                    "formatted_name": self.first.formatted_name,
                    "emails": [email.address for email in (self.first.emails or [])],
                    "phones": [phone.value for phone in (self.first.phones or [])],
                    "profile_urls": [sn.profile_url for sn in (self.first.social_networks or [])]
                },
                "second": {
                    "first_name": self.second.first_name,
                    "middle_name": self.second.middle_name,
                    "last_name": self.second.last_name,
                    "formatted_name": self.second.formatted_name,
                    "emails": [email.address for email in (self.second.emails or [])],
                    "phones": [phone.value for phone in (self.second.phones or [])],
                    "profile_urls": [sn.profile_url for sn in (self.second.social_networks or [])]
                }
            }
        }
        # Match name, yes, high, medium or low
        self.match = None
        # How many match sets exist
        self.match_count = 0

    def get_merged_data(self):
        """
        This method returns updated merged data which will be saved against candidate first.
        e.g. if first candidate has 2 emails and second candidate also has 2 emails and one is common so after merging
        there will be three emails in this data.
        :rtype: dict
        """
        # Some function like first_name return a tuple like this (True, ('Zohaib', 'Zohaib'))
        # where 1st item is status of match and second is also a tuple contains values of first name for candidate
        # first and candidate second respectively. So in order to merge second, we need to keep values first candidate
        # and for list fields, we will merge both list values into one.

        merged_data = {
            'last_name': (self.last_name()[1][1]).title(),
            'addresses': self.merge_addresses(),
            'phones': self.merge_phones(),
            'id': int(self.first.id),
            'first_name': (self.first_name()[1][1]).title(),
            'middle_name': (self.middle_name()[1][1]).title(),
            'formatted_name': (self.full_name()[1][1]).title(),
            'talent_pool_id': self.first.talent_pool_id,
            'status_id': self.first.status_id,
            'educations': self.merge_educations(),
            'experiences': self.merge_jobs(),
            'emails': self.merge_emails(),
            'source_id': self.get_source_id(),
            'source_product_id': self.source_product_id()[1][1]
        }
        data = self.first.copy()
        data.update(merged_data)
        return data

    def merge_addresses(self, weight=EXACT):
        """
        This method combines addresses of first and second candidates into addresses of first candidate.
        :return: list of addresses
        """
        addresses = []
        for address2 in self.second.addresses or []:
            is_same = False
            for address1 in self.first.addresses or []:
                address_line_1_match = self.match_address_line_1(address1.address_line_1, address2.address_line_1,
                                                                 weight=weight)
                city_match = address1.city == address2.city
                zip_code_match = address1.zip_code == address2.zip_code
                if address1.id == address2.id or (address_line_1_match and city_match) or \
                        (address_line_1_match and zip_code_match):
                    is_same = True
                    address1.update(**address2)
                    track_edits(update_dict=address2, table_name='candidate_address',
                                candidate_id=self.first.id, user_id=self.first.user_id, query_obj=address1)
                    break
            if not is_same:
                address2.is_default = False
                addresses.append(address2)

        addresses += self.first.addresses or []
        return addresses

    def merge_educations(self):
        """
        This method combines educations of first and second candidates into educations of first candidate.
        :return: list of educations
        """
        degree_fields = ["type", "title", "start_year", "start_month", "end_year", "end_month", "gpa"]
        educations = []
        is_same_education = False
        educations1 = (self.first.educations or [])[:]
        for education2 in self.second.educations or []:
            matches = 0
            for index, education1 in enumerate(educations1):
                index -= matches
                same_school = education2.school_name == education1.school_name
                same_city = education1.city == education2.city
                is_same_education = same_school and same_city
                if is_same_education:
                    degrees = []
                    is_same_degree = False
                    for degree2 in education2.degrees or []:
                        for degree1 in education1.degrees or []:
                            if all(getattr(degree1, key) == getattr(degree2, key) for key in degree_fields):
                                is_same_degree = True
                                break
                        if not is_same_degree:
                            degrees.append(degree2)
                            is_same_degree = False
                    degrees += education1.degrees or []
                    education = education1
                    education['degrees'] = degrees
                    educations.append(education)
                    educations1.pop(index)
                    matches += 1
            if not is_same_education:
                educations.append(education2)
                is_same_education = False

        educations += educations1
        return educations

    def merge_emails(self):
        """
        This method combines emails of first and second candidates into emails of first candidate.
        :return: list of emails
        """
        emails = []
        is_same = False
        for email2 in self.second.emails or []:
            for email1 in self.first.emails or []:
                val1, val2 = (email1.address or '').lower().strip(), (email2.address or '').lower().strip()
                if val1 == val2:
                    is_same = True
                    break
            if not is_same:
                email2['is_default'] = False
                emails.append(email2)
                is_same = False

        emails += self.first.emails or []
        return emails

    def merge_phones(self):
        """
        This method combines phones of first and second candidates into phones of first candidate.
        :return: list of phones
        """
        phones1 = (self.first.phones or [])[:]
        phones = []
        is_same = False
        for phone2 in self.second.phones or []:
            val2 = self.phone_parser(phone2.value)
            matches = 0
            for index, phone1 in enumerate(phones1):
                index -= matches
                val1 = self.phone_parser(phone1.value)
                is_same, _, _ = self.get_match_details(val1, val2)
                if is_same:
                    phone1['value'] = self.pick_longer(phone1.value, phone2.value)
                    break
            if not is_same:
                phone2['is_default'] = False
                phones.append(phone2)
                is_same = False
        phones += phones1
        return phones

    def merge_jobs(self, weight=EXACT):
        """
        This method combines jobs of first and second candidates into jobs of first candidate.
        :param weight: Levenshtein distance
        :return: list of jobs
        """
        jobs = []
        matched = False
        for second in self.first.experiences or []:
            title = second.position
            for first in self.first.experiences or []:
                title2 = first.position
                is_same_title = fuzz.ratio(title, title2) >= weight and title and title2
                same_date = first.start_year == second.start_year and first.start_month == second.start_month
                same_organization = fuzz.ratio(first.organization, second.organization) >= weight
                if is_same_title and same_date and same_organization:
                    matched = True
                    break
            if not matched:
                jobs.append(second)
                matched = False
        jobs += self.first.experiences or []
        for job in jobs:
            position = job.position or ''
            if position:
                for posts in JOB_TITLE_VARIATIONS:
                    if re.findall(posts[0], position):
                        job['position'] = re.sub(posts[0], posts[1], position)
                        break
        return jobs

    def compare(self):
        """
        This method will be invoked on MergeHub instance which will perform all matches.
        :return: boolean
        """
        # if both objects are same, return false
        if self.first.id == self.second.id:
            return False

        # Match sets of conditions given by each category
        for name in self.categories:
            result = getattr(self, 'match_{}'.format(name))()
            if not self.match and result[0]:
                self.match = name
                self.match_count = result[1]

        # This field is not part of any comparison
        self.middle_name()
        self.job_description()
        first_photos = self.first.photos or []
        second_photos = self.second.photos or []
        photos_first = filter(lambda photo: photo.is_default, first_photos)
        photos_second = filter(lambda photo: photo.is_default, second_photos)
        first_image_url = photos_first[0].image_url if len(photos_first) \
            else first_photos[0].image_url if len(first_photos) else None
        second_image_url = photos_second.image_url if len(photos_second) \
            else photos_second.image_url if len(photos_second) else None
        self.cache['image_url'] = [first_image_url, second_image_url]
        self.cache['added_datetime'] = [
            self.first.added_datetime, self.second.added_datetime
        ]

    def compare_field(self, name, weight=EXACT):
        """
        This method takes name of of the field to be matched and a Levenshtein distance (weight) <= 100
        :param name: field name e.g. first_name, last_name, name_1
        :param weight: Levenshtein distance
        """
        try:
            return getattr(self, name)(weight=weight)
        except Exception as e:
            logger.error('Error: {}'.format(e))
            return False, None

    def compare_with_weight(self, key):
        """
        By default all fields will be matched by 100 % match or for exact same values.
        If we want a Levenshtein Distance match, we will pass custom integer weight value less than
        or equal to 100.
        :param str key: a key containing field name and weight. e.g "first_name,90"
        :return: boolean, whether given field values matched for two candidates with given Levenshtein Distance.
        """
        name = key.split(',')
        if len(name) == 1:
            name, weight = name[0], EXACT
        elif len(name) == 2:
            name, weight = name[0], int(name[1])
        else:
            raise InvalidUsage('Invalid key format. Given "{}", required "name,weight"'.format(key))
        return self.compare_field(name, weight)[0]

    def match_category(self, cases):
        """
        This function matches all cases possible for a category,e.g. Exact match (Yes), High match and returns
        status of match (True or False) and number of count, how many condition sets were matched in this category.
        e.g for Yes category there are three sets of conditions
            1. email
            2. name_1, name_2, name_3, phone
            3. social_profile_url
        So if if none of the above sets of fields match, status will be False otherwise True
        and if match count will be incremented with match of each set of conditions.
        e.g. if (name_1, name_2, name_3, phone) match, count will be incremented by 1 and it can be upto number of
        condition sets for that category.

        :param list[tuple] cases: list of tuples
        :return: boolean, whether any case matched or not for this category

        :Example:
            # first and second are dynamodb candidate objects
            >>> merge_hub = MergeHub(first, second)
            >>> yes_categories = [('email',), ('name_1', 'name_2', 'name_3', 'phone'), ('social_profile_url',)]
            >>> yes_match_status, yes_match_count = merge_hub.match_category(yes_categories)
        """
        match_count = 0
        for match_set in cases:
            if all(self.compare_with_weight(name) for name in match_set):
                match_count += 1
        return match_count > 0, match_count

    def create_date(self, year, month, day):
        """
        This method creates a date object given year, month and day.
        :param int year: year number, e.g. 2017
        :param int month: month number, 1-12
        :param int day: 1-30
        :return: date object or None in case of error
        """
        try:
            return str(date(year=year, month=month, day=day))
        except Exception:
            return None

    def get(self, name, default=''):
        """
        This method takes name of the field and returns a tuple of values for that key in candidate
        first and candidate second
        :param str name: key/field name
        :param type(t) default: default value of field
        """
        first = (getattr(self.first, name) or default)
        second = (getattr(self.second, name) or default)
        if isinstance(first, basestring) and isinstance(second, basestring):
            first, second = first.lower(), second.lower()
        return first, second

    def match_list_value(self, list_key, value_key, weight=EXACT, value_parser=None, comparator=None):
        """
        This method compares list fields like educations, addresses etc.
        :param list_key: key name with value as list of objects
        :param value_key: key of child object, like address_line_1 for location
        :param weight: Levenshtein distance
        :param value_parser: value parser
        :param str comparator: function name which will be used to compare values
        """
        values1 = list(set(map(lambda item: getattr(item, value_key), getattr(self.first, list_key) or [])))
        values2 = list(set(map(lambda item: getattr(item, value_key), getattr(self.second, list_key) or [])))
        values = {
            'status': False,
            'first': [],
            'second': []
        }
        matched = 0
        for index1, first in enumerate(values1):
            index1 = index1 - matched
            val1 = first if not value_parser else getattr(self, value_parser)(first)

            for index2, second in enumerate(values2):
                val2 = second if not value_parser else getattr(self, value_parser)(second)
                status, _, (val1, val2) = self.get_match_details(val1, val2, comparator=comparator, weight=weight)
                if status:
                    values['status'] |= True
                    values['first'].append((True, first))
                    values['second'].append((True, second))
                    values1.pop(index1)
                    values2.pop(index2)
                    matched += 1
                    break
        values['first'].extend(map(lambda item: (False, item), values1))
        values['second'].extend(map(lambda item: (False, item), values2))

        return values['status'], values

    @staticmethod
    def pick_longer(first, second):
        """
        This methods selects value that has more length from the given two string values
        :param str first: first str value
        :param second: second str value
        """
        len1 = len(first)
        len2 = len(second)
        return first if len1 >= len2 else second

    @staticmethod
    def get_match(matches):
        """
        This method takes a list of matches where each item is a tuple of three values.
        1st value is the status of match, 2nd value is percentage of match and 3rd value is the resultant value.
        e.g. while matching phone numbers of two candidates
        matches = [(True, 100, '+923046769700'), (False, 40, '+923041212121')]
        :param list matches: list of tuples
        :return: a tuple, match status and value with maximum match percentage
        """
        # Each item in matches list is like this so
        # item[0] -> True or False
        # item[1] -> Percentage match 0 - 100 %
        # item[2] -> value of matching field, e.g. in case of phone number it will be e.g. +923046769700

        # filter out all those records that have True status
        matches = filter(lambda item: item[0], matches)
        # If there is no record with matching status, return False and empty value
        if not matches:
            return False, ''
        # if there are some matches, find the match with maximum percentage match
        match = max(matches, key=lambda x: x[1])[2] if matches else ''
        return True if match else False, match

    def get_match_details(self, first, second, comparator=None, weight=EXACT):
        """
        This method takes two string values and finds the Levenshtein distance (percentage match) between them.
        Then it selects a value which is longer or contains more info (hopefully) and finally returns a tuple with
        three values e.g. (True, 100, '+923046769700')
        # item[0] -> True or False
        # item[1] -> Percentage match 0 - 100 %
        # item[2] -> value of matching field, e.g. in case of phone number it will be e.g. +923046769700
        :param str first: first string value
        :param str second: second string value
        :param str comparator: function name which will be used to compare values
        :param weight: Levenshtein distance
        :return: tuple
        """
        matched = first and second
        if comparator:
            matched = matched and getattr(self, comparator)(first, second, weight=EXACT)
            percentage = weight
        else:
            percentage = fuzz.ratio(first, second)
            matched = matched and percentage >= weight
        return bool(matched), percentage, (first, second)

    def phone_parser(self, value, digits=7):
        return (value or '')[-digits:]

    @cache_match
    def match_yes(self):
        """
        This methods matches all those conditions that are required for Auto Merge.
        :return: boolean, True or False
        """
        return self.match_category(YES_MATCH_CASES)

    @cache_match
    def match_high(self):
        """
        This methods matches all those conditions that are required for High Confidence match
        :return: boolean, True or False
        """
        return self.match_category(HIGH_MATCH_CASES)

    @cache_match
    def match_medium(self):
        """
        This methods matches all those conditions that are required for Medium Confidence match
        :return: boolean, True or False
        """
        return self.match_category(MEDIUM_MATCH_CASES)

    @cache_match
    def match_low(self):
        """
        This methods matches all those conditions that are required for Low Confidence match
        :return: boolean, True or False
        """
        return self.match_category(LOW_MATCH_CASES)

    @cache_match
    def email(self, weight=EXACT):
        """
        Match email addresses of given two candidates
        :param weight: Levenshtein distance
        """
        return self.match_list_value('emails', 'address', weight=weight)

    @cache_match
    def social_profile_url(self, weight=EXACT):
        """
        Match social_profile_url of given two candidates
        :param weight: Levenshtein distance
        """
        return self.match_list_value('social_networks', 'profile_url', weight=weight)

    @cache_match
    def phone(self, weight=EXACT):
        """
        Match phone number of given two candidates
        :param weight: Levenshtein distance
        """
        return self.match_list_value('phones', 'value', weight=weight, value_parser='phone_parser')

    def get_source_id(self):
        # Check which source id is less otherwise return source_id of first candidate
        source = self.first.source_id and self.second.source_id and self.second.source_id < self.first.source_id
        return self.second.source_id if source else self.first.source_id

    def source_product_id(self):
        values = self.get('source_product_id')
        return values[0] == values[1], values

    @staticmethod
    def match_address_line_1(address1, address2, weight=EXACT):
        """
        This method matches given two address_line_1 values with given criteria.

        Here is criteria:
            "155 national" would match to "155 national st" and "155 national street"
            "155 national ave" is a match to "155 national avenue"
        :param str address1: first value of address_line_1
        :param str address2: second value of address_line_1
        :param int weight: comparison weight, 100 for exact match, default 100
        :return: boolean
        :rtype: bool
        """
        address1 = (address1 or '').lower().strip()
        address2 = (address2 or '').lower().strip()
        address_type = ADDRESS_NOTATIONS[0]
        val1 = re.sub('|'.join(address_type), '', address1)
        val2 = re.sub('|'.join(address_type), '', address2)
        if fuzz.ratio(val1, val2) >= weight:
            return True
        for address_type in ADDRESS_NOTATIONS[1:]:
            if re.findall('|'.join(address_type), address1) and re.findall('|'.join(address_type), address2):
                val1 = re.sub('|'.join(address_type), '', address1)
                val2 = re.sub('|'.join(address_type), '', address2)
                if fuzz.ratio(val1, val2) >= weight:
                    return True
        return False

    @cache_match
    def first_name(self, weight=EXACT):
        """
        Match first_name of given two candidates
        :param weight: Levenshtein distance
        """
        values = self.get('first_name')
        return fuzz.ratio(*values) >= weight, values

    @cache_match
    def last_name(self, weight=EXACT):
        """
        Match last_name of given two candidates
        :param weight: Levenshtein distance
        """
        values = self.get('last_name')
        # Choose latest name. values[1] is latest because it belongs to second candidate which is latest
        return fuzz.ratio(*values) >= weight, values

    @cache_match
    def full_name(self, weight=EXACT):
        """
        Match full_name of given two candidates
        :param weight: Levenshtein distance
        """
        first = ' '.join([self.first_name()[1][0], self.middle_name()[1][0], self.last_name()[1][0]])
        second = ' '.join([self.first_name()[1][1], self.middle_name()[1][1], self.last_name()[1][1]])
        # Choose latest name. values[1] is latest because it belongs to second candidate which is latest
        return fuzz.ratio(first, second) >= weight, (first, second)

    @cache_match
    def middle_name(self, weight=EXACT):
        """
        Match middle_name of given two candidates
        :param weight: Levenshtein distance
        """
        values = self.get('middle_name')
        # Choose latest name. values[1] is latest because it belongs to second candidate which is latest
        return fuzz.ratio(*values) >= weight, values

    @cache_match
    def first_initial(self, weight=EXACT):
        """
        Match first_initial of given two candidates
        :param weight: Levenshtein distance
        """
        first, second = self.get('first_name')
        if not (first and second):
            return False, None
        # Choose latest name. seconds[0] is latest initial because it belongs to second candidate which is latest
        return fuzz.ratio(first[0], second[0]) >= weight, (first[0], second[0])

    @cache_match
    def name_1(self, weight=EXACT):
        """
        Match name_1 of given two candidates
        :param weight: Levenshtein distance
        """
        [first, second] = [getattr(self, name)(weight) for name in ['first_name', 'last_name']]
        return first[0] and second[0], (first[1], second[1])

    @cache_match
    def name_2(self, weight=EXACT):
        """
        Match name_2 of given two candidates
        :param weight: Levenshtein distance
        """
        return self.full_name(weight)

    @cache_match
    def name_3(self, weight=EXACT):
        """
        Match name_3 of given two candidates
        :param weight: Levenshtein distance
        """
        [first, second] = [getattr(self, name)(weight) for name in ['first_initial', 'last_name']]
        return first[0] and second[0], (first[1], second[1])

    @cache_match
    def name_4(self, weight=EXACT):
        """
        Match name_4 of given two candidates
        :param weight: Levenshtein distance
        """
        return self.last_name(weight)

    @cache_match
    def name_5(self, weight=EXACT):
        """
        Match name_5 of given two candidates
        :param weight: Levenshtein distance
        """
        return self.first_name(weight)

    @cache_match
    def job_title(self, weight=EXACT):
        """
        Match job_title of given two candidates
        :param weight: Levenshtein distance
        """
        experiences1 = list(set(map(lambda exp: exp.position, self.first.experiences or [])))
        experiences2 = list(set(map(lambda exp: exp.position, self.second.experiences or [])))
        positions = {
            'status': False,
            'first': [],
            'second': []
        }
        matched = 0
        for index1, first in enumerate(experiences1):
            index1 = index1 - matched
            first_sections = (first or '').strip().lower().split(' ')
            first_post = first_sections.pop(0)

            for index2, second in enumerate(experiences2):
                second_sections = (second or '').strip().lower().split(' ')
                second_post = second_sections.pop(0)

                post = None
                for posts in JOB_TITLE_VARIATIONS:
                    if first_post in posts and second_post in posts:
                        post = posts[-1]
                        break

                first_job_title = ' '.join(first_sections)
                second_job_title = ' '.join(second_sections)
                first_job_title = (post or first_post) + ' ' + first_job_title
                second_job_title = (post or second_post) + ' ' + second_job_title
                if fuzz.ratio(first_job_title, second_job_title) >= weight:
                    positions['status'] |= True
                    positions['first'].append((True, first))
                    positions['second'].append((True, second))
                    experiences1.pop(index1)
                    experiences2.pop(index2)
                    matched += 1
                    break
        positions['first'].extend(map(lambda item: (False, item), experiences1))
        positions['second'].extend(map(lambda item: (False, item), experiences2))

        return positions['status'], positions

    @cache_match
    def job_description(self, weight=EXACT):
        """
        Match job_description of given two candidates
        :param weight: Levenshtein distance
        """
        return self.match_list_value('experiences', 'description', weight=weight)

    @cache_match
    def job_start_date(self, weight=EXACT):
        """
        Match job start date of given two candidates
        :param weight: Levenshtein distance
        """
        for first in self.first.experiences or []:
            first_start_date = self.create_date(first.start_year, first.start_month, 1)
            for second in self.second.experiences or []:
                second_start_date = self.create_date(second.start_year, second.start_month, 1)
                if (first_start_date and second_start_date and first_start_date == second_start_date and fuzz.ratio(
                        first.position, second.position) >= weight):
                    return True, (first_start_date, second_start_date)
        return False, None

    @cache_match
    def job_end_date(self, weight=EXACT):
        """
        Match job end date of given two candidates
        :param weight: Levenshtein distance
        """
        for first in self.first.experiences or []:
            first_end_date = self.create_date(first.end_year, first.end_month, 1)
            for second in self.second.experiences or []:
                second_end_date = self.create_date(second.end_year, second.end_month, 1)
                if (first_end_date and second_end_date and first_end_date == second_end_date and fuzz.ratio(
                        first.position, second.position) >= weight):
                    return True, (first_end_date, second_end_date)
        return False, None

    @cache_match
    def school(self, weight=EXACT):
        """
        Match school name of given two candidates
        :param weight: Levenshtein distance
        """
        return self.match_list_value('educations', 'school_name', weight=weight)

    @cache_match
    def degree(self, weight=EXACT):
        """
        Match degrees names of given two candidates
        :param weight: Levenshtein distance
        """
        degrees1 = list(chain(*(map(lambda exp: exp.degrees or [], self.first.educations or []))))
        degrees2 = list(chain(*(map(lambda exp: exp.degrees or [], self.second.educations or []))))
        degrees = {
            'status': False,
            'first': [],
            'second': []
        }
        matched = 0
        for index1, first in enumerate(degrees1):
            index1 = index1 - matched
            title1 = first.title

            for index2, second in enumerate(degrees2):
                title2 = second.title
                for degree_titles in DEGREES:
                    if (title1 in degree_titles and title2 in degree_titles) \
                            or fuzz.ratio(title1, title2) >= weight:
                        degrees['status'] |= True
                        degrees['first'].append((True, first.title))
                        degrees['second'].append((True, second.title))
                        degrees1.pop(index1)
                        degrees2.pop(index2)
                        matched += 1
                        break
        degrees['first'].extend(map(lambda item: (False, item.title), degrees1))
        degrees['second'].extend(map(lambda item: (False, item.title), degrees2))

        return degrees['status'], degrees

    @cache_match
    def company(self, weight=EXACT):
        """
        Match company name of given two candidates
        :param weight: Levenshtein distance
        """
        return self.match_list_value('experiences', 'organization', weight=weight)

    @cache_match
    def location_1(self, weight=EXACT):
        """
        Match location_1 (Street address or PO Box) of given two candidates
        :param weight: Levenshtein distance
        """
        address_line_1 = self.match_list_value('addresses', 'address_line_1',
                                               comparator='match_address_line_1', weight=weight)
        po_box = self.match_list_value('addresses', 'po_box', weight=weight)
        if weight not in self.cache:
            self.cache[weight] = {}
        self.cache[weight]['address_line_1'] = address_line_1
        self.cache[weight]['po_box'] = po_box
        return address_line_1[0] or po_box[0], (address_line_1[1], po_box[1])

    @cache_match
    def location_2(self, weight=EXACT):
        """
        Match location_2 (city or zipcode) of given two candidates
        :param weight: Levenshtein distance
        """
        city = self.match_list_value('addresses', 'city', weight=weight)
        zip_code = self.match_list_value('addresses', 'zip_code', weight=weight)
        if weight not in self.cache:
            self.cache[weight] = {}
        self.cache[weight]['city'] = city
        self.cache[weight]['zip_code'] = zip_code
        return city[0] or zip_code[0], (city[1], zip_code[1])

    @cache_match
    def location_3(self, weight=EXACT):
        """
        Match location_3 (state or country) of given two candidates
        :param weight: Levenshtein distance
        """
        state = self.match_list_value('addresses', 'state', weight=weight)
        country = self.match_list_value('addresses', 'iso3166_country', weight=weight)
        return state[0] or country[0], (state[1], country[1])
