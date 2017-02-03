"""
This module contains API endpoints for TalentbotAuth table
Author: Kamal Hasan <kamalhasan.qc@gmail.com>
"""
# Standard imports
import types
# App specific imports
from talentbot_service import logger
from talentbot_service.common.utils.handy_functions import get_valid_json_data
from talentbot_service.common.error_handling import InvalidUsage, ForbiddenError, NotFoundError
from talentbot_service.modules.validations import validate_user_id, validate_and_format_request_data_for_sms, \
    validate_and_format_data_for_slack, validate_and_format_request_data_for_facebook, \
    validate_and_format_data_for_email
# Common modules
from talentbot_service.common.utils.api_utils import api_route, ApiResponse
from talentbot_service.common.talent_api import TalentApi
from talentbot_service.common.routes import TalentBotApi
from talentbot_service.common.utils.auth_utils import require_oauth
from talentbot_service.common.models.user import UserPhone, TalentbotAuth
# Third party imports
from flask_restful import Resource
from flask import request
from flask import Blueprint
from contracts import contract

talentbot_blueprint = Blueprint('talentbot_api', __name__)
api = TalentApi()
api.init_app(talentbot_blueprint)
api.route = types.MethodType(api_route, api)


@api.route(TalentBotApi.TALENTBOT_AUTH)
class TalentbotAuthApi(Resource):
    """
    This class contains post endpoint of TalentbotAuth table, which takes data validates it
    and create a record in TalentbotAuth table
    """
    # Access token decorator
    decorators = [require_oauth()]

    def post(self):
        """
        This method takes data to create a talentbot_auth entry in database
        Example:
            {
            "user_id": 5000,
            "sms": {
                    "user_phone_id": 7
            },
            "slack": {
                        "access_token": "xoxp-XXXXXXXX-XXXXXXXX-XXXXX",
                        "scope": "incoming-webhook,commands,bot",
                        "team_name": "Team Installing Your Hook",
                        "team_id": "XXXXXXXXXX",
                        "incoming_webhook": {
                                "url": "https://hooks.slack.com/TXXXXX/BXXXXX/XXXXXXXXXX",
                                "channel": "#channel-it-will-post-to",
                                "configuration_url": "https://teamname.slack.com/services/BXXXXX"
                                },
                        "bot":{
                            "bot_user_id":"UTTTTTTTTTTR",
                            "bot_access_token":"xoxb-XXXXXXXXXXXX-TTTTTTTTTTTTTT"
                        }
                    },
            "facebook": {
                "facebook_user_id": "18174932627987"
            },
            "email":{
                "email": "kamalhasan.qc@gmail.com"
            }
        }

        headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }
        .. Response::

            {
               "id": 30
            }
        """
        data = get_valid_json_data(request)
        validate_user_id(data)
        user_id = data['user_id']
        is_facebook, is_slack, is_sms, is_email = data.get("facebook"), data.get("slack"), data.get("sms"),\
                                                  data.get("email")
        formatted_data = {"user_id": user_id}
        if is_sms:
            formatted_data.update(validate_and_format_request_data_for_sms(data['sms']))
        if is_facebook:
            formatted_data.update(validate_and_format_request_data_for_facebook(data['facebook']))
        if is_email:
            formatted_data.update(validate_and_format_data_for_email(data['email']))
        if is_slack:
            formatted_data.update(validate_and_format_data_for_slack(data['slack']))
        user_phone = formatted_data.get('user_phone')
        user_phone_id = formatted_data.get('user_phone_id')
        if user_phone:
            # TODO: Use API for adding phone
            # response = send_request('put', UserServiceApiUrl.USER % user_id, request.headers.get('AUTHORIZATION'),
            #                         data={"phone": user_phone})
            # if not response.ok:
            #     raise InternalServerError("Something went wrong while adding user_phone")
            # phone_object = UserPhone.get_by_phone_value(user_phone)

            phone_object = UserPhone(user_id=user_id, value=user_phone, phone_label_id=6)
            phone_object.save()
            if phone_object:
                del formatted_data["user_phone"]
                formatted_data.update({"user_phone_id": phone_object.id})
                return save_talentbot_auth(formatted_data)
        elif user_phone_id:
            requested_phone = UserPhone.get_by_id(user_phone_id) if user_phone_id else None
            if not requested_phone:
                raise NotFoundError("Either user_phone_id is not provided or user_phone doesn't exist")
            return save_talentbot_auth(formatted_data)
        logger.error("Error occurred while adding talentbot_auth data: %s" % data)
        return ApiResponse({"error": {"message": "Something went wrong while adding talentbot auth"}}, status=500)


@api.route(TalentBotApi.TALENTBOT_AUTH_BY_ID)
class TalentbotAuthById(Resource):
    """
    This class contains put, get and delete endpoints
    """
    decorators = [require_oauth()]

    def put(self, **kwargs):
        """
        This method takes data validates it and update in database
        Example:
            {
                "user_id": 5000,
                "sms":{
                    "user_phone_id": 9
                }
            }
        headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }
        .. Response::

            {
                "user_id": 5000,
                "sms":{
                    "user_phone_id": 9
                }
            }

        """
        data = get_valid_json_data(request)
        _id = kwargs.get('id')
        check_if_auth_exists(_id)
        validate_user_id(data)
        user_id = data.get('user_id')  # Required
        is_sms = data.get('sms')
        updated_dict = {}
        if is_sms:
            user_phone_id = is_sms.get("user_phone_id")  # Required
            if not user_phone_id:
                raise InvalidUsage("Please provide user_phone_id it is a required field")
            if not isinstance(user_phone_id, (int, long)):
                raise InvalidUsage("Invalid user_phone_id type")
            requested_phone = UserPhone.get_by_id(user_phone_id)
            if not requested_phone:
                raise NotFoundError("user_phone doesn't exist against given user_phone_id")
            updated_dict.update({
                "user_id": user_id,
                "user_phone_id": user_phone_id
            })
        TalentbotAuth.query.filter(TalentbotAuth.id == _id).update(updated_dict)
        return ApiResponse(data)

    def get(self, **kwargs):
        """
        The method returns record against id
        Example:
            make a get request to /v1/auth/30[GET]

            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }
        .. Response
            {
                "user_id": 5000,
                "facebook_user_id": "18174932627987",
                "id": 2,
                "slack_team_name": null,
                "user_phone_id": 7,
                "slack_user_id": null,
                "email": "kamalhasan.qc@gmail.com"
            }
        """
        # Checking if user has permission to delete specific record
        _id = kwargs.get('id')
        requested_auth_object = check_if_auth_exists(_id)
        if requested_auth_object.user_id == request.user.id or request.user.role.id == 2:
            requested_auth_object = check_if_auth_exists(_id)
            return ApiResponse(requested_auth_object.__str__())
        raise ForbiddenError("You don't have permission to view this record")

    def delete(self, **kwargs):
        """
        The method deletes record against id
        Example:
            make a get request to /v1/auth/30[DELETE]

            headers = {
                        'Authorization': 'Bearer <access_token>',
                        'Content-Type': 'application/json'
                       }
        .. Response
            {
                "talentbot_auth_id": 2
            }
        """
        # Checking if user has permission to delete specific record
        _id = kwargs.get('id')
        requested_auth_object = check_if_auth_exists(_id)
        if requested_auth_object.user_id == request.user.id or request.user.role.id == 2:
            TalentbotAuth.remove(requested_auth_object)
            return ApiResponse({"talentbot_auth_id": requested_auth_object.id})
        raise ForbiddenError("You don't have permission to delete this record")


@contract
def save_talentbot_auth(kwargs):
    """
    This method takes dict object of TalentbotAuth and saves in database
    :param dict kwargs: TalentbotAuth dict object
    :rtype: type (y)
    """
    try:
        auth = TalentbotAuth(**kwargs)
        response_object = auth.save()
        return ApiResponse({"id": response_object.id})
    except Exception as error:
        logger.error("Error occurred while saving talentbot auth Error: %s" % error.message)
        return ApiResponse({"error": {"message": "Oops! something went wrong while saving talentbot auth"}}, status=500)


@contract
def check_if_auth_exists(_id):
    """
    This method checks if a record exists in TalentbotAuth table against an id
    :param int|long _id: TalentbotAuth id
    :rtype: type (x)
    """
    requested_auth_object = TalentbotAuth.get_by_id(_id) if id else None
    if not requested_auth_object:
        raise NotFoundError("Either talentbot_auth_id is not provided or doesn't exist")
    return requested_auth_object
