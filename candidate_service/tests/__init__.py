import uuid
import datetime

from candidate_service.candidate_app import db
from candidate_service.modules.talent_candidates import create_or_update_candidate_from_params

# Various U.S. locations in (city, state, zipcode) format, which can be used to populate candidate locations
VARIOUS_US_LOCATIONS = (('San Jose', 'CA', '95132'), ('Providence', 'Rhode Island', '02905'),
                        ('Lubbock', 'Texas', '79452'), ('Philadelphia', 'Pennsylvania', '19184'),
                        ('Delray Beach', 'Florida', '33448'), ('Houston', 'Texas', '77080'),
                        ('Boston', 'Massachusetts', '02163'), ('Fairbanks', 'Alaska', '99709'),
                        ('Los Angeles', 'California', '90087'), ('Clearwater', 'Florida', '34615'),
                        ('Seattle', 'Washington', '98158'))


def populate_candidates(owner_user_id, count=1, first_name=True, last_name=True, added_time=True, objective=False,
                        phone=False, current_company=False, current_title=False, candidate_text_comment=False,
                        source_id=None, city=False, state=False, zip_code=False, area_of_interest_ids=None,
                        university=False, major=False, degree=False, university_start_year=False,
                        university_start_month=False, graduation_year=False, graduation_month=False,
                        military_branch=False, military_status=False, military_grade=False, military_to_date=False,
                        candidate_skill_dicts=None, custom_fields_dict=None, candidate_experience_dicts=None,
                        update_now=True):
    """
    :param count:
    :param owner_user_id:
    :param first_name:
    :type first_name: bool | str
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
    # TODO: Update function as search service is merged
    candidate_ids = []
    for i in range(count):
        data = {
            'id': 'Not yet assigned',
            'first_name': {True: uuid.uuid4().__str__()[0:8], False: None}.get(first_name, first_name),
            'last_name': {True: uuid.uuid4().__str__()[0:8], False: None}.get(last_name, last_name),
            'added_time': {True: datetime.datetime.now(), False: None}.get(added_time, added_time),
            'email': [{'label': 'primary', 'address': '%s@candidate.example.com' % (uuid.uuid4().__str__())}],
            'objective': {True: uuid.uuid4().__str__()[0:8], False: None}.get(objective, objective),
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
            'military_to_date': {True: datetime.datetime.today(), False: None}.get(military_to_date, military_to_date),
            'source_id': source_id,
            'area_of_interest_ids': area_of_interest_ids,
            'candidate_skill_dicts': candidate_skill_dicts,
            'custom_fields_dict': custom_fields_dict,
            'candidate_experience_dicts': candidate_experience_dicts,
        }
        candidate = create_or_update_candidate_from_params(
            owner_user_id,
            first_name=data['first_name'],
            last_name=data['last_name'],
            added_time=data['added_time'],
            objective=data['objective'],
            # domain_can_read=True,
            # domain_can_write=True,
            emails=data['email'],
            phones=None,
            # current_company=data['current_company'],
            # current_title=data['current_title'],
            source_id=data['source_id'],
            # city=data['city'],
            # state=data['state'],
            # zip_code=data['zip_code'],
            # country_id=1,
            # area_of_interest_ids=data['area_of_interest_ids'],
            # university=data['university'],
            # major=data['major_name'],
            # candidate_skill_dicts=data['candidate_skill_dicts'],
            # custom_fields_dict=data['custom_fields_dict'],
            # candidate_experience_dicts=data['candidate_experience_dicts'],
            # degree=data['degree'],
            # military_branch=data['military_branch'],
            # military_status=data['military_status'],
            # military_grade=data['military_grade'],
            # military_to_date=data['military_to_date'],
            )
        candidate_ids.append(candidate['candidate_id'])

    if update_now:
        # Will immediately updated candidates in db and cloudsearch
        db.session.commit()
        # Update cloud_search
        # upload_candidate_documents(candidate_ids) TODO when search service is merged
    return candidate_ids


def _update_now(candidate_ids):
    """
    If update_now is set to False in populate_candidates function, then call this function to update them all at once.
    :param candidate_ids: list of candidate ids to sent to cloudsearch to update candidate.
    :return:
    """
    db.session.commit()
    # Update cloudsearch
    # upload_candidate_documents(candidate_ids) # TODO
    return
