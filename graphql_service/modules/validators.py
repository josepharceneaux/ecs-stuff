"""

"""


def does_address_exist(candidate, address_dict):
    """
    :type address_dict:  dict[str]
    :rtype:  bool
    """
    for address in candidate.addresses:
        address_line_1, address_line_2 = (address.address_line_1 or '').lower(), (address.address_line_2 or '').lower()
        address_dict_address_line_1 = (address_dict.get('address_line_1') or '').lower()
        address_dict_address_line_2 = (address_dict.get('address_line_2') or '').lower()
        if address_line_1 and not address_line_2:
            if address_line_1 == address_dict_address_line_1:
                return True
        elif address_line_1 and address_line_2:
            if address_line_1 == address_dict_address_line_1 and address_line_2 == address_dict_address_line_2:
                return True
    return False
