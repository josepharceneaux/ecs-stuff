"""
This file entails functions that will help keep track of all changes made to candidate(s)
Possible changes include:
      i. any updates
     ii. any deletes
    iii. any additions
"""
import datetime
from candidate_service.common.models.db import db
from candidate_service.common.models.candidate_edit import CandidateEdit


def track_edits(update_dict, table_name, candidate_id, user_id, query_obj=None):
    for field in update_dict:
        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id(table_name, field)
        if not field_id:
            continue

        # Do not add record if old_value and new_value are equal
        old_value = getattr(query_obj, field) if query_obj else None
        new_value = update_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_datetime=datetime.datetime.utcnow()
        ))


def track_areas_of_interest_edits(area_of_interest_id, candidate_id, user_id, edit_datetime):
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
