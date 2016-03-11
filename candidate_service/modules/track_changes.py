"""
This file entails functions that will help keep track of all changes made to candidate(s)
Possible changes include:
      i. any updates
     ii. any deletes
    iii. any additions
"""
from candidate_service.common.models.db import db
from candidate_service.common.models.candidate_edit import CandidateEdit
from candidate_service.common.models.candidate import (
    Candidate, CandidateAddress, CandidateCustomField, CandidateEducation, CandidateEducationDegree,
    CandidateEducationDegreeBullet, CandidateExperience, CandidateExperienceBullet, CandidateWorkPreference,
    CandidateEmail, CandidatePhone, CandidateMilitaryService, CandidatePreferredLocation, CandidateSkill,
    CandidateSocialNetwork, CandidatePhoto
)


def _track_candidate_edits(update_dict, candidate, user_id, edit_datetime):
    """
    :type candidate:  Candidate
    """
    for field in update_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id(table_name='candidate', field_name=field)
        if not field_id:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,  # TODO: Null if Openweb, otherwise ID of the user updating
            candidate_id=candidate.id,
            field_id=field_id,
            old_value=getattr(candidate, field),
            new_value=update_dict.get(field),
            edit_datetime=edit_datetime
        ))


def _track_candidate_address_edits(address_dict, candidate_id, user_id, edit_time, candidate_address=None):
    """
    :type candidate_address:  CandidateAddress
    """
    for field in address_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_address', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value = getattr(candidate_address, field) if candidate_address else None
        new_value = address_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,    # TODO: Null if Openweb, otherwise ID of the user updating
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_time
        ))


def _track_areas_of_interest_edits(area_of_interest_id, candidate_id, user_id, edit_datetime):
    """
    Currently, only adding an area of interest is permitted, so this function will assume
     old_value to be null, and new_value to be the ID of the area of interest
    """
    field_id = CandidateEdit.get_field_id('candidate_area_of_interest', 'area_of_interest_id')
    old_value, new_value = None, area_of_interest_id
    db.session.add(CandidateEdit(
        user_id=user_id,
        candidate_id=candidate_id,
        field_id=field_id,
        old_value=old_value,
        new_value=new_value,
        edit_datetime=edit_datetime
    ))


def _track_custom_field_edits(custom_field_dict, candidate_id, user_id, edit_datetime, candidate_custom_field=None):
    """
    :type candidate_custom_field:  CandidateCustomField
    """
    for field in custom_field_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_custom_field', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value = getattr(candidate_custom_field, field) if candidate_custom_field else None
        new_value = custom_field_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,    # TODO: Null if Openweb, otherwise ID of the user updating
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            is_custom_field=True,
            edit_datetime=edit_datetime
        ))


def _track_education_edits(education_dict, candidate_id, user_id, edit_datetime, candidate_education=None):
    """
    :type candidate_education:  CandidateEducation
    """
    for field in education_dict:

        # If field_id is not found, do not add to record
        field_id = CandidateEdit.get_field_id('candidate_education', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value = getattr(candidate_education, field) if candidate_education else None
        new_value = education_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,    # TODO: Null if Openweb, otherwise ID of the user updating
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_datetime
        ))


def _track_education_degree_edits(degree_dict, candidate_id, user_id, edit_datetime, candidate_education_degree=None):
    """
    :type candidate_education_degree:  CandidateEducationDegree
    """
    for field in degree_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_education_degree', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value = getattr(candidate_education_degree, field) if candidate_education_degree else None
        new_value = degree_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,    # TODO: Null if Openweb, otherwise ID of the user updating
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_datetime
        ))


def _track_education_degree_bullet_edits(degree_bullet_dict, candidate_id, user_id, edit_datetime,
                                         candidate_education_degree_bullet=None):
    """
    :type candidate_education_degree_bullet:  CandidateEducationDegreeBullet
    """
    for field in degree_bullet_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_education_degree_bullet', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value = getattr(candidate_education_degree_bullet, field) if candidate_education_degree_bullet else None
        new_value = degree_bullet_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,    # TODO: Null if Openweb, otherwise ID of the user updating
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_datetime
        ))


def _track_work_experience_edits(experience_dict, candidate_id, user_id, edit_datetime, candidate_experience=None):
    """
    :type candidate_experience:  CandidateExperience
    """
    for field in experience_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_experience', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value = getattr(candidate_experience, field) if candidate_experience else None
        new_value = experience_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_datetime
        ))


def _track_work_experience_bullet_edits(bullet_dict, candidate_id, user_id, edit_datetime,
                                        candidate_experience_bullet=None):
    """
    :type candidate_experience_bullet:  CandidateExperienceBullet
    """
    for field in bullet_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_experience_bullet', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value = getattr(candidate_experience_bullet, field) if candidate_experience_bullet else None
        new_value = bullet_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_datetime
        ))


def _track_work_preference_edits(work_preference_dict, candidate_id, user_id, edit_datetime,
                                 candidate_work_preference=None):
    """
    :type candidate_work_preference:  CandidateWorkPreference
    """
    for field in work_preference_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_work_preference', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value = getattr(candidate_work_preference, field) if candidate_work_preference else None
        new_value = work_preference_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_datetime
        ))


def _track_email_edits(email_dict, candidate_id, user_id, edit_datetime, candidate_email=None):
    """
    :type candidate_email:  CandidateEmail
    """
    for field in email_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_email', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value = getattr(candidate_email, field) if candidate_email else None
        new_value = email_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_datetime
        ))


def _track_phone_edits(phone_dict, candidate_id, user_id, edit_datetime, candidate_phone=None):
    """
    :type candidate_phone:  CandidatePhone
    """
    for field in phone_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_phone', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value = getattr(candidate_phone, field) if candidate_phone else None
        new_value = phone_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_datetime
        ))


def _track_military_service_edits(military_service_dict, candidate_id,  user_id, edit_datetime,
                                  candidate_military_service=None):
    """
    :type candidate_military_service:  CandidateMilitaryService
    """
    for field in military_service_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_military_service', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value = getattr(candidate_military_service, field) if candidate_military_service else None
        new_value = military_service_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_datetime
        ))


def _track_preferred_location_edits(preferred_location_dict, candidate_id, user_id,
                                    edit_datetime, candidate_preferred_location=None):
    """
    :type candidate_preferred_location:  CandidatePreferredLocation
    """
    for field in preferred_location_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_preferred_location', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value = getattr(candidate_preferred_location, field) if candidate_preferred_location else None
        new_value = preferred_location_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_datetime
        ))


def _track_skill_edits(skill_dict, candidate_id, user_id, edit_datetime, candidate_skill=None):
    """
    :type candidate_skill:  CandidateSkill
    """
    for field in skill_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_skill', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value = getattr(candidate_skill, field) if candidate_skill else None
        new_value = skill_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_datetime
        ))


def _track_social_network_edits(sn_dict, candidate_id, user_id, edit_datetime, candidate_social_network=None):
    """
    :type candidate_social_network:  CandidateSocialNetwork
    """
    for field in sn_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_social_network', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value = getattr(candidate_social_network, field) if candidate_social_network else None
        new_value = sn_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_datetime
        ))


def _track_candidate_photo_edits(photo_dict, candidate_photo, candidate_id, user_id, edit_datetime):
    """
    :type candidate_photo:  CandidatePhoto
    """
    for field in photo_dict:
        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_photo', field)
        if not field:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_photo, field), photo_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_datetime
        ))
