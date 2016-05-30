"""Various misc validators"""
# Standard Imports
import re

# Third Party
import phonenumbers
from phonenumbers.phonenumber import PhoneNumber
import pycountry
from jsonschema import validate, FormatChecker, ValidationError

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


def get_phone_number_extension_if_exists(phone_number):
    """
    Function will extract & return phone-number, extension prefix, and extension-number if an extension is provided
    :return: phone number, extension-prefix & extension number; e.g. ('4084059934', 'ext', '45') | (None, None, None)
    :rtype:  tuple
    """
    # TODO: compile regex at application startup
    # Link from where regex was copied:
    #   https://www.quora.com/What-is-the-best-way-to-parse-and-standardize-phone-numbers-in-Python?share=1
    matched = re.match(r'([^a-zA-Z]+)([a-zA-Z]+\D*)(\d+)', phone_number)
    return matched.groups() if matched else (None, None, None)


def parse_phone_number(phone_number, iso3166_country_code=None):
    """
    Function will parse phone number. If phone number does not have country code, it will look for
      provided iso3166_country_code. If iso3166_country_code is not provided it will save phone number
      as provided. InvalidUsage will be raised if phone number is not properly formatted or is invalid
    :type phone_number:  str
    :param phone_number: +14084056677 | 4084056677 | 4084056677ext456 (must be at least 7 digits long)
    :type iso3166_country_code:  str
    :param iso3166_country_code:  Alpha-2 code per ISO 3166 standards
    :rtype:  PhoneNumber
    :return  PhoneNumber(country_code=1, national_number=4084056677, extension=None,
                         italian_leading_zero=None, number_of_leading_zeros=None, country_code_source=None,
                         preferred_domestic_carrier_code=None)
    """
    try:  # Maybe the number is already internationally formatted
        return phonenumbers.parse(str(phone_number))
    except phonenumbers.NumberParseException:
        pass

    if iso3166_country_code:
        try:  # Maybe the country_code is correct
            return phonenumbers.parse(number=str(phone_number), region=iso3166_country_code.upper())
        except phonenumbers.NumberParseException:
            raise InvalidUsage(error_message="format_phone_number({}, {}): Couldn't parse phone number".
                               format(phone_number, iso3166_country_code))

    # If phone number contains an extension, it must be parsed
    number, extension_prefix, extension_value = get_phone_number_extension_if_exists(phone_number)

    # Phone number is considered invalid if it's less than 7 digits; see:
    #   http://stackoverflow.com/questions/14894899/what-is-the-minimum-length-of-a-valid-international-phone-number
    if number:
        number = re.sub('\D', '', number)  # Number must contain only digits
        if len(number) < 7:
            raise InvalidUsage("Invalid phone number: {}".format(number))

    phone_number = re.sub('\D', '', phone_number)  # Number must contain only digits
    if len(phone_number) < 7:
        raise InvalidUsage("Invalid phone number: {}".format(number))

    # If phone number is not prefixed with international code and country_code is not provided
    #    it will be saved as-is unless if phone number is invalid, e.g. "letter56"
    try:
        return PhoneNumber(national_number=number or phone_number, extension=extension_value)
    except ValueError:
        raise InvalidUsage("Invalid phone number: {}".format(phone_number))


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


def validate_and_return_immutable_value(is_immutable):
    """
    This function validates the is_immutable value that came from user's end to make sure
    that it is either 0 or 1. Raises in-valid usage exception if other value is received.
    :param is_immutable: Value for is_immutable that came from user's end and needs to be validated.
    :return value of is_immutable after validating it
    """

    if (is_immutable is None) or str(is_immutable) not in ('0', '1'):
        raise InvalidUsage(error_message='Invalid input: is_immutable should be integer with value 0 or 1')
    else:
        return is_immutable


def is_country_code_valid(country_code):
    """
    Checks to see if country-code is a valid country code per ISO-3166 standards
    :param country_code: must be ALL CAPS Alpha2 iso3166 country code, e.g. "US"
    """
    try:
        pycountry.countries.get(alpha2=country_code)
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


def get_json_if_exist(_request):
    """ Function will ensure data's content-type is JSON, and it isn't empty
    :type _request:  request
    """
    if "application/json" not in _request.content_type:
        raise InvalidUsage("Request body must be a JSON object")
    if not _request.get_data():
        raise InvalidUsage("Request body cannot be empty")
    return _request.get_json()


def get_json_data_if_validated(request_body, json_schema, format_checker=True):
    """
    Function will compare requested json data with provided json schema
    :type request_body:  request
    :type json_schema:  dict
    :param format_checker:  If True, specified formats will need to be validated, e.g. datetime
    :return:  JSON data if validation passes
    """
    try:
        body_dict = get_json_if_exist(request_body)
        if format_checker:
            validate(instance=body_dict, schema=json_schema, format_checker=FormatChecker())
        else:
            validate(instance=body_dict, schema=json_schema)
    except ValidationError as e:
        raise InvalidUsage('JSON schema validation error: {}'.format(e))
    return body_dict
