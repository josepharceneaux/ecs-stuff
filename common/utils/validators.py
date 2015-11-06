import re
from common.error_handling import *


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def is_valid_email(email):
    """
    According to: http://www.w3.org/TR/html5/forms.html#valid-e-mail-address

    :type email: str
    """
    regex = """^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"""
    return email and re.match(regex, email)


def format_phone_number(phone_number):
    """
    Format US/Canada phone numbers in +1 (123) 456-7899 format
    :return: Formatted phone numbers
    :rtype: str
    """
    import phonenumbers
    try:
        parsed_phone_numbers = phonenumbers.parse(str(phone_number), region="US")
        if phonenumbers.is_valid_number_for_region(parsed_phone_numbers, 'US'):
            # Phone number format is : +1 (123) 456-7899
            return '+1 ' + phonenumbers.format_number(parsed_phone_numbers, phonenumbers.PhoneNumberFormat.NATIONAL)
        else:
            raise InvalidUsage(error_message="[%s] is an invalid or non-US/Canada Phone Number" % phone_number)
    except:
        raise InvalidUsage("[%s] is an invalid or non-US/Canada Phone Number" % phone_number)


def sanitize_zip_code(zip_code):
    """
    :param zip_code:
    :return:
    """
    zip_code = str(zip_code)
    zip_code = ''.join(filter(lambda character: character not in ' -', zip_code))
    if zip_code and not ''.join(filter(lambda character: not character.isdigit(), zip_code)):
        zip_code = zip_code.zfill(5) if len(zip_code) <= 5 else zip_code.zfill(9) if len(zip_code) <= 9 else ''
        if zip_code:
            return (zip_code[:5] + ' ' + zip_code[5:]).strip()
    # logger.info("[%s] is not a valid US Zip Code", zip_code)
    return None

