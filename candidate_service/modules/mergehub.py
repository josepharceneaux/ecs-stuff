"""
This module contains all functions and classes that will be used for Candidate De-Duping

Author: Zohaib Ijaz, QC-Technologies, <mzohaib.qc@gmail.com
"""
import re
from fuzzywuzzy import fuzz

from candidate_service.common.error_handling import InvalidUsage
from candidate_service.modules.track_changes import track_edits
from constants import (EXACT, DEGREES, ADDRESS_NOTATIONS)


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

    def __init__(self, first, second):
        """
        This class allows us to compare and merge two candidates' list objects like addresses, educations, degrees etc.
        """
        self.first = GtDict(first) if isinstance(first, dict) else first
        self.second = GtDict(second) if isinstance(second, dict) else second

        '''
        self.cache will contain information about candidate first and second match data.
        '''
        self.cache = {}
        # Match name, yes, high, medium or low
        self.match = None
        # How many match sets exist
        self.match_count = 0

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
                # TODO: @amir please confirm that is this comparison is right. I am doeing this in de-duping
                city_match = address1.city == address2.city
                zip_code_match = address1.zip_code == address2.zip_code
                if address1.id == address2.id or (address_line_1_match and city_match) or \
                        (address_line_1_match and zip_code_match):
                    is_same = True
                    track_edits(update_dict=address2, table_name='candidate_address',
                                candidate_id=self.first.id, user_id=self.first.user_id, query_obj=address1)
                    address1.update(**address2)
                    break
            if not is_same:
                addresses.append(address2)

        addresses += self.first.addresses or []
        return addresses

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

    def merge_educations(self, weight=EXACT):
        """
        This method matches candidate's existing educations with newly added educations
        """
        new_educations = []
        for education2 in self.second.educations or []:
            is_same_education = False
            for education_obj in self.first.educations or []:
                same_school = fuzz.ratio(education2.school_name, education_obj.school_name) >= weight
                same_city = education_obj.city == education2.city
                is_same_education = education_obj.id == education2.id or same_school and same_city
                if is_same_education:

                    new_educations.append((education2, education_obj))
                    track_edits(update_dict=education2, table_name='candidate_education',
                                candidate_id=self.first.id, user_id=self.first.user_id, query_obj=education_obj)
                    education_obj.update(**education2)
                    break
            if not is_same_education:
                new_educations.append((education2, None))

        return new_educations

    def merge_degrees(self, degrees1, degrees2, weight=EXACT):
        """
        This method compares degrees of existing education with degrees of new education
        """
        degree_fields = ["degree_type", "start_year", "start_month", "end_year", "end_month"]
        degrees, new_degrees = [], []
        for degree2 in degrees2 or []:
            is_same_degree = False
            for degree_obj in degrees1 or []:
                if degree_obj.id and degree2.id and degree_obj.id != degree2.id:
                    continue
                if degree_obj.id and degree2.id and degree_obj.id == degree2.id:
                    is_same_degree = True
                    start_year = degree2.get('start_year')
                    end_year = degree2.get('end_year')
                    # If start year needs to be updated, it cannot be greater than existing end year
                    if start_year and not end_year and (start_year > degree_obj.end_year):
                        raise InvalidUsage('Start year ({}) cannot be greater than end year ({})'.format(
                            start_year, degree_obj.end_year))

                    # If end year needs to be updated, it cannot be less than existing start year
                    if end_year and not start_year and (end_year < degree_obj.start_year):
                        raise InvalidUsage('End year ({}) cannot be less than start year ({})'.format(
                            end_year, degree_obj.start_year))
                is_same_title = False
                for degree_titles in DEGREES:
                    degree_titles = [val.lower() for val in degree_titles]
                    old_title = (degree_obj.degree_title or '').lower()
                    new_title = (degree2.degree_title or '').lower()
                    if (old_title in degree_titles and new_title in degree_titles) \
                            or fuzz.ratio(old_title, new_title) >= weight:
                        is_same_title = True

                if is_same_title and all(getattr(degree_obj, key) == getattr(degree2, key) for key in degree_fields):
                    is_same_degree = True
                if is_same_degree:
                    new_degrees.append((degree2, degree_obj))
                    track_edits(update_dict=degree2, table_name='candidate_education_degree',
                                candidate_id=self.first.id, user_id=self.first.user_id, query_obj=degree_obj)
                    degree_obj.update(**degree2)
                    break
            if not is_same_degree:
                degrees.append(degree2)
                new_degrees.append((degree2, None))
        return new_degrees

    def merge_bullets(self, bullets1, bullets2, weight=EXACT):
        """
        This method compares degree's existing bullets with newly added bullets
        """
        new_bullets = []
        for bullet2 in bullets2 or []:
            is_same_bullet = False
            for bullet1 in bullets1 or []:
                if bullet1.id and bullet2.id and bullet1.id != bullet2.id:
                    continue
                if bullet1.id and bullet2.id and bullet1.id == bullet2.id:
                    is_same_bullet = True

                # TODO: @amir, help me to determine the conditions for bullet match
                if bullet1.concentration_type == bullet2.concentration_type:
                    is_same_bullet = True
                if is_same_bullet:
                    new_bullets.append((bullet2, bullet1))
                    track_edits(update_dict=bullet2,
                                table_name='candidate_education_degree_bullet',
                                candidate_id=self.first.id, user_id=self.first.user_id,
                                query_obj=bullet1)
                    bullet1.update(**bullet2)
                    break
            if not is_same_bullet:
                new_bullets.append((bullet2, None))
        return new_bullets
