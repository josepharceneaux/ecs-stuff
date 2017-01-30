from talentbot_service.common.error_handling import InvalidUsage, InternalServerError
from talentbot_service.common.models.user import UserPhone


def validate_and_format_request_data_for_sms(data):
    """
    Validates and formats request data
    :param dict data: Request data
    :return: dictionary of formatted data
    :rtype: dict
    """
    user_id = data.get('user_id')  # Required
    if not user_id:
        raise InvalidUsage("user_id is a required field")
    elif user_id:
        pass
        if not isinstance(user_id, (int, long)):
            raise InvalidUsage("Invalid user_id type")
    user_phone_id = data.get('user_phone_id')
    user_phone = data.get('user_phone')
    if bool(user_phone) == bool(user_phone_id):  # Only one field must exist
        raise InvalidUsage("One field should be provided either user_phone or user_phone_id")
    if user_phone_id:
        if not isinstance(user_phone_id, (int, long)):
            raise InvalidUsage("Invalid user_phone_id type")
        phone = UserPhone.get_by_id(user_phone_id)
        if not phone:
            raise InvalidUsage("No resource found against specified user_phone_id")
    formatted_dict = {
        "user_id": user_id
    }
    formatted_dict.update({"user_phone": user_phone.strip()} if user_phone else {"user_phone_id": user_phone_id})
    return formatted_dict
