"""Misc functions that have no logical grouping to a module."""
__author__ = 'erikfarmer'

import re
import random
import string
<<<<<<< HEAD
from ..models.user import User, UserScopedRoles
from itertools import izip_longest
=======
from ..models.user import User, UserScopedRoles, DomainRole
>>>>>>> 3d5fd167d33af41992032f17745daedc3bbb1938


def random_word(length):
    """Creates a random lowercase string, usefull for testing data."""
    return ''.join(random.choice(string.lowercase) for i in xrange(length))


def random_letter_digit_string(size=6, chars=string.lowercase + string.digits):
    """Creates a random string of lowercase/uppercase letter and digits."""
    return ''.join(random.choice(chars) for _ in range(size))


def add_role_to_test_user(test_user, role_names):
    """
    This function will add roles to a test_user just for testing purpose
    :param User test_user: User object
    :param list[str] role_names: List of role names
    :return:
    """
    for role_name in role_names:
        if not DomainRole.get_by_name(role_name):
            DomainRole.save(role_name)
    UserScopedRoles.add_roles(test_user, role_names)


def camel_case_to_snake_case(name):
    """ Convert camel case to underscore case
        socialNetworkId --> social_network_id

            :Example:

                result = camel_case_to_snake_case('socialNetworkId')
                assert result == 'social_network_id'

    """
    # name_ = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    # return re.sub('([a-z0-9])([A-Z0-9])', r'\1_\2', name_).lower()
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    name = re.sub('(.)([0-9]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def grouper(iterable, group_size, fillvalue=None):
    """
    Collect data into fixed-length chunks or blocks
    i.e grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    :param iterable: Iterable item for 'chunking'.
    :param group_size: How many items should be in a group.
    :param fillvalue: Optional arg to fill chunks that are less than the defined group size.
    :return type: itertools.izip_longest
    """
    args = [iter(iterable)] * group_size
    return izip_longest(*args, fillvalue=fillvalue)
