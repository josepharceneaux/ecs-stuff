"""
Miscellaneous utility functions for Candidate service
"""
__author__ = 'scotland@gettalent.com'


def get_candidate_name(first_name, last_name, formatted_name):
    """
    Attempts to return best possible name option
    :param first_name: str
    :param last_name: str
    :param formatted_name: str
    :rtype: str
    """
    if formatted_name:
        return formatted_name
    if first_name and last_name:
        return first_name + ' ' + last_name
    if first_name:
        return first_name
    return 'Unknown'
