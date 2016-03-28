"""Various misc validators"""
# Standard Imports
import re

# Third Party
import phonenumbers
import pycountry

# Application Specific
from ..error_handling import InvalidUsage


def is_number(s):
    try:
        float(s)
        return True
    except Exception:
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
        # Maybe the number is already internationally formatted
        try:
            parsed_phone_number = phonenumbers.parse(str(phone_number))
            formatted_number = phonenumbers.format_number(parsed_phone_number, phonenumbers.PhoneNumberFormat.E164)
            return dict(formatted_number=formatted_number, extension=parsed_phone_number.extension)
        except phonenumbers.NumberParseException:
            pass

        # Maybe the country_code is correct
        try:
            parsed_phone_number = phonenumbers.parse(str(phone_number), region=country_code)
            formatted_number = phonenumbers.format_number(parsed_phone_number, phonenumbers.PhoneNumberFormat.E164)

            return dict(formatted_number=str(formatted_number), extension=parsed_phone_number.extension)
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
    zip_code = ''.join([char for char in zip_code if char not in ' -'])
    if zip_code and not ''.join([char for char in zip_code if not char.isdigit()]):
        zip_code = zip_code.zfill(5) if len(zip_code) <= 5 else zip_code.zfill(9) if len(zip_code) <= 9 else ''
        if zip_code:
            return (zip_code[:5] + ' ' + zip_code[5:]).strip()
    # logger.info("[%s] is not a valid US Zip Code", zip_code)
    return None


def is_valid_url_format(url):
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


def parse_openweb_date(openweb_date):
    """
    :param openweb_date:
    :return: datetime.date | None
    """
    from datetime import date

    date_obj = None
    if isinstance(openweb_date, basestring):
        try:  # If string, try to parse as ISO 8601
            import dateutil.parser

            date_obj = dateutil.parser.parse(openweb_date)
        except ValueError:
            date_obj = None
        if not date_obj:  # If fails, try to convert to int
            try:
                openweb_date = int(openweb_date) or None  # Sometimes the openweb_date is "0", which is invalid
            except ValueError:
                date_obj = None

    if not date_obj and isinstance(openweb_date, int):  # If still not found, parse it as an int
        try:
            date_obj = date.fromtimestamp(openweb_date / 1000)
        except ValueError:
            date_obj = None

    if date_obj and (date_obj.year > date.today().year + 2):  # Filters out any year 2 more than the current year
        date_obj = None

    if date_obj and (date_obj.year == 1970):  # Sometimes, it can't parse out the year so puts 1970, just for the hell of it
        date_obj = None

    return date_obj


def is_country_code_valid(country_code):
    """
    Checks to see if country-code is a valid country code per ISO-3166 standards
    """
    try:
        pycountry.countries.get(alpha2=country_code.upper())
    except KeyError:
        return False
    return True


def raise_if_not_instance_of(obj, instances, exception=InvalidUsage):
    """
    This validates that given object is an instance of given instance. If it is not, it raises
    the given exception.
    :param obj: obj e,g. User object
    :param instances: Class for which given object is expected to be an instance.
    :param exception: Exception to be raised
    :type obj: object
    :type instances: class
    :type exception: Exception
    :exception: Invalid Usage
    """
    if not isinstance(obj, instances):
        given_obj_name = dict(obj=obj).keys()[0]
        error_message = '%s must be an instance of %s.' % (given_obj_name, '%s')
        if isinstance(instances, (list, tuple)):
            raise exception(error_message % ", ".join([instance.__name__
                                                       for instance in instances]))
        else:
            raise exception(error_message % instances.__name__)