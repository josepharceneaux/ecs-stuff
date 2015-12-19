__author__ = 'ufarooqi'

import uuid
import time
from datetime import datetime
import json
import requests
from random import randint
from faker import Faker
from ..routes import CandidateApiUrl

fake = Faker()

# Various U.S. locations in (city, state, zipcode) format, which can be used to populate candidate locations
VARIOUS_US_LOCATIONS = (('San Jose', 'CA', '95132'), ('Providence', 'Rhode Island', '02905'),
                        ('Lubbock', 'Texas', '79452'), ('Philadelphia', 'Pennsylvania', '19184'),
                        ('Delray Beach', 'Florida', '33448'), ('Houston', 'Texas', '77080'),
                        ('Boston', 'Massachusetts', '02163'), ('Fairbanks', 'Alaska', '99709'),
                        ('Los Angeles', 'California', '90087'), ('Clearwater', 'Florida', '34615'),
                        ('Seattle', 'Washington', '98158'))


def populate_candidates(oauth_token, count=1, first_name=True, middle_name=False, last_name=True,
                        added_time=True, objective=False, current_company=False, current_title=False,
                        candidate_text_comment=False, source_id=None, city=False, state=False, zip_code=False,
                        area_of_interest_ids=None, university=False, major=False, degree=False,
                        military_branch=False, military_status=False, military_grade=False,
                        military_to_date=False, military_from_date=False, candidate_skill_dicts=None,
                        custom_fields_dict=None, candidate_experience_dicts=None, talent_pool_id=None):
    """
    :param count:
    :param owner_user_id:
    :param first_name:
    :type first_name: bool | str
    :param middle_name:
    :type middle_name: bool | str
    :param last_name:
    :type last_name: bool | str
    :param added_time:
    :type added_time: bool | datetime.date
    :param objective:
    :type objective: bool | str
    :param phone:
    :param current_company:
    :type current_company: bool | str
    :param current_title:
    :type current_title: bool | str
    :param candidate_text_comment:
    :type candidate_text_comment: bool | str
    :param source_id:
    :type source_id: None | int
    :param city:
    :type city: bool | str
    :param state:
    :type state: bool | str
    :param zip_code:
    :type zip_code: bool | str | long
    :param area_of_interest_ids: List of areas of interest ids
    :type area_of_interest_ids: None | list[int]
    :param university:
    :type university: bool | str
    :param major:
    :type major: bool | str
    :param degree:
    :type degree: bool | str
    :param university_start_year:
    :param university_start_month:
    :param graduation_year:
    :param graduation_month:
    :param military_branch:
    :type military_branch: bool | str
    :param military_status:
    :type military_status: bool | str
    :param military_grade:
    :type military_grade: bool | str
    :param military_to_date:
    :type military_to_date: datetime.date
    :param military_from_date:
    :type military_from_date: datetime.date
    :param candidate_skill_dicts
    :type candidate_skill_dicts: None | list[dict[basestring, basestring | integer | datetime.date]]
    :param custom_fields_dict: custom_field_id -> value
    :type custom_fields_dict: dict[int, str] | None
    :param candidate_experience_dicts: dicts of organization, position, startMonth, startYear, endMonth, endYear,
    isCurrent
    :type candidate_experience_dicts: None | list[dict[basestring, int | basestring | list]]
    :param update_now: Will update immediately after creating all candidates. Set it to False, if willing to create
    different combination of candidates and update at last to save time.
    :return:
    """
    candidate_ids = []
    work_experiences = {}
    addresses = {}
    educations = {}
    email_address = {}
    military_services = {}
    degree_dict = {}
    degree_bullets_dict = {}
    aoi_ids = list()
    custom_fields_list = list()
    talent_pool_ids = list()

    for i in range(count):
        data = {
            'id': 'Not yet assigned',
            'first_name': {True: uuid.uuid4().__str__()[0:8], False: None}.get(first_name, first_name),
            'middle_name': {True: uuid.uuid4().__str__()[0:8], False: None}.get(middle_name, middle_name),
            'last_name': {True: uuid.uuid4().__str__()[0:8], False: None}.get(last_name, last_name),
            'added_time': {True: datetime.now(), False: None}.get(added_time, added_time),
            'email': '%s@candidate.example.com' % (uuid.uuid4().__str__()),
            'objective': {True: uuid.uuid4().__str__()[0:8], False: None}.get(objective, objective),
            'candidate_text_comment': {True: '\n'.join(fake.sentences()), False: None}.get(
                candidate_text_comment, candidate_text_comment),
            'city': {True: VARIOUS_US_LOCATIONS[0][0], False: None}.get(city, city),
            'state': {True: VARIOUS_US_LOCATIONS[0][1], False: None}.get(state, state),
            'zip_code': {True: VARIOUS_US_LOCATIONS[0][2], False: None}.get(zip_code, zip_code),
            'current_company': {True: uuid.uuid4().__str__()[0:8], False: None}.get(current_company, current_company),
            'current_title': {True: uuid.uuid4().__str__()[0:8], False: None}.get(current_title, current_title),
            'university': {True: uuid.uuid4().__str__()[0:8], False: None}.get(university, university),
            'major_name': {True: uuid.uuid4().__str__()[0:8], False: None}.get(major, major),
            'degree': {True: uuid.uuid4().__str__()[0:8], False: None}.get(degree, degree),
            'military_branch': {True: uuid.uuid4().__str__()[0:8], False: None}.get(military_branch, military_branch),
            'military_status': {True: uuid.uuid4().__str__()[0:8], False: None}.get(military_status, military_status),
            'military_grade': {True: uuid.uuid4().__str__()[0:8], False: None}.get(military_grade, military_grade),
            'military_from_date': {True: datetime.strptime(fake.date(), "%Y-%m-%d"), False: None}.get(
                military_from_date, military_from_date),
            'military_to_date': {True: datetime.today(), False: None}.get(military_to_date, military_to_date),
            'source_id': source_id,
            'area_of_interest_ids': area_of_interest_ids,
            'candidate_skill_dicts': candidate_skill_dicts,
            'custom_fields_dict': custom_fields_dict,
            'candidate_experience_dicts': candidate_experience_dicts,
        }

        if data['email']:
            email_address['address'] = data['email']
        if data['current_company'] or data['current_title']:
            work_experiences['organization'] = data['current_company']
            work_experiences['position'] = data['current_title']
        if data['city'] or data['state'] or data['zip_code']:
            addresses['city'] = data['city']
            addresses['state'] = data['state']
            addresses['zip_code'] = data['zip_code']
        if data['university'] or data['degree'] or data['major_name']:
            educations['school_name'] = data['university']
            degree_dict['type'] = data['degree']
            educations['degrees'] = [degree_dict]
            degree_bullets_dict['major'] = data['major_name']
            degree_dict['bullets'] = [degree_bullets_dict]
        if data['military_branch'] or data['military_status'] or data['military_grade']:
            military_services['service_status'] = data['military_status']
            military_services['branch'] = data['military_branch']
            military_services['highest_grade'] = data['military_grade']
            military_services['from_date'] = data['military_from_date']
            military_services['to_date'] = data['military_to_date']
            military_services['highest_rank'] = randint(0, 3)
        if data['area_of_interest_ids']:
            aoi_ids = [{"area_of_interest_id": aoi_id} for aoi_id in data['area_of_interest_ids']]
        if data['custom_fields_dict']:
            custom_fields_list.append(data['custom_fields_dict'])
        if talent_pool_id:
            talent_pool_ids = {'add': [talent_pool_id]}

        candidate = dict(
            first_name=data['first_name'],
            last_name=data['last_name'],
            emails=[email_address],
            work_experiences=[work_experiences] if work_experiences else None,
            source_id=data['source_id'],
            addresses=[addresses] if addresses else None,
            educations=[educations] if educations else None,
            areas_of_interest=aoi_ids,
            military_services=[military_services] if military_services else None,
            skills=data['candidate_skill_dicts'],
            custom_fields=custom_fields_list,
            talent_pool_ids=talent_pool_ids
            # major=data['major_name'],
            # candidate_experience_dicts=data['candidate_experience_dicts'],
        )

        candidate = dict((k, v) for k, v in candidate.iteritems() if v)

        try:
            r = requests.post(CandidateApiUrl.CANDIDATES, data=json.dumps({'candidates': [candidate]}),
                              headers={'Authorization': 'Bearer %s' % oauth_token})

            if r.status_code == 201:
                candidate_ids.append(r.json().get('candidates')[0].get('id'))
            else:
                raise Exception('Response body: %s, Status code: %s' % (r.json(), r.status_code))

        except Exception as e:
            print "Couldn't create candidate because: %s" % e.message

    return candidate_ids


def search_candidates(access_token, params):
    # wait for cloud-search to update the candidates.
    time.sleep(30)
    response = requests.get(
        url=CandidateApiUrl.CANDIDATE_SEARCH_URI, params=params, headers={
            'Authorization': 'Bearer %s' % access_token, 'Content-type': 'application/json'}
    )
    return response


def assert_results(candidate_ids, response):
    """
    Assert statements for all search results
    :param candidate_ids: list of candidate ids created by the authorized user under same domain
    :param resultant_candidates: list of candidate ids from the search results
    :return:
    """
    resultant_candidate_ids = [long(candidate['id']) for candidate in response['candidates']]
    print candidate_ids
    print resultant_candidate_ids

    # Test whether every element in the set candidate_ids is in resultant_candidate_ids.
    assert set(candidate_ids) == set(resultant_candidate_ids)