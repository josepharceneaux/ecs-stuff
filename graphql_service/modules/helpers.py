"""
Common/helper functions
"""
import datetime
from deepdiff import DeepDiff
from graphql_service.common.utils.datetime_utils import DatetimeUtils


def clean(value):
    """
    :rtype: str
    """
    return (value or '').strip()


# todo: unit test this
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


class Diff(object):
    def __init__(self, attribute, existing_data, new_data, user_id, updated_datetime):
        self.attribute = attribute
        self.existing_data = existing_data
        self.new_data = new_data
        self.user_id = user_id
        self.updated_datetime = updated_datetime
        self.changed = dict()

    def find_diffs(self):
        if self.attribute.lower() == 'primary_data':
            err_msg = "{} must be of type dict".format(self.attribute)
            assert isinstance(self.existing_data, dict) and isinstance(self.new_data, dict), err_msg

            # self.changed[self.attribute] = {}

            for k, v in self.existing_data.iteritems():
                if self.new_data.get(k) and self.new_data[k] != v:
                    self.changed[k] = {}
                    self.changed[k]['old_value'] = v
                    self.changed[k]['new_value'] = self.new_data[k]
                    self.changed[k]['user_id'] = self.user_id
                    self.changed[k]['updated_datetime'] = self.updated_datetime
                else:
                    continue
            return self.changed
        else:
            err_msg = "{} must be of type list".format(self.attribute)
            assert isinstance(self.existing_data, list) and isinstance(self.new_data, list), err_msg

            self.changed[self.attribute] = []

            for index, item in enumerate(self.existing_data):
                for k, v in item.iteritems():
                    if self.new_data[index][k] != v:
                        self.changed[self.attribute].append({k: {}})
                        self.changed[self.attribute][index][k]['old_value'] = v
                        self.changed[self.attribute][index][k]['new_value'] = self.new_data[index][k]
            return self.changed


def track_updates(user_id, attribute, existing_data, new_data, updated_datetime):

    changed_data = Diff(
        attribute=attribute, existing_data=existing_data,
        new_data=new_data, user_id=user_id, updated_datetime=updated_datetime
    ).find_diffs()

    if isinstance(changed_data, dict):
        pass
        # changed_data.update(dict(user_id=user_id, updated_datetime=updated_datetime))

    elif isinstance(changed_data[attribute], list):
        for index, item in enumerate(changed_data[attribute]):
            changed_data[attribute][index].update(dict(user_id=user_id, updated_datetime=updated_datetime))
    return changed_data
