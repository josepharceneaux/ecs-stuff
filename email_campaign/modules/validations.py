from email_campaign.common.models.db import db
from email_campaign.common.models.smart_list import SmartList
from email_campaign.common.models.user import User
from email_campaign.common.error_handling import InvalidUsage, UnprocessableEntity
__author__ = 'jitesh'


def validate_and_format_request_data(data):
    """
    Validates the request form data and returns the formatted data with leading and trailing
    white spaces stripped.
    :param data: request.form
    :return: Dictionary of formatted data with trimmed whitespaces
    :rtype: dict
    """
    campaign_name = data.get('email_campaign_name')  # required
    email_subject = data.get('email_subject')        # required
    email_from = data.get('email_from')              # required
    reply_to = data.get('email_reply_to')
    email_body_html = data.get('email_body_html')    # required
    email_body_text = data.get('email_body_text')
    list_ids = data.get('list_ids')                  # required
    email_client_id = data.get('email_client_id')
    send_time = data.get('send_time')
    stop_time = data.get('stop_time')
    frequency = data.get('frequency')

    # Raise errors if invalid input
    if campaign_name is None or campaign_name.strip() == '':
        raise InvalidUsage('email_campaign_name is required')  # 400 Bad request
    if email_subject is None or email_subject.strip() == '':
        raise InvalidUsage('email_subject is required')
    if email_from is None or email_from.strip() == '':
        raise InvalidUsage('email_from is required')
    if email_body_html is None or email_body_html.strip() == '':
        raise InvalidUsage('email_body_html is required')
    if list_ids is None or list_ids.strip() == '':
        raise InvalidUsage('list_ids are required to send email campaigns')

    # TODO: Validate send_time & stop time

    # If frequency is there then there must be a send time
    if frequency is not None and send_time is None:
        # 422 - Unprocessable Entity. Server understands the request but cannot process
        # because along with frequency it needs send time.
        # https://tools.ietf.org/html/rfc4918#section-11.2
        # 400 or 422? Will decide it later.
        raise UnprocessableEntity("Frequency requires send time.")

    # strip whitespaces and return data
    return {'campaign_name': campaign_name.strip() if campaign_name else campaign_name,
            'email_subject': email_subject.strip() if email_subject else email_subject,
            'email_from': email_from.strip() if email_from else email_from,
            'reply_to': reply_to.strip() if reply_to else reply_to,
            'email_body_html': email_body_html.strip() if email_body_html else email_body_html,
            'email_body_text': email_body_text.strip() if email_body_text else email_body_text,
            'list_ids': list_ids.strip() if list_ids else list_ids,
            'email_client_id': email_client_id.strip() if email_client_id else email_client_id,
            'send_time': send_time.strip() if send_time else send_time,
            'stop_time': stop_time.strip() if stop_time else stop_time,
            'frequency': frequency.strip() if frequency else frequency,
            }


def validate_lists_belongs_to_domain(list_ids, user_id):
    """
    Validates if list ids belongs to user's domain
    :param list_ids:
    :param user_id:
    :return:False, if any of list given not belongs to current user domain else True
    """
    user = User.query.get(user_id)
    smart_lists = db.session.query(SmartList.id).join(User, SmartList.user_id == User.id).filter(
        User.domain_id == user.domain_id).all()

    smart_list_ids = [smart_list[0] for smart_list in smart_lists]
    result_of_list_belong_domain = set(list_ids) - set(smart_list_ids)
    if len(result_of_list_belong_domain) == 0:
        return True
    return False


def validate_inputs(campaign_name, email_subject, email_from, email_body_html, list_ids, frequency, send_time):
    if not campaign_name:
        raise InvalidUsage('email_campaign_name is a required field')  # 400 Bad request
    # If frequency is there then there must be a send time
    if frequency is not None and send_time is None:
        # 422 - Unprocessable Entity. Server understands the request but cannot process
        # because along with frequency it needs send time.
        # https://tools.ietf.org/html/rfc4918#section-11.2
        # 400 or 422? Will decide it later.
        raise UnprocessableEntity("Frequency requires send time.")