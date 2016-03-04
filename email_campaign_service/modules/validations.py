from dateutil.parser import parse
from email_campaign_service.common.models.misc import Frequency
from email_campaign_service.common.models.smartlist import Smartlist
from email_campaign_service.common.models.email_campaign import EmailClient
from email_campaign_service.common.models.user import User
from email_campaign_service.common.error_handling import InvalidUsage, UnprocessableEntity, ForbiddenError
import datetime
__author__ = 'jitesh'


def validate_datetime(datetime_text, field_name=None):
    """
    Validates given datetime string in ISO format
    :param datetime_text: date time
    :type datetime_text: unicode | basestring
    """
    try:
        parsed_date = parse(datetime_text)
    except Exception:
        raise InvalidUsage("%s should be in valid ISO format" % field_name if field_name else 'Datetime')
    if parsed_date < datetime.datetime.utcnow():
        raise InvalidUsage("The %s cannot be before today." % field_name)
    return parsed_date


def validate_and_format_request_data(data, user_id):
    """
    Validates the request form data and returns the formatted data with leading and trailing
    white spaces stripped.
    :param data:
    :return: Dictionary of formatted data
    :rtype: dict
    """
    name = data.get('name')  # required
    subject = data.get('subject')        # required
    _from = data.get('from')
    reply_to = data.get('reply_to')
    body_html = data.get('body_html')    # required
    body_text = data.get('body_text')
    list_ids = data.get('list_ids')                  # required
    email_client_id = data.get('email_client_id')
    start_datetime = data.get('start_datetime')
    end_datetime = data.get('end_datetime')
    frequency_id = data.get('frequency_id')
    template_id = data.get('template_id')

    # Raise errors if invalid input
    if name is None or name.strip() == '':
        raise InvalidUsage('name is required')  # 400 Bad request
    if subject is None or subject.strip() == '':
        raise InvalidUsage('subject is required')
    if body_html is None or body_text.strip() == '':
        raise InvalidUsage('body_html is required')
    if not list_ids:
        raise InvalidUsage('`list_ids` are required to send email campaign')
    if not isinstance(list_ids, list):
        raise InvalidUsage("`list_ids` must be in list format")
    if filter(lambda list_id: not isinstance(list_id, (int, long)), list_ids):
        raise InvalidUsage("`list_ids` should be a list of integers")

    # If frequency is there then there must be a send time
    frequency = Frequency.get_seconds_from_id(frequency_id)
    if frequency and not start_datetime:
        raise UnprocessableEntity("Frequency requires send time.")

    if start_datetime and end_datetime:
        job_send_datetime = validate_datetime(start_datetime, '`send_datetime`')
        job_stop_datetime = validate_datetime(end_datetime, '`stop_datetime`')
        if job_send_datetime > job_stop_datetime:
            raise UnprocessableEntity("`stop_datetime` cannot be before `send_datetime`")

    if email_client_id:
        # Check if email_client_id is valid
        email_client = EmailClient.query.get(email_client_id)
        if not email_client:
            raise InvalidUsage("`email_client_id` is not valid id.")

        # If email_client_id is there then set template_id to None. Why??
        template_id = None

    # Validation for list ids belonging to same domain
    validate_lists_belongs_to_domain(list_ids, user_id)

    # strip whitespaces and return data
    return {
        'name': name.strip(),
        'subject': subject.strip(),
        'from': get_or_set_valid_value(_from, basestring, '').strip(),
        'reply_to': get_or_set_valid_value(reply_to, basestring, '').strip(),
        'body_html': body_html.strip(),
        'body_text': get_or_set_valid_value(body_text, basestring, '').strip(),
        'list_ids': list_ids,
        'email_client_id': email_client_id,
        'start_datetime': start_datetime,
        'end_datetime': end_datetime,
        'frequency_id': frequency_id,
        'template_id': template_id
    }


def validate_lists_belongs_to_domain(list_ids, user_id):
    """
    Validates if list ids belongs to user's domain
    :param list_ids:
    :param user_id:
    :return:False, if any of list given not belongs to current user domain else True
    """
    user = User.query.get(user_id)
    smartlists = Smartlist.query.with_entities(Smartlist.id).join(Smartlist.user).filter(
        User.domain_id == user.domain_id).all()

    smartlist_ids = [smartlist.id for smartlist in smartlists]
    list_ids_not_in_domain = set(list_ids) - set(smartlist_ids)
    if not len(list_ids_not_in_domain) == 0:
        raise ForbiddenError("list ids: %s does not belong to user's domain" % list_ids_not_in_domain)


def get_or_set_valid_value(required_value, required_instance, default):
    """
    This checks if `required_value` is an instance of `required_instance`. If it is, it returns the
    `required_value`, otherwise it sets the `default` value and returns it.
    :param required_value: value to be validated
    :param required_instance: expected instance of `required_value`
    :param default: default value to be set
    """
    if not isinstance(required_value, required_instance):
        required_value = default
    return required_value
