from talentbot_service import logger
from talentbot_service.common.error_handling import InvalidUsage, InternalServerError
from talentbot_service.common.models.user import UserPhone, TalentbotAuth


def validate_and_format_request_data_for_sms(data):
    """
    Validates and formats request data related to SMS
    :param dict data: Request data
    :return: dictionary of formatted data
    :rtype: dict
    """
    user_id = data.get('user_id')  # Required
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
        tb_auth = TalentbotAuth.get_talentbot_auth(user_phone_id=user_phone_id)
        if tb_auth:
            raise InvalidUsage("user_phone_id is already being used")
    formatted_dict = {
        "user_id": user_id
    }
    formatted_dict.update({"user_phone": user_phone.strip()} if user_phone else {"user_phone_id": user_phone_id})
    return formatted_dict


def validate_and_format_request_data_for_facebook(data):
    """
    Validates and formats request data related to Facebook
    :param data:
    :return:
    """
    user_id = data.get('user_id')  # Required
    facebook_user_id = data.get('facebook_user_id')
    if not facebook_user_id:
        raise InvalidUsage("No facebook_user_id provided")
    return {
        "user_id": user_id,
        "facebook_user_id": facebook_user_id.strip()
    }


def validate_and_format_data_for_slack(data):
    access_token = data.get('access_token')  # Required
    team_id = data.get('team_id')  # Required
    team_name = data.get('team_name')  # Required
    slack_user_id = data.get('user_id')  # Required
    bot_id = data.get('bot').get('bot_user_id') if data.get('bot') else None  # Required
    bot_token = data.get('bot').get('bot_access_token') if data.get('bot') else None  # Required

    dict_of_request_data = {
        "access_token": access_token,
        "team_id": team_id,
        "team_name": team_name,
        "slack_user_id": slack_user_id,
        "bot_id": bot_id,
        "bot_token": bot_token
    }

    auth_entry = TalentbotAuth.query.filter_by(slack_user_id=slack_user_id).first() if slack_user_id else None

    if auth_entry:
        raise InvalidUsage("Slack_user_id already exists")
    if not (access_token and team_id and team_name and bot_id and slack_user_id and bot_token):
        raise InvalidUsage("Please provide these required fields %s" % [key for key in dict_of_request_data if
                                                                        dict_of_request_data[key] is None])
    for key in dict_of_request_data:
        dict_of_request_data[key] = dict_of_request_data[key].strip()
    return dict_of_request_data


def validate_and_format_data_for_email(data):
    email = data.get("email")
    if not email:
        raise InvalidUsage("No email specified")
    return {
        "email": email.strip()
    }


def validate_user_id(data):
    user_id = data.get('user_id')
    if not user_id:
        raise InvalidUsage("user_id is a required field")
    if not isinstance(user_id, (int, long)):
        raise InvalidUsage("Invalid user_id type")


def validate_and_prepare_post_data(data):
    post_data = {}
    at_least_1_endpoint_data_available = False
    validate_user_id(data)
    post_data.update({"user_id": data['user_id']})
    try:
        post_data.update(validate_and_format_request_data_for_sms(data))
        at_least_1_endpoint_data_available = True
    except Exception as  error:
        logger.info("SMS data doesn't exist")

    try:
        post_data.update(validate_and_format_request_data_for_facebook(data))
        at_least_1_endpoint_data_available = True
    except Exception as  error:
        logger.info("Facebook data doesn't exist")

    try:
        post_data.update(validate_and_format_data_for_email(data))
        at_least_1_endpoint_data_available = True
    except Exception as  error:
        logger.info("Email data doesn't exist")

    try:
        post_data.update(validate_and_format_data_for_slack(data))
        at_least_1_endpoint_data_available = True
    except Exception as  error:
        logger.info("Slack data doesn't exist")

    if at_least_1_endpoint_data_available:
        return post_data
    raise InvalidUsage("No valid data found, make sure the types are correct and data doesn't already exist")
