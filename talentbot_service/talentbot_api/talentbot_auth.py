# Standard imports
import types
# App specific imports
from talentbot_service.modules.validations import validate_user_id, validate_and_format_request_data_for_sms, validate_and_format_data_for_slack, validate_and_format_request_data_for_facebook, validate_and_format_data_for_email
# Common modules
from talentbot_service.common.utils.api_utils import api_route, ApiResponse
from talentbot_service.common.talent_api import TalentApi
from talentbot_service.common.routes import TalentBotApi, UserServiceApiUrl
from talentbot_service.common.utils.auth_utils import require_oauth, InternalServerError, NotFoundError
from talentbot_service.common.utils.handy_functions import send_request
from talentbot_service.common.models.user import UserPhone, TalentbotAuth, User
# Third party imports
from flask_restful import Resource
from flask import request
from flask import Blueprint

talentbot_blueprint = Blueprint('talentbot_api', __name__)
api = TalentApi()
api.init_app(talentbot_blueprint)
api.route = types.MethodType(api_route, api)

# TODO: This api only works for SMS endpoint related data for now


@api.route(TalentBotApi.TALENTBOT_AUTHS)
class TalentbotAuthApi(Resource):

    # Access token decorator
    decorators = [require_oauth()]

    def post(self):
        data = request.get_json()
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
                return save_talentbot_auth(formatted_data)
        elif user_phone_id:
            requested_phone = UserPhone.get_by_id(user_phone_id) if user_phone_id else None
            if not requested_phone:
                raise NotFoundError("Either user_phone_id is not provided or user_phone doesn't exist")
            return save_talentbot_auth(formatted_data)
        raise InternalServerError("Something went wrong while adding talentbot auth")


@api.route(TalentBotApi.TALENTBOT_AUTH)
class TalentbotAuthById(Resource):

    decorators = [require_oauth()]

    def put(self, **kwargs):
        _id = kwargs.get('id')
        check_if_auth_exists(_id)
        data = request.get_json()
        user_id = data.get('user_id')  # Required
        requested_user = User.query.get(user_id) if user_id else None
        if not requested_user:
            raise NotFoundError("Either user_id is not provided or user doesn't exist")
        user_phone_id = data.get('user_phone_id')
        requested_phone = UserPhone.get_by_id(user_phone_id) if user_phone_id else None
        if not requested_phone:
            raise NotFoundError("Either user_phone_id is not provided or user_phone doesn't exist")
        updated_dict = {
            "user_id": user_id,
            "user_phone_id": user_phone_id
        }
        TalentbotAuth.query.filter(TalentbotAuth.id == _id).update(updated_dict)
        return ApiResponse(updated_dict)

    def get(self, **kwargs):
        _id = kwargs.get('id')
        requested_auth_object = check_if_auth_exists(_id)
        return ApiResponse(requested_auth_object.__str__())

    def delete(self, **kwargs):
        _id = kwargs.get('id')
        requested_auth_object = check_if_auth_exists(_id)
        TalentbotAuth.remove(requested_auth_object)
        return ApiResponse({"talentbot_auth_id": requested_auth_object.id})


def save_talentbot_auth(kwargs):
    auth = TalentbotAuth(**kwargs)
    auth.save()
    return ApiResponse(kwargs)


def check_if_auth_exists(_id):
    requested_auth_object = TalentbotAuth.get_by_id(_id) if id else None
    if not requested_auth_object:
        raise NotFoundError("Either talentbot_auth_id is not provided or doesn't exist")
    return requested_auth_object
