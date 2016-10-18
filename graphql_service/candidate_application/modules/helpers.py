"""
Common/helper functions
"""
import datetime
from deepdiff import DeepDiff
from graphql_service.common.utils.datetime_utils import DatetimeUtils


def remove_duplicates(collection):
    """
    Function will remove duplicate dict_data from collection
    :type collection: list
    :rtype: list
    """
    seen = set()
    unique_addresses = []
    for dict_data in collection:
        t = tuple(dict_data.items())
        if t not in seen:
            seen.add(t)
            unique_addresses.append(dict_data)
    return unique_addresses


# TODO: complete function logic
def track_updates(user_id, new_data, attribute, existing_candidate_data):
    # Create edit collection for candidate's attribute if it doesn't already exist
    candidate_edits = existing_candidate_data.get('edits')
    if candidate_edits:
        if not candidate_edits.get(attribute):
            candidate_edits[attribute] = []
    else:
        existing_candidate_data['edits'] = {}
        existing_candidate_data['edits'][attribute] = []

    edits = []
    old_data = existing_candidate_data.get(attribute)

    all_changes = DeepDiff(old_data, new_data)

    for field, dict_data in all_changes:
        edits.append(dict(
            attribute=attribute,  # email
            field=field,  # address
            old_value=dict_data['old_value'],  # old@gmail.com
            new_value=dict_data['new_value'],  # new@gmail.com
            user_id=user_id,
            edit_datetime=DatetimeUtils.to_utc_str(datetime.datetime.utcnow())
        ))

    return existing_candidate_data['edits'] + edits
