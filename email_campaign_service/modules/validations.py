from email_campaign_service.common.models.misc import Frequency
from email_campaign_service.common.models.smartlist import Smartlist
from email_campaign_service.common.models.email_campaign import EmailClient
from email_campaign_service.common.models.user import User
from email_campaign_service.common.error_handling import InvalidUsage, UnprocessableEntity, ForbiddenError
import datetime
__author__ = 'jitesh'


def validate_datetime(datetime_text, field_name=None):
    """
    Validates given datetime string for desired format YYYY-MM-DD hh:mm:ss
    :param datetime_text: date time
    :type datetime_text: unicode | basestring
    """
    try:
        parsed_date = datetime.datetime.strptime(datetime_text, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        raise InvalidUsage("%s should be in valid format `YYYY-MM-DD hh:mm:ss`" % field_name if field_name else 'Datetime')
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
    campaign_name = data.get('email_campaign_name')  # required
    email_subject = data.get('email_subject')        # required
    email_from = data.get('email_from')
    reply_to = data.get('email_reply_to')
    email_body_html = data.get('email_body_html')    # required
    email_body_text = data.get('email_body_text')
    list_ids = data.get('list_ids')                  # required
    email_client_id = data.get('email_client_id')
    send_datetime = data.get('send_datetime')
    stop_datetime = data.get('stop_datetime')
    frequency_id = data.get('frequency_id')
    template_id = data.get('template_id')

    # Raise errors if invalid input
    if campaign_name is None or campaign_name.strip() == '':
        raise InvalidUsage('email_campaign_name is required')  # 400 Bad request
    if email_subject is None or email_subject.strip() == '':
        raise InvalidUsage('email_subject is required')
    if email_body_html is None or email_body_html.strip() == '':
        raise InvalidUsage('email_body_html is required')
    if not list_ids:
        raise InvalidUsage('`list_ids` are required to send email campaign')
    if not isinstance(list_ids, list):
        raise InvalidUsage("`list_ids` must be in list format")
    if filter(lambda list_id: not isinstance(list_id, (int, long)), list_ids):
        raise InvalidUsage("`list_ids` should be a list of integers")

    # If frequency is there then there must be a send time
    frequency = Frequency.get_seconds_from_id(frequency_id)
    if frequency and not send_datetime:
        raise UnprocessableEntity("Frequency requires send time.")

    if send_datetime and stop_datetime:
        job_send_datetime = validate_datetime(send_datetime, '`send_datetime`')
        job_stop_datetime = validate_datetime(stop_datetime, '`stop_datetime`')
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
        'campaign_name': campaign_name.strip(),
        'email_subject': email_subject.strip(),
        'email_from': get_or_set_valid_value(email_from, basestring, '').strip(),
        'reply_to': get_or_set_valid_value(reply_to, basestring, '').strip(),
        'email_body_html': email_body_html.strip(),
        'email_body_text': get_or_set_valid_value(email_body_text, basestring, '').strip(),
        'list_ids': list_ids,
        'email_client_id': email_client_id,
        'send_datetime': send_datetime,
        'stop_datetime': stop_datetime,
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
