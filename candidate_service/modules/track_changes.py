"""
This file entails functions that will help keep track of all changes made to candidate(s)
Possible changes include:
      i. any updates
     ii. any deletes
    iii. any additions
"""
from candidate_service.common.models.db import db
from candidate_service.common.models.candidate_edit import CandidateEdit


def _track_candidate_edits(update_dict, candidate, user_id, edit_time):
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
            edit_datetime=edit_time
        ))


def _track_candidate_address_edits(address_dict, candidate_id, candidate_address, user_id, edit_time):
    for field in address_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_address', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_address, field), address_dict.get(field)
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


def _track_candidate_custom_field_edits(custom_field_dict, candidate_custom_field,
                                        candidate_id, user_id, edit_time):
    for field in custom_field_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_custom_field', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_custom_field, field), custom_field_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,    # TODO: Null if Openweb, otherwise ID of the user updating
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            is_custom_field=True,
            edit_datetime=edit_time
        ))


def _track_candidate_education_edits(education_dict, candidate_education,
                                     candidate_id, user_id, edit_time):
    for field in education_dict:

        # If field_id is not found, do not add to record
        field_id = CandidateEdit.get_field_id('candidate_education', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_education, field), education_dict.get(field)
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


def _track_candidate_education_degree_edits(degree_dict, candidate_education_degree,
                                            candidate_id, user_id, edit_time):
    for field in degree_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_education_degree', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_education_degree, field), degree_dict.get(field)
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


def _track_candidate_education_degree_bullet_edits(degree_bullet_dict, candidate_education_degree_bullet,
                                                   candidate_id, user_id, edit_time):
    for field in degree_bullet_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_education_degree_bullet', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_education_degree_bullet, field), degree_bullet_dict.get(field)
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


def _track_candidate_experience_edits(experience_dict, candidate_experience, candidate_id,
                                      user_id, edit_time):
    for field in experience_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_experience', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_experience, field), experience_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_time
        ))


def _track_candidate_experience_bullet_edits(bullet_dict, candidate_experience_bullet, candidate_id,
                                             user_id, edit_time):
    for field in bullet_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_experience_bullet', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_experience_bullet, field), bullet_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_time
        ))


def _track_candidate_work_preference_edits(work_preference_dict, candidate_work_preference,
                                           candidate_id, user_id, edit_time):
    for field in work_preference_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_work_preference', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_work_preference, field), work_preference_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_time
        ))


def _track_candidate_email_edits(email_dict, candidate_email, candidate_id, user_id, edit_time):
    for field in email_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_email', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_email, field), email_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_time
        ))


def _track_candidate_phone_edits(phone_dict, candidate_phone, candidate_id, user_id, edit_time):
    for field in phone_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_phone', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_phone, field), phone_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_time
        ))


def _track_candidate_military_service_edits(military_service_dict, candidate_military_service,
                                            candidate_id, user_id, edit_time):
    for field in military_service_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_military_service', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_military_service, field), military_service_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_time
        ))


def _track_candidate_preferred_location_edits(preferred_location_dict, candidate_preferred_location,
                                              candidate_id, user_id, edit_time):
    for field in preferred_location_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_preferred_location', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_preferred_location, field), preferred_location_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_time
        ))


def _track_candidate_skill_edits(skill_dict, candidate_skill, candidate_id, user_id, edit_time):
    for field in skill_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_skill', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_skill, field), skill_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_time
        ))


def _track_candidate_social_network_edits(sn_dict, candidate_social_network, candidate_id, user_id, edit_time):
    for field in sn_dict:

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id('candidate_social_network', field)
        if not field_id:
            continue

        # If old_value and new_value are equal, do not add record
        old_value, new_value = getattr(candidate_social_network, field), sn_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=edit_time
        ))


def _track_candidate_photo_edits(photo_dict, candidate_photo, candidate_id, user_id, edit_time):
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
            edit_datetime=edit_time
        ))
