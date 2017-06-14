"""
This module contains all functions and classes that will be used for Candidate De-Duping

Author: Zohaib Ijaz, QC-Technologies, <mzohaib.qc@gmail.com
"""

from candidate_service.common.error_handling import InvalidUsage
from candidate_service.common.utils.helpers import GtDict
from candidate_service.modules.track_changes import track_edits


class MergeHub(object):

    def __init__(self, existing_candidate, new_candidate):
        """
        This class allows us to compare and merge two candidates' list objects like addresses, educations, degrees etc.
        """
        self.existing_candidate = GtDict(existing_candidate
                                         ) if isinstance(existing_candidate, dict) else existing_candidate
        self.new_candidate = GtDict(new_candidate) if isinstance(new_candidate, dict) else new_candidate

    def merge_addresses(self):
        """
        This method combines addresses of first and second candidates into addresses of first candidate.
        Address objects looks like this
        {
            'is_default': True,
            'city': u'San Jose',
            'state': u'CA',
            'candidate_id': 1085L,
            'resume_id': 1085L,
            'coordinates': '37.3382082,-121.8863286'
        }

        We have list of address dict (GtDict) objects that end-user want to add or update in existing
        addresses of a specific candidate. We will loop over new es and will compare each new degree object with all
        existing candidate's addresses objects and if it matches, we will update existing addresses object with new
        address object (dict) data and will append in addresses list.
        :return: list of addresses
        """
        addresses = []
        for new_address in self.new_candidate.addresses or []:
            is_same_address = False
            for existing_address_obj in self.existing_candidate.addresses or []:
                if existing_address_obj == new_address:
                    is_same_address = True
                    track_edits(update_dict=new_address, table_name='candidate_address',
                                candidate_id=self.existing_candidate.id, user_id=self.existing_candidate.user_id,
                                query_obj=existing_address_obj)
                    existing_address_obj.update(**new_address)
                    break
            if not is_same_address:
                addresses.append(new_address)

        addresses += self.existing_candidate.addresses or []
        return addresses

    def merge_educations(self):
        """
        This method matches candidate's existing educations with newly added educations
        Education objects looks like this
        {
            'school_type': u'college',
            'city': u'North Maren',
            'state': u'Florida',
            'is_current': True,
            list_order': 1,
            'school_name': u'westvalley',
            'iso3166_country': u'NI'
        }

        We have list of education dict (GtDict) objects that end-user want to add or update in existing
        educations of a specific candidate. We will loop over new degrees and will compare each new degree object with
        all existing candidate's education objects and if it matches, we will update existing education object with new
        education object (dict) data and will append a tuple (new_education, existing_education) in degrees list and if
        it will not match, we will append tuple (new_education, None) in degrees list.
        """
        educations = []
        for new_education in self.new_candidate.educations or []:
            is_same_education = False
            for existing_education in self.existing_candidate.educations or []:
                if existing_education == new_education:
                    is_same_education = True
                    educations.append((new_education, existing_education))
                    track_edits(update_dict=new_education, table_name='candidate_education',
                                candidate_id=self.existing_candidate.id, user_id=self.existing_candidate.user_id,
                                query_obj=existing_education)
                    existing_education.update(**new_education)
                    break
            if not is_same_education:
                educations.append((new_education, None))

        return educations

    def merge_degrees(self, existing_degrees, new_degrees):
        """
        This method compares degrees of existing education with degrees of new education
        EducationDegree objects looks like this
        {
            'start_month': 11,
            'start_year': 2002,
            'end_year': 2006,
            'degree_type': u'ms',
            'end_month': 12,
            'end_time': datetime.datetime(2006, 12, 1, 0, 0),
            'degree_title': u'M.Sc',
            'gpa_num': 1.5
        }

        We have list of education degrees dict (GtDict) objects that end-user want to add or update in existing
        degrees of a specific candidate. We will loop over new degrees and will compare each new degree object with all
        existing candidate's degree objects and if it matches, we will update existing degree object with new degree
        object (dict) data and will append a tuple (new_degree, existing degree) in degrees list and if it will not
        match, we will append tuple (new_degree, None) in degrees list.
        """
        degrees = []
        for new_degree in new_degrees or []:
            is_same_degree = False
            for existing_degree_obj in existing_degrees or []:
                start_year = new_degree.start_year
                end_year = new_degree.end_year
                # If start year needs to be updated, it cannot be greater than existing end year
                if start_year and not end_year and (start_year > existing_degree_obj.end_year):
                    raise InvalidUsage('Start year ({}) cannot be greater than end year ({})'.format(
                        start_year, existing_degree_obj.end_year))

                # If end year needs to be updated, it cannot be less than existing start year
                if end_year and not start_year and (end_year < existing_degree_obj.start_year):
                    raise InvalidUsage('End year ({}) cannot be less than start year ({})'.format(
                        end_year, existing_degree_obj.start_year))

                if existing_degree_obj == new_degree:
                    is_same_degree = True
                    degrees.append((new_degree, existing_degree_obj))
                    track_edits(update_dict=new_degree, table_name='candidate_education_degree',
                                candidate_id=self.existing_candidate.id, user_id=self.existing_candidate.user_id,
                                query_obj=existing_degree_obj)
                    existing_degree_obj.update(**new_degree)
                    break
            if not is_same_degree:
                degrees.append((new_degree, None))
        return degrees

    def merge_bullets(self, bullets1, bullets2):
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

                if bullet1.concentration_type == bullet2.concentration_type:
                    is_same_bullet = True
                if is_same_bullet:
                    new_bullets.append((bullet2, bullet1))
                    track_edits(update_dict=bullet2,
                                table_name='candidate_education_degree_bullet',
                                candidate_id=self.existing_candidate.id, user_id=self.existing_candidate.user_id,
                                query_obj=bullet1)
                    bullet1.update(**bullet2)
                    break
            if not is_same_bullet:
                new_bullets.append((bullet2, None))
        return new_bullets
