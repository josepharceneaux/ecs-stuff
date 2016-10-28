from candidate_service.common.utils.datetime_utils import DatetimeUtils
from candidate_service.common.models.candidate_edit import CandidateEdit


def fetch_candidate_edits(candidate_id):
    """
    :type candidate_id:  int|long
    :rtype:  list[dict]
    """
    all_edits = []
    for edit in CandidateEdit.get_by_candidate_id(candidate_id):

        table_and_field_names_tuple = CandidateEdit.get_table_and_field_names_from_id(edit.field_id)
        edit_datetime = edit.edit_datetime

        all_edits.append(
            {
                'user_id': edit.user_id,
                'table_name': table_and_field_names_tuple[0],
                'field_name': table_and_field_names_tuple[1],
                'old_value': edit.old_value,
                'new_value': edit.new_value,
                'edit_action': CandidateEdit.actions.get(edit.edit_action),
                'is_custom_field': edit.is_custom_field,
                'edit_datetime': DatetimeUtils.to_utc_str(edit_datetime) if edit_datetime else None,
                'edit_type': edit.edit_type or 0
            }
        )
    return all_edits
