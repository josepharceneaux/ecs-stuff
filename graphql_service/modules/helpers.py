"""
Common/helper functions
"""


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
