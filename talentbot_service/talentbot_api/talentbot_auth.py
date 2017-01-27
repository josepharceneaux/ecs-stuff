# Standard imports
import types
# App specific imports
from talentbot_service.modules.validations import validate_and_format_request_data_for_sms
# Common modules
from talentbot_service.common.utils.api_utils import api_route
from talentbot_service.common.talent_api import TalentApi
from talentbot_service.common.routes import TalentBotApi, UserServiceApiUrl
from talentbot_service.common.utils.auth_utils import require_oauth, InternalServerError
from talentbot_service.common.utils.handy_functions import http_request
from talentbot_service.common.models.user import UserPhone, db, TalentbotAuth
# Third party imports
from flask_restful import Resource
from flask import request
from flask import Blueprint

talentbot_blueprint = Blueprint('talentbot_api', __name__)
api = TalentApi()
api.init_app(talentbot_blueprint)
api.route = types.MethodType(api_route, api)


@api.route(TalentBotApi.TALENTBOT_AUTH)
class TalentbotAuthApi(Resource):

    # Access token decorator
    decorators = [require_oauth()]

    def post(self):
        data = request.get_json()
        formatted_data = validate_and_format_request_data_for_sms(data)
        user_id = formatted_data['user_id']
        user_phone = formatted_data.get('user_phone')
        user_phone_id = formatted_data.get('user_phone_id')
        if user_phone:
            response = http_request('put', UserServiceApiUrl.USER % user_id, headers=request.headers,
                                    data={"phone": user_phone})
            if not response.ok:
                raise InternalServerError("Something went wrong while adding user_phone")
            db.session.commit()
            phone_object = UserPhone.get_by_phone_value(user_phone)
            if phone_object:
                return save_talentbot_auth(phone_object.id, user_id)
        elif user_phone_id:
            return save_talentbot_auth(user_phone_id, user_id)
        raise InternalServerError("Something went wrong while adding talentbot auth")


def save_talentbot_auth(phone_id, user_id):
    auth = TalentbotAuth(user_phone_id=phone_id, user_id=user_id)
    auth.save()
    return {"talentbot_auth": auth}
