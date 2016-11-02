"""
This file entails functions that will help keep track of all changes made to candidate(s)
Possible changes include:
      i. any updates
     ii. any deletes
    iii. any additions
"""
from datetime import datetime
from candidate_service.common.models.db import db
from candidate_service.common.models.candidate_edit import CandidateEdit


def track_edits(update_dict, table_name, candidate_id, user_id, edit_action=None,
                query_obj=None, value=None, column_name=None):
    """
    Function will insert
    :param update_dict:  dict data that contains candidate's updated information
    :param table_name:  name of the candidate table that's record must be updated
    :param candidate_id:  candidate's ID
    :param user_id:  candidate's owner user's ID
    :param edit_action: action used to edit record(s); e.g. added, deleted, updated
    :param query_obj:  mysql query object
    :param value: new value for updating
    :param column_name: name of the table-column. This should only be provided if update_dict's
                        key(s) do not match any of table's column's name
    """
    # TODO: use CandidateEdit.actions once facebook's graphql is implemented and the module codes have been updated

    for iteration, field in enumerate(update_dict, start=1):

        if column_name and iteration == 1:
            field = column_name

        # If field_id is not found, do not add record
        field_id = CandidateEdit.get_field_id(table_name, field)
        if not field_id:
            continue

        # Do not add record if old_value and new_value are equal
        old_value = getattr(query_obj, field) if query_obj else None
        new_value = value if value else update_dict.get(field)
        if old_value == new_value:
            continue

        db.session.add(CandidateEdit(
            user_id=user_id,
            candidate_id=candidate_id,
            field_id=field_id,
            old_value=old_value,
            new_value=new_value,
            edit_action=edit_action,
            edit_datetime=datetime.utcnow(),
            is_custom_field=True if table_name == 'candidate_custom_field' else False
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
