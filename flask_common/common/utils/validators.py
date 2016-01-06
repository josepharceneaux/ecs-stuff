import re
from ..error_handling import *

# Third Part Imports
from dateutil.parser import parse
from pytz import timezone


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


def format_phone_number(phone_number, country_code='US'):
    """
    Format US/Canada phone numbers in +1 (123) 456-7899 format
    :return: {"formatted_number": "+118006952635" , "extension": "165"}
    :rtype: dict
    """
    try:
        import phonenumbers

        # Maybe the number is already internationally formatted
        try:
            parsed_phone_number = phonenumbers.parse(str(phone_number))
            formatted_number = phonenumbers.format_number(parsed_phone_number, phonenumbers.PhoneNumberFormat.E164)
            return formatted_number
        except phonenumbers.NumberParseException:
            pass

        # Maybe the country_code is correct
        try:
            parsed_phone_number = phonenumbers.parse(str(phone_number), region=country_code)
            formatted_number = phonenumbers.format_number(parsed_phone_number, phonenumbers.PhoneNumberFormat.E164)
            return dict(formatted_number=formatted_number, extension=parsed_phone_number.extension)
        except phonenumbers.NumberParseException:
            raise InvalidUsage(error_message="format_phone_number(%s, %s): Couldn't parse phone number" %
                                             (phone_number, country_code))
    except:
        raise InvalidUsage(error_message="format_phone_number(%s, %s): Received other exception" %
                                         (phone_number, country_code))


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


def get_valid_data(data, key):
    """
    Methods to Check if key exist and returns associated value
    :param data: json data with keyvalue pair
    :param key: key to check if missing or invalid value
    :return: value of associated key
    """
    try:
        value = data[key]
    except KeyError:
        raise InvalidUsage(error_message="Missing key: %s" % key)
    return value


def get_valid_datetime(data, key):
    """
    Check if datetime is valid, if no, then raise invalid value exception
    """
    value = get_valid_data(data, key)
    try:
        value = parse(value).replace(tzinfo=timezone('UTC'))
    except Exception:
        raise InvalidUsage(
            error_message="Invalid value of %s %s. %s should be in datetime format" % (key, value, key))
    return value


def get_valid_integer(data, key):
    """
    Check if integer is valid, if no, then raise invalid value exception
    """
    value = get_valid_data(data, key)
    if not str(value).isdigit():
        raise InvalidUsage(error_message='Invalid value of %s. It should be integer' % key)
    return value


def get_valid_url(data, key):
    """
    Check if url is valid, if no, then raise invalid value exception
    """
    value = get_valid_data(data, key)
    if not is_valid_url(value):
        raise InvalidUsage(error_message='Invalid value of %s.' % key)
    return value


def is_valid_url(url):
    """
    Reference: https://github.com/django/django-old/blob/1.3.X/django/core/validators.py#L42
    """
    regex = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url is not None and regex.search(url)

